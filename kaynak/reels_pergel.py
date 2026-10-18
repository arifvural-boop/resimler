"""
Beta Vinç - Instagram Reels: kolon tipi pergel vincin siparişten kuruluma yolculuğu
(2B motion graphics, 1080x1920, 30 sn, Türkçe + İngilizce tek video).

reels.py altyapısını kullanır; pergele özgü sahneleri ve metinleri değiştirir.

Kullanım:
    python reels_pergel.py <cikti.mp4>
    python reels_pergel.py --kare <sn> <cikti.png>
"""
import math
import os
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
    kanca3="Bir pergel vinç nasıl doğar?", kanca3_en="How is a jib crane born?",
    b1="Sipariş geldi!", e1="Order in!", s1="2 ton · 5 m kol",
    b2="Ölç. İki kere.", e2="Measure twice.", s2="Atölyede yerinde keşif",
    b3="Tasarla.", e3="Design it.", s3="Statik hesap + 3B model",
    b4=("Kaynak.", "Boya.", "Montaj."), e4=("Weld.", "Paint.", "Assemble."),
    s4="Beta Üretim Merkezi · Production Center",
    b5="Yükle.", e5="Load up.", s5="Güvenle sabitlendi",
    b6="Yola çık.", e6="Hit the road.", s6="Takipli, sigortalı nakliye",
    b7="Kur. Döndür.", e7="Install. Swing.", s7="360° dönüş + 2 ton yük testi",
    chat1="Merhaba, atölyemize 2 tonluk kolon tipi pergel vinç lazım. Kol boyu 5 m.",
    chat1_en="Hi, we need a 2-tonne pillar jib crane for our workshop. Arm length 5 m.",
    chat2="Hemen keşfe geliyoruz, teklifiniz hazır!",
    chat2_en="We're coming for the site survey, your quote is ready!",
    onay="ONAYLANDI · APPROVED", tamam="TESLİM · DELIVERED", km="km",
    son1="Sıradaki proje sizin.", son2="Your project is next.", cta="Takip et · Follow   betavinc.com",
    slogan="vinç sistemleri", slogan_en="crane systems", adim="ADIM · STEP",
    etiketler=[("kapasite", "capacity"), ("kol boyu", "arm"), ("dönüş", "slewing")],
    kart=("2 t", "5 m", "360°"),
)
R.T["pergel"] = L

ZEMIN = 1620
KX = 250          # kolon ekseni
KOL_UST = 880     # kolon üst kotu (dönen başlık altı)
BOM_UST = 880     # bom üst kotu
BOM_L = 640       # bom uzunluğu (5 m)


