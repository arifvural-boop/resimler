"""
Beta Vinç - C raylı festoon kablo sistemi tanıtım paftası (3200x2400, TR + EN).

Köprülü vinç genel render'ı (numaralı açıklamalarla), festoon detay render'ı ve gerçek ürün
fotoğrafları (C ray profili, festoon arabası) tek sayfada toplanır.

Kullanım:
    python festoon_pafta.py <cikti.png>
Girdi: ../gercekci/festoon_kopru_vinc.png (+ _noktalar.json), ../gercekci/festoon_detay.png,
       vinc_foto/c_ray_profili.png, vinc_foto/festoon_arabasi.jpg
"""
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

KOK = os.path.dirname(os.path.abspath(__file__))
GER = os.environ.get("GIRDI", os.path.join(KOK, "..", "gercekci"))
FOTO = os.path.join(KOK, "vinc_foto")
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"

TURUNCU = (233, 154, 42)
ANTRASIT = (60, 66, 75)
GRI = (90, 98, 107)
ACIK = (242, 243, 245)
W, H = 3200, 2400

PARCA = [  # (anahtar, TR, EN, etiket kayması px: hero görüntüsünde)
    ("ray", "C ray profili", "C-track rail", (60, -260)),
    ("araba", "Kablo arabası", "Cable trolley", (40, -290)),
    ("kablo", "Yassı kablo", "Flat cable", (-40, 300)),
    ("cekme", "Çekme arabası", "Towing trolley", (120, -280)),
    ("buat", "Besleme buatı", "Junction box", (-110, -280)),
    ("konsol", "Ray konsolu", "Rail bracket", (60, -280)),
]


def font(boy, agirlik="Bold"):
    return ImageFont.truetype(FONT.format(agirlik), boy)


def kirp_beyaz(img, pay=40):
    """Beyaz zemini kırp (içerik sınır kutusu + pay); kutuyu da döndür."""
    fark = ImageChops.difference(img.convert("RGB"), Image.new("RGB", img.size, (255, 255, 255)))
    x0, y0, x1, y1 = fark.point(lambda v: 255 if v > 12 else 0).getbbox()
    kutu = (max(0, x0 - pay), max(0, y0 - pay), min(img.width, x1 + pay), min(img.height, y1 + pay))
    return img.crop(kutu), kutu


