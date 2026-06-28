#!/usr/bin/env python3
"""
render_war_timeline.py — Render a war-history timeline as an EU4-cover-style PNG
(gold-on-dark, original heraldic shields, no game art).

Input: a JSON list of war dicts. Each war:
{
  "zh": "意大利战争",                 # display name (any language)
  "main": "VEN",                      # opponent tag; first letter goes on the shield
  "enemies": "威尼斯·萨伏伊·骑士团等",  # subtitle line
  "start": "1452", "end": "1454",     # year span (start==end -> single year)
  "tier": "大",                        # 大 / 中 / 小  -> color + label on the right
  "c1": "#9c7510", "c2": "#e8c34a"     # heraldic colors: left/primary, right/overlay
}

Usage:
    python render_war_timeline.py wars.json --out timeline.png \
        --title "奥地利 · 哈布斯堡战争史" \
        --eyebrow "EUROPA UNIVERSALIS IV · 铁人局" \
        --subtitle "1446 — 1485 · 共 12 场主要战争"

IMPORTANT — fonts: this uses Noto CJK from the standard Linux path. If absent,
install with: apt-get install -y fonts-noto-cjk  (or point --font-dir elsewhere).
Heraldic colors are ORIGINAL color blocks, NOT extracted EU4 flag textures
(those are Paradox copyright). Pick historical tinctures per country.
"""
import json, argparse
from PIL import Image, ImageDraw, ImageFont

GOLD, GOLD_DK, CREAM, PARCH = '#e8c34a', '#b08d4a', '#f5e7c0', '#9c8050'
TIER_COLOR = {"大": '#d4423e', "中": '#d98a2b', "小": '#7a8a5c'}
TIER_LABEL = {"大": "大国对撞", "中": "中等战争", "小": "边境冲突"}

FONT_DIR = '/usr/share/fonts/opentype/noto'
FONTS = {
    'sans_b': f'{FONT_DIR}/NotoSansCJK-Bold.ttc',
    'sans_m': f'{FONT_DIR}/NotoSansCJK-Medium.ttc',
    'sans_r': f'{FONT_DIR}/NotoSansCJK-Regular.ttc',
    'serif_b': f'{FONT_DIR}/NotoSerifCJK-Bold.ttc',
}


