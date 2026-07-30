"""Crop the top render around a board-mm region for visual inspection."""
import sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
# board bbox in mm (Edge.Cuts extents) -> supplied as argv[7..10]
bx0, by0, bx1, by1 = (float(v) for v in sys.argv[7:11])
im = Image.open(src)
W, H = im.size
# render.py fits the board into the image preserving aspect; compute scale/offset
sw, sh = (bx1 - bx0), (by1 - by0)
s = min(W / sw, H / sh)
ox, oy = (W - sw * s) / 2, (H - sh * s) / 2


def px(mx, my):
    return (ox + (mx - bx0) * s, oy + (my - by0) * s)


a, b = px(x0, y0), px(x1, y1)
im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1]))).resize(
    (min(1100, int(b[0] - a[0]) * 2), min(1100, int(b[1] - a[1]) * 2))).save(dst)
print(dst, im.size, "->", (int(a[0]), int(a[1]), int(b[0]), int(b[1])))
