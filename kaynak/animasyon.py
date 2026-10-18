"""
Beta Vinç - "Bir vincin yolculuğu" kurumsal animasyonu (2B, flat illüstrasyon).

Tek kirişli köprülü vinç: sipariş -> keşif/ölçü -> mühendislik -> imalat -> sevkiyat -> nakliye -> kurulum.

Kullanım:
    python animasyon.py <cikti.mp4> [baslangic_sn bitis_sn]   # aralık verilirse yalnız o kısım
    python animasyon.py --kare <sn> <cikti.png>             # tek kare önizleme
"""
import math
import random
import subprocess
import sys

import cairo

W, H, FPS = 1920, 1080, 30
ZEMIN = 880
FONT = "Inter"


def renk(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


C = dict(
    turuncu=renk("#E99A2A"), turuncu_a=renk("#F3B23D"), turuncu_k=renk("#C97F16"),
    antrasit=renk("#3C424B"), koyu=renk("#262A30"), gri=renk("#8A9099"), gri_a=renk("#C9CDD2"),
    zemin=renk("#E9E6E0"), duvar=renk("#F4F2EE"), beyaz=renk("#FFFFFF"), cam=renk("#BFD8EA"),
    mavi=renk("#163552"), mavi_a=renk("#2D5F8C"), kirmizi=renk("#E5483B"), yesil=renk("#3BAA5C"),
    gok=renk("#CFE6F5"), gok_a=renk("#F2F8FC"), tepe=renk("#B9D3A8"), tepe_k=renk("#8DB37A"),
    agac=renk("#5E9A63"), yol=renk("#55595F"), beton=renk("#B7B3AB"),
)


# ---------------------------------------------------------------- yardımcılar
def sinir(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def dilim(t, a, b):
    return sinir((t - a) / (b - a)) if b > a else float(t >= a)


def yumusak(x):
    x = sinir(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = sinir(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = sinir(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def geri(x):  # hafif taşmalı
    x = sinir(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_renk(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(4))


def boya(ctx, c, a=None):
    if a is None:
        ctx.set_source_rgba(*c)
    else:
        ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)


def kutu(ctx, x, y, w, h, c, r=0.0, a=None, cizgi=None, lw=2):
    if r:
        r = min(r, w / 2, h / 2)
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        ctx.close_path()
    else:
        ctx.rectangle(x, y, w, h)
    boya(ctx, c, a)
    if cizgi:
        ctx.fill_preserve()
        boya(ctx, cizgi)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def gradyan_kutu(ctx, x, y, w, h, c1, c2, r=0, dikey=True):
    g = cairo.LinearGradient(x, y, x if dikey else x + w, y + h if dikey else y)
    g.add_color_stop_rgba(0, *c1)
    g.add_color_stop_rgba(1, *c2)
    if r:
        kutu(ctx, x, y, w, h, (0, 0, 0, 0), r)
        ctx.new_path()
        r = min(r, w / 2, h / 2)
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        ctx.close_path()
    else:
        ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def daire(ctx, x, y, r, c, a=None):
    ctx.new_sub_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    boya(ctx, c, a)
    ctx.fill()


def cizgi(ctx, pts, c, lw=3, a=None, kesik=None, uc=cairo.LINE_CAP_ROUND):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    boya(ctx, c, a)
    ctx.set_line_width(lw)
    ctx.set_line_cap(uc)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if kesik:
        ctx.set_dash(kesik)
    ctx.stroke()
    ctx.set_dash([])


def cokgen(ctx, pts, c, a=None):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    boya(ctx, c, a)
    ctx.fill()


def yazi(ctx, s, x, y, boy, c, kalin=False, hiza="sol", a=None, aralik=0.0):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if kalin else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(boy)
    if aralik:
        gen = sum(ctx.text_extents(ch).x_advance for ch in s) + aralik * (len(s) - 1)
    else:
        gen = ctx.text_extents(s).x_advance
    if hiza == "orta":
        x -= gen / 2
    elif hiza == "sag":
        x -= gen
    boya(ctx, c, a)
    if aralik:
        for ch in s:
            ctx.move_to(x, y)
            ctx.show_text(ch)
            x += ctx.text_extents(ch).x_advance + aralik
    else:
        ctx.move_to(x, y)
        ctx.show_text(s)
    return gen


def golge(ctx, x, y, w, h=18, a=0.18):
    g = cairo.RadialGradient(x, y, 0, x, y, w / 2)
    g.add_color_stop_rgba(0, 0, 0, 0, a)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(1, h / w)
    ctx.translate(-x, -y)
    ctx.arc(x, y, w / 2, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def logo(ctx, x, y, boy, c_yazi=C["antrasit"], a=1.0, etiket=True):
    """beta logosu: kalın küçük harf 'beta' + turuncu alt çizgi."""
    gen = yazi(ctx, "beta", x, y, boy, c_yazi, kalin=True, a=a)
    kutu(ctx, x, y + boy * 0.12, gen, boy * 0.09, C["turuncu"], r=boy * 0.04, a=a)
    if etiket:
        yazi(ctx, "VİNÇ SİSTEMLERİ", x, y + boy * 0.42, boy * 0.2, c_yazi, a=a * 0.85, aralik=boy * 0.03)
    return gen


# ---------------------------------------------------------------- çizim parçaları
def insan(ctx, x, yz, boy=180, govde=C["antrasit"], baret=C["turuncu"], adim=0.0, kol=0.0, yuz_sag=True, yelek=True):
    """Basit flat insan figürü (ayakta). adim: yürüme fazı (radyan), kol: sağ kol açısı."""
    s = boy / 180
    kalca = yz - 95 * s
    # bacaklar
    for i, f in enumerate((0, math.pi)):
        a = math.sin(adim + f) * 0.35 if adim else 0
        ux, uy = math.sin(a) * 92 * s, math.cos(a) * 92 * s
        cizgi(ctx, [(x + (i - 0.5) * 10 * s, kalca), (x + (i - 0.5) * 10 * s + ux, kalca + uy)], C["koyu"], lw=17 * s)
        kutu(ctx, x + (i - 0.5) * 10 * s + ux - 9 * s, kalca + uy - 5 * s, 24 * s, 10 * s, C["koyu"], r=4 * s)
    # gövde
    kutu(ctx, x - 24 * s, yz - 165 * s + 22 * s, 48 * s, 78 * s, govde, r=14 * s)
    if yelek:
        kutu(ctx, x - 24 * s, yz - 130 * s, 48 * s, 7 * s, renk("#F7E36A"), a=0.95)
        kutu(ctx, x - 24 * s, yz - 112 * s, 48 * s, 7 * s, renk("#F7E36A"), a=0.95)
    # kollar
    yon = 1 if yuz_sag else -1
    omuz = (x + yon * 18 * s, yz - 133 * s)
    a = kol
    el = (omuz[0] + yon * math.cos(a) * 58 * s, omuz[1] + math.sin(a) * 58 * s)
    cizgi(ctx, [omuz, el], govde, lw=14 * s)
    sinv = math.sin(adim) * 0.4 if adim else 0.15
    omuz2 = (x - yon * 18 * s, yz - 133 * s)
    cizgi(ctx, [omuz2, (omuz2[0] - yon * math.sin(sinv) * 20 * s, omuz2[1] + 55 * s)], govde, lw=14 * s)
    # baş
    daire(ctx, x, yz - 165 * s, 20 * s, renk("#E8B48E"))
    if baret:
        ctx.new_sub_path()
        ctx.arc(x, yz - 168 * s, 22 * s, math.pi, 2 * math.pi)
        boya(ctx, baret)
        ctx.fill()
        kutu(ctx, x - 27 * s, yz - 170 * s, 54 * s, 6 * s, baret, r=3 * s)
    return el


def i_profil(ctx, x, y, w, h, c):
    kutu(ctx, x, y, w, h * 0.18, c)
    kutu(ctx, x, y + h * 0.82, w, h * 0.18, c)
    kutu(ctx, x + w * 0.42, y, w * 0.16, h, c)


def kopru_vinc(ctx, x0, x1, y_ray, kiris_y=None, ilerle=1.0, bas=True, caraskal=True, cx=None, kanca_y=None,
               yuk=None, renk_kiris=None, logo_goster=True, kiris_a=1.0):
    """Tek kirişli köprülü vinç (yan görünüş). y_ray: yürüyüş yolu ray üst kotu."""
    if kiris_y is None:
        kiris_y = y_ray - 92
    kc = renk_kiris or C["turuncu"]
    L = x1 - x0 + 70
    kx = x0 - 35
    # kiriş (kutu kiriş + ışık şeridi)
    gradyan_kutu(ctx, kx, kiris_y, L, 54, lerp_renk(kc, C["beyaz"], 0.18), lerp_renk(kc, C["koyu"], 0.15))
    kutu(ctx, kx, kiris_y - 6, L, 8, C["antrasit"], a=kiris_a)
    for i in range(1, 9):
        cizgi(ctx, [(kx + i * L / 9, kiris_y + 4), (kx + i * L / 9, kiris_y + 50)], C["koyu"], lw=1.5, a=0.12)
    if logo_goster:
        kutu(ctx, kx + L / 2 - 70, kiris_y + 12, 140, 30, C["beyaz"], r=4, a=0.95)
        yazi(ctx, "beta", kx + L / 2, kiris_y + 36, 24, C["antrasit"], kalin=True, hiza="orta")
    if bas:
        for xb in (x0, x1):
            kutu(ctx, xb - 70, kiris_y + 44, 140, 40, C["antrasit"], r=6)
            for dx in (-42, 42):
                daire(ctx, xb + dx, kiris_y + 84 - 2, 12, C["koyu"])
                daire(ctx, xb + dx, kiris_y + 84 - 2, 5, C["gri_a"])
            kutu(ctx, xb - 20, kiris_y + 52, 40, 22, C["turuncu_k"], r=4)
    if caraskal:
        if cx is None:
            cx = (x0 + x1) / 2
        ky = kiris_y + 54
        kutu(ctx, cx - 46, ky, 92, 18, C["koyu"], r=3)
        kutu(ctx, cx - 58, ky + 16, 116, 54, C["turuncu_k"], r=8)
        kutu(ctx, cx - 58, ky + 16, 34, 54, C["antrasit"], r=8)
        kutu(ctx, cx + 22, ky + 16, 36, 54, C["antrasit"], r=8)
        kutu(ctx, cx + 25, ky + 30, 28, 14, C["beyaz"], r=2)
        if kanca_y is None:
            kanca_y = ky + 160
        cizgi(ctx, [(cx - 6, ky + 70), (cx - 6, kanca_y)], C["gri"], lw=3)
        cizgi(ctx, [(cx + 6, ky + 70), (cx + 6, kanca_y)], C["gri"], lw=3)
        kutu(ctx, cx - 18, kanca_y, 36, 26, C["turuncu"], r=5)
        ctx.new_sub_path()
        ctx.arc(cx, kanca_y + 46, 14, -math.pi * 0.05, math.pi * 1.25)
        boya(ctx, C["koyu"])
        ctx.set_line_width(7)
        ctx.stroke()
        cizgi(ctx, [(cx, kanca_y + 26), (cx, kanca_y + 34)], C["koyu"], lw=7)
        if yuk:
            yw, yh, metin = yuk
            for dx in (-yw / 2 + 10, yw / 2 - 10):
                cizgi(ctx, [(cx, kanca_y + 52), (cx + dx, kanca_y + 110)], C["koyu"], lw=2.5)
            kutu(ctx, cx - yw / 2, kanca_y + 110, yw, yh, C["gri"], r=4)
            yazi(ctx, metin, cx, kanca_y + 110 + yh / 2 + 14, 36, C["beyaz"], kalin=True, hiza="orta")


def hol(ctx, x0, x1, y_ray, kolon_x, cati=True, ray=True, isik=True):
    """Müşteri üretim holü (iç mekan): duvar, kolonlar, konsollar, yürüyüş yolu kirişleri."""
    gradyan_kutu(ctx, 0, 0, W, ZEMIN, C["duvar"], renk("#E3E0DA"))
    if isik:
        for i in range(5):
            kutu(ctx, 160 + i * 360, 70, 200, 26, C["gok_a"], r=4, a=0.9)
    kutu(ctx, 0, ZEMIN, W, H - ZEMIN, C["zemin"])
    for i in range(14):
        cizgi(ctx, [(i * 150, ZEMIN), (i * 150 - 80, H)], C["gri"], lw=1, a=0.25)
    if cati:
        cizgi(ctx, [(0, 120), (W, 120)], C["gri"], lw=6, a=0.6)
        for i in range(16):
            xx = i * 130
            cizgi(ctx, [(xx, 120), (xx + 65, 40), (xx + 130, 120)], C["gri"], lw=3, a=0.4)
        cizgi(ctx, [(0, 40), (W, 40)], C["gri"], lw=5, a=0.5)
    for xk in kolon_x:
        kutu(ctx, xk - 34, 120, 68, ZEMIN - 120, C["beton"])
        kutu(ctx, xk - 34, 120, 14, ZEMIN - 120, renk("#A29E96"))
        kutu(ctx, xk - 34 if xk > W / 2 else xk + 20, y_ray + 34, 14 + 34 - 20, 46, C["beton"])
        if ray:
            yon = -1 if xk > W / 2 else 1
            i_profil(ctx, xk + yon * 60 - 36, y_ray, 72, 34, C["antrasit"])


def tir(ctx, x, yz, teker=0.0, yuk=None, s=1.0, ters=False):
    """Beta logolu tır (çekici + low-bed dorse). x: çekicinin ön tamponu. yuk(ctx, x_dorse_basi, y_dorse_ust)."""
    ctx.save()
    if ters:
        ctx.translate(x, 0)
        ctx.scale(-1, 1)
        ctx.translate(-x, 0)
    ctx.translate(x, yz)
    ctx.scale(s, s)
    golge(ctx, -520, 6, 1100, 22)
    # dorse
    kutu(ctx, -1010, -112, 820, 26, C["koyu"], r=4)
    kutu(ctx, -1010, -86, 820, 10, C["antrasit"])
    for i in range(10):
        kutu(ctx, -1000 + i * 82, -108, 60, 6, C["gri"], a=0.5)
    kutu(ctx, -260, -150, 70, 50, C["koyu"], r=6)  # boyun
    if yuk:
        yuk(ctx, -1010, -112)
    # çekici
    kutu(ctx, -230, -76, 230, 24, C["koyu"], r=4)
    gradyan_kutu(ctx, -150, -268, 150, 196, C["antrasit"], C["koyu"], r=16)
    kutu(ctx, -150, -268, 150, 30, C["turuncu"], r=10)
    kutu(ctx, -150, -248, 150, 12, C["turuncu"])
    kutu(ctx, -110, -228, 104, 70, C["cam"], r=10)
    kutu(ctx, -106, -224, 34, 62, C["beyaz"], r=8, a=0.35)
    kutu(ctx, -146, -140, 140, 20, C["turuncu"])
    yazi(ctx, "beta", -76, -96, 34, C["beyaz"], kalin=True, hiza="orta")
    kutu(ctx, -8, -120, 10, 28, C["gok_a"], r=3)
    kutu(ctx, -230, -170, 70, 96, C["antrasit"], r=8)
    # tekerlekler
    for wx in (-60, -205, -880, -800, -720):
        daire(ctx, wx, -26, 32, C["koyu"])
        daire(ctx, wx, -26, 15, C["gri_a"])
        for k in range(4):
            a = teker + k * math.pi / 2
            cizgi(ctx, [(wx, -26), (wx + math.cos(a) * 14, -26 + math.sin(a) * 14)], C["gri"], lw=3)
    ctx.restore()


def kiris_yuk(uzun=760):
    """Tır üzerindeki taşıma yükü: turuncu vinç kirişi + takozlar."""
    def ciz(ctx, xd, yd):
        for i in range(4):
            kutu(ctx, xd + 60 + i * (uzun - 100) / 3, yd - 14, 46, 14, renk("#9C7A4F"))
        gradyan_kutu(ctx, xd + 30, yd - 68, uzun, 54, C["turuncu_a"], C["turuncu_k"])
        kutu(ctx, xd + 30, yd - 74, uzun, 8, C["antrasit"])
        kutu(ctx, xd + 30 + uzun / 2 - 60, yd - 56, 120, 28, C["beyaz"], r=4, a=0.95)
        yazi(ctx, "beta", xd + 30 + uzun / 2, yd - 34, 22, C["antrasit"], kalin=True, hiza="orta")
        for i, xb in enumerate((xd + 40, xd + 30 + uzun - 130)):
            kutu(ctx, xb, yd - 14 - 40, 0, 0, C["antrasit"])
        # spanzet
        for xs in (xd + 200, xd + uzun - 140):
            cizgi(ctx, [(xs, yd - 74), (xs - 20, yd)], C["kirmizi"], lw=5, a=0.9)
    return ciz


def mobil_vinc(ctx, x, yz, uc, s=1.0):
    """Mobil vinç: taşıyıcı + teleskopik bom; uc: bom ucu (x, y) dünya koord. Döner: bom ucu."""
    px, py = x + 40 * s, yz - 190 * s
    golge(ctx, x, yz + 4, 520 * s, 20)
    kutu(ctx, x - 230 * s, yz - 120 * s, 470 * s, 70 * s, C["gri_a"], r=10 * s)
    kutu(ctx, x - 230 * s, yz - 120 * s, 470 * s, 16 * s, C["turuncu"], r=6 * s)
    kutu(ctx, x + 150 * s, yz - 200 * s, 110 * s, 86 * s, C["gri_a"], r=12 * s)
    kutu(ctx, x + 172 * s, yz - 188 * s, 70 * s, 40 * s, C["cam"], r=6 * s)
    for wx in (-180, -100, 120, 200):
        daire(ctx, x + wx * s, yz - 34 * s, 34 * s, C["koyu"])
        daire(ctx, x + wx * s, yz - 34 * s, 14 * s, C["gri"])
    kutu(ctx, x - 40 * s, yz - 210 * s, 150 * s, 92 * s, C["gri_a"], r=10 * s)
    kutu(ctx, x - 250 * s, yz - 60 * s, 30 * s, 60 * s, C["antrasit"])  # destek ayağı
    kutu(ctx, x + 230 * s, yz - 60 * s, 30 * s, 60 * s, C["antrasit"])
    ux, uy = uc
    a = math.atan2(uy - py, ux - px)
    L = math.hypot(ux - px, uy - py)
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(a)
    for i, (w, c) in enumerate(((34, C["turuncu_k"]), (26, C["turuncu"]), (18, C["turuncu_a"]))):
        kutu(ctx, i * L * 0.3 - 10, -w / 2, L * (1 - i * 0.3) + 10, w, c, r=6)
    ctx.restore()
    daire(ctx, px, py, 22 * s, C["antrasit"])
    daire(ctx, ux, uy, 12 * s, C["antrasit"])
    # piston
    cizgi(ctx, [(x - 10 * s, yz - 150 * s), (px + math.cos(a) * L * 0.35, py + math.sin(a) * L * 0.35)], C["gri"], lw=14 * s)
    return ux, uy


def kanca_ve_halat(ctx, uc, hy, yuk_genislik=0):
    cizgi(ctx, [uc, (uc[0], hy)], C["koyu"], lw=3)
    kutu(ctx, uc[0] - 14, hy, 28, 22, C["antrasit"], r=4)
    if yuk_genislik:
        for dx in (-yuk_genislik / 2, yuk_genislik / 2):
            cizgi(ctx, [(uc[0], hy + 22), (uc[0] + dx, hy + 92)], C["koyu"], lw=2.5)


def kivilcim(ctx, x, y, kare, n=26, yay=1.0):
    rnd = random.Random(kare * 7919)
    for _ in range(n):
        a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
        v = rnd.uniform(30, 140) * yay
        t = rnd.uniform(0.2, 1.0)
        ex, ey = x + math.cos(a) * v * t, y + math.sin(a) * v * t + 90 * t * t
        cizgi(ctx, [(x + math.cos(a) * v * t * 0.7, y + math.sin(a) * v * t * 0.7 + 50 * t * t), (ex, ey)],
              renk("#FFD36B"), lw=2.2, a=1 - t * 0.6)
    g = cairo.RadialGradient(x, y, 0, x, y, 60)
    g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.95)
    g.add_color_stop_rgba(0.3, 1, 0.75, 0.3, 0.45)
    g.add_color_stop_rgba(1, 1, 0.6, 0.2, 0)
    ctx.arc(x, y, 60, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()


def onay(ctx, x, y, r, t, c=C["yesil"]):
    if t <= 0:
        return
    s = geri(dilim(t, 0, 0.5))
    daire(ctx, x, y, r * s, c)
    p = dilim(t, 0.3, 0.8)
    if p > 0:
        pts = [(x - r * 0.45, y), (x - r * 0.12, y + r * 0.32), (x + r * 0.5, y - r * 0.35)]
        L1 = math.dist(pts[0], pts[1])
        L2 = math.dist(pts[1], pts[2])
        d = p * (L1 + L2)
        if d <= L1:
            q = [pts[0], (lerp(pts[0][0], pts[1][0], d / L1), lerp(pts[0][1], pts[1][1], d / L1))]
        else:
            k = (d - L1) / L2
            q = [pts[0], pts[1], (lerp(pts[1][0], pts[2][0], k), lerp(pts[1][1], pts[2][1], k))]
        cizgi(ctx, q, C["beyaz"], lw=r * 0.18)


def olcu_cizgisi(ctx, a, b, metin, c=C["kirmizi"], ilerle=1.0, boy=30, ofs=-34, zemin=C["beyaz"]):
    ax, ay = a
    bx, by = lerp(a[0], b[0], ilerle), lerp(a[1], b[1], ilerle)
    cizgi(ctx, [(ax, ay), (bx, by)], c, lw=3)
    for (px, py) in ((ax, ay),) + (((bx, by),) if ilerle > 0.98 else ()):
        if ay == by:
            cizgi(ctx, [(px, py - 16), (px, py + 16)], c, lw=3)
        else:
            cizgi(ctx, [(px - 16, py), (px + 16, py)], c, lw=3)
    if metin:
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if ay == by:
            kutu(ctx, mx - 120, my + ofs - 34, 240, 46, zemin, r=8, a=0.9)
            yazi(ctx, metin, mx, my + ofs, boy, c, kalin=True, hiza="orta")
        else:
            kutu(ctx, mx + 18, my - 26, 210, 46, zemin, r=8, a=0.9)
            yazi(ctx, metin, mx + 32, my + 8, boy, c, kalin=True)


# ---------------------------------------------------------------- ortak arayüz
ADIMLAR = ["Sipariş", "Keşif ve Ölçü", "Mühendislik", "İmalat", "Sevkiyat", "Nakliye", "Kurulum ve Test"]


def baslik_karti(ctx, no, baslik, alt, t, koyu_zemin=False):
    p = ease_out(dilim(t, 0.2, 1.0))
    a = sinir(p)
    x = lerp(-620, 80, p)
    y = 136
    kutu(ctx, x, y, 600, 120, C["koyu"], r=18, a=0.88 * a)
    kutu(ctx, x, y, 12, 120, C["turuncu"], r=6, a=a)
    yazi(ctx, f"{no:02d}", x + 36, y + 84, 70, C["turuncu"], kalin=True, a=a)
    yazi(ctx, baslik, x + 156, y + 56, 38, C["beyaz"], kalin=True, a=a)
    yazi(ctx, alt, x + 156, y + 96, 22, C["gri_a"], a=a)


def ilerleme_cubugu(ctx, adim, t_adim):
    y = 1010
    x0, x1 = 160, W - 160
    kutu(ctx, x0, y - 3, x1 - x0, 6, C["koyu"], r=3, a=0.18)
    n = len(ADIMLAR)
    oran = (adim + sinir(t_adim)) / (n - 1) if adim < n - 1 else 1.0
    kutu(ctx, x0, y - 3, (x1 - x0) * sinir(oran), 6, C["turuncu"], r=3)
    for i, ad in enumerate(ADIMLAR):
        xx = x0 + i * (x1 - x0) / (n - 1)
        aktif = i <= adim
        daire(ctx, xx, y, 13 if i == adim else 9, C["turuncu"] if aktif else C["gri_a"])
        if i == adim:
            daire(ctx, xx, y, 5, C["beyaz"])
        yazi(ctx, ad, xx, y + 44, 21 if i == adim else 18, C["koyu"] if i == adim else C["gri"],
             kalin=i == adim, hiza="orta")


def kose_logo(ctx, a=1.0, acik=False):
    kutu(ctx, 60, 44, 168, 70, C["beyaz"] if not acik else C["koyu"], r=12, a=0.9 * a)
    logo(ctx, 82, 94, 46, C["antrasit"] if not acik else C["beyaz"], a=a, etiket=False)


# ---------------------------------------------------------------- sahneler
def s_acilis(ctx, t, kare):
    gradyan_kutu(ctx, 0, 0, W, H, C["antrasit"], C["koyu"])
    # arka planda ince vinç silüeti
    a = dilim(t, 0.3, 1.5) * 0.12
    ctx.save()
    ctx.translate(0, 80)
    for xx in range(-200, W + 200, 120):
        cizgi(ctx, [(xx + t * 30, 200), (xx + 60 + t * 30, 130), (xx + 120 + t * 30, 200)], C["beyaz"], lw=2, a=a)
    cizgi(ctx, [(0, 200), (W, 200), ], C["beyaz"], lw=3, a=a)
    cizgi(ctx, [(0, 130), (W, 130)], C["beyaz"], lw=3, a=a)
    ctx.restore()
    s = geri(dilim(t, 0.3, 1.3))
    ctx.save()
    ctx.translate(W / 2, 470)
    ctx.scale(s, s)
    yazi(ctx, "beta", 0, 0, 230, C["beyaz"], kalin=True, hiza="orta", a=sinir(s))
    ctx.restore()
    gen = 470 * ease_out(dilim(t, 1.0, 1.8))
    kutu(ctx, W / 2 - 235, 500, gen, 20, C["turuncu"], r=8)
    yazi(ctx, "VİNÇ SİSTEMLERİ", W / 2, 572, 34, C["gri_a"], hiza="orta", a=dilim(t, 1.4, 2.0), aralik=10)
    a2 = dilim(t, 2.4, 3.2)
    yazi(ctx, "Bir vincin yolculuğu", W / 2, 720, 64, C["beyaz"], kalin=True, hiza="orta", a=a2)
    yazi(ctx, "Tek kirişli köprülü vinç  ·  siparişten kuruluma", W / 2, 776, 32, C["turuncu"], hiza="orta", a=a2)


def ofis_arka(ctx):
    gradyan_kutu(ctx, 0, 0, W, ZEMIN, renk("#F6F3EE"), renk("#ECE8E1"))
    kutu(ctx, 0, ZEMIN, W, H - ZEMIN, renk("#D9D3C9"))
    # pencere
    kutu(ctx, 120, 150, 520, 380, C["gok"], r=10)
    for i in range(3):
        kutu(ctx, 140 + i * 160, 300 - i * 40, 120, 230 + i * 40, renk("#A8C3D8"))
    cizgi(ctx, [(380, 150), (380, 530)], C["beyaz"], lw=10)
    cizgi(ctx, [(120, 340), (640, 340)], C["beyaz"], lw=10)
    kutu(ctx, 120, 150, 520, 380, (0, 0, 0, 0), r=10, cizgi=C["beyaz"], lw=12)
    # masa
    kutu(ctx, 260, 640, 760, 26, renk("#8C6A48"), r=6)
    kutu(ctx, 300, 666, 22, ZEMIN - 666, renk("#6E5236"))
    kutu(ctx, 960, 666, 22, ZEMIN - 666, renk("#6E5236"))


def s_siparis(ctx, t, kare):
    ofis_arka(ctx)
    # müşteri + dizüstü
    insan(ctx, 420, ZEMIN, boy=200, govde=renk("#2D5F8C"), baret=None, yelek=False, kol=-0.25)
    kutu(ctx, 560, 540, 260, 100, C["antrasit"], r=8)
    kutu(ctx, 572, 552, 236, 80, C["cam"], r=4)
    kutu(ctx, 530, 636, 320, 12, C["koyu"], r=4)
    # ekrandaki gönder butonu
    p = dilim(t, 0.8, 2.0)
    kutu(ctx, 600, 590, 180, 28, C["turuncu"], r=6, a=0.5 + 0.5 * p)
    yazi(ctx, "Teklif iste", 690, 610, 18, C["beyaz"], kalin=True, hiza="orta")
    # uçan zarf
    z = ease_io(dilim(t, 2.0, 3.0))
    if 0 < z < 1:
        zx, zy = lerp(690, 1230, z), lerp(580, 300, z) - math.sin(z * math.pi) * 140
        kutu(ctx, zx - 34, zy - 22, 68, 44, C["beyaz"], r=4, cizgi=C["turuncu"], lw=3)
        cizgi(ctx, [(zx - 34, zy - 22), (zx, zy + 4), (zx + 34, zy - 22)], C["turuncu"], lw=3)
    # sipariş kartı
    k = ease_out(dilim(t, 2.8, 3.8))
    kx, ky = lerp(W + 50, 1130, k), 200
    golge(ctx, kx + 330, ky + 640, 600, 30, 0.12 * k)
    kutu(ctx, kx, ky, 660, 610, C["beyaz"], r=18)
    kutu(ctx, kx, ky, 660, 90, C["antrasit"], r=18)
    kutu(ctx, kx, ky + 60, 660, 30, C["antrasit"])
    logo(ctx, kx + 30, ky + 62, 44, C["beyaz"], etiket=False)
    yazi(ctx, "SİPARİŞ FORMU", kx + 630, ky + 58, 26, C["turuncu"], kalin=True, hiza="sag", aralik=2)
    alanlar = [("Ürün", "Tek kirişli köprülü vinç"), ("Kapasite", "5 ton"), ("Açıklık", "12 m"),
               ("Kaldırma yüksekliği", "6 m"), ("Kumanda", "Butonyer + uzaktan kumanda"), ("Teslim", "Kurulum dahil")]
    for i, (et, deger) in enumerate(alanlar):
        yy = ky + 150 + i * 70
        p = dilim(t, 3.6 + i * 0.45, 4.2 + i * 0.45)
        yazi(ctx, et, kx + 40, yy, 22, C["gri"])
        n = int(len(deger) * p)
        yazi(ctx, deger[:n], kx + 330, yy, 26, C["koyu"], kalin=True)
        cizgi(ctx, [(kx + 40, yy + 18), (kx + 620, yy + 18)], C["gri_a"], lw=1.5)
    # onay damgası
    d = dilim(t, 7.0, 7.6)
    if d > 0:
        s = lerp(2.2, 1.0, ease_out(d))
        ctx.save()
        ctx.translate(kx + 470, ky + 560)
        ctx.rotate(-0.18)
        ctx.scale(s, s)
        kutu(ctx, -150, -42, 300, 72, (0, 0, 0, 0), r=10, cizgi=C["yesil"], lw=6)
        yazi(ctx, "ONAYLANDI", 0, 12, 40, C["yesil"], kalin=True, hiza="orta", a=sinir(d * 2))
        ctx.restore()
    baslik_karti(ctx, 1, "Sipariş", "İhtiyaç dinlenir, teklif ve sipariş netleşir", t)


def s_kesif(ctx, t, kare):
    xl, xr, yr = 360, 1560, 400
    hol(ctx, xl, xr, yr, [300, 1620])
    # teknisyen yürüyüp gelir
    w = ease_out(dilim(t, 0.0, 2.0))
    tx = lerp(-100, 520, w)
    adim = t * 9 if w < 0.99 else 0
    el = insan(ctx, tx, ZEMIN, boy=190, kol=-0.55 if w > 0.99 else 0.2, adim=adim)
    # lazer metre ölçümü (açıklık)
    p = dilim(t, 2.4, 4.6)
    if w > 0.99:
        kutu(ctx, el[0] - 10, el[1] - 14, 30, 22, C["turuncu"], r=4)
    if p > 0:
        cizgi(ctx, [(xl + 60, yr + 17), (lerp(xl + 60, xr - 60, ease_io(p)), yr + 17)], C["kirmizi"], lw=3, a=0.9)
        olcu_cizgisi(ctx, (xl + 24, yr - 60), (xr - 24, yr - 60), f"{int(12000 * ease_io(p)):,} mm".replace(",", "."),
                     ilerle=ease_io(p))
    # yükseklik ölçümü
    p2 = dilim(t, 4.8, 6.6)
    if p2 > 0:
        olcu_cizgisi(ctx, (W / 2 + 260, ZEMIN), (W / 2 + 260, lerp(ZEMIN, yr, ease_io(p2))),
                     f"{int(7500 * ease_io(p2)):,} mm".replace(",", "."), ilerle=1.0)
    # tablet notları
    tb = ease_out(dilim(t, 6.6, 7.4))
    if tb > 0:
        tx0, ty0 = lerp(W + 40, 1290, tb), 420
        kutu(ctx, tx0, ty0, 420, 330, C["antrasit"], r=22)
        kutu(ctx, tx0 + 16, ty0 + 16, 388, 298, C["beyaz"], r=12)
        yazi(ctx, "Keşif raporu", tx0 + 40, ty0 + 66, 28, C["koyu"], kalin=True)
        maddeler = ["Ray açıklığı 12.000 mm", "Ray kotu 7.500 mm", "Yürüyüş yolu kontrolü", "Enerji beslemesi"]
        for i, m in enumerate(maddeler):
            yy = ty0 + 118 + i * 50
            onay(ctx, tx0 + 56, yy - 8, 15, dilim(t, 7.4 + i * 0.35, 8.0 + i * 0.35))
            yazi(ctx, m, tx0 + 84, yy, 22, C["koyu"])
    baslik_karti(ctx, 2, "Keşif ve Ölçü", "Sahada ray açıklığı ve kotlar ölçülür", t)


def s_muhendislik(ctx, t, kare):
    gradyan_kutu(ctx, 0, 0, W, H, C["mavi"], renk("#0F2740"))
    for i in range(0, W, 40):
        cizgi(ctx, [(i, 0), (i, H)], C["beyaz"], lw=1, a=0.06 if i % 200 else 0.12)
    for j in range(0, H, 40):
        cizgi(ctx, [(0, j), (W, j)], C["beyaz"], lw=1, a=0.06 if j % 200 else 0.12)
    p = lambda a, b: ease_io(dilim(t, a, b))  # noqa: E731
    mavi = renk("#DDEBFA")
    x0, x1, yk = 420, 1500, 470

    def ciz_kismi(pts, prog, lw=3):
        if prog <= 0:
            return
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        d = prog * L
        q = [pts[0]]
        for i in range(len(pts) - 1):
            s = math.dist(pts[i], pts[i + 1])
            if d >= s:
                q.append(pts[i + 1])
                d -= s
            else:
                k = d / s
                q.append((lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)))
                break
        cizgi(ctx, q, mavi, lw=lw)

    ciz_kismi([(x0, yk), (x1, yk), (x1, yk + 60), (x0, yk + 60), (x0, yk)], p(0.3, 1.8))
    for xb in (x0 + 40, x1 - 40):
        ciz_kismi([(xb - 70, yk + 60), (xb + 70, yk + 60), (xb + 70, yk + 104), (xb - 70, yk + 104), (xb - 70, yk + 60)],
                  p(1.2, 2.2), lw=2.5)
    for xk in (x0 - 40, x1 + 40):
        ciz_kismi([(xk, yk + 120), (xk, 870)], p(1.6, 2.6), lw=2.5)
    cx = 960
    ciz_kismi([(cx - 55, yk + 60), (cx + 55, yk + 60), (cx + 55, yk + 130), (cx - 55, yk + 130), (cx - 55, yk + 60)],
              p(2.2, 3.0), lw=2.5)
    ciz_kismi([(cx, yk + 130), (cx, yk + 300)], p(2.8, 3.3), lw=2)
    if t > 3.2:
        a = dilim(t, 3.2, 3.8)
        olcu_cizgisi(ctx, (x0 + 40, yk - 70), (x1 - 40, yk - 70), "12.000", c=renk("#FFD36B"), ilerle=a, ofs=-24,
                     zemin=renk("#0F2740"))
        yazi(ctx, "TEK KİRİŞLİ KÖPRÜLÜ VİNÇ  ·  5 t", W / 2 + 200, 330, 40, mavi, kalin=True, hiza="orta", a=a, aralik=2)
    if t > 3.8:
        a = dilim(t, 3.8, 4.4)
        for i, s in enumerate(["Statik hesap", "3B model", "İmalat resimleri"]):
            onay(ctx, 520 + i * 360, 930, 20, dilim(t, 3.9 + i * 0.4, 4.6 + i * 0.4))
            yazi(ctx, s, 552 + i * 360, 940, 28, mavi, a=a)
    baslik_karti(ctx, 3, "Mühendislik", "Statik hesap, 3B model ve imalat resimleri", t)


def fabrika_arka(ctx):
    gradyan_kutu(ctx, 0, 0, W, ZEMIN, renk("#EDEAE4"), renk("#DAD6CF"))
    kutu(ctx, 0, ZEMIN, W, H - ZEMIN, renk("#CFCBC3"))
    for i in range(6):
        kutu(ctx, 100 + i * 330, 110, 210, 120, C["gok"], r=6, a=0.8)
    # tavan vinci (fabrika içi)
    kutu(ctx, 0, 270, W, 14, C["antrasit"], a=0.7)
    kutu(ctx, 520, 250, 880, 34, C["turuncu"], a=0.85)
    yazi(ctx, "BETA ÜRETİM MERKEZİ", W - 90, 210, 30, C["antrasit"], kalin=True, hiza="sag", aralik=3)
    cizgi(ctx, [(0, 300), (W, 300)], C["gri"], lw=2, a=0.3)
    # sehpalar
    for xs in (560, 1360):
        cokgen(ctx, [(xs - 50, ZEMIN), (xs - 10, 700), (xs + 10, 700), (xs + 50, ZEMIN)], C["antrasit"])


def s_imalat(ctx, t, kare):
    fabrika_arka(ctx)
    gx0, gx1, gy = 420, 1500, 640
    boyama = ease_io(dilim(t, 4.0, 7.2))
    ham = renk("#9AA0A8")
    # kiriş: boyama sağdan sola renk değişimi (boya kabini)
    sinir_x = lerp(gx1, gx0, boyama)
    gradyan_kutu(ctx, gx0, gy, gx1 - gx0, 60, lerp_renk(ham, C["beyaz"], 0.15), lerp_renk(ham, C["koyu"], 0.15))
    if boyama > 0:
        gradyan_kutu(ctx, sinir_x, gy, gx1 - sinir_x, 60, C["turuncu_a"], C["turuncu_k"])
    kutu(ctx, gx0, gy - 8, gx1 - gx0, 8, C["antrasit"])
    for i in range(1, 9):
        cizgi(ctx, [(gx0 + i * (gx1 - gx0) / 9, gy + 4), (gx0 + i * (gx1 - gx0) / 9, gy + 56)], C["koyu"], lw=1.5, a=0.15)
    # kaynak: kaynakçı kiriş boyunca ilerler
    k = dilim(t, 0.4, 3.8)
    if 0 < k < 1:
        kx = lerp(gx0 + 80, gx1 - 80, k)
        el = insan(ctx, kx - 70, ZEMIN, boy=190, kol=-0.7, baret=C["antrasit"])
        kutu(ctx, kx - 92, ZEMIN - 210, 44, 34, C["koyu"], r=6)  # kaynak maskesi
        cizgi(ctx, [el, (kx, gy + 58)], C["koyu"], lw=6)
        kivilcim(ctx, kx, gy + 60, kare)
        cizgi(ctx, [(gx0 + 80, gy + 60), (kx, gy + 60)], renk("#6E737B"), lw=4)
    elif k >= 1 and t < 7.4:
        # boya tabancası
        bx = sinir_x
        insan(ctx, bx + 80, ZEMIN, boy=190, kol=-0.9, yuz_sag=False, baret=None, govde=renk("#F1F1F1"), yelek=False)
        for i in range(14):
            rnd = random.Random(kare * 31 + i)
            daire(ctx, bx + rnd.uniform(-20, 30), gy + rnd.uniform(0, 60), rnd.uniform(4, 10), C["turuncu_a"], a=0.35)
    # montaj: baş arabaları ve caraskal
    m = ease_out(dilim(t, 7.4, 8.8))
    if m > 0:
        for xb, yon in ((gx0 + 40, -1), (gx1 - 40, 1)):
            x = xb + yon * (1 - m) * 500
            kutu(ctx, x - 70, gy + 52, 140, 40, C["antrasit"], r=6)
            for dx in (-42, 42):
                daire(ctx, x + dx, gy + 92, 12, C["koyu"])
    h = ease_out(dilim(t, 8.6, 9.8))
    if h > 0:
        cx = 960
        cy = lerp(300, gy + 60, h)
        cizgi(ctx, [(cx, 284), (cx, cy)], C["koyu"], lw=3)
        kutu(ctx, cx - 58, cy, 116, 54, C["turuncu_k"], r=8)
        kutu(ctx, cx - 58, cy, 34, 54, C["antrasit"], r=8)
        kutu(ctx, cx + 22, cy, 36, 54, C["antrasit"], r=8)
    if boyama >= 1:
        kutu(ctx, (gx0 + gx1) / 2 - 70, gy + 15, 140, 30, C["beyaz"], r=4, a=dilim(t, 7.2, 7.6))
        yazi(ctx, "beta", (gx0 + gx1) / 2, gy + 39, 24, C["antrasit"], kalin=True, hiza="orta", a=dilim(t, 7.2, 7.6))
    # kalite kontrol rozeti
    q = dilim(t, 10.0, 11.0)
    if q > 0:
        s = geri(q)
        ctx.save()
        ctx.translate(1600, 470)
        ctx.scale(s, s)
        daire(ctx, 0, 0, 120, C["yesil"])
        daire(ctx, 0, 0, 104, (0, 0, 0, 0))
        ctx.arc(0, 0, 104, 0, 2 * math.pi)
        boya(ctx, C["beyaz"])
        ctx.set_line_width(4)
        ctx.stroke()
        yazi(ctx, "KALİTE", 0, -18, 32, C["beyaz"], kalin=True, hiza="orta")
        yazi(ctx, "KONTROL", 0, 20, 32, C["beyaz"], kalin=True, hiza="orta")
        yazi(ctx, "✓", 0, 70, 44, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    alt = "Kesim, kaynak, boya ve montaj" if t < 10 else "Kalite kontrol ve yük testi"
    baslik_karti(ctx, 4, "İmalat", alt, t)


def avlu_arka(ctx):
    gradyan_kutu(ctx, 0, 0, W, ZEMIN, C["gok"], C["gok_a"])
    # fabrika cephesi
    kutu(ctx, 980, 260, 1000, ZEMIN - 260, renk("#E4E1DB"))
    cokgen(ctx, [(960, 270), (1480, 170), (2000, 270)], renk("#D2CEC7"))
    for i in range(4):
        kutu(ctx, 1040 + i * 220, 330, 160, 90, C["cam"], r=4)
    kutu(ctx, 1080, 520, 380, ZEMIN - 520, renk("#B8B4AD"))
    for j in range(8):
        cizgi(ctx, [(1080, 530 + j * 44), (1460, 530 + j * 44)], C["gri"], lw=2, a=0.4)
    kutu(ctx, 1520, 470, 320, 110, C["antrasit"], r=10)
    logo(ctx, 1550, 540, 58, C["beyaz"], etiket=False)
    yazi(ctx, "ÜRETİM MERKEZİ", 1720, 540, 20, C["turuncu"], kalin=True, aralik=2)
    kutu(ctx, 0, ZEMIN, W, H - ZEMIN, renk("#BDB9B2"))
    for i in range(12):
        cizgi(ctx, [(i * 180, ZEMIN + 40), (i * 180 + 100, ZEMIN + 40)], C["beyaz"], lw=4, a=0.5)


def s_yukleme(ctx, t, kare):
    avlu_arka(ctx)
    tir_x = 1520
    dorse_bas = tir_x - 1010
    dorse_ust = ZEMIN - 112
    hedef_x = dorse_bas + 30 + 380  # kiriş merkezi
    # kirişin yolu: yerden kalk -> yüksel -> sağa -> in
    p1 = ease_io(dilim(t, 0.8, 2.4))
    p2 = ease_io(dilim(t, 2.4, 4.4))
    p3 = ease_io(dilim(t, 4.4, 5.6))
    bx0, by0 = 300, ZEMIN - 60  # yerdeki kiriş merkezi (üst)
    lx = lerp(bx0, hedef_x, p2)
    ly = lerp(by0, 420, p1) if p3 == 0 else lerp(420, dorse_ust - 74, p3)
    if p2 < 1 and p3 == 0:
        ly = lerp(by0, 420, p1)
    # mobil vinç solda, bom ucu yükün üstünde
    mobil_vinc(ctx, -60, ZEMIN, (lx, 220), s=1.0)
    teker = 0
    yerde = t >= 5.6

    def yuk(c, xd, yd):
        if yerde:
            kiris_yuk()(c, xd, yd)
    tir(ctx, tir_x, ZEMIN, teker, yuk=yuk)
    if not yerde:
        kanca_ve_halat(ctx, (lx, 220), ly - 120, 600)
        gx = lx - 380
        gradyan_kutu(ctx, gx, ly - 54, 760, 54, C["turuncu_a"], C["turuncu_k"])
        kutu(ctx, gx, ly - 60, 760, 8, C["antrasit"])
        kutu(ctx, lx - 60, ly - 42, 120, 28, C["beyaz"], r=4, a=0.95)
        yazi(ctx, "beta", lx, ly - 20, 22, C["antrasit"], kalin=True, hiza="orta")
        golge(ctx, lx, ZEMIN + 6, 700 * (1 - 0.5 * p1), 18, 0.16)
    else:
        kanca_ve_halat(ctx, (lx, 220), lerp(dorse_ust - 194, 300, ease_io(dilim(t, 5.8, 7.0))), 0)
    if t > 6.4:
        onay(ctx, 1620, 380, 46, dilim(t, 6.4, 7.2))
        yazi(ctx, "Sevkiyata hazır", 1690, 394, 36, C["koyu"], kalin=True, a=dilim(t, 6.6, 7.2))
    baslik_karti(ctx, 5, "Sevkiyat", "Ürün güvenle tıra yüklenir ve sabitlenir", t)


def s_nakliye(ctx, t, kare):
    gradyan_kutu(ctx, 0, 0, W, 700, renk("#A9D3EF"), C["gok_a"])
    # güneş, bulutlar
    daire(ctx, 1600, 170, 70, renk("#FFE7A3"))
    for i, (bx, by, bs) in enumerate(((300, 160, 1.0), (900, 110, 0.8), (1350, 200, 1.2))):
        x = (bx - t * 20 * (i + 1)) % (W + 400) - 200
        for dx, r in ((0, 40), (40, 52), (90, 38)):
            daire(ctx, x + dx * bs, by, r * bs, C["beyaz"], a=0.95)
    # uzak tepeler (parallax)
    for katman, (renk1, hiz, yuk, gen) in enumerate(((C["tepe"], 60, 640, 0.004), (C["tepe_k"], 140, 690, 0.007))):
        pts = [(0, 760)]
        for x in range(0, W + 20, 20):
            pts.append((x, yuk - 60 * math.sin((x + t * hiz) * gen) - 30 * math.sin((x + t * hiz) * gen * 2.3)))
        pts.append((W, 760))
        cokgen(ctx, pts, renk1)
    # ağaçlar
    for i in range(14):
        x = (i * 190 - t * 420) % (W + 200) - 100
        kutu(ctx, x - 6, 690, 12, 50, renk("#6B4F35"))
        daire(ctx, x, 670, 36, C["agac"])
    # yol
    kutu(ctx, 0, 740, W, H - 740, C["yol"])
    kutu(ctx, 0, 740, W, 10, renk("#7A7E84"))
    for i in range(12):
        x = (i * 220 - t * 900) % (W + 220) - 110
        kutu(ctx, x, 905, 120, 12, C["beyaz"], r=3)
    # tır (yerinde, hafif titreşim)
    zipla = math.sin(t * 22) * 1.5
    tir(ctx, 1500, 880 + zipla, teker=t * 14, yuk=kiris_yuk())
    # rota kartı
    a = ease_out(dilim(t, 0.6, 1.4))
    kx, ky = lerp(W + 40, 1380, a), 60
    kutu(ctx, kx, ky, 480, 300, C["beyaz"], r=18, a=0.96)
    pts = [(kx + 70, ky + 230), (kx + 160, ky + 150), (kx + 260, ky + 190), (kx + 330, ky + 110), (kx + 410, ky + 90)]
    cizgi(ctx, pts, C["gri_a"], lw=8)
    pr = ease_io(dilim(t, 1.2, 7.8))
    L = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    d = pr * sum(L)
    q = [pts[0]]
    for i, s in enumerate(L):
        if d >= s:
            q.append(pts[i + 1])
            d -= s
        else:
            q.append((lerp(pts[i][0], pts[i + 1][0], d / s), lerp(pts[i][1], pts[i + 1][1], d / s)))
            break
    cizgi(ctx, q, C["turuncu"], lw=8)
    daire(ctx, *pts[0], 12, C["antrasit"])
    daire(ctx, *pts[-1], 12, C["yesil"] if pr >= 1 else C["gri"])
    daire(ctx, *q[-1], 14, C["turuncu"])
    yazi(ctx, "Beta Üretim Merkezi", kx + 40, ky + 270, 20, C["koyu"], kalin=True)
    yazi(ctx, "Müşteri tesisi", kx + 440, ky + 60, 20, C["koyu"], kalin=True, hiza="sag")
    baslik_karti(ctx, 6, "Nakliye", "Planlı rota, sigortalı ve takipli taşıma", t)


def s_kurulum(ctx, t, kare):
    xl, xr, yr = 360, 1560, 400
    hol(ctx, xl, xr, yr, [300, 1620])
    # tır içeri girer
    g = ease_out(dilim(t, 0.0, 2.0))
    tir_x = lerp(-200, 1700, g)
    kalk = ease_io(dilim(t, 2.4, 5.4))  # kiriş kaldırma
    tasindi = t >= 2.4
    dorse_ust = ZEMIN - 112
    yuk = None if tasindi else kiris_yuk(760)
    tir_cik = ease_io(dilim(t, 5.6, 7.0))
    tir(ctx, tir_x + tir_cik * 1600, ZEMIN, teker=t * 10, yuk=yuk)
    # kiriş kalkıyor: tır üzerinden yürüyüş yolu kotuna, sonra açıklığa oturur
    kiris_hedef_y = yr - 92
    if tasindi:
        bas_y = dorse_ust - 74
        ky = lerp(bas_y, kiris_hedef_y - 40, kalk)
        oturt = ease_io(dilim(t, 5.4, 6.4))
        ky = lerp(ky, kiris_hedef_y, oturt) if kalk >= 1 else ky
        # zincir askısı (çatı makarasından)
        if oturt < 1:
            cizgi(ctx, [(W / 2, 40), (W / 2, ky - 80)], C["koyu"], lw=3)
            for dx in (-420, 420):
                cizgi(ctx, [(W / 2, ky - 80), (W / 2 + dx, ky)], C["koyu"], lw=2.5)
            kutu(ctx, W / 2 - 20, ky - 100, 40, 26, C["antrasit"], r=4)
        bas = t >= 6.6
        car = ease_out(dilim(t, 7.2, 8.6))
        kanca_in = ease_io(dilim(t, 8.6, 9.6))
        yuk_kalk = ease_io(dilim(t, 10.0, 11.4))
        gez = ease_io(dilim(t, 11.4, 12.8))
        if not bas:
            # kiriş tek başına
            x0, x1 = xl, xr
            L = x1 - x0 + 70
            gradyan_kutu(ctx, x0 - 35, ky, L, 54, C["turuncu_a"], C["turuncu_k"])
            kutu(ctx, x0 - 35, ky - 6, L, 8, C["antrasit"])
            kutu(ctx, W / 2 - 70, ky + 12, 140, 30, C["beyaz"], r=4, a=0.95)
            yazi(ctx, "beta", W / 2, ky + 36, 24, C["antrasit"], kalin=True, hiza="orta")
        else:
            cx = lerp(W / 2 + 900, 760, car) if car < 1 else lerp(760, 1200, gez)
            kanca_y = lerp(kiris_hedef_y + 130, ZEMIN - 230, kanca_in)
            kanca_y = lerp(kanca_y, ZEMIN - 420, yuk_kalk)
            yuk_ciz = (180, 120, "5 t") if t >= 10.0 else None
            kopru_vinc(ctx, xl, xr, yr, kiris_y=kiris_hedef_y, caraskal=car > 0, cx=cx, kanca_y=kanca_y, yuk=yuk_ciz)
            if t < 10.0 and kanca_in > 0.5:
                kutu(ctx, 760 - 90, ZEMIN - 120, 180, 120, C["gri"], r=4)
                yazi(ctx, "5 t", 760, ZEMIN - 46, 36, C["beyaz"], kalin=True, hiza="orta")
            # cıvata parıltıları (baş arabaları bağlantısı)
            pb = dilim(t, 6.6, 7.2)
            if 0 < pb < 1:
                for xb in (xl, xr):
                    for dx in (-30, 0, 30):
                        daire(ctx, xb + dx, kiris_hedef_y + 64, 10 * math.sin(pb * math.pi), renk("#FFF3C4"), a=0.9)
    if t > 12.4:
        onay(ctx, 1660, 520, 50, dilim(t, 12.4, 13.0))
    alt = "Kiriş montajı, bağlantılar ve yük testi" if t < 10 else "Yük testi tamam, devreye alma"
    baslik_karti(ctx, 7, "Kurulum ve Test", alt, t)


def s_kapanis(ctx, t, kare):
    gradyan_kutu(ctx, 0, 0, W, H, C["turuncu"], C["turuncu_k"])
    a = dilim(t, 0.2, 1.0)
    ctx.save()
    ctx.translate(0, 120)
    ctx.scale(1, 1)
    # silüet vinç
    kutu(ctx, 300, 520, 1320, 30, C["koyu"], a=0.18 * a)
    kutu(ctx, 300, 300, 60, 600, C["koyu"], a=0.12 * a)
    kutu(ctx, 1560, 300, 60, 600, C["koyu"], a=0.12 * a)
    ctx.restore()
    s = geri(dilim(t, 0.4, 1.4))
    ctx.save()
    ctx.translate(W / 2, 460)
    ctx.scale(s, s)
    yazi(ctx, "beta", 0, 0, 220, C["beyaz"], kalin=True, hiza="orta", a=sinir(s))
    ctx.restore()
    kutu(ctx, W / 2 - 220, 488, 440 * ease_out(dilim(t, 1.0, 1.8)), 18, C["antrasit"], r=8)
    yazi(ctx, "VİNÇ SİSTEMLERİ", W / 2, 556, 32, C["beyaz"], hiza="orta", a=dilim(t, 1.3, 1.9), aralik=10)
    b = dilim(t, 2.0, 2.8)
    yazi(ctx, "Siparişten kuruluma, tek elden.", W / 2, 700, 58, C["koyu"], kalin=True, hiza="orta", a=b)
    yazi(ctx, "www.betavinc.com", W / 2, 780, 40, C["beyaz"], kalin=True, hiza="orta", a=dilim(t, 2.6, 3.4))


SAHNELER = [  # (süre sn, fonksiyon, adım no, açık arka plan mı)
    (5.0, s_acilis, None, False),
    (9.0, s_siparis, 0, True),
    (9.5, s_kesif, 1, True),
    (6.0, s_muhendislik, 2, False),
    (12.0, s_imalat, 3, True),
    (8.0, s_yukleme, 4, True),
    (9.0, s_nakliye, 5, True),
    (13.5, s_kurulum, 6, True),
    (6.0, s_kapanis, None, False),
]
GECIS = 0.6
TOPLAM = sum(s[0] for s in SAHNELER) - GECIS * (len(SAHNELER) - 1)


def sahne_ciz(i, t, kare):
    sure, fn, adim, acik = SAHNELER[i]
    yuzey = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(yuzey)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    fn(ctx, t, kare)
    if adim is not None:
        kose_logo(ctx)
        # ilerleme çubuğu zemini
        kutu(ctx, 0, 968, W, 112, C["beyaz"], a=0.86)
        ilerleme_cubugu(ctx, adim, t / sure)
    return yuzey


def kare_ciz(tg, kare):
    bas = 0.0
    for i, (sure, *_r) in enumerate(SAHNELER):
        son = bas + sure
        if tg < son or i == len(SAHNELER) - 1:
            t = tg - bas
            y1 = sahne_ciz(i, t, kare)
            if i + 1 < len(SAHNELER) and t > sure - GECIS:
                k = yumusak((t - (sure - GECIS)) / GECIS)
                y2 = sahne_ciz(i + 1, t - (sure - GECIS), kare)
                ctx = cairo.Context(y1)
                ctx.set_source_surface(y2, 0, 0)
                ctx.paint_with_alpha(k)
            return y1
        bas = son - GECIS
    return sahne_ciz(len(SAHNELER) - 1, 0, kare)


def main():
    if sys.argv[1] == "--kare":
        tg = float(sys.argv[2])
        kare_ciz(tg, int(tg * FPS)).write_to_png(sys.argv[3])
        return
    cikti = sys.argv[1]
    t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    t1 = float(sys.argv[3]) if len(sys.argv) > 3 else TOPLAM
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti],
                          stdin=subprocess.PIPE)
    for n in range(n0, n1):
        y = kare_ciz(n / FPS, n)
        ff.stdin.write(bytes(y.get_data()))
    ff.stdin.close()
    ff.wait()
    print(f"{cikti}: {n1 - n0} kare, {(n1 - n0) / FPS:.1f} sn")


if __name__ == "__main__":
    main()