def sigdir(img, w, h, doldur=False):
    """Oranı koruyarak w x h kutusuna sığdır (doldur=True: kutuyu tamamen kapla, ortadan kırp)."""
    s = (max if doldur else min)(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    if doldur:
        x, y = (img.width - w) // 2, (img.height - h) // 2
        img = img.crop((x, y, x + w, y + h))
    return img, s


def kart(sayfa, d, x, y, w, h, img, no, tr, en, zemin=ACIK, doldur=False):
    """Yuvarlak köşeli kart: üstte görsel, altta numara + TR/EN başlık."""
    alt = 92
    d.rounded_rectangle((x, y, x + w, y + h), 28, fill=zemin)
    g, _ = sigdir(img, w - 40, h - alt - 40, doldur)
    maske = Image.new("L", g.size, 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, g.width, g.height), 18, fill=255)
    if g.mode == "RGBA":
        maske = ImageChops.multiply(maske, g.getchannel("A"))
    sayfa.paste(g.convert("RGB"), (x + (w - g.width) // 2, y + 20 + (h - alt - 40 - g.height) // 2), maske)
    tx = x + 100 if no else x + 36
    if no:
        rozet(d, x + 54, y + h - alt / 2 - 6, no)
    d.text((tx, y + h - alt / 2 - 6), tr, font=font(40), fill=ANTRASIT, anchor="lm")
    tw = d.textlength(tr, font=font(40))
    d.text((tx + tw + 18, y + h - alt / 2 - 4), en, font=font(32, "Medium"), fill=TURUNCU, anchor="lm")


def rozet(d, x, y, no, r=30):
    d.ellipse((x - r, y - r, x + r, y + r), fill=TURUNCU)
    d.text((x, y + 1), str(no), font=font(int(r * 1.15), "ExtraBold"), fill=(255, 255, 255), anchor="mm")


def main():
    cikti = sys.argv[1]
    sayfa = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(sayfa)

    # üst bant: logo, başlık
    logo = Image.open(os.path.join(KOK, "logo", "beta_logo_koyu.png")).convert("RGBA")
    logo, _ = sigdir(logo, 520, 130)
    sayfa.paste(logo, (110, 60), logo)
    d.text((W - 110, 130), "betavinc.com", font=font(44, "SemiBold"), fill=GRI, anchor="rm")
    d.text((110, 340), "C RAYLI FESTOON KABLO SİSTEMİ", font=font(104, "ExtraBold"), fill=ANTRASIT, anchor="ls")
    d.text((112, 415), "C-track festoon cable system  ·  köprülü vinç uygulaması / overhead crane application",
           font=font(46, "Medium"), fill=TURUNCU, anchor="ls")
    d.rectangle((110, 450, W - 110, 456), fill=TURUNCU)

    # sol: genel görünüş + numaralı açıklamalar
    hx, hy, hw, hh = 90, 500, 1940, 1420
    genel = Image.open(os.path.join(GER, "festoon_kopru_vinc.png")).convert("RGB")
    with open(os.path.join(GER, "festoon_kopru_vinc_noktalar.json")) as f:
        nok = json.load(f)
    kirpik, (kx, ky, _, _) = kirp_beyaz(genel)
    g, s = sigdir(kirpik, hw, hh)
    ox, oy = hx + (hw - g.width) // 2, hy + (hh - g.height) // 2
    sayfa.paste(g, (ox, oy))
    for i, (ad, tr, en, (dx, dy)) in enumerate(PARCA, 1):
        px = ox + (nok[ad][0] * genel.width - kx) * s
        py = oy + (nok[ad][1] * genel.height - ky) * s
        lx, ly = px + dx, py + dy
        d.line((px, py, lx, ly), fill=ANTRASIT, width=4)
        d.ellipse((px - 9, py - 9, px + 9, py + 9), fill=ANTRASIT)
        rozet(d, lx, ly, i, r=34)

    # sağ: detay render + fotoğraflar
    sx, sw = 2080, 1030
    detay = Image.open(os.path.join(GER, "festoon_detay.png")).convert("RGB")
    kart(sayfa, d, sx, 500, sw, 880, detay, None, "Festoon detayı", "Festoon detail", zemin=(255, 255, 255), doldur=True)
    d.rounded_rectangle((sx, 500, sx + sw, 1380), 28, outline=(225, 227, 230), width=3)
    yw = (sw - 30) // 2
    cray = Image.open(os.path.join(FOTO, "c_ray_profili.png")).convert("RGBA")
    kart(sayfa, d, sx, 1410, yw, 510, cray, 1, "C ray", "C-track")
    foto = Image.open(os.path.join(FOTO, "festoon_arabasi.jpg")).convert("RGB")
    kart(sayfa, d, sx + yw + 30, 1410, yw, 510, foto, 2, "Araba", "Trolley", zemin=foto.getpixel((5, 5)), doldur=True)

    # alt: parça listesi
    y0 = 1990
    d.rectangle((110, y0, W - 110, y0 + 3), fill=(225, 227, 230))
    kol = (W - 220) / 3
    for i, (ad, tr, en, _) in enumerate(PARCA):
        cx = 110 + (i % 3) * kol
        cy = y0 + 90 + (i // 3) * 120
        rozet(d, cx + 34, cy, i + 1, r=34)
        d.text((cx + 90, cy - 4), tr, font=font(46), fill=ANTRASIT, anchor="ls")
        d.text((cx + 90, cy + 40), en, font=font(34, "Medium"), fill=TURUNCU, anchor="ls")
    d.text((W / 2, H - 50), "beta vinç sistemleri  ·  crane systems  ·  www.betavinc.com", font=font(34, "Medium"),
           fill=GRI, anchor="ms")
    sayfa.save(cikti)
    print(cikti)


if __name__ == "__main__":
    main()
