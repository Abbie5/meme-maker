from PIL import Image, ImageDraw, ImageFont, ImageColor
import os
import pprint
import datetime
from typing import Tuple, List
import json


pp = pprint.PrettyPrinter(indent=4)
DATE_TIME_FORMAT = "%Y%m%d%H%M%S%f"
# fallback if style not specified anywhere
DEFAULT_STYLE = {
    "text_align": "center",  # can be "left", "center" or "right"
    "vert_align": "center",  # can be "top", "center" or "bottom"
    "font": "arial.ttf",  # any font file name
    "text_fill": "black",  # see https://pillow.readthedocs.io/en/stable/reference/ImageColor.html#color-names
    "stroke_fill": "white",  # as above
    "stroke_width": 0,  # in pixels
}
DEBUG = False


def text_wrap(text: str, font: ImageFont, stroke_width: int, max_width: int) -> str:
    if font.getsize_multiline(text, stroke_width=stroke_width)[0] <= max_width:
        return text
    else:
        result = ""
        first_word = True
        for word in text.split():
            if first_word:
                result += word
                first_word = False
            else:
                if (
                    font.getsize_multiline(
                        result + " " + word, stroke_width=stroke_width
                    )[0]
                    > max_width
                ):
                    result += "\n" + word
                else:
                    result += " " + word

    return result


def fit_text(
    text: str, font_name: str, stroke_width: int, dimensions: Tuple[int, int]
) -> Tuple[str, ImageFont.ImageFont, Tuple[int, int]]:
    size = width = height = 0
    max_width, max_height = dimensions
    wrapped_text = text
    while True:
        new_size = size + 1
        font = ImageFont.truetype(font_name, size=new_size)
        new_wrapped_text = text_wrap(text, font, stroke_width, max_width)
        new_width, new_height = font.getsize_multiline(
            new_wrapped_text, stroke_width=stroke_width
        )
        new_height += font.getmetrics()[
            1
        ]  # getsize_multiline() doesn't include the height of descenders

        if new_width > max_width or new_height > max_height:
            break
        else:
            wrapped_text = new_wrapped_text
            size = new_size
            width = new_width
            height = new_height

    return wrapped_text, ImageFont.truetype(font_name, size=size), (width, height)


def get_style(style_name, box, macro, global_style):
    if "style" in box and style_name in box["style"]:
        return box["style"][style_name]
    elif "style" in macro and style_name in macro["style"]:
        return macro["style"][style_name]
    elif style_name in global_style:
        return global_style[style_name]
    elif style_name in DEFAULT_STYLE:
        return DEFAULT_STYLE[style_name]
    else:
        raise Exception("invalid style name!")


def macro_fill(macro, texts: List[str]) -> Image:
    if len(texts) != len(macro["text_boxes"]):
        raise Exception("incorrect number of texts!")

    with Image.open(os.path.join("templates", macro["filename"])) as img:
        draw = ImageDraw.Draw(img)
        for box, text in zip(macro["text_boxes"], texts):
            text_align = get_style("text_align", box, macro, global_style)
            vert_align = get_style("vert_align", box, macro, global_style)
            font_name = get_style("font", box, macro, global_style)
            text_fill = get_style("text_fill", box, macro, global_style)
            stroke_fill = get_style("stroke_fill", box, macro, global_style)
            stroke_width = get_style("stroke_width", box, macro, global_style)

            box_pos = tuple(box["pos"])
            box_dimensions = tuple(box["dimensions"])
            text, font, text_dimensions = fit_text(
                text, font_name, stroke_width, box_dimensions
            )

            if vert_align == "top":
                text_y = box_pos[1]
            elif vert_align == "center":
                text_y = box_pos[1] + (box_dimensions[1] - text_dimensions[1]) // 2
            elif vert_align == "bottom":
                text_y = box_pos[1] + box_dimensions[1] - text_dimensions[1]
            else:
                raise Exception("invalid vertical align!")

            if text_align == "left":
                text_x = box_pos[0]
            elif text_align == "center":
                text_x = box_pos[0] + (box_dimensions[0] - text_dimensions[0]) // 2
            elif text_align == "right":
                text_x = box_pos[0] + box_dimensions[0] - text_dimensions[0]
            else:
                raise Exception("invalid text align!")

            text_pos = (text_x, text_y)

            if DEBUG:
                # debug layout rectangles
                # pp.pprint(ImageColor.getrgb("pink"))
                # pp.pprint([box_pos, tuple(map(sum, zip(box_pos, box_dimensions)))])
                box_rect = Image.new("RGBA", box_dimensions, (255, 0, 0, 128))
                text_rect = Image.new("RGBA", text_dimensions, (0, 0, 255, 128))
                rectangles = Image.new("RGBA", img.size, (0, 0, 0, 0))
                box_img = rectangles.copy()
                box_img.paste(box_rect, box_pos)
                text_img = rectangles.copy()
                text_img.paste(text_rect, text_pos)
                rectangles_img = Image.alpha_composite(box_img, text_img)
                img = Image.alpha_composite(img.convert("RGBA"), rectangles_img)
                draw = ImageDraw.Draw(img)

                # rectangle_draw = ImageDraw.Draw(rectangles)
                # rectangle_draw.rectangle(
                #     [box_pos, tuple(map(sum, zip(box_pos, box_dimensions)))],
                #     fill=(255, 0, 0, 64),
                # )
                #
                # rectangle_draw.rectangle(
                #     [text_pos, tuple(map(sum, zip(text_pos, text_dimensions)))],
                #     fill=(0, 0, 255, 64),
                # )
                # img = Image.alpha_composite(img, rectangles)

            draw.text(
                text_pos,
                text,
                fill=ImageColor.getrgb(text_fill),
                font=font,
                stroke_fill=ImageColor.getrgb(stroke_fill),
                stroke_width=stroke_width,
                align=text_align,
            )

        return img


if __name__ == "__main__":
    with open("macros.json", "r") as f:
        macros = json.load(f)

    with open("global_style.json") as f:
        global_style = json.load(f)

    print(f"available macros:\n{' '.join(macros.keys())}")

    macro_name = None
    while macro_name not in macros.keys():
        macro_name = input("select a macro: ")

    macro = macros[macro_name]

    texts = []
    for index in range(len(macro["text_boxes"])):
        texts.append(input(f"enter text {index+1}: "))

    out = macro_fill(macro, texts).convert("RGB")

    if not os.path.isdir("out"):
        os.mkdir("out")

    timestamp = datetime.datetime.now().strftime(DATE_TIME_FORMAT)
    out.save(os.path.join("out", f"{timestamp}.jpg"), format="JPEG")