# ---------------------------------------------------------------- pergel çizimi
def pergel(ctx, aci=0.0, cx=0.8, kanca_y=None, yuk=None, parcalar=("temel", "kolon", "bom", "gergi", "caraskal"),
           kolon_dy=0.0, bom_dx=0.0, a_bom=1.0):
    """Kolon tipi pergel (yan görünüş). aci: dönme açısı (derece) — kol boyu cos ile kısalır (3B dönüş hissi).
    cx: caraskalın kol üzerindeki konumu (0..1). kanca_y: kanca kotu."""
    cosa = math.cos(math.radians(aci))
    on = math.sin(math.radians(aci)) < 0  # kol izleyiciye doğru mu
    Lb = BOM_L * cosa
    if "temel" in parcalar:
        kutu(ctx, KX - 150, ZEMIN, 300, 34, C["beton"])
        kutu(ctx, KX - 150, ZEMIN, 300, 8, a2.renk("#A29E96"))
    ky = kolon_dy
    if "kolon" in parcalar:
        kutu(ctx, KX - 110, ZEMIN - 26 + ky, 220, 26, C["antrasit"], r=3)
        for sx in (-1, 1):
            a2.cokgen(ctx, [(KX + sx * 36, ZEMIN - 26 + ky), (KX + sx * 100, ZEMIN - 26 + ky), (KX + sx * 36, ZEMIN - 150 + ky)],
                      C["antrasit"])
            for bx in (KX + sx * 80,):
                kutu(ctx, bx - 8, ZEMIN - 40 + ky, 16, 14, C["gri_a"], r=2)
        a2.gradyan_kutu(ctx, KX - 36, KOL_UST + ky, 72, ZEMIN - 26 - KOL_UST, a2.renk("#6B737D"), a2.renk("#4E555E"), dikey=False)
        kutu(ctx, KX - 40, KOL_UST + 40 + ky, 80, 22, C["antrasit"], r=4)

    def bom_ve_gergi():
        if "bom" not in parcalar:
            return
        bx = bom_dx
        # dönen başlık + gergi direği
        kutu(ctx, KX - 44 + bx, BOM_UST - 8, 88, 70, C["antrasit"], r=8, a=a_bom)
        kutu(ctx, KX - 44 + bx, BOM_UST + 20, 88, 10, C["turuncu"], a=a_bom)
        kutu(ctx, KX - 22 + bx, BOM_UST - 170, 44, 165, a2.renk("#5E666F"), r=4, a=a_bom)
        kutu(ctx, KX - 28 + bx, BOM_UST - 180, 56, 12, C["antrasit"], r=3, a=a_bom)
        # bom (IPE): üst/alt başlık + gövde; uzaklaşırken incelir
        if abs(Lb) > 4:
            x0 = KX + 44 + bx
            x1 = KX + 44 + bx + Lb
            xa, xb = min(x0, x1), max(x0, x1)
            hb = 56
            a2.gradyan_kutu(ctx, xa, BOM_UST, xb - xa, hb, C["turuncu_a"], C["turuncu_k"])
            kutu(ctx, xa, BOM_UST - 6, xb - xa, 8, C["turuncu_k"], a=a_bom)
            kutu(ctx, xa, BOM_UST + hb - 2, xb - xa, 8, C["turuncu_k"], a=a_bom)
            if xb - xa > 260:
                kutu(ctx, (xa + xb) / 2 - 62, BOM_UST + 14, 124, 28, C["beyaz"], r=4, a=a_bom)
                R.resim(ctx, R.LOGO_K, (xa + xb) / 2, BOM_UST + 28, 92, a=a_bom, orta=True)
            kutu(ctx, x1 - 6 if Lb > 0 else x1, BOM_UST - 8, 8, hb + 14, C["antrasit"], a=a_bom)
            if "gergi" in parcalar:
                gx = x0 + Lb * 0.72
                cizgi(ctx, [(KX + bx, BOM_UST - 172), (gx, BOM_UST - 4)], C["turuncu"], lw=14, a=a_bom)
                kutu(ctx, gx - 14, BOM_UST - 20, 28, 18, C["antrasit"], r=3, a=a_bom)
                daire(ctx, KX + bx, BOM_UST - 170, 9, C["gri_a"], a=a_bom)
        return

    def caraskal():
        if "caraskal" not in parcalar or abs(Lb) < 60:
            return
        x = KX + 44 + bom_dx + Lb * cx
        yt = BOM_UST + 56
        kutu(ctx, x - 40, yt - 6, 80, 30, C["antrasit"], r=4)
        kutu(ctx, x - 58, yt + 24, 116, 58, C["turuncu"], r=10)
        kutu(ctx, x - 58, yt + 24, 34, 58, C["antrasit"], r=10)
        kutu(ctx, x + 22, yt + 24, 36, 58, C["antrasit"], r=10)
        kutu(ctx, x + 26, yt + 40, 28, 14, C["beyaz"], r=2)
        kutu(ctx, x - 48, yt + 86, 36, 80, C["koyu"], r=4)  # zincir torbası
        ky_ = kanca_y if kanca_y is not None else yt + 260
        for k in range(int((ky_ - yt - 82) / 14)):
            daire(ctx, x + 8, yt + 88 + k * 14, 4, C["gri"])
        kutu(ctx, x - 6, ky_, 28, 22, C["turuncu"], r=5)
        ctx.new_sub_path()
        ctx.arc(x + 8, ky_ + 40, 13, -math.pi * 0.05, math.pi * 1.25)
        a2.boya(ctx, C["koyu"])
        ctx.set_line_width(7)
        ctx.stroke()
        if yuk:
            yw, yh, metin = yuk
            for dx in (-yw / 2 + 10, yw / 2 - 10):
                cizgi(ctx, [(x + 8, ky_ + 52), (x + 8 + dx, ky_ + 104)], C["koyu"], lw=2.5)
            kutu(ctx, x + 8 - yw / 2, ky_ + 104, yw, yh, C["gri"], r=4)
            yazi(ctx, metin, x + 8, ky_ + 104 + yh / 2 + 14, 38, C["beyaz"], kalin=True, hiza="orta")

    # kol izleyiciye doğru geliyorsa kolonun önünde çiz
    if on:
        bom_ve_gergi()
        caraskal()
    else:
        bom_ve_gergi()
        caraskal()


