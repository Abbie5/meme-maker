from PIL import Image, ImageDraw, ImageFont
import os
import pprint
import datetime
from typing import Tuple, List, Dict
import json


pp = pprint.PrettyPrinter(indent=4)
DATE_TIME_FORMAT = "%Y%m%d%H%M%S%f"

COLOURS: Dict[str, Tuple[int, int, int, int]] = {
    "black": (0x00, 0x00, 0x00, 0xFF),
    "white": (0xFF, 0xFF, 0xFF, 0xFF),
    "grey": (0x80, 0x80, 0x80, 0xFF),
    "red": (0xFF, 0x00, 0x00, 0xFF),
    "green": (0x00, 0xFF, 0x00, 0xFF),
    "yellow": (0xFF, 0xFF, 0x00, 0xFF),
    "blue": (0x00, 0x00, 0xFF, 0xFF),
    "magenta": (0xFF, 0x00, 0xFF),
    "pink": (0xFF, 0xC0, 0xCB, 0xFF),
    "cyan": (0x00, 0xFF, 0xFF, 0xFF),
    "none": (0x00, 0x00, 0x00, 0x00),
}


def text_wrap(text: str, font: ImageFont, stroke_width: int, max_width: int) -> str:
    if font.getsize_multiline(text)[0] + 2 * stroke_width <= max_width:
        return text
    else:
        result = ""
        for word in text.split():
            if (
                font.getsize_multiline(result + " " + word)[0] + 2 * stroke_width
                > max_width
            ):
                result += "\n"
            result += word + " "

    return result


def macro_fill(macro, texts: List[str]) -> Image:
    if len(texts) != len(macro["text_boxes"]):
        raise Exception("incorrect number of texts!")

    with Image.open(os.path.join("templates", macro["filename"])) as img:
        draw = ImageDraw.Draw(img)
        for box, text in zip(macro["text_boxes"], texts):
            font = ImageFont.truetype(box["font"]["name"], size=box["font"]["size"])
            vert_align = box["align"]["vertical"]
            horiz_align = box["align"]["horizontal"]
            stroke_width = box["stroke_width"]
            max_width = box["max_width"]
            print(f"text before: {text}")
            print(f"textsize before: {font.getsize_multiline(text)}")
            text = text_wrap(text, font, stroke_width, max_width)
            print(f"text after: {text}")
            print(f"textsize after: {font.getsize_multiline(text)}")
            text_width, text_height = font.getsize_multiline(text)
            text_width += 2 * stroke_width
            text_height += 2 * stroke_width

            x = box["pos"]["x"]
            y = box["pos"]["y"]
            if vert_align == "TOP":
                pass
            elif vert_align == "MIDDLE":
                y -= text_height / 2
            elif vert_align == "BOTTOM":
                y -= text_height
            else:
                raise Exception("invalid vertical align!")

            if horiz_align == "LEFT":
                text_align = "left"
            elif horiz_align == "MIDDLE":
                x -= text_width / 2
                text_align = "center"
            elif horiz_align == "RIGHT":
                x -= text_width
                text_align = "right"
            else:
                raise Exception("invalid horizontal align!")

            draw.text(
                (x, y),
                text,
                fill=COLOURS[box["text_fill"]],
                font=font,
                stroke_fill=COLOURS[box["stroke_fill"]],
                stroke_width=stroke_width,
                align=text_align,
            )

        return img


with open("macros.json", "r") as f:
    macros = json.load(f)


if __name__ == "__main__":

    print(f"available macros:\n{' '.join(macros.keys())}")

    macro_name = None
    while macro_name not in macros.keys():
        macro_name = input("select a macro: ")

    macro = macros[macro_name]

    texts = []
    for index in range(len(macro["text_boxes"])):
        texts.append(input(f"enter text {index+1}: "))

    out = macro_fill(macro, texts)

    timestamp = datetime.datetime.now().strftime(DATE_TIME_FORMAT)
    if not os.path.isdir("out"):
        os.mkdir("out")
    out.save(os.path.join("out", f"{macro_name}-{timestamp}.png"), format="PNG")
