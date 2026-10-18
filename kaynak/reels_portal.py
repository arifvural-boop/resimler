"""
Beta Vinç - Instagram Reels: çift kirişli portal vincin siparişten kuruluma yolculuğu
(2B motion graphics, 1080x1920, 30 sn, Türkçe + İngilizce tek video).

reels.py altyapısını kullanır; portale özgü sahneleri ve metinleri değiştirir.

Kullanım:
    python reels_portal.py <cikti.mp4>
    python reels_portal.py --kare <sn> <cikti.png>
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animasyon as a2  # noqa: E402
import reels as R  # noqa: E402

W, H = R.W, R.H
C = a2.C
kutu, yazi, cizgi, daire = a2.kutu, a2.yazi, a2.cizgi, a2.daire
dilim, eo, eio, geri, lerp = R.dilim, R.eo, R.eio, R.geri, R.lerp

L = dict(
    iki=True,
    kanca1="SİPARİŞTEN", kanca2="KURULUMA",
    kanca3="Bir portal vinç nasıl doğar?", kanca3_en="How is a gantry crane born?",
    b1="Sipariş geldi!", e1="Order in!", s1="10 ton · 15 m açıklık",
    b2="Ölç. İki kere.", e2="Measure twice.", s2="Açık sahada ray keşfi",
    b3="Tasarla.", e3="Design it.", s3="Statik hesap + 3B model",
    b4=("Kaynak.", "Boya.", "Montaj."), e4=("Weld.", "Paint.", "Assemble."),
    s4="Beta Üretim Merkezi · Production Center",
    b5="Yükle.", e5="Load up.", s5="Güvenle sabitlendi",
    b6="Yola çık.", e6="Hit the road.", s6="Takipli, sigortalı nakliye",
    b7="Kur. Yürüt.", e7="Install. Roll.", s7="Raylarda yürüyüş + 10 ton yük testi",
    chat1="Merhaba, stok sahamıza 10 tonluk çift kirişli portal vinç lazım. Açıklık 15 m.",
    chat1_en="Hi, we need a 10-tonne double girder gantry crane for our stock yard. Span 15 m.",
    chat2="Hemen keşfe geliyoruz, teklifiniz hazır!",
    chat2_en="We're coming for the site survey, your quote is ready!",
    onay="ONAYLANDI · APPROVED", tamam="TESLİM · DELIVERED", km="km",
    son1="Sıradaki proje sizin.", son2="Your project is next.", cta="Takip et · Follow   betavinc.com",
    slogan="vinç sistemleri", slogan_en="crane systems", adim="ADIM · STEP",
    etiketler=[("kapasite", "capacity"), ("açıklık", "span"), ("kaldırma", "lift")],
    kart=("10 t", "15 m", "8 m"),
)
R.T["portal"] = L

ZEMIN = 1620
XL, XR = 175, 905     # ayak eksenleri (ray konumları)
KIRIS_UST = 900       # kiriş üst kotu
KIRIS_H = 70


# ---------------------------------------------------------------- portal çizimi
def ray_kesit(ctx, x):
    a2.i_profil(ctx, x - 30, ZEMIN - 26, 60, 26, C["antrasit"])


def ayak(ctx, x, dy=0.0, yon=1, teker=0.0):
    """A tipi ayak (açıklık görünüşünde, kiriş doğrultusunda tek kol + baş arabası kesiti)."""
    alt_y = ZEMIN - 26 - 70 + dy
    ust_y = KIRIS_UST + KIRIS_H + dy
    # konik kol: altta geniş
    a2.cokgen(ctx, [(x - 46, alt_y), (x + 46, alt_y), (x + 28, ust_y), (x - 28, ust_y)], C["turuncu"])
    a2.cokgen(ctx, [(x - 46, alt_y), (x - 30, alt_y), (x - 18, ust_y), (x - 28, ust_y)], C["turuncu_a"])
    # ara bağ ve flanşlar
    kutu(ctx, x - 52, alt_y - 8, 104, 10, C["turuncu_k"], r=2)
    kutu(ctx, x - 34, ust_y - 4, 68, 10, C["turuncu_k"], r=2)
    for k in range(3):
        kutu(ctx, x - 40 + k * 32, alt_y - 6, 10, 6, C["gri_a"], r=1)
    # baş arabası (kesit) + tekerlek
    kutu(ctx, x - 62, alt_y, 124, 56, C["antrasit"], r=8)
    daire(ctx, x, ZEMIN - 26 - 20 + dy, 26, C["koyu"])
    daire(ctx, x, ZEMIN - 26 - 20 + dy, 11, C["gri_a"])
    for k in range(4):
        a = teker + k * math.pi / 2
        cizgi(ctx, [(x, ZEMIN - 46 + dy), (x + math.cos(a) * 11, ZEMIN - 46 + dy + math.sin(a) * 11)], C["gri"], lw=3)
    kutu(ctx, x + yon * 40 - 18, alt_y + 6, 36, 30, C["turuncu_k"], r=4)  # tahrik


def kiris(ctx, dy=0.0, a=1.0):
    x0, x1 = XL - 70, XR + 70
    y = KIRIS_UST + dy
    # uç kirişler
    for x in (XL, XR):
        kutu(ctx, x - 60, y - 10, 120, KIRIS_H + 20, C["turuncu_k"], r=6, a=a)
        for k in range(3):
            cizgi(ctx, [(x - 30 + k * 16, y + 8), (x - 12 + k * 16, y + KIRIS_H - 8)], C["koyu"], lw=5, a=a * 0.8)
    a2.gradyan_kutu(ctx, x0 + 40, y, x1 - x0 - 80, KIRIS_H, C["turuncu_a"], C["turuncu_k"])
    kutu(ctx, x0 + 40, y - 8, x1 - x0 - 80, 10, C["turuncu_k"], a=a)
    for k in range(1, 8):
        xx = x0 + 40 + k * (x1 - x0 - 80) / 8
        cizgi(ctx, [(xx, y + 6), (xx, y + KIRIS_H - 6)], C["koyu"], lw=2, a=0.15 * a)
    kutu(ctx, (x0 + x1) / 2 - 80, y + 18, 160, 34, C["beyaz"], r=5, a=a)
    R.resim(ctx, R.LOGO_K, (x0 + x1) / 2, y + 35, 116, a=a, orta=True)
    # ray (kiriş üstü) + korkuluk
    kutu(ctx, x0 + 50, y - 14, x1 - x0 - 100, 6, C["gri"], a=a)
    for k in range(9):
        xx = x0 + 60 + k * (x1 - x0 - 120) / 8
        cizgi(ctx, [(xx, y - 14), (xx, y - 70)], a2.renk("#F2C200"), lw=4, a=a)
    cizgi(ctx, [(x0 + 60, y - 70), (x1 - 60, y - 70)], a2.renk("#F2C200"), lw=4, a=a)


def araba(ctx, cx, kanca_y, yuk=None, dy=0.0):
    """Halatlı vinç arabası kiriş üstünde; halatlar kirişin arkasından kanca bloğuna."""
    y = KIRIS_UST - 14 + dy
    kutu(ctx, cx - 120, y - 92, 240, 92, C["turuncu"], r=10)
    kutu(ctx, cx - 120, y - 92, 240, 16, C["turuncu_k"], r=6)
    daire(ctx, cx - 40, y - 46, 32, C["gri_a"])
    for k in range(6):
        cizgi(ctx, [(cx - 70, y - 64 + k * 7), (cx - 10, y - 64 + k * 7)], C["gri"], lw=2)
    kutu(ctx, cx + 20, y - 76, 80, 56, C["antrasit"], r=8)
    kutu(ctx, cx + 30, y - 66, 60, 18, C["beyaz"], r=3)
    R.resim(ctx, R.LOGO_K, cx + 60, y - 57, 46, orta=True)
    daire(ctx, cx - 90, y - 104, 9, C["kirmizi"])
    for sx in (-80, 80):
        daire(ctx, cx + sx, y + 2, 12, C["koyu"])
    # halatlar (kiriş alt kotundan kancaya)
    for dx in (-10, 10):
        cizgi(ctx, [(cx + dx, KIRIS_UST + KIRIS_H + dy), (cx + dx, kanca_y)], C["gri"], lw=3)
    kutu(ctx, cx - 34, kanca_y, 68, 46, C["turuncu"], r=8)
    daire(ctx, cx, kanca_y + 22, 14, C["antrasit"])
    ctx.new_sub_path()
    ctx.arc(cx, kanca_y + 74, 18, -math.pi * 0.05, math.pi * 1.25)
    a2.boya(ctx, C["koyu"])
    ctx.set_line_width(8)
    ctx.stroke()
    if yuk:
        yw, yh, metin = yuk
        for dx in (-yw / 2 + 12, yw / 2 - 12):
            cizgi(ctx, [(cx, kanca_y + 92), (cx + dx, kanca_y + 150)], C["koyu"], lw=3)
        kutu(ctx, cx - yw / 2, kanca_y + 150, yw, yh, C["gri"], r=5)
        yazi(ctx, metin, cx, kanca_y + 150 + yh / 2 + 16, 44, C["beyaz"], kalin=True, hiza="orta")


def saha(ctx, kayma=0.0, ray=True):
    """Açık stok sahası: gökyüzü, uzak depo, sac/bobin istifleri (paralaks), beton zemin."""
    a2.gradyan_kutu(ctx, 0, 560, W, ZEMIN - 560, a2.renk("#9CC8E8"), a2.renk("#E4F1F9"))
    k = kayma
    for i in range(4):
        x = (i * 420 - k * 0.3) % (W + 420) - 210
        kutu(ctx, x, 1180, 360, 440, a2.renk("#D9D6D0"))
        a2.cokgen(ctx, [(x - 10, 1190), (x + 180, 1110), (x + 370, 1190)], a2.renk("#C9C5BE"))
        for j in range(3):
            kutu(ctx, x + 30 + j * 110, 1250, 80, 50, C["cam"], r=3)
    kutu(ctx, 0, 1480, W, ZEMIN - 1480, a2.renk("#BDB9B2"))
    for i in range(7):
        x = (i * 260 - k) % (W + 260) - 130
        for j in range(3):  # bobin istifi
            daire(ctx, x + j * 52, ZEMIN - 30, 26, a2.renk("#8A9099"))
            daire(ctx, x + j * 52, ZEMIN - 30, 10, a2.renk("#5E666F"))
        daire(ctx, x + 26, ZEMIN - 74, 26, a2.renk("#9AA0A8"))
        daire(ctx, x + 26, ZEMIN - 74, 10, a2.renk("#5E666F"))
    kutu(ctx, 0, ZEMIN, W, 1720 - ZEMIN, a2.renk("#A9A59E"))
    for i in range(12):
        x = (i * 120 - k) % (W + 120) - 60
        cizgi(ctx, [(x, ZEMIN + 10), (x - 60, 1720)], C["gri"], lw=1, a=0.3)
    if ray:
        for x in (XL, XR):
            ray_kesit(ctx, x)


def portal(ctx, cx=None, kanca_y=None, yuk=None, teker=0.0, parcalar=("ayak", "kiris", "araba"),
           ayak_dy=0.0, kiris_dy=0.0, araba_dy=0.0):
    if "ayak" in parcalar:
        ayak(ctx, XL, ayak_dy, yon=-1, teker=teker)
        ayak(ctx, XR, ayak_dy, yon=1, teker=teker)
    if "kiris" in parcalar:
        kiris(ctx, kiris_dy)
    if "araba" in parcalar:
        cx = (XL + XR) / 2 if cx is None else cx
        araba(ctx, cx, KIRIS_UST + 260 if kanca_y is None else kanca_y, yuk=yuk, dy=araba_dy)


# ---------------------------------------------------------------- sahneler
def s_olcu(ctx, L_, t):
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    saha(ctx)
    w = eo(dilim(t, 0.0, 0.5))
    tx = lerp(-80, 330, w)
    el = a2.insan(ctx, tx, ZEMIN, boy=230, kol=-0.25 if w >= 1 else 0.2, adim=t * 10 if w < 1 else 0)
    if w >= 1:
        kutu(ctx, el[0] - 12, el[1] - 16, 36, 26, C["turuncu"], r=5)
    p = eio(dilim(t, 0.5, 1.6))
    ly = ZEMIN - 40
    if p > 0:
        cizgi(ctx, [(XL, ly), (lerp(XL, XR, p), ly)], C["kirmizi"], lw=5)
        daire(ctx, lerp(XL, XR, p), ly, 10, C["kirmizi"])
        a2.olcu_cizgisi(ctx, (XL, 1040), (lerp(XL, XR, p), 1040), None)
    dx, dy = R.sarsinti(t, [1.6])
    s = 1 + 0.12 * math.exp(-max(0, t - 1.6) * 12) * (t >= 1.6)
    ctx.save()
    ctx.translate(W / 2 + dx, 900 + dy)
    ctx.scale(s, s)
    a = dilim(t, 0.4, 0.6)
    kutu(ctx, -300, -84, 600, 116, C["beyaz"], r=22, a=0.96 * a)
    yazi(ctx, f"{R.mm(L_, int(15000 * p))} mm", 0, 6, 86, C["kirmizi"], kalin=True, hiza="orta", a=a)
    ctx.restore()
    p2 = eio(dilim(t, 1.7, 2.4))
    if p2 > 0:
        hx = 700
        a2.olcu_cizgisi(ctx, (hx, ZEMIN), (hx, lerp(ZEMIN, 1120, p2)), None)
        kutu(ctx, hx + 22, 1260, 260, 70, C["beyaz"], r=14, a=0.96)
        yazi(ctx, f"{R.mm(L_, int(8000 * p2))} mm", hx + 152, 1310, 44, C["kirmizi"], kalin=True, hiza="orta")
    if t > 2.4:
        a2.onay(ctx, W / 2, 1790, 48, dilim(t, 2.4, 2.9))
    R.baslik(ctx, L_, L_["b2"], L_["s2"], t, en=L_["e2"])
    R.ust_bant(ctx, L_, 2, t)


def s_tasarim(ctx, L_, t):
    a2.gradyan_kutu(ctx, 0, 0, W, H, C["mavi"], a2.renk("#0F2740"))
    for i in range(0, W, 45):
        cizgi(ctx, [(i, 0), (i, H)], C["beyaz"], lw=1, a=0.07)
    for j in range(0, H, 45):
        cizgi(ctx, [(0, j), (W, j)], C["beyaz"], lw=1, a=0.07)
    mavi = a2.renk("#DDEBFA")
    sari = a2.renk("#FFD36B")

    def parca(pts, a0, a1, lw=4):
        p = eio(dilim(t, a0, a1))
        if p <= 0:
            return
        Ls = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        d = p * sum(Ls)
        q = [pts[0]]
        for i, s_ in enumerate(Ls):
            if d >= s_:
                q.append(pts[i + 1])
                d -= s_
            else:
                q.append((lerp(pts[i][0], pts[i + 1][0], d / s_), lerp(pts[i][1], pts[i + 1][1], d / s_)))
                break
        cizgi(ctx, q, mavi, lw=lw)

    parca([(60, ZEMIN), (1020, ZEMIN)], 0.1, 0.4, 3)
    alt = ZEMIN - 96
    ust = KIRIS_UST + KIRIS_H
    for x in (XL, XR):
        parca([(x - 46, alt), (x + 46, alt), (x + 28, ust), (x - 28, ust), (x - 46, alt)], 0.2, 0.9)
        parca([(x - 62, alt), (x + 62, alt), (x + 62, alt + 56), (x - 62, alt + 56), (x - 62, alt)], 0.5, 1.0, 3)
    parca([(XL - 70, KIRIS_UST), (XR + 70, KIRIS_UST), (XR + 70, ust), (XL - 70, ust), (XL - 70, KIRIS_UST)], 0.7, 1.2, 5)
    cx = (XL + XR) / 2
    parca([(cx - 120, KIRIS_UST - 106), (cx + 120, KIRIS_UST - 106), (cx + 120, KIRIS_UST - 14),
           (cx - 120, KIRIS_UST - 14), (cx - 120, KIRIS_UST - 106)], 1.0, 1.3, 4)
    parca([(cx, ust), (cx, 1300)], 1.2, 1.5, 3)
    parca([(cx - 34, 1300), (cx + 34, 1300), (cx + 34, 1346), (cx - 34, 1346), (cx - 34, 1300)], 1.4, 1.6, 3)
    if t > 1.3:
        a2.olcu_cizgisi(ctx, (XL, 720), (XR, 720), "15.000", c=sari, ilerle=dilim(t, 1.3, 1.7), ofs=-24,
                        zemin=a2.renk("#0F2740"))
    if t > 1.5:
        a2.olcu_cizgisi(ctx, (1010, ZEMIN), (1010, lerp(ZEMIN, KIRIS_UST, dilim(t, 1.5, 1.9))), None, c=sari)
        a = dilim(t, 1.7, 1.9)
        ctx.save()
        ctx.translate(1050, (ZEMIN + KIRIS_UST) / 2)
        ctx.rotate(-math.pi / 2)
        yazi(ctx, "8.000", 0, 0, 34, sari, kalin=True, hiza="orta", a=a)
        ctx.restore()
        yazi(ctx, "10 t", cx + 50, 1330, 40, sari, kalin=True, a=a)
    if t > 1.9:
        a2.onay(ctx, W / 2, 1790, 46, dilim(t, 1.9, 2.4))
    R.baslik(ctx, L_, L_["b3"], L_["s3"], t, en=L_["e3"])
    R.ust_bant(ctx, L_, 3, t)


def s_imalat(ctx, L_, t):
    if t < 3.8:
        return R_s_imalat(ctx, L_, t)
    t_alt = t - 3.8
    R.koyu_zemin(ctx, a2.renk("#33383F"), C["koyu"])
    R.kelime_pop(ctx, L_["b4"][2], W / 2, 400, 116, 0.02, t_alt, renk=C["beyaz"])
    R.kelime_pop(ctx, L_["e4"][2], W / 2, 476, 60, 0.15, t_alt, renk=C["turuncu"])
    yazi(ctx, L_["s4"], W / 2, 540, 30, C["gri_a"], kalin=True, hiza="orta")
    kutu(ctx, 0, ZEMIN, W, 300, a2.renk("#3E444C"))
    for x in (XL, XR):
        ray_kesit(ctx, x)
    k = geri(dilim(t_alt, 0.0, 0.35))
    b = geri(dilim(t_alt, 0.35, 0.75))
    c_ = geri(dilim(t_alt, 0.8, 1.2))
    dx, dy = R.sarsinti(t_alt, [0.35, 0.75, 1.2], guc=10)
    ctx.save()
    ctx.translate(dx, dy)
    portal(ctx, parcalar=("ayak",), ayak_dy=(1 - k) * 900)
    if b > 0:
        portal(ctx, parcalar=("kiris",), kiris_dy=-(1 - b) * 900)
    if c_ > 0:
        portal(ctx, parcalar=("araba",), araba_dy=-(1 - c_) * 700, kanca_y=KIRIS_UST + 300 - (1 - c_) * 700)
    ctx.restore()
    R.ust_bant(ctx, L_, 4, t)


def s_kurulum(ctx, L_, t):
    """0-1.0 ayaklar raylara iner; 1.0-1.9 kiriş mobil vinçle oturur; 1.9-2.3 araba;
    2.3-3.3 portal raylarda yürür (paralaks); 3.3-4.6 10 t yük testi ve araba gezintisi."""
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    yuru = eio(dilim(t, 2.3, 3.3))
    kayma = yuru * 900
    teker = yuru * 30
    saha(ctx, kayma=kayma)
    ayak_in = eio(dilim(t, 0.0, 0.9))
    kiris_in = eio(dilim(t, 1.0, 1.8))
    car = eo(dilim(t, 1.9, 2.3))
    kanca_in = eio(dilim(t, 3.3, 3.7))
    kalk = eio(dilim(t, 3.7, 4.2))
    gez = eio(dilim(t, 4.2, 4.8))
    dx, dy = R.sarsinti(t, [0.9, 1.8, 2.3], guc=12)
    ctx.save()
    ctx.translate(dx, dy)
    ad = -(1 - ayak_in) * 520
    if t < 0.95:
        for x in (XL, XR):
            cizgi(ctx, [(x, 560), (x, KIRIS_UST + KIRIS_H + ad - 20)], C["koyu"], lw=3)
    portal(ctx, parcalar=("ayak",), ayak_dy=ad, teker=teker)
    pb = dilim(t, 0.85, 1.1)
    if 0 < pb < 1:
        for x in (XL, XR):
            daire(ctx, x, ZEMIN - 30, 22 * math.sin(pb * math.pi), a2.renk("#FFF3C4"), a=0.95)
    if t >= 1.0:
        kd = -(1 - kiris_in) * 520
        if t < 1.85:
            cizgi(ctx, [((XL + XR) / 2, 560), ((XL + XR) / 2, KIRIS_UST + kd - 110)], C["koyu"], lw=3)
            for d in (-300, 300):
                cizgi(ctx, [((XL + XR) / 2, KIRIS_UST + kd - 110), ((XL + XR) / 2 + d, KIRIS_UST + kd - 8)], C["koyu"], lw=2.5)
        portal(ctx, parcalar=("kiris",), kiris_dy=kd)
    if car > 0:
        x_yuk = 380
        cx = lerp(W + 200, x_yuk, car) if gez == 0 else lerp(x_yuk, 700, gez)
        ky = lerp(KIRIS_UST + 260, ZEMIN - 260, kanca_in)
        ky = lerp(ky, ZEMIN - 520, kalk)
        yuk = (190, 130, "10 t") if t >= 3.7 else None
        if 3.3 <= t < 3.7:
            kutu(ctx, x_yuk - 95, ZEMIN - 130, 190, 130, C["gri"], r=5)
            yazi(ctx, "10 t", x_yuk, ZEMIN - 50, 44, C["beyaz"], kalin=True, hiza="orta")
        portal(ctx, parcalar=("araba",), cx=cx, kanca_y=ky, yuk=yuk)
    if 2.3 <= t < 3.5:
        a = dilim(t, 2.3, 2.5) * (1 - dilim(t, 3.3, 3.5))
        kutu(ctx, W / 2 - 200, 650, 400, 100, C["koyu"], r=22, a=0.9 * a)
        yazi(ctx, f"{yuru * 40:.0f} m  →", W / 2, 722, 62, C["turuncu"], kalin=True, hiza="orta", a=a)
        for k in range(10):  # hız çizgileri
            rnd = random.Random(k)
            y = rnd.uniform(1300, 1560)
            x = (rnd.uniform(0, W) - t * 2400) % (W + 300) - 150
            cizgi(ctx, [(x, y), (x + rnd.uniform(60, 160), y)], C["beyaz"], lw=4, a=0.6 * a)
    ctx.restore()
    R.baslik(ctx, L_, L_["b7"], L_["s7"], t, en=L_["e7"])
    p = geri(dilim(t, 4.5, 4.8))
    if p > 0:
        ctx.save()
        ctx.translate(W / 2, 1790)
        ctx.scale(p, p)
        ctx.rotate(-0.08)
        kutu(ctx, -340, -60, 680, 110, C["yesil"], r=20)
        yazi(ctx, L_["tamam"], 0, 18, 50, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    R.ust_bant(ctx, L_, 7, t)


R_s_imalat = R.s_imalat
R.FONK.update(olcu=s_olcu, tasarim=s_tasarim, imalat=s_imalat, kurulum=s_kurulum)


def main():
    if sys.argv[1] == "--kare":
        R.kare(float(sys.argv[2]), L).write_to_png(sys.argv[3])
        return
    sys.argv = [sys.argv[0], "portal", sys.argv[1]]
    R.main()


if __name__ == "__main__":
    main()
