"""
Beta Vinç - Instagram Reels: "30 saniyede bir vincin yolculuğu" (2B motion graphics, 1080x1920, 9:16).

Kullanım:
    python reels.py <dil: tr|en> <cikti.mp4> [--sessiz]
    python reels.py <dil> --kare <sn> <cikti.png>
"""
import math
import os
import random
import subprocess
import sys
import wave

import cairo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animasyon as a2  # noqa: E402

W, H, FPS = 1080, 1920, 30
BPM = 120
VURUS = 60 / BPM
C = a2.C
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
kutu, yazi, cizgi, daire = a2.kutu, a2.yazi, a2.cizgi, a2.daire
dilim, eo, eio, lerp, sinir = a2.dilim, a2.ease_out, a2.ease_io, a2.lerp, a2.sinir


def geri(x):
    v = a2.geri(x)
    return v if v > 0.01 else 0.0

# sahneler: (ad, başlangıç, bitiş)  — kesmeler vuruşlara (0,5 sn) oturur
SAHNE = [("kanca", 0.0, 2.5), ("siparis", 2.5, 5.5), ("olcu", 5.5, 8.5), ("tasarim", 8.5, 11.0),
         ("imalat", 11.0, 16.5), ("yukleme", 16.5, 19.5), ("yol", 19.5, 22.5), ("kurulum", 22.5, 27.5),
         ("kapanis", 27.5, 30.0)]
TOPLAM = 30.0
GECIS = 0.22

T = {
    "tr": dict(
        kanca1="SİPARİŞTEN", kanca2="KURULUMA", kanca3="30 saniyede bir vincin yolculuğu",
        b1="Sipariş geldi!", s1="5 ton · 12 m açıklık",
        chat1="Merhaba, 5 tonluk tek kirişli köprülü vinç lazım. Açıklık 12 m.",
        chat2="Hemen keşfe geliyoruz, teklifiniz hazır!", onay="ONAYLANDI",
        b2="Ölç. İki kere.", s2="Sahada milimetrik keşif",
        b3="Tasarla.", s3="Statik hesap + 3B model",
        b4=("Kaynak.", "Boya.", "Montaj."), s4="Beta Üretim Merkezi",
        b5="Yükle.", s5="Güvenle sabitlendi",
        b6="Yola çık.", s6="Takipli, sigortalı nakliye", km="km",
        b7="Kur. Test et.", s7="5 ton yük testi", tamam="TESLİM",
        son1="Sizin projeniz", son2="sırada.", cta="Takip et  ·  betavinc.com", slogan="vinç sistemleri",
        adim="ADIM",
    ),
    "en": dict(
        kanca1="FROM ORDER", kanca2="TO INSTALL", kanca3="A crane's journey in 30 seconds",
        b1="Order in!", s1="5 t · 12 m span",
        chat1="Hi, we need a 5-tonne single girder overhead crane. Span is 12 m.",
        chat2="We're coming for the site survey, your quote is ready!", onay="APPROVED",
        b2="Measure twice.", s2="Millimetre-precise site survey",
        b3="Design it.", s3="Structural calc + 3D model",
        b4=("Weld.", "Paint.", "Assemble."), s4="Beta Production Center",
        b5="Load up.", s5="Secured for the road",
        b6="Hit the road.", s6="Tracked & insured transport", km="km",
        b7="Install. Test.", s7="5-tonne load test", tamam="DELIVERED",
        son1="Your project", son2="is next.", cta="Follow  ·  betavinc.com", slogan="crane systems",
        adim="STEP",
    ),
}


def png(ad):
    return cairo.ImageSurface.create_from_png(os.path.join(LOGO, ad))


LOGO_B = png("beta_isaret_beyaz.png")
LOGO_K = png("beta_isaret_koyu.png")


def resim(ctx, surf, x, y, gen, a=1.0, orta=False):
    s = gen / surf.get_width()
    h = surf.get_height() * s
    ctx.save()
    ctx.translate(x - (gen / 2 if orta else 0), y - (h / 2 if orta else 0))
    ctx.scale(s, s)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(a)
    ctx.restore()
    return h