def atolye(ctx, tezgah=True):
    """Dikey kadraj atölye: duvar, pencereler, iş tezgâhı, zemin."""
    a2.gradyan_kutu(ctx, 0, 560, W, ZEMIN - 560, C["duvar"], a2.renk("#E3E0DA"))
    for i in range(3):
        kutu(ctx, 520 + i * 180, 640, 140, 120, C["gok"], r=6, a=0.85)
    cizgi(ctx, [(0, 600), (W, 600)], C["gri"], lw=5, a=0.5)
    kutu(ctx, 0, ZEMIN, W, 1720 - ZEMIN, C["zemin"])
    for i in range(10):
        cizgi(ctx, [(i * 130, ZEMIN), (i * 130 - 70, 1720)], C["gri"], lw=1, a=0.25)
    if not tezgah:
        return
    # tezgâh ve parça
    kutu(ctx, 700, ZEMIN - 160, 300, 18, a2.renk("#8C6A48"), r=4)
    for x in (712, 978):
        kutu(ctx, x, ZEMIN - 142, 12, 142, a2.renk("#6E5236"))
    kutu(ctx, 760, ZEMIN - 230, 110, 70, C["gri"], r=4)


# ---------------------------------------------------------------- sahneler
def s_olcu(ctx, L_, t):
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    atolye(ctx)
    # temel yeri işareti
    kutu(ctx, KX - 150, ZEMIN, 300, 34, C["beton"], a=0.6)
    a2.cizgi(ctx, [(KX - 26, ZEMIN + 17), (KX + 26, ZEMIN + 17)], C["kirmizi"], lw=4)
    a2.cizgi(ctx, [(KX, ZEMIN - 9), (KX, ZEMIN + 43)], C["kirmizi"], lw=4)
    w = eo(dilim(t, 0.0, 0.5))
    tx = lerp(1180, 600, w)
    el = a2.insan(ctx, tx, ZEMIN, boy=230, kol=-2.6 if w >= 1 else 3.0, yuz_sag=False, adim=t * 10 if w < 1 else 0)
    p = eio(dilim(t, 0.5, 1.6))
    # kol boyu: kolon ekseninden yatay
    yl = 1000
    if p > 0:
        cizgi(ctx, [(KX, yl), (lerp(KX, KX + 44 + BOM_L, p), yl)], C["kirmizi"], lw=5)
        daire(ctx, lerp(KX, KX + 44 + BOM_L, p), yl, 10, C["kirmizi"])
        # taranan dönüş alanı (zeminde elips)
        ctx.save()
        ctx.translate(KX, ZEMIN + 10)
        ctx.scale(1, 0.12)
        ctx.arc(0, 0, (44 + BOM_L) * p, 0, 2 * math.pi)
        a2.boya(ctx, C["kirmizi"], 0.15)
        ctx.fill()
        ctx.restore()
    dx, dy = R.sarsinti(t, [1.6])
    s = 1 + 0.12 * math.exp(-max(0, t - 1.6) * 12) * (t >= 1.6)
    ctx.save()
    ctx.translate(W / 2 + dx, 760 + dy)
    ctx.scale(s, s)
    a = dilim(t, 0.4, 0.6)
    kutu(ctx, -280, -84, 560, 116, C["beyaz"], r=22, a=0.96 * a)
    yazi(ctx, f"R {R.mm(L_, int(5000 * p))} mm", 0, 6, 80, C["kirmizi"], kalin=True, hiza="orta", a=a)
    ctx.restore()
    p2 = eio(dilim(t, 1.7, 2.4))
    if p2 > 0:
        hx = 140
        a2.olcu_cizgisi(ctx, (hx, ZEMIN), (hx, lerp(ZEMIN, BOM_UST, p2)), None)
        kutu(ctx, hx + 22, 1180, 260, 70, C["beyaz"], r=14, a=0.96)
        yazi(ctx, f"{R.mm(L_, int(4500 * p2))} mm", hx + 152, 1230, 44, C["kirmizi"], kalin=True, hiza="orta")
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

    def kutu_p(x0, y0, x1, y1, a0, a1, lw=4):
        parca([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], a0, a1, lw)

    parca([(60, ZEMIN), (1020, ZEMIN)], 0.1, 0.4, 3)
    kutu_p(KX - 110, ZEMIN - 26, KX + 110, ZEMIN, 0.2, 0.5)
    kutu_p(KX - 36, KOL_UST, KX + 36, ZEMIN - 26, 0.3, 0.9)
    kutu_p(KX - 22, BOM_UST - 170, KX + 22, BOM_UST - 5, 0.6, 1.0, 3)
    kutu_p(KX + 44, BOM_UST, KX + 44 + BOM_L, BOM_UST + 56, 0.7, 1.2, 5)
    parca([(KX, BOM_UST - 172), (KX + 44 + BOM_L * 0.72, BOM_UST - 4)], 1.0, 1.3, 3)
    hx = KX + 44 + BOM_L * 0.8
    kutu_p(hx - 58, BOM_UST + 80, hx + 58, BOM_UST + 138, 1.1, 1.4, 3)
    parca([(hx, BOM_UST + 138), (hx, 1340)], 1.3, 1.5, 3)
    # dönüş yayı (plan)
    if t > 1.2:
        pa = eio(dilim(t, 1.2, 1.9))
        ctx.save()
        ctx.translate(KX, 1450)
        ctx.scale(1, 0.18)
        ctx.arc(0, 0, 44 + BOM_L, -math.pi * 0.95, -math.pi * 0.95 + 2 * math.pi * pa)
        ctx.restore()
        a2.boya(ctx, sari)
        ctx.set_line_width(3)
        ctx.set_dash([12, 8])
        ctx.stroke()
        ctx.set_dash([])
        yazi(ctx, "360°", KX + 44 + BOM_L - 60, 1430, 40, sari, kalin=True, a=pa)
    if t > 1.3:
        a2.olcu_cizgisi(ctx, (KX, 650), (KX + 44 + BOM_L, 650), "5.000", c=sari, ilerle=dilim(t, 1.3, 1.7),
                        ofs=-24, zemin=a2.renk("#0F2740"))
    if t > 1.5:
        a2.olcu_cizgisi(ctx, (1000, ZEMIN), (1000, lerp(ZEMIN, BOM_UST, dilim(t, 1.5, 1.9))), None, c=sari)
        a = dilim(t, 1.7, 1.9)
        ctx.save()
        ctx.translate(1040, (ZEMIN + BOM_UST) / 2)
        ctx.rotate(-math.pi / 2)
        yazi(ctx, "4.500", 0, 0, 34, sari, kalin=True, hiza="orta", a=a)
        ctx.restore()
        yazi(ctx, "2 t", hx + 30, 1330, 40, sari, kalin=True, a=a)
    if t > 1.9:
        a2.onay(ctx, W / 2, 1790, 46, dilim(t, 1.9, 2.4))
    R.baslik(ctx, L_, L_["b3"], L_["s3"], t, en=L_["e3"])
    R.ust_bant(ctx, L_, 3, t)


