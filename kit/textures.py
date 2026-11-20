#!/usr/bin/env python3
"""kit/textures.py -- painted sign / poster textures with PIL (system Python, not Blender's). No third-party assets, drawn from scratch.
    python3 kit/textures.py <out_dir>            writes sign_<name>.png (1024x256) and poster_wanted.png (512x768)"""
import sys, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SIGNS = {"saloon": ("SALOON", (122, 40, 34), (244, 222, 170)), "hotel": ("HOTEL", (44, 76, 120), (244, 230, 190)), "general": ("GENERAL STORE", (60, 96, 60), (240, 226, 180)),
         "bank": ("BANK", (50, 46, 44), (232, 196, 96)), "jail": ("JAIL", (70, 56, 46), (230, 214, 180)), "barber": ("BARBER", (120, 48, 40), (244, 236, 214)),
         "livery": ("LIVERY STABLE", (92, 62, 38), (240, 220, 170)), "undertaker": ("UNDERTAKER", (36, 34, 40), (214, 204, 184)), "church": ("CHURCH", (200, 184, 150), (80, 56, 44))}
def font(size):
    c = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"]
    try:
        import matplotlib; c.append(os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSerif-Bold.ttf"))
    except Exception: pass
    for p in c:
        if os.path.isfile(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()
def weather(im, seed, planks=True):
    r = random.Random(seed); d = ImageDraw.Draw(im); W, H = im.size
    if planks:
        for y in range(0, H, H // 4): d.line([(0, y), (W, y)], fill=(0, 0, 0), width=2)
    px = im.load()
    for _ in range(W * H // 40):
        x, y = r.randrange(W), r.randrange(H); a = r.randint(-26, 10); p = px[x, y]; px[x, y] = tuple(max(0, min(255, c + a)) for c in p[:3])
    return im.filter(ImageFilter.GaussianBlur(.6))
def sign(name, text, bg, fg, W=1024, H=256):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im); size = int(H * .52)
    f = font(size)
    while d.textlength(text, font=f) > W * .86 and size > 20: size -= 6; f = font(size)
    d.rectangle((8, 8, W - 9, H - 9), outline=fg, width=7); d.rectangle((24, 24, W - 25, H - 25), outline=tuple(int(c * .6) for c in fg), width=2)
    d.text((W // 2 + 3, H // 2 + 4), text, font=f, fill=tuple(int(c * .25) for c in bg), anchor="mm"); d.text((W // 2, H // 2), text, font=f, fill=fg, anchor="mm")
    weather(im, sum(map(ord, name)), False).save(os.path.join(OUT, "sign_%s.png" % name))
def poster():
    W, H = 512, 768; im = Image.new("RGB", (W, H), (226, 204, 156)); d = ImageDraw.Draw(im)
    d.rectangle((10, 10, W - 11, H - 11), outline=(90, 60, 40), width=8); d.text((W // 2, 90), "WANTED", font=font(96), fill=(110, 30, 24), anchor="mm")
    d.rectangle((90, 170, W - 90, 470), fill=(206, 182, 136), outline=(90, 60, 40), width=5)
    d.ellipse((190, 210, 322, 360), fill=(150, 116, 90)); d.pieslice((170, 190, 342, 300), 180, 360, fill=(70, 46, 34)); d.rectangle((150, 300, 362, 316), fill=(70, 46, 34))
    d.text((W // 2, 530), "DEAD OR ALIVE", font=font(44), fill=(110, 30, 24), anchor="mm"); d.text((W // 2, 640), "$500", font=font(110), fill=(60, 40, 30), anchor="mm")
    weather(im, 7, False).save(os.path.join(OUT, "poster_wanted.png"))
if __name__ == "__main__":
    OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
    for k, (t, bg, fg) in SIGNS.items(): sign(k, t, bg, fg)
    poster(); print("kit textures:", sorted(os.listdir(OUT)))