def render(wars, out, title, eyebrow, subtitle, font_dir=None):
    if font_dir:
        for k in FONTS:
            FONTS[k] = FONTS[k].replace(FONT_DIR, font_dir)
    SCALE = 2
    W = 1280
    M = 70
    top_pad = 300
    row_h = 150
    gap = 22
    H = top_pad + len(wars) * (row_h + gap) + 90

    img = Image.new('RGB', (W * SCALE, H * SCALE), '#140d05')
    d = ImageDraw.Draw(img)
    F = lambda p, s: ImageFont.truetype(p, s * SCALE)
    S = lambda v: v * SCALE

    f_eyebrow = F(FONTS['sans_m'], 22)
    f_title = F(FONTS['serif_b'], 64)
    f_sub = F(FONTS['sans_r'], 26)
    f_war = F(FONTS['sans_b'], 40)
    f_enemy = F(FONTS['sans_r'], 23)
    f_year = F(FONTS['sans_b'], 40)
    f_tier = F(FONTS['sans_m'], 21)
    f_shield = F(FONTS['serif_b'], 44)

    # frame
    d.rounded_rectangle([S(28), S(28), S(W - 28), S(H - 28)], radius=S(20), outline='#5c4420', width=S(3))
    d.rounded_rectangle([S(38), S(38), S(W - 38), S(H - 38)], radius=S(16), outline='#3a2a12', width=S(1))

    cx = W // 2
    def ctext(y, text, font, fill):
        bb = d.textbbox((0, 0), text, font=font)
        d.text((S(cx) - (bb[2] - bb[0]) // 2, S(y)), text, font=font, fill=fill)

    ctext(75, eyebrow, f_eyebrow, GOLD_DK)
    ctext(110, title, f_title, CREAM)
    ctext(200, subtitle, f_sub, GOLD_DK)
    d.line([S(M + 40), S(255), S(W - M - 40), S(255)], fill='#5c4420', width=S(2))
    d.polygon([(S(cx), S(248)), (S(cx + 9), S(255)), (S(cx), S(262)), (S(cx - 9), S(255))], fill=GOLD)

    def draw_shield(cx_, cy_, c1, c2, letter):
        sw, sh = 78, 92
        x0, y0 = cx_ - sw // 2, cy_ - sh // 2
        poly = [(x0 + 4, y0 + 4), (x0 + sw - 4, y0 + 4),
                (x0 + sw - 4, y0 + int(sh * 0.52)),
                (x0 + int(sw * 0.78), y0 + int(sh * 0.82)),
                (x0 + sw // 2, y0 + sh - 3),
                (x0 + int(sw * 0.22), y0 + int(sh * 0.82)),
                (x0 + 4, y0 + int(sh * 0.52))]
        polyS = [(S(px), S(py)) for px, py in poly]
        d.polygon(polyS, fill=c1, outline=GOLD)
        half = [(x0 + sw // 2, y0 + 4), (x0 + sw - 4, y0 + 4),
                (x0 + sw - 4, y0 + int(sh * 0.52)),
                (x0 + int(sw * 0.78), y0 + int(sh * 0.82)),
                (x0 + sw // 2, y0 + sh - 3)]
        halfS = [(S(px), S(py)) for px, py in half]
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        r = int(c2[1:3], 16); g = int(c2[3:5], 16); b = int(c2[5:7], 16)
        od.polygon(halfS, fill=(r, g, b, 140))
        merged = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
        img.paste(merged, (0, 0))
        d.polygon(polyS, fill=None, outline=GOLD)
        d.line([polyS[0], polyS[-1]], fill=GOLD, width=S(2))
        d.line([(S(x0 + sw // 2), S(y0 + 4)), (S(x0 + sw // 2), S(y0 + sh - 3))], fill=GOLD, width=S(1))
        bb = d.textbbox((0, 0), letter, font=f_shield)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        d.text((S(cx_) - lw // 2 - bb[0], S(cy_) - lh // 2 - bb[1]), letter,
               font=f_shield, fill='#ffffff', stroke_width=S(2), stroke_fill='#00000088')

    y = top_pad
    for w in wars:
        rx0, ry0, rx1, ry1 = M, y, W - M, y + row_h
        tc = TIER_COLOR.get(w['tier'], '#7a8a5c')
        d.rounded_rectangle([S(rx0), S(ry0), S(rx1), S(ry1)], radius=S(12), fill='#20160a', outline='#3a2a12', width=S(1))
        d.rounded_rectangle([S(rx0), S(ry0), S(rx0 + 8), S(ry1)], radius=S(4), fill=tc)
        draw_shield(rx0 + 95, (ry0 + ry1) // 2, w['c1'], w['c2'], w['main'][0])
        tx = rx0 + 165
        d.text((S(tx), S(ry0 + 38)), w['zh'], font=f_war, fill=CREAM)
        d.text((S(tx), S(ry0 + 95)), w['enemies'], font=f_enemy, fill=PARCH)
        yspan = w['start'] if w['start'] == w['end'] else f"{w['start']}\u2013{w['end']}"
        bb = d.textbbox((0, 0), yspan, font=f_year)
        d.text((S(rx1 - 30) - (bb[2] - bb[0]), S(ry0 + 40)), yspan, font=f_year, fill=GOLD)
        tl = TIER_LABEL.get(w['tier'], '')
        bb2 = d.textbbox((0, 0), tl, font=f_tier)
        d.text((S(rx1 - 30) - (bb2[2] - bb2[0]), S(ry0 + 95)), tl, font=f_tier, fill=tc)
        y += row_h + gap

    ctext(H - 58, "数据来源：存档快照时间线 · 战争区间为快照估计", f_tier, '#6b5530')
    img.resize((W, H), Image.LANCZOS).save(out, 'PNG')
    print(f"saved {out}  ({W}x{H})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wars', help='JSON list of war dicts')
    ap.add_argument('--out', default='/mnt/user-data/outputs/war_timeline.png')
    ap.add_argument('--title', default='战争史')
    ap.add_argument('--eyebrow', default='EUROPA UNIVERSALIS IV')
    ap.add_argument('--subtitle', default='')
    ap.add_argument('--font-dir', default=None)
    a = ap.parse_args()
    wars = json.load(open(a.wars))
    render(wars, a.out, a.title, a.eyebrow, a.subtitle, a.font_dir)


if __name__ == '__main__':
    main()