def s_imalat(ctx, L_, t):
    """Kaynak ve boya: bom (kiriş) yakın plan (reels.py ile aynı); montaj: kolon + bom + caraskal birleşir."""
    if t < 3.8:
        return R_s_imalat(ctx, L_, t)
    i, t_alt = 2, t - 3.8
    R.koyu_zemin(ctx, a2.renk("#33383F"), C["koyu"])
    R.kelime_pop(ctx, L_["b4"][i], W / 2, 400, 116, 0.02, t_alt, renk=C["beyaz"])
    R.kelime_pop(ctx, L_["e4"][i], W / 2, 476, 60, 0.15, t_alt, renk=C["turuncu"])
    yazi(ctx, L_["s4"], W / 2, 540, 30, C["gri_a"], kalin=True, hiza="orta")
    kutu(ctx, 0, ZEMIN, W, 300, a2.renk("#3E444C"))
    # kolon aşağıdan yükselir, bom yandan kayar, caraskal yukarıdan iner
    k = geri(dilim(t_alt, 0.0, 0.35))
    b = geri(dilim(t_alt, 0.35, 0.75))
    c_ = geri(dilim(t_alt, 0.8, 1.2))
    dx, dy = R.sarsinti(t_alt, [0.35, 0.75, 1.2], guc=10)
    ctx.save()
    ctx.translate(dx, dy)
    ctx.save()
    ctx.translate(0, (1 - k) * 900)
    pergel(ctx, parcalar=("kolon",))
    ctx.restore()
    if b > 0:
        pergel(ctx, parcalar=("bom", "gergi"), bom_dx=(1 - b) * 900)
    if c_ > 0:
        ctx.save()
        ctx.translate(0, -(1 - c_) * 700)
        pergel(ctx, parcalar=("caraskal",), cx=0.8, kanca_y=BOM_UST + 330)
        ctx.restore()
    ctx.restore()
    R.ust_bant(ctx, L_, 4, t)


