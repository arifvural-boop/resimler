"""
Beta Vinç - 3B ürün render'ını gerçek ürün fotoğrafı görünümüne getirme (PIL + numpy).

Adımlar: 2,5x büyütme, ürün maskesi (beyaz zemin), ton eğrisi ve renk dengesi, yerel kontrast,
boya yüzeyi mikro dokusu (portakal kabuğu), parlak noktalarda hafif ışıma, ince keskinlik,
sensör greni; ürün saf beyaz stüdyo zemine geri oturtulur (gölgesiz katalog fotoğrafı).

Kullanım:
    python foto_gercekci.py <girdi> <cikti.png> [--etiket x0,y0,x1,y1,METIN]
    --etiket: girdi koordinatlarındaki siyah kapasite etiketini METIN ile yeniden yazar (ör. kanca bloğu).
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OLCEK = 2.5
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


def etiket_duzelt(img, kutu, metin):
    """Siyah etiket alanını bul, aynı siyahla kapat ve metni (satırlar '|' ile) beyaz yaz."""
    x0, y0, x1, y1 = kutu
    a = np.asarray(img.crop(kutu).convert("L"), np.float32)
    ys, xs = np.nonzero(a < 70)
    bx0, by0, bx1, by1 = x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max()
    d = ImageDraw.Draw(img)
    d.rectangle((bx0 + 1, by0 + 1, bx1 - 1, by1 - 1), fill=(22, 22, 24))
    satir = metin.split("|")
    h = (by1 - by0) / (len(satir) + 0.6)
    f = ImageFont.truetype(FONT, max(6, int(h * 0.72)))
    for i, s in enumerate(satir):
        d.text(((bx0 + bx1) / 2, by0 + h * (i + 0.8)), s, font=f, fill=(232, 232, 230), anchor="mm")
    return img


def maske(rgb):
    """Beyaz zeminden ayrılan ürün alanı (0..1), kenarı yumuşatılmış."""
    fark = 255.0 - rgb.min(axis=2)
    m = np.clip((fark - 6) / 14, 0, 1)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    return np.asarray(mi.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255


def ton_egrisi(x):
    """Filmik S eğrisi: gölgeler derinleşir, parlaklar yumuşak sıkışır (0..1)."""
    x = np.clip(x, 0, 1)
    s = x * x * (3 - 2 * x)
    return np.clip(0.70 * x + 0.30 * s, 0, 1) ** 0.98


def gercekci(img, tohum=7):
    rnd = np.random.default_rng(tohum)
    W, H = img.size
    img = img.resize((round(W * OLCEK), round(H * OLCEK)), Image.LANCZOS)
    rgb = np.asarray(img, np.float32)
    m = maske(rgb)[..., None]
    x = rgb / 255
    # renk dengesi: hafif sıcak beyaz dengesi + turuncu boyada doygunluk
    x = x * np.array([1.004, 1.0, 0.99])
    lum = (x @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    x = lum + (x - lum) * 1.03
    x = ton_egrisi(x)
    # yerel kontrast (clarity): geniş yarıçaplı keskinlik
    p = Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))
    p = p.filter(ImageFilter.UnsharpMask(radius=40, percent=28, threshold=0))
    x = np.asarray(p, np.float32) / 255
    # boya mikro dokusu (portakal kabuğu) ve hafif lekelenme: yalnız ürün üzerinde
    doku = rnd.normal(0, 1, (x.shape[0], x.shape[1])).astype(np.float32)
    doku = np.asarray(Image.fromarray(np.uint8(np.clip(doku * 40 + 128, 0, 255))).filter(ImageFilter.GaussianBlur(1.6)),
                      np.float32) / 128 - 1
    leke = rnd.normal(0, 1, (x.shape[0] // 64 + 2, x.shape[1] // 64 + 2)).astype(np.float32)
    leke = np.asarray(Image.fromarray(np.uint8(np.clip(leke * 40 + 128, 0, 255))).resize((x.shape[1], x.shape[0]),
                      Image.BICUBIC).filter(ImageFilter.GaussianBlur(20)), np.float32) / 128 - 1
    x = x * (1 + (0.026 * doku + 0.008 * leke)[..., None])
    # parlak noktalarda ışıma (yansıyan stüdyo ışığı)
    lum = x @ np.array([0.2126, 0.7152, 0.0722])
    parlak = np.clip((lum - 0.80) / 0.2, 0, 1)
    glow = np.asarray(Image.fromarray(np.uint8(parlak * 255)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    x = x + 0.10 * glow[..., None] * m
    # ince keskinlik + sensör greni (luminans ağırlıklı, gölgelerde biraz daha belirgin)
    p = Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70,
                                                                                                    threshold=1))
    x = np.asarray(p, np.float32) / 255
    gren = rnd.normal(0, 1, x.shape[:2]).astype(np.float32)[..., None] * 0.012 * (1.2 - lum[..., None])
    gren = gren + rnd.normal(0, 1, x.shape).astype(np.float32) * 0.003
    x = x + gren
    # ürünü saf beyaz zemine oturt
    x = x * m + (1 - m)
    return Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))


def main():
    girdi, cikti = sys.argv[1], sys.argv[2]
    img = Image.open(girdi).convert("RGB")
    if "--etiket" in sys.argv:
        v = sys.argv[sys.argv.index("--etiket") + 1].split(",")
        img = etiket_duzelt(img, tuple(int(k) for k in v[:4]), v[4])
    gercekci(img).save(cikti)
    print(cikti)


if __name__ == "__main__":
    main()
