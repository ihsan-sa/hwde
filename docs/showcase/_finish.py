#!/usr/bin/env python3
"""Turn one raw kicad-cli render into the committed showcase image.

Crops the transparent margin so the board fills the frame, composites onto the
document's page colour, downscales to 1600 px on the long side, and keeps the
file under the size budget (PNG first, high-quality JPG if PNG is too big).

Called by render_boards.sh; usable on its own:
    _finish.py [--opaque-only] raw.png out.png

--opaque-only throws away the semi-transparent drop shadow. It reads as depth on
an angled view and as grey blocks around the board on a straight-down one.
"""
import os
import sys

from PIL import Image

CANVAS = (250, 249, 246)   # #FAF9F6, the diagrams' page colour
LONG_EDGE = 1600
PAD = 0.025                # fraction of the long side left as margin
BUDGET = 480_000           # bytes


SHADOW_CUT = 200           # alpha below this is shadow, not board


def main(src, dst, opaque_only=False):
    im = Image.open(src).convert("RGBA")
    if opaque_only:
        alpha = im.split()[3].point(lambda v: 255 if v >= SHADOW_CUT else 0)
        im.putalpha(alpha)
    bbox = im.split()[3].getbbox()
    if bbox is None:
        print(f"WARNING {os.path.basename(dst)}: render is entirely empty")
        bbox = (0, 0, im.width, im.height)
    else:
        touch = [n for n, hit in (("left", bbox[0] == 0), ("top", bbox[1] == 0),
                                  ("right", bbox[2] == im.width),
                                  ("bottom", bbox[3] == im.height)) if hit]
        if touch:
            # Usually the soft drop shadow, not the board. Worth an eyeball.
            print(f"NOTE {os.path.basename(dst)}: non-transparent pixels reach "
                  f"the frame ({', '.join(touch)}) - check nothing is clipped, "
                  f"and lower the zoom for it if so")

    pad = int(PAD * max(bbox[2] - bbox[0], bbox[3] - bbox[1]))
    box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
           min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))
    im = im.crop(box)

    scale = LONG_EDGE / max(im.size)
    if scale < 1:
        im = im.resize((max(1, round(im.width * scale)),
                        max(1, round(im.height * scale))), Image.LANCZOS)

    flat = Image.new("RGB", im.size, CANVAS)
    flat.paste(im, (0, 0), im)

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    flat.save(dst, "PNG", optimize=True)
    size = os.path.getsize(dst)
    if size > BUDGET:
        # 256-colour PNG usually wins on these renders; JPG is the fallback.
        quant = flat.convert("P", palette=Image.ADAPTIVE, colors=256)
        alt = dst + ".q.png"
        quant.save(alt, "PNG", optimize=True)
        if os.path.getsize(alt) <= size:
            os.replace(alt, dst)
            size = os.path.getsize(dst)
        else:
            os.remove(alt)
    if size > BUDGET:
        jpg = os.path.splitext(dst)[0] + ".jpg"
        flat.save(jpg, "JPEG", quality=88, optimize=True, progressive=True)
        if os.path.getsize(jpg) < size:
            os.remove(dst)
            dst, size = jpg, os.path.getsize(jpg)
        else:
            os.remove(jpg)
    print(f"{os.path.basename(dst)}  {flat.width}x{flat.height}  {size // 1024} KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    opaque = "--opaque-only" in args
    args = [a for a in args if a != "--opaque-only"]
    if len(args) != 2:
        sys.exit("usage: _finish.py [--opaque-only] <raw.png> <out.png>")
    main(args[0], args[1], opaque)