def pergel_yuku():
    """Tır üzerinde: yatırılmış kolon (gri) + bom (turuncu) + taban levhası, takozlar ve spanzetler."""
    def ciz(c, xd, yd):
        for i in range(4):
            kutu(c, xd + 70 + i * 220, yd - 14, 46, 14, a2.renk("#9C7A4F"))
        a2.gradyan_kutu(c, xd + 40, yd - 60, 600, 46, a2.renk("#6B737D"), a2.renk("#4E555E"))
        kutu(c, xd + 640, yd - 76, 26, 76, C["antrasit"], r=3)
        a2.gradyan_kutu(c, xd + 40, yd - 122, 720, 56, C["turuncu_a"], C["turuncu_k"])
        kutu(c, xd + 40, yd - 128, 720, 8, C["turuncu_k"])
        kutu(c, xd + 340, yd - 108, 124, 28, C["beyaz"], r=4)
        yazi(c, "beta", xd + 402, yd - 86, 22, C["antrasit"], kalin=True, hiza="orta")
        for xs in (xd + 180, xd + 560):
            cizgi(c, [(xs, yd - 128), (xs - 20, yd)], C["kirmizi"], lw=5, a=0.9)
    return ciz


def s_kurulum(ctx, L_, t):
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    atolye(ctx, tezgah=False)
    # 0-1.2: kolon askıyla iner ve temele oturur, cıvatalar parlar
    # 1.2-2.0: bom + caraskal takılır; 2.0-3.4: 360° dönüş; 3.4-4.6: 2 t yük testi
    inis = eio(dilim(t, 0.0, 1.0))
    bom_tak = eo(dilim(t, 1.15, 1.6))
    don = eio(dilim(t, 2.0, 3.4))
    aci = 360 * don
    kanca = eio(dilim(t, 3.4, 3.9))
    kalk = eio(dilim(t, 3.9, 4.5))
    dx, dy = R.sarsinti(t, [1.0, 1.6], guc=12)
    ctx.save()
    ctx.translate(dx, dy)
    kolon_dy = -(1 - inis) * 520
    pergel(ctx, parcalar=("temel",))
    if t < 1.15:
        cizgi(ctx, [(KX, 560), (KX, KOL_UST + kolon_dy - 30)], C["koyu"], lw=3)
        kutu(ctx, KX - 18, KOL_UST + kolon_dy - 50, 36, 24, C["antrasit"], r=4)
        pergel(ctx, parcalar=("kolon",), kolon_dy=kolon_dy)
    else:
        pergel(ctx, parcalar=("kolon",))
    pb = dilim(t, 0.95, 1.3)
    if 0 < pb < 1:
        for x in (KX - 80, KX + 80):
            daire(ctx, x, ZEMIN - 34, 16 * math.sin(pb * math.pi), a2.renk("#FFF3C4"), a=0.95)
    if bom_tak > 0:
        ky = lerp(BOM_UST + 230, ZEMIN - 230, kanca)
        ky = lerp(ky, ZEMIN - 430, kalk)
        yuk = (150, 110, "2 t") if t >= 3.9 else None
        if 3.4 <= t < 3.9:
            hx = KX + 44 + BOM_L * 0.8 + 8
            kutu(ctx, hx - 75, ZEMIN - 110, 150, 110, C["gri"], r=4)
            yazi(ctx, "2 t", hx, ZEMIN - 42, 38, C["beyaz"], kalin=True, hiza="orta")
        pergel(ctx, aci=aci, cx=0.8, kanca_y=ky, yuk=yuk, parcalar=("bom", "gergi", "caraskal"),
               bom_dx=(1 - bom_tak) * 900)
        # dönüş göstergesi
        if 2.0 <= t < 3.6:
            a = dilim(t, 2.0, 2.2) * (1 - dilim(t, 3.4, 3.6))
            kutu(ctx, W / 2 + 80, 700, 300, 110, C["koyu"], r=22, a=0.9 * a)
            yazi(ctx, f"{int(aci)}°", W / 2 + 230, 778, 72, C["turuncu"], kalin=True, hiza="orta", a=a)
    ctx.restore()
    R.baslik(ctx, L_, L_["b7"], L_["s7"], t, en=L_["e7"])
    p = geri(dilim(t, 4.3, 4.6))
    if p > 0:
        ctx.save()
        ctx.translate(W / 2, 1790)
        ctx.scale(p, p)
        ctx.rotate(-0.08)
        kutu(ctx, -340, -60, 680, 110, C["yesil"], r=20)
        yazi(ctx, L_["tamam"], 0, 18, 50, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    R.ust_bant(ctx, L_, 7, t)


# reels.py fonksiyonlarını pergel sürümleriyle değiştir
R_s_imalat = R.s_imalat
R.FONK.update(olcu=s_olcu, tasarim=s_tasarim, imalat=s_imalat, kurulum=s_kurulum)
a2.kiris_yuk = lambda uzun=760: pergel_yuku()


def main():
    if sys.argv[1] == "--kare":
        R.kare(float(sys.argv[2]), L).write_to_png(sys.argv[3])
        return
    sys.argv = [sys.argv[0], "pergel", sys.argv[1]]
    R.main()


if __name__ == "__main__":
    main()
