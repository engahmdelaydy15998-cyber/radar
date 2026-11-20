"""سكّتي icon: speedometer bezel + perspective S-road + glowing pin + hazard badges, in the radar-AI style.

Writes sk_icon.png (round, transparent corners), sk_maskable.png (full bleed, art at 80% for the
safe zone) and sk_sheet.png (preview at several sizes) into the current folder.
"""
from PIL import Image, ImageDraw, ImageFilter
import math, random

S = 3; N = 512 * S; C = N // 2
random.seed(11)
YEL = (245, 196, 81); AMB = (255, 160, 40); ORG = (255, 122, 61); GRN = (95, 211, 160); RED = (255, 90, 110)


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))
def layer(): return Image.new("RGBA", (N, N), (0, 0, 0, 0))
def over(base, top): base.alpha_composite(top)


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u**3 * p0[i] + 3 * u * u * t * p1[i] + 3 * u * t * t * p2[i] + t**3 * p3[i] for i in range(2))


def speedo_color(t):                     # green -> yellow -> red along the bezel sweep
    return lerp(GRN, YEL, t / 0.55) if t < 0.55 else lerp(YEL, RED, (t - 0.55) / 0.45)


def build():
    base = Image.new("RGBA", (N, N), (5, 5, 6, 255))
    # warm depth glow from below the centre
    gl = layer(); gd = ImageDraw.Draw(gl)
    for i in range(50, 0, -1):
        r = N * 0.5 * i / 50; a = int(120 * ((1 - i / 50) ** 1.8))
        gd.ellipse([C - r, C + N * 0.06 - r, C + r, C + N * 0.06 + r], fill=AMB + (a,))
    over(base, gl.filter(ImageFilter.GaussianBlur(8 * S)))
    # bokeh
    bk = layer(); bd = ImageDraw.Draw(bk)
    for _ in range(10):
        a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.28, 0.44) * N; r = random.uniform(0.01, 0.026) * N
        x = C + math.cos(a) * rr; y = C + math.sin(a) * rr
        bd.ellipse([x - r, y - r, x + r, y + r], fill=YEL + (random.randint(18, 45),))
    over(base, bk.filter(ImageFilter.GaussianBlur(5 * S)))
    # dark dial plate
    pl = layer(); pd = ImageDraw.Draw(pl); PR = N * 0.445
    for i in range(40, 0, -1):
        r = PR * i / 40
        pd.ellipse([C - r, C - r, C + r, C + r], fill=lerp((34, 30, 22), (12, 12, 13), i / 40) + (int(235 * min(1, 0.5 + i / 80)),))
    over(base, pl)
    # faint inner rings for depth
    for i, r in enumerate([0.23, 0.30, 0.37]):
        rl = layer(); rd = ImageDraw.Draw(rl); R = N * r
        rd.ellipse([C - R, C - R, C + R, C + R], outline=YEL + (40 - i * 9,), width=int(1.6 * S))
        over(base, rl.filter(ImageFilter.GaussianBlur(i * 0.5 * S)))

    # speedometer bezel: 270° sweep starting bottom-left (225°) clockwise to bottom-right (-45°)
    A0, SW = 225, 270
    hd = layer(); hdd = ImageDraw.Draw(hd)
    for k in range(0, 91):
        t = k / 90; deg = A0 - SW * t; a = math.radians(deg); heavy = k % 10 == 0
        r0 = N * (0.405 if heavy else 0.418); r1 = N * 0.44
        col = speedo_color(t)
        hdd.line([(C + math.cos(a) * r0, C - math.sin(a) * r0), (C + math.cos(a) * r1, C - math.sin(a) * r1)],
                 fill=col + (235 if heavy else 120,), width=int((3.2 if heavy else 1.5) * S))
    # glowing colour arc
    arc = layer(); ad = ImageDraw.Draw(arc); R = N * 0.458
    for k in range(120):
        t0, t1 = k / 120, (k + 1) / 120
        # PIL arcs go clockwise from 3 o'clock in screen coordinates
        s0 = -(A0 - SW * t0); s1 = -(A0 - SW * t1)
        ad.arc([C - R, C - R, C + R, C + R], s0, s1 + 0.6, fill=speedo_color(t0) + (230,), width=int(6 * S))
    over(base, arc.filter(ImageFilter.GaussianBlur(5 * S)))
    over(base, arc)
    over(base, hd)
    # outer ring edge
    ed = layer(); edd = ImageDraw.Draw(ed)
    edd.ellipse([C - N * 0.478, C - N * 0.478, C + N * 0.478, C + N * 0.478], outline=(60, 56, 46, 255), width=int(4 * S))
    edd.ellipse([C - N * 0.488, C - N * 0.488, C + N * 0.488, C + N * 0.488], outline=(20, 20, 22, 255), width=int(6 * S))
    over(base, ed)

    # perspective S road, clipped to the dial
    p0, p1, p2, p3 = (C + N * 0.02, N * 1.07), (C + N * 0.27, N * 0.77), (C - N * 0.27, N * 0.56), (C + N * 0.03, N * 0.31)
    pts = [bez(p0, p1, p2, p3, i / 160) for i in range(161)]
    def width_at(t): return N * (0.25 * (1 - t) ** 1.3 + 0.026)
    left, right, norms = [], [], []
    for i, (x, y) in enumerate(pts):
        j0, j1 = max(0, i - 1), min(160, i + 1)
        dx = pts[j1][0] - pts[j0][0]; dy = pts[j1][1] - pts[j0][1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L; w = width_at(i / 160) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w)); norms.append((nx, ny, w))
    road = layer(); rd = ImageDraw.Draw(road)
    rd.polygon(left + right[::-1], fill=(48, 48, 54, 255))
    # asphalt shading: lighter toward the horizon
    sh = layer(); sd = ImageDraw.Draw(sh)
    for i in range(0, 160, 2):
        t = i / 160
        quad = [left[i], left[i + 2], right[i + 2], right[i]]
        sd.polygon(quad, fill=lerp((38, 38, 44), (92, 88, 80), t ** 1.6) + (255,))
    road = sh
    rd = ImageDraw.Draw(road)
    # white edge lines
    for side in (left, right):
        for i in range(160):
            t = i / 160
            rd.line([side[i], side[i + 1]], fill=(235, 235, 240, int(230 - 120 * t)), width=max(1, int(S * (5.5 * (1 - t) + 1.2))))
    # yellow centre dashes shrinking with distance
    i = 0; on = True
    while i < 160:
        t = i / 160; seg = max(2, int(14 * (1 - t) ** 1.3) + 2)
        if on:
            for j in range(i, min(160, i + seg)):
                tt = j / 160
                rd.line([pts[j], pts[j + 1]], fill=YEL + (255,), width=max(1, int(S * (6.5 * (1 - tt) + 1))))
        i += seg; on = not on
    mask = Image.new("L", (N, N), 0); ImageDraw.Draw(mask).ellipse([C - N * 0.445, C - N * 0.445, C + N * 0.445, C + N * 0.445], fill=255)
    road.putalpha(Image.composite(road.getchannel("A"), Image.new("L", (N, N), 0), mask))
    # road glow underneath
    glow = road.copy().filter(ImageFilter.GaussianBlur(10 * S))
    tint = Image.new("RGBA", (N, N), AMB + (0,)); tint.putalpha(glow.getchannel("A").point(lambda v: v * 0.45))
    over(base, tint)
    over(base, road)

    # location pin at the end of the road
    px, py = p3[0], p3[1] - N * 0.035; pr = N * 0.062
    pg = layer(); pgd = ImageDraw.Draw(pg)
    for i in range(30, 0, -1):
        r = pr * 2.4 * i / 30; pgd.ellipse([px - r, py - r, px + r, py + r], fill=YEL + (int(70 * (1 - i / 30) ** 1.4),))
    over(base, pg.filter(ImageFilter.GaussianBlur(4 * S)))
    pin = layer(); pn = ImageDraw.Draw(pin)
    for i in range(24, 0, -1):
        t = i / 24; r = pr * t
        pn.ellipse([px - r, py - r, px + r, py + r], fill=lerp((255, 236, 170), ORG, t) + (255,))
    pn.polygon([(px - pr * 0.72, py + pr * 0.55), (px + pr * 0.72, py + pr * 0.55), (px, py + pr * 1.75)], fill=ORG + (255,))
    pn.ellipse([px - pr * 0.36, py - pr * 0.36, px + pr * 0.36, py + pr * 0.36], fill=(25, 18, 10, 255))
    over(base, pin)

    # hazard badges on the inner ring (camera, toll, checkpoint, u-turn), lit toward the centre
    def badge(cx, cy, r, glyph, col, dim):
        b = layer(); bd = ImageDraw.Draw(b)
        for i in range(18, 0, -1):
            rr = r * i / 18; bd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=lerp((70, 64, 50), (20, 20, 22), i / 18) + (int(250 * dim),))
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (int(220 * dim),), width=int(2 * S))
        g = r * 0.55; w = max(2, int(2.4 * S)); fc = (240, 240, 240, int(255 * dim))
        if glyph == "cam":
            bd.rounded_rectangle([cx - g, cy - g * 0.6, cx + g, cy + g * 0.7], radius=g * 0.2, outline=fc, width=w)
            bd.ellipse([cx - g * 0.38, cy - g * 0.3, cx + g * 0.38, cy + g * 0.46], outline=fc, width=w)
            bd.rectangle([cx - g * 0.5, cy - g * 0.85, cx - g * 0.05, cy - g * 0.6], fill=fc)
        elif glyph == "toll":
            bd.line([(cx - g, cy + g), (cx - g, cy - g * 0.9)], fill=fc, width=w + 2)
            for k in range(4):
                x0 = cx - g + k * g * 0.5
                bd.line([(x0, cy - g * 0.35), (x0 + g * 0.5, cy - g * 0.35)], fill=(RED if k % 2 == 0 else (240, 240, 240)) + (int(255 * dim),), width=w + 3)
        elif glyph == "cone":
            bd.polygon([(cx, cy - g), (cx + g * 0.75, cy + g * 0.75), (cx - g * 0.75, cy + g * 0.75)], fill=ORG + (int(255 * dim),))
            bd.line([(cx - g * 0.42, cy + g * 0.08), (cx + g * 0.42, cy + g * 0.08)], fill=fc, width=w)
            bd.line([(cx - g * 0.9, cy + g * 0.82), (cx + g * 0.9, cy + g * 0.82)], fill=fc, width=w)
        elif glyph == "uturn":
            bd.arc([cx - g * 0.7, cy - g, cx + g * 0.7, cy + g * 0.2], 180, 360, fill=fc, width=w)
            bd.line([(cx + g * 0.7, cy - g * 0.4), (cx + g * 0.7, cy + g)], fill=fc, width=w)
            bd.line([(cx - g * 0.7, cy - g * 0.4), (cx - g * 0.7, cy + g * 0.4)], fill=fc, width=w)
            bd.polygon([(cx - g * 1.05, cy + g * 0.25), (cx - g * 0.35, cy + g * 0.25), (cx - g * 0.7, cy + g * 0.85)], fill=fc)
        return b
    R = N * 0.33
    for deg, glyph, col, dim, rr in [(150, "cam", RED, 1.0, 0.052), (35, "toll", YEL, 0.95, 0.046), (205, "cone", ORG, 0.8, 0.04), (-25, "uturn", GRN, 0.72, 0.038)]:
        a = math.radians(deg); bx = C + math.cos(a) * R; by = C - math.sin(a) * R
        b = badge(bx, by, N * rr, glyph, col, dim)
        over(base, b.filter(ImageFilter.GaussianBlur((1 - dim) * 2.5 * S)) if dim < 0.9 else b)

    # glossy highlight on the upper half of the dial
    gs = layer(); gsd = ImageDraw.Draw(gs)
    gsd.ellipse([C - N * 0.40, C - N * 0.44, C + N * 0.40, C - N * 0.02], fill=(255, 255, 255, 14))
    over(base, gs.filter(ImageFilter.GaussianBlur(14 * S)))
    return base


def finish(img, size, round_mask):
    im = img.resize((size, size), Image.LANCZOS)
    if round_mask:
        m = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(m).ellipse([size * 4 * 0.012, size * 4 * 0.012, size * 4 * 0.988, size * 4 * 0.988], fill=255)
        im.putalpha(m.resize((size, size), Image.LANCZOS))
    return im


if __name__ == "__main__":
    art = build()
    finish(art, 512, True).save("sk_icon.png")
    mk = Image.new("RGBA", (N, N), (5, 5, 6, 255))
    small = art.resize((int(N * 0.8), int(N * 0.8)), Image.LANCZOS)
    mk.alpha_composite(small, ((N - small.width) // 2, (N - small.height) // 2))
    finish(mk, 512, False).save("sk_maskable.png")
    sheet = Image.new("RGBA", (512 + 192 + 96 + 48 + 80, 512), (240, 240, 240, 255)); x = 0
    for s in (512, 192, 96, 48):
        sheet.alpha_composite(finish(art, s, True), (x, (512 - s) // 2)); x += s + 20
    sheet.save("sk_sheet.png")