def sarsinti(t, anlar, guc=14):
    """Darbe anlarında kısa kamera sarsıntısı (dx, dy)."""
    for a in anlar:
        if a <= t < a + 0.25:
            k = 1 - (t - a) / 0.25
            rnd = random.Random(int(t * 1000))
            return rnd.uniform(-1, 1) * guc * k, rnd.uniform(-1, 1) * guc * k
    return 0.0, 0.0


def kelime_pop(ctx, metin, x, y, boy, t0, t, renk=C["beyaz"], vurgu=None, hiza="orta", aralik=0.08):
    """Kelime kelime büyüyerek beliren kalın başlık; vurgu: turuncu zeminli kelime dizini."""
    kel = metin.split(" ")
    ctx.select_font_face(a2.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(boy)
    genler = [ctx.text_extents(k).x_advance for k in kel]
    bosluk = ctx.text_extents(" ").x_advance
    top = sum(genler) + bosluk * (len(kel) - 1)
    xx = x - top / 2 if hiza == "orta" else x
    for i, k in enumerate(kel):
        p = dilim(t, t0 + i * aralik, t0 + i * aralik + 0.22)
        if p <= 0:
            xx += genler[i] + bosluk
            continue
        s = max(0.01, geri(p))
        cx = xx + genler[i] / 2
        ctx.save()
        ctx.translate(cx, y - boy * 0.35)
        ctx.scale(s, s)
        ctx.translate(-cx, -(y - boy * 0.35))
        if vurgu is not None and i in vurgu:
            kutu(ctx, xx - 14, y - boy * 0.86, genler[i] + 28, boy * 1.08, C["turuncu"], r=12)
        yazi(ctx, k, xx, y, boy, renk, kalin=True, a=sinir(p * 1.5))
        ctx.restore()
        xx += genler[i] + bosluk


def ust_bant(ctx, L, no, t):
    """Üstte adım çipi + ilerleme çizgisi (Reels güvenli alanı içinde)."""
    a = dilim(t, 0.0, 0.2)
    kutu(ctx, 70, 170, 210, 64, C["turuncu"], r=32, a=a)
    yazi(ctx, f"{L['adim']} {no}/7", 175, 213, 30, C["koyu"], kalin=True, hiza="orta", a=a)
    kutu(ctx, 300, 198, 650, 8, C["beyaz"], r=4, a=0.35 * a)
    kutu(ctx, 300, 198, 650 * (no - 1 + sinir(t / 2.6)) / 7, 8, C["turuncu"], r=4, a=a)
    resim(ctx, LOGO_B, 70, 104, 150, a=0.95)


def baslik(ctx, L, metin, alt, t, koyu=False, y=420):
    c = C["koyu"] if koyu else C["beyaz"]
    kelime_pop(ctx, metin, W / 2, y, 104, 0.05, t, renk=c)
    yazi(ctx, alt, W / 2, y + 74, 40, C["turuncu"] if not koyu else C["antrasit"], kalin=True, hiza="orta",
         a=dilim(t, 0.35, 0.6))


def dunya(ctx, s, cx, cy, fn):
    """1920x1080'lik illüstrasyon dünyasını ölçekleyip (cx, cy) merkezine çiz."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.translate(-960, -540)
    fn(ctx)
    ctx.restore()


def koyu_zemin(ctx, ust=C["antrasit"], alt=C["koyu"]):
    a2.gradyan_kutu(ctx, 0, 0, W, H, ust, alt)


# ---------------------------------------------------------------- sahneler
def s_kanca(ctx, L, t):
    koyu_zemin(ctx)
    # arka planda dönen ince tel kafes kiriş
    for i in range(14):
        y = 200 + i * 130 + (t * 120) % 130
        cizgi(ctx, [(0, y), (W, y - 260)], C["beyaz"], lw=2, a=0.05)
    dx, dy = sarsinti(t, [0.15, 0.65])
    ctx.save()
    ctx.translate(dx, dy)
    s1 = geri(dilim(t, 0.05, 0.35))
    s2 = geri(dilim(t, 0.55, 0.85))
    for s, metin, y, vurgu in ((s1, L["kanca1"], 820, False), (s2, L["kanca2"], 960, True)):
        if s <= 0:
            continue
        ctx.save()
        ctx.translate(W / 2, y - 40)
        ctx.scale(s, s)
        ctx.translate(-W / 2, -(y - 40))
        if vurgu:
            ctx.select_font_face(a2.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(124)
            g = ctx.text_extents(metin).x_advance
            kutu(ctx, W / 2 - g / 2 - 26, y - 112, g + 52, 140, C["turuncu"], r=18)
            yazi(ctx, metin, W / 2, y, 124, C["koyu"], kalin=True, hiza="orta")
        else:
            yazi(ctx, metin, W / 2, y, 124, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    ctx.restore()
    a = dilim(t, 1.0, 1.3)
    yazi(ctx, L["kanca3"], W / 2, 1090, 46, C["gri_a"], hiza="orta", a=a)
    # 30 sn sayacı
    p = dilim(t, 1.2, 1.5)
    if p > 0:
        r = 92
        cx, cy = W / 2, 1330
        daire(ctx, cx, cy, r * geri(p), C["koyu"])
        ctx.arc(cx, cy, r - 10, -math.pi / 2, -math.pi / 2 + 2 * math.pi * sinir((t - 1.2) / 1.3))
        a2.boya(ctx, C["turuncu"])
        ctx.set_line_width(12)
        ctx.stroke()
        yazi(ctx, "30", cx, cy + 22, 64, C["beyaz"], kalin=True, hiza="orta", a=p)
    resim(ctx, LOGO_B, W / 2, 560, 300, a=dilim(t, 0.0, 0.3), orta=True)


def telefon(ctx, x, y, w, h):
    kutu(ctx, x - 10, y - 10, w + 20, h + 20, C["koyu"], r=70)
    kutu(ctx, x, y, w, h, renk_acik(), r=60)
    kutu(ctx, x + w / 2 - 80, y + 18, 160, 34, C["koyu"], r=17)


def renk_acik():
    return a2.renk("#F2EFEA")


def balon(ctx, metin, x, y, gen, sag, t, t0, boy=34):
    p = eo(dilim(t, t0, t0 + 0.25))
    if p <= 0:
        return y
    ctx.select_font_face(a2.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(boy)
    satirlar, satir = [], ""
    for k in metin.split(" "):
        dene = (satir + " " + k).strip()
        if ctx.text_extents(dene).x_advance > gen - 60:
            satirlar.append(satir)
            satir = k
        else:
            satir = dene
    satirlar.append(satir)
    h = 34 + len(satirlar) * (boy * 1.3)
    bx = x + (0 if not sag else 0)
    ctx.save()
    ctx.translate(0, (1 - p) * 40)
    kutu(ctx, bx, y, gen, h, C["turuncu"] if sag else C["beyaz"], r=30, a=p)
    for i, s in enumerate(satirlar):
        yazi(ctx, s, bx + 30, y + 22 + boy + i * boy * 1.3, boy, C["koyu"], a=p)
    ctx.restore()
    return y + h + 26


def s_siparis(ctx, L, t):
    koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    baslik(ctx, L, L["b1"], L["s1"], t)
    px, py, pw, ph = 190, 600, 700, 1060
    ctx.save()
    ctx.translate(0, (1 - eo(dilim(t, 0.0, 0.35))) * 900)
    telefon(ctx, px, py, pw, ph)
    kutu(ctx, px, py + 70, pw, 110, C["antrasit"])
    resim(ctx, LOGO_B, px + 40, py + 98, 150)
    daire(ctx, px + pw - 60, py + 125, 14, C["yesil"])
    y = py + 220
    y = balon(ctx, L["chat1"], px + 30, y, 560, False, t, 0.45)
    y = balon(ctx, L["chat2"], px + 110, y, 560, True, t, 1.15)
    # sipariş kartı + damga
    p = eo(dilim(t, 1.7, 2.0))
    if p > 0:
        kutu(ctx, px + 40, y, pw - 80, 250, C["beyaz"], r=24, a=p)
        for k, v in enumerate(("5 t", "12 m", "6 m")):
            yazi(ctx, v, px + 140 + k * 210, y + 120, 76, C["koyu"], kalin=True, hiza="orta", a=p)
        for i, et in enumerate(("kapasite" if L is T["tr"] else "capacity", "açıklık" if L is T["tr"] else "span",
                                "kaldırma" if L is T["tr"] else "lift")):
            yazi(ctx, et, px + 140 + i * 210, y + 170, 26, C["gri"], hiza="orta", a=p)
        d = dilim(t, 2.15, 2.4)
        if d > 0:
            s = lerp(2.6, 1.0, eo(d))
            ctx.save()
            ctx.translate(px + pw / 2, y + 215)
            ctx.rotate(-0.12)
            ctx.scale(s, s)
            kutu(ctx, -200, -46, 400, 82, a2.renk("#FFFFFF", 0.9), r=12, cizgi=C["yesil"], lw=7)
            yazi(ctx, L["onay"], 0, 14, 48, C["yesil"], kalin=True, hiza="orta", a=sinir(d * 2))
            ctx.restore()
    ctx.restore()
    ust_bant(ctx, L, 1, t)


def s_olcu(ctx, L, t):
    def ciz(c):
        a2.hol(c, 360, 1560, 400, [300, 1620])
        a2.insan(c, 520, a2.ZEMIN, boy=190, kol=-0.55)
        p = eio(dilim(t, 0.4, 1.7))
        cizgi(c, [(420, 417), (lerp(420, 1500, p), 417)], C["kirmizi"], lw=5)
        daire(c, lerp(420, 1500, p), 417, 9, C["kirmizi"])
    koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    baslik(ctx, L, L["b2"], L["s2"], t)
    dunya(ctx, 0.9, W / 2 + 40, 1180, ciz)
    p = eio(dilim(t, 0.4, 1.7))
    deger = int(12000 * p)
    metin = f"{deger:,}".replace(",", ".") if L is T["tr"] else f"{deger:,}"
    dx, dy = sarsinti(t, [1.7])
    s = 1 + 0.12 * math.exp(-max(0, t - 1.7) * 12) * (t >= 1.7)
    ctx.save()
    ctx.translate(W / 2 + dx, 760 + dy)
    ctx.scale(s, s)
    kutu(ctx, -330, -100, 660, 140, C["beyaz"], r=24, a=0.95 * dilim(t, 0.3, 0.5))
    yazi(ctx, f"{metin} mm", 0, 6, 104, C["kirmizi"], kalin=True, hiza="orta", a=dilim(t, 0.3, 0.5))
    ctx.restore()
    if t > 1.8:
        a2.onay(ctx, W / 2, 1560, 48, dilim(t, 1.8, 2.3))
    ust_bant(ctx, L, 2, t)


def s_tasarim(ctx, L, t):
    a2.gradyan_kutu(ctx, 0, 0, W, H, C["mavi"], a2.renk("#0F2740"))
    for i in range(0, W, 45):
        cizgi(ctx, [(i, 0), (i, H)], C["beyaz"], lw=1, a=0.07)
    for j in range(0, H, 45):
        cizgi(ctx, [(0, j), (W, j)], C["beyaz"], lw=1, a=0.07)
    baslik(ctx, L, L["b3"], L["s3"], t)
    mavi = a2.renk("#DDEBFA")

    def parca(pts, a0, a1, lw=5):
        p = eio(dilim(t, a0, a1))
        if p <= 0:
            return
        Ls = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        d = p * sum(Ls)
        q = [pts[0]]
        for i, s in enumerate(Ls):
            if d >= s:
                q.append(pts[i + 1])
                d -= s
            else:
                q.append((lerp(pts[i][0], pts[i + 1][0], d / s), lerp(pts[i][1], pts[i + 1][1], d / s)))
                break
        cizgi(ctx, q, mavi, lw=lw)
    x0, x1, yk = 120, 960, 900
    parca([(x0, yk), (x1, yk), (x1, yk + 70), (x0, yk + 70), (x0, yk)], 0.2, 0.9)
    for xb in (x0 + 40, x1 - 40):
        parca([(xb - 70, yk + 70), (xb + 70, yk + 70), (xb + 70, yk + 120), (xb - 70, yk + 120), (xb - 70, yk + 70)], 0.6, 1.1, 4)
    parca([(500, yk + 70), (580, yk + 70), (580, yk + 160), (500, yk + 160), (500, yk + 70)], 0.9, 1.3, 4)
    parca([(540, yk + 160), (540, yk + 420)], 1.2, 1.5, 3)
    parca([(x0 - 40, yk + 140), (x0 - 40, 1500)], 0.9, 1.4, 4)
    parca([(x1 + 40, yk + 140), (x1 + 40, 1500)], 0.9, 1.4, 4)
    if t > 1.4:
        a2.olcu_cizgisi(ctx, (x0 + 40, yk - 90), (x1 - 40, yk - 90), "12.000" if L is T["tr"] else "12,000",
                        c=a2.renk("#FFD36B"), ilerle=dilim(t, 1.4, 1.8), ofs=-24, zemin=a2.renk("#0F2740"))
    # dönen dişli / onay
    if t > 1.8:
        a2.onay(ctx, W / 2, 1620, 44, dilim(t, 1.8, 2.3))
    ust_bant(ctx, L, 3, t)


def s_imalat(ctx, L, t):
    i = 0 if t < 2.0 else 1 if t < 3.8 else 2
    t_alt = t - (0, 2.0, 3.8)[i]
    koyu_zemin(ctx, a2.renk("#33383F"), C["koyu"])
    kelime_pop(ctx, L["b4"][i], W / 2, 420, 120, 0.02, t_alt, renk=C["beyaz"])
    yazi(ctx, L["s4"], W / 2, 500, 40, C["turuncu"], kalin=True, hiza="orta")
    gx0, gx1, gy = 90, 990, 1000
    # kiriş (büyük, yakın plan)
    ham = a2.renk("#9AA0A8")
    boya = eio(dilim(t, 2.0, 3.6))
    sinx = lerp(gx1, gx0, boya)
    dx, dy = sarsinti(t, [3.85, 4.4, 4.9], guc=10)
    ctx.save()
    ctx.translate(dx, dy)
    a2.gradyan_kutu(ctx, gx0, gy, gx1 - gx0, 120, a2.lerp_renk(ham, C["beyaz"], 0.15), a2.lerp_renk(ham, C["koyu"], 0.2))
    if boya > 0:
        a2.gradyan_kutu(ctx, sinx, gy, gx1 - sinx, 120, C["turuncu_a"], C["turuncu_k"])
    kutu(ctx, gx0, gy - 14, gx1 - gx0, 14, C["antrasit"])
    for k in range(1, 7):
        cizgi(ctx, [(gx0 + k * (gx1 - gx0) / 7, gy + 6), (gx0 + k * (gx1 - gx0) / 7, gy + 114)], C["koyu"], lw=2, a=0.15)
    if i == 0:
        kx = lerp(gx0 + 40, gx1 - 40, eio(dilim(t, 0.1, 1.9)))
        cizgi(ctx, [(gx0 + 40, gy + 120), (kx, gy + 120)], a2.renk("#6E737B"), lw=7)
        a2.kivilcim(ctx, kx, gy + 122, int(t * FPS), n=40, yay=1.8)
    elif i == 1:
        for k in range(26):
            rnd = random.Random(int(t * FPS) * 31 + k)
            daire(ctx, sinx + rnd.uniform(-30, 60), gy + rnd.uniform(-10, 130), rnd.uniform(5, 14), C["turuncu_a"], a=0.35)
        # boya tabancası
        kutu(ctx, sinx + 40, gy - 150, 90, 50, C["antrasit"], r=10)
        kutu(ctx, sinx + 40, gy - 110, 24, 70, C["antrasit"], r=6)
    if boya >= 1:
        kutu(ctx, W / 2 - 150, gy + 30, 300, 60, C["beyaz"], r=8)
        resim(ctx, LOGO_K, W / 2, gy + 60, 200, orta=True)
    if i == 2:
        for k, (xb, yon, t0) in enumerate(((gx0 + 70, -1, 3.8), (gx1 - 70, 1, 4.3))):
            m = geri(dilim(t, t0, t0 + 0.3))
            x = xb + yon * (1 - m) * 700
            kutu(ctx, x - 110, gy + 110, 220, 70, C["antrasit"], r=10)
            for d in (-60, 60):
                daire(ctx, x + d, gy + 180, 20, C["koyu"])
                daire(ctx, x + d, gy + 180, 8, C["gri_a"])
        h = geri(dilim(t, 4.8, 5.1))
        if h > 0:
            cy = lerp(600, gy + 120, h)
            kutu(ctx, W / 2 - 100, cy, 200, 100, C["turuncu_k"], r=14)
            kutu(ctx, W / 2 - 100, cy, 60, 100, C["antrasit"], r=14)
            kutu(ctx, W / 2 + 40, cy, 60, 100, C["antrasit"], r=14)
            cizgi(ctx, [(W / 2, cy + 100), (W / 2, cy + 300)], C["gri"], lw=5)
    ctx.restore()
    ust_bant(ctx, L, 4, t)


def s_yukleme(ctx, L, t):
    def ciz(c):
        a2.avlu_arka(c)
        tir_x = 1520
        dorse_bas = tir_x - 1010
        hedef_x = dorse_bas + 30 + 380
        p1 = eio(dilim(t, 0.1, 0.9))
        p2 = eio(dilim(t, 0.9, 1.9))
        p3 = eio(dilim(t, 1.9, 2.5))
        lx = lerp(300, hedef_x, p2)
        ly = lerp(a2.ZEMIN - 60, 420, p1) if p3 == 0 else lerp(420, a2.ZEMIN - 112 - 74, p3)
        a2.mobil_vinc(c, -60, a2.ZEMIN, (lx, 220))
        yerde = t >= 2.5

        def yuk(cc, xd, yd):
            if yerde:
                a2.kiris_yuk()(cc, xd, yd)
        a2.tir(c, tir_x, a2.ZEMIN, 0, yuk=yuk)
        if not yerde:
            a2.kanca_ve_halat(c, (lx, 220), ly - 120, 600)
            gx = lx - 380
            a2.gradyan_kutu(c, gx, ly - 54, 760, 54, C["turuncu_a"], C["turuncu_k"])
            kutu(c, gx, ly - 60, 760, 8, C["antrasit"])
    koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    baslik(ctx, L, L["b5"], L["s5"], t)
    dx, dy = sarsinti(t, [2.5], guc=12)
    dunya(ctx, 0.62, W / 2 + 60 + dx, 1150 + dy, ciz)
    if t > 2.5:
        a2.onay(ctx, W / 2, 1600, 48, dilim(t, 2.5, 2.9))
    ust_bant(ctx, L, 5, t)


def s_yol(ctx, L, t):
    a2.gradyan_kutu(ctx, 0, 0, W, H, a2.renk("#7FB6DE"), a2.renk("#D9ECF7"))
    for katman, (renk1, hiz, yuk, gen) in enumerate(((C["tepe"], 160, 1180, 0.004), (C["tepe_k"], 360, 1230, 0.007))):
        pts = [(0, 1400)]
        for x in range(0, W + 20, 20):
            pts.append((x, yuk - 70 * math.sin((x + t * hiz) * gen) - 30 * math.sin((x + t * hiz) * gen * 2.3)))
        pts.append((W, 1400))
        a2.cokgen(ctx, pts, renk1)
    for k in range(9):
        x = (k * 170 - t * 1100) % (W + 200) - 100
        kutu(ctx, x - 7, 1230, 14, 60, a2.renk("#6B4F35"))
        daire(ctx, x, 1205, 44, C["agac"])
    kutu(ctx, 0, 1280, W, 640, C["yol"])
    for k in range(8):
        x = (k * 260 - t * 2200) % (W + 260) - 130
        kutu(ctx, x, 1560, 150, 16, C["beyaz"], r=4)
    # hız çizgileri
    for k in range(14):
        rnd = random.Random(k)
        y = rnd.uniform(1300, 1500)
        x = (rnd.uniform(0, W) - t * 2600 * rnd.uniform(0.8, 1.3)) % (W + 400) - 200
        cizgi(ctx, [(x, y), (x + rnd.uniform(80, 200), y)], C["beyaz"], lw=4, a=0.6)
    zipla = math.sin(t * 24) * 2
    dunya(ctx, 0.72, W / 2 + 120, 1150 + zipla, lambda c: a2.tir(c, 1500, a2.ZEMIN, teker=t * 18, yuk=a2.kiris_yuk()))
    baslik(ctx, L, L["b6"], L["s6"], t, koyu=True)
    km = int(350 * eio(dilim(t, 0.2, 2.6)))
    kutu(ctx, W / 2 - 230, 660, 460, 150, C["koyu"], r=26, a=0.9)
    yazi(ctx, f"{km} {L['km']}", W / 2, 765, 92, C["turuncu"], kalin=True, hiza="orta")
    ust_bant(ctx, L, 6, t)


def s_kurulum(ctx, L, t):
    def ciz(c):
        xl, xr, yr = 360, 1560, 400
        a2.hol(c, xl, xr, yr, [300, 1620])
        kalk = eio(dilim(t, 0.1, 1.4))
        oturt = eio(dilim(t, 1.4, 1.8))
        hedef = yr - 92
        if t < 1.9:
            ky = lerp(a2.ZEMIN - 186, hedef - 40, kalk)
            ky = lerp(ky, hedef, oturt) if kalk >= 1 else ky
            cizgi(c, [(960, 40), (960, ky - 80)], C["koyu"], lw=3)
            for d in (-420, 420):
                cizgi(c, [(960, ky - 80), (960 + d, ky)], C["koyu"], lw=2.5)
            a2.gradyan_kutu(c, 325, ky, 1270, 54, C["turuncu_a"], C["turuncu_k"])
            kutu(c, 325, ky - 6, 1270, 8, C["antrasit"])
        else:
            car = eo(dilim(t, 1.9, 2.4))
            inis = eio(dilim(t, 2.4, 3.0))
            kalk2 = eio(dilim(t, 3.0, 3.8))
            gez = eio(dilim(t, 3.8, 4.6))
            cx = lerp(1700, 760, car) if car < 1 else lerp(760, 1180, gez)
            kz = lerp(hedef + 130, a2.ZEMIN - 230, inis)
            kz = lerp(kz, a2.ZEMIN - 430, kalk2)
            yukv = (180, 120, "5 t") if t >= 3.0 else None
            a2.kopru_vinc(c, xl, xr, yr, kiris_y=hedef, cx=cx, kanca_y=kz, yuk=yukv)
            if t < 3.0 and inis > 0.5:
                kutu(c, 670, a2.ZEMIN - 120, 180, 120, C["gri"], r=4)
                yazi(c, "5 t", 760, a2.ZEMIN - 46, 36, C["beyaz"], kalin=True, hiza="orta")
    koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    baslik(ctx, L, L["b7"], L["s7"], t)
    dx, dy = sarsinti(t, [1.8], guc=14)
    dunya(ctx, 0.9, W / 2 + dx, 1150 + dy, ciz)
    p = geri(dilim(t, 4.3, 4.6))
    if p > 0:
        ctx.save()
        ctx.translate(W / 2, 1630)
        ctx.scale(p, p)
        ctx.rotate(-0.08)
        kutu(ctx, -230, -60, 460, 110, C["yesil"], r=20)
        yazi(ctx, L["tamam"], 0, 18, 58, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    ust_bant(ctx, L, 7, t)


def s_kapanis(ctx, L, t):
    a2.gradyan_kutu(ctx, 0, 0, W, H, C["turuncu_a"], C["turuncu_k"])
    s = geri(dilim(t, 0.05, 0.4))
    if s > 0:
        ctx.save()
        ctx.translate(W / 2, 640)
        ctx.scale(s, s)
        resim(ctx, LOGO_B, 0, 0, 760, orta=True)
        ctx.restore()
    yazi(ctx, L["slogan"], W / 2, 790, 50, C["beyaz"], hiza="orta", a=dilim(t, 0.3, 0.6), aralik=14)
    kelime_pop(ctx, L["son1"], W / 2, 1060, 96, 0.6, t, renk=C["koyu"])
    kelime_pop(ctx, L["son2"], W / 2, 1180, 96, 0.8, t, renk=C["beyaz"], vurgu={0, 1})
    p = eo(dilim(t, 1.2, 1.5))
    kutu(ctx, W / 2 - 360, 1330, 720, 110, C["koyu"], r=55, a=p)
    yazi(ctx, L["cta"], W / 2, 1402, 42, C["beyaz"], kalin=True, hiza="orta", a=p)


FONK = dict(kanca=s_kanca, siparis=s_siparis, olcu=s_olcu, tasarim=s_tasarim, imalat=s_imalat,
            yukleme=s_yukleme, yol=s_yol, kurulum=s_kurulum, kapanis=s_kapanis)


def sahne_ciz(i, t, L):
    ad, a, b = SAHNE[i]
    y = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(y)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    FONK[ad](ctx, L, t)
    return y


def kare(tg, L):
    for i, (ad, a, b) in enumerate(SAHNE):
        if tg < b or i == len(SAHNE) - 1:
            t = tg - a
            y1 = sahne_ciz(i, t, L)
            if i + 1 < len(SAHNE) and tg > b - GECIS:
                k = eio((tg - (b - GECIS)) / GECIS)
                y2 = sahne_ciz(i + 1, 0.0, L)
                out = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
                c = cairo.Context(out)
                c.set_source_surface(y1, 0, -k * H)  # yukarı kaydırmalı geçiş (Reels kaydırma hissi)
                c.paint()
                c.set_source_surface(y2, 0, (1 - k) * H)
                c.paint()
                return out
            return y1


# ---------------------------------------------------------------- müzik (telifsiz, üretilmiş)
def muzik(yol, sure=TOPLAM, sr=44100):
    import numpy as np
    n = int(sure * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    vurus = VURUS

    def ekle(baslangic, sinyal):
        i = int(baslangic * sr)
        j = min(n, i + len(sinyal))
        out[i:j] += sinyal[: j - i]
    # kick
    kl = int(0.35 * sr)
    tk = np.arange(kl) / sr
    kick = np.sin(2 * np.pi * (45 + 110 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 9)
    # snare / clap
    rng = np.random.default_rng(1)
    sl = int(0.22 * sr)
    ts = np.arange(sl) / sr
    snare = (rng.standard_normal(sl) * 0.6 + np.sin(2 * np.pi * 190 * ts)) * np.exp(-ts * 22)
    hl = int(0.05 * sr)
    hat = rng.standard_normal(hl) * np.exp(-np.arange(hl) / sr * 90) * 0.35
    # bas (kök notalar: A1 F1 C2 G1 döngüsü)
    notalar = [55.0, 43.65, 65.41, 49.0]
    k = 0
    zaman = 0.0
    while zaman < sure:
        bar = int(zaman / (vurus * 4))
        if zaman >= 0.0:
            ekle(zaman, kick * (0.95 if zaman > 2.4 else 0.75))
        if k % 2 == 1 and zaman > 2.4:
            ekle(zaman, snare * 0.5)
        ekle(zaman + vurus / 2, hat)
        f = notalar[bar % 4]
        bl = int(vurus * sr)
        tb = np.arange(bl) / sr
        bas = (np.sign(np.sin(2 * np.pi * f * tb)) * 0.18 + np.sin(2 * np.pi * f * 2 * tb) * 0.2) * np.exp(-tb * 3)
        if zaman > 2.4 and zaman < sure - 2.0:
            ekle(zaman, bas * 0.6)
        zaman += vurus
        k += 1
    # geçiş "whoosh"ları
    for _, a, _b in SAHNE[1:]:
        wl = int(0.35 * sr)
        tw = np.arange(wl) / sr
        g = rng.standard_normal(wl) * np.sin(np.pi * tw / tw[-1]) ** 2 * 0.25
        ekle(a - 0.25, g)
    # başlangıç vuruşu ve kapanış akoru
    for f in (220, 277.2, 329.6):
        ekle(sure - 2.5, np.sin(2 * np.pi * f * t[: int(2.5 * sr)]) * np.exp(-t[: int(2.5 * sr)] * 1.2) * 0.12)
    out = out / max(1e-6, np.max(np.abs(out))) * 0.85
    pcm = (out * 32767).astype(np.int16)
    with wave.open(yol, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    dil = sys.argv[1]
    L = T[dil]
    if sys.argv[2] == "--kare":
        kare(float(sys.argv[3]), L).write_to_png(sys.argv[4])
        return
    cikti = sys.argv[2]
    sessiz = "--sessiz" in sys.argv
    gecici = cikti + ".video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
                           cikti if sessiz else gecici], stdin=subprocess.PIPE)
    for f in range(int(TOPLAM * FPS)):
        ff.stdin.write(bytes(kare(f / FPS, L).get_data()))
    ff.stdin.close()
    ff.wait()
    if not sessiz:
        wav = cikti + ".wav"
        muzik(wav)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", gecici, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", cikti], check=True)
        os.remove(gecici)
        os.remove(wav)
    print(cikti)


if __name__ == "__main__":
    main()
