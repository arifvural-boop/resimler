"""
Beta Vinç - Instagram Reels: yük asansörünün siparişten kuruluma yolculuğu
(2B motion graphics, 1080x1920, 30 sn, Türkçe + İngilizce tek video).

reels.py altyapısını kullanır; yük asansörüne özgü sahneleri ve metinleri değiştirir.

Kullanım:
    python reels_asansor.py <cikti.mp4>
    python reels_asansor.py --kare <sn> <cikti.png>
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
    kanca3="Bir yük asansörü nasıl doğar?", kanca3_en="How is a freight lift born?",
    b1="Sipariş geldi!", e1="Order in!", s1="3 ton · 4 durak",
    b2="Ölç. İki kere.", e2="Measure twice.", s2="Kuyu ve kat yükseklikleri",
    b3="Tasarla.", e3="Design it.", s3="Statik hesap + 3B model",
    b4=("Kaynak.", "Boya.", "Montaj."), e4=("Weld.", "Paint.", "Assemble."),
    s4="Beta Üretim Merkezi · Production Center",
    b5="Yükle.", e5="Load up.", s5="Güvenle sabitlendi",
    b6="Yola çık.", e6="Hit the road.", s6="Takipli, sigortalı nakliye",
    b7="Kur. Yükselt.", e7="Install. Lift.", s7="4 durak + 3 ton yük testi",
    chat1="Merhaba, depomuza 3 tonluk yük asansörü lazım. 4 durak, kabin 2×3 m.",
    chat1_en="Hi, we need a 3-tonne freight lift for our warehouse. 4 stops, 2×3 m car.",
    chat2="Hemen keşfe geliyoruz, teklifiniz hazır!",
    chat2_en="We're coming for the site survey, your quote is ready!",
    onay="ONAYLANDI · APPROVED", tamam="TESLİM · DELIVERED", km="km",
    son1="Sıradaki proje sizin.", son2="Your project is next.", cta="Takip et · Follow   betavinc.com",
    slogan="vinç sistemleri", slogan_en="crane systems", adim="ADIM · STEP",
    etiketler=[("kapasite", "capacity"), ("durak", "stops"), ("kabin", "car")],
    kart=("3 t", "4", "2×3 m"),
)
R.T["asansor"] = L

ZEMIN = 1700           # zemin kat döşeme üstü
KAT_H = 240            # kat yüksekliği (ekranda) ≈ 4 m
KATLAR = 4
KX0, KX1 = 330, 750    # kuyu iç kenarları
UST = ZEMIN - KAT_H * (KATLAR - 1) - 360   # kuyu tepesi (makine dairesi + üst boşluk)


def kat_y(i):
    return ZEMIN - i * KAT_H


# ---------------------------------------------------------------- çizim
def bina(ctx, kesit=True):
    """Depo binası kesiti: 4 kat döşemesi, kuyu boşluğu, kat kapıları yerleri."""
    a2.gradyan_kutu(ctx, 0, 560, W, ZEMIN - 560, a2.renk("#EAE7E1"), a2.renk("#DCD8D1"))
    kutu(ctx, 0, ZEMIN, W, 1800 - ZEMIN, C["zemin"])
    for i in range(KATLAR):
        y = kat_y(i)
        if i > 0:
            kutu(ctx, 0, y, KX0 - 40, 28, C["beton"])
            kutu(ctx, KX1 + 40, y, W - KX1 - 40, 28, C["beton"])
        # depo rafları
        for k in range(2):
            x = 60 + k * 120
            if y - 170 > 600:
                kutu(ctx, x, y - 150, 90, 150, a2.renk("#C9C3B8"), a=0.7)
                for j in range(3):
                    kutu(ctx, x + 6, y - 140 + j * 48, 78, 36, a2.renk("#B0895E"), r=3, a=0.8)
        yazi(ctx, f"{i}", W - 70, y - 30, 40, C["gri"], kalin=True, hiza="orta")
    # kuyu duvarları
    kutu(ctx, KX0 - 40, UST, 40, ZEMIN - UST, C["beton"])
    kutu(ctx, KX1, UST, 40, ZEMIN - UST, C["beton"])
    kutu(ctx, KX0 - 40, UST - 30, KX1 - KX0 + 80, 30, C["beton"])
    if kesit:
        a2.gradyan_kutu(ctx, KX0, UST, KX1 - KX0, ZEMIN - UST, a2.renk("#D3CFC8"), a2.renk("#C2BDB5"), dikey=False)


def raylar(ctx, ust=UST, a=1.0):
    for x in (KX0 + 18, KX1 - 30):
        kutu(ctx, x, ust, 12, ZEMIN - ust, C["antrasit"], a=a)
        for k in range(int((ZEMIN - ust) / 120)):
            kutu(ctx, x - 10 if x < W / 2 else x + 4, ust + 40 + k * 120, 18, 10, C["gri"], a=a)


def makine(ctx, a=1.0):
    """Kuyu tepesinde tahrik grubu: motor + redüktör + tambur."""
    y = UST + 20
    kutu(ctx, KX0 + 60, y, KX1 - KX0 - 120, 18, C["antrasit"], a=a)
    kutu(ctx, KX0 + 90, y + 18, 120, 70, C["turuncu"], r=10, a=a)
    kutu(ctx, KX0 + 210, y + 26, 80, 54, C["antrasit"], r=8, a=a)
    daire(ctx, KX0 + 330, y + 54, 34, C["gri_a"], a=a)
    daire(ctx, KX0 + 330, y + 54, 12, C["antrasit"], a=a)


def kabin(ctx, yk, kapi=0.0, yuk=None, halat=True, a=1.0):
    """Kabin: taban kotu yk; kapi: 0 kapalı, 1 açık (makaslı kapı)."""
    x0, x1 = KX0 + 44, KX1 - 44
    h = 170
    if halat:
        for dx in (-14, 0, 14):
            cizgi(ctx, [((KX0 + KX1) / 2 + dx, UST + 70), ((KX0 + KX1) / 2 + dx, yk - h - 20)], C["gri"], lw=3, a=a)
    kutu(ctx, x0 - 10, yk - h - 30, x1 - x0 + 20, 30, C["turuncu_k"], r=4, a=a)       # üst kiriş
    kutu(ctx, x0 - 10, yk - 8, x1 - x0 + 20, 22, C["turuncu_k"], r=4, a=a)            # taban
    for x in (x0 - 10, x1 - 4):
        kutu(ctx, x, yk - h - 30, 14, h + 44, C["turuncu"], a=a)                       # dikmeler
    kutu(ctx, x0 + 4, yk - h, x1 - x0 - 8, h - 8, a2.renk("#F6EFE4"), a=0.5 * a)      # iç
    for k in range(5):
        cizgi(ctx, [(x0 + 4, yk - h + 20 + k * 40), (x1 - 4, yk - h + 20 + k * 40)], C["turuncu"], lw=2, a=0.35 * a)
    kutu(ctx, (x0 + x1) / 2 - 60, yk - h - 26, 120, 22, C["beyaz"], r=3, a=a)
    R.resim(ctx, R.LOGO_K, (x0 + x1) / 2, yk - h - 15, 84, a=a, orta=True)
    if yuk:
        yw, metin = yuk
        cx = (x0 + x1) / 2
        kutu(ctx, cx - yw / 2, yk - 22, yw, 14, a2.renk("#9C7A4F"), a=a)   # palet
        kutu(ctx, cx - yw / 2 + 6, yk - 130, yw - 12, 108, C["gri"], r=4, a=a)
        yazi(ctx, metin, cx, yk - 64, 42, C["beyaz"], kalin=True, hiza="orta", a=a)
    # makaslı kapı (önden)
    kap = 1 - kapi
    if kap > 0.02:
        gen = (x1 - x0) * kap
        for k in range(int(gen / 26) + 1):
            xx = x0 + k * 26
            if xx > x0 + gen:
                break
            cizgi(ctx, [(xx, yk - h), (min(xx + 26, x0 + gen), yk - 10)], C["antrasit"], lw=3, a=a)
            cizgi(ctx, [(min(xx + 26, x0 + gen), yk - h), (xx, yk - 10)], C["antrasit"], lw=3, a=a)


def kat_kapilari(ctx, acik_kat=None, acik=0.0):
    for i in range(KATLAR):
        y = kat_y(i)
        for x in (KX0 - 40, KX1):
            kutu(ctx, x, y - 230, 40, 230, C["antrasit"], a=0.9)
        if acik_kat == i:
            kutu(ctx, KX0 - 40, y - 230, 40, 230, C["yesil"], a=0.5 * acik)


def gosterge(ctx, kat, a=1.0):
    """Dijital kat göstergesi (kuyu üstünde)."""
    x, y = W - 160, UST + 90
    kutu(ctx, x - 150, y - 60, 300, 110, C["koyu"], r=20, a=a)
    yazi(ctx, "▲" if kat >= 0 else "", x - 80, y + 20, 50, C["yesil"], kalin=True, hiza="orta", a=a)
    yazi(ctx, f"{max(0, int(round(kat)))}", x + 40, y + 28, 84, C["turuncu"], kalin=True, hiza="orta", a=a)


# ---------------------------------------------------------------- sahneler
def s_olcu(ctx, L_, t):
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    bina(ctx)
    kat_kapilari(ctx)
    w = eo(dilim(t, 0.0, 0.5))
    tx = lerp(1180, 900, w)
    el = a2.insan(ctx, tx, ZEMIN, boy=220, kol=-2.7 if w >= 1 else 3.0, yuz_sag=False, adim=t * 10 if w < 1 else 0)
    p = eio(dilim(t, 0.5, 1.4))
    ly = ZEMIN - 120
    if p > 0:
        cizgi(ctx, [(KX1, ly), (lerp(KX1, KX0, p), ly)], C["kirmizi"], lw=5)
        daire(ctx, lerp(KX1, KX0, p), ly, 10, C["kirmizi"])
        a2.olcu_cizgisi(ctx, (KX0, UST + 120), (lerp(KX0, KX1, p), UST + 120), None)
    dx, dy = R.sarsinti(t, [1.4])
    ctx.save()
    ctx.translate(W / 2 + dx, 760 + dy)
    a = dilim(t, 0.4, 0.6)
    kutu(ctx, -260, -84, 520, 116, C["beyaz"], r=22, a=0.96 * a)
    yazi(ctx, f"{R.mm(L_, int(2600 * p))} mm", 0, 6, 82, C["kirmizi"], kalin=True, hiza="orta", a=a)
    ctx.restore()
    p2 = eio(dilim(t, 1.5, 2.4))
    if p2 > 0:
        hx = 900
        a2.olcu_cizgisi(ctx, (hx, ZEMIN), (hx, lerp(ZEMIN, kat_y(3), p2)), None)
        kutu(ctx, hx - 300, 1280, 280, 70, C["beyaz"], r=14, a=0.96)
        yazi(ctx, f"{R.mm(L_, int(12000 * p2))} mm", hx - 160, 1330, 44, C["kirmizi"], kalin=True, hiza="orta")
    if t > 2.4:
        a2.onay(ctx, W / 2, 1830, 44, dilim(t, 2.4, 2.9))
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

    parca([(40, ZEMIN), (1040, ZEMIN)], 0.1, 0.4, 3)
    for i in range(1, KATLAR):
        parca([(40, kat_y(i)), (KX0 - 40, kat_y(i))], 0.2, 0.5, 3)
        parca([(KX1 + 40, kat_y(i)), (1040, kat_y(i))], 0.2, 0.5, 3)
    kutu_p(KX0 - 40, UST - 30, KX1 + 40, ZEMIN, 0.3, 0.9, 4)
    kutu_p(KX0, UST, KX1, ZEMIN, 0.4, 1.0, 2)
    for x in (KX0 + 24, KX1 - 24):
        parca([(x, UST), (x, ZEMIN)], 0.6, 1.0, 3)
    kutu_p(KX0 + 90, UST + 38, KX0 + 290, UST + 108, 0.8, 1.1, 3)
    yc = kat_y(1)
    kutu_p(KX0 + 34, yc - 200, KX1 - 34, yc, 0.9, 1.3, 5)
    parca([((KX0 + KX1) / 2, UST + 110), ((KX0 + KX1) / 2, yc - 200)], 1.1, 1.4, 3)
    if t > 1.3:
        a2.olcu_cizgisi(ctx, (KX0, 585), (KX1, 585), "2.600", c=sari, ilerle=dilim(t, 1.3, 1.7), ofs=-24,
                        zemin=a2.renk("#0F2740"))
    if t > 1.5:
        a2.olcu_cizgisi(ctx, (960, ZEMIN), (960, lerp(ZEMIN, kat_y(3), dilim(t, 1.5, 1.9))), None, c=sari)
        a = dilim(t, 1.7, 1.9)
        ctx.save()
        ctx.translate(1000, (ZEMIN + kat_y(3)) / 2)
        ctx.rotate(-math.pi / 2)
        yazi(ctx, "12.000", 0, 0, 34, sari, kalin=True, hiza="orta", a=a)
        ctx.restore()
        yazi(ctx, "3 t", (KX0 + KX1) / 2 - 30, yc - 100, 48, sari, kalin=True, a=a)
        for i in range(KATLAR):
            yazi(ctx, f"{i}", 80, kat_y(i) - 30, 34, sari, kalin=True, hiza="orta", a=a)
    if t > 1.9:
        a2.onay(ctx, W / 2, 1830, 44, dilim(t, 1.9, 2.4))
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
    r = geri(dilim(t_alt, 0.0, 0.35))
    k = geri(dilim(t_alt, 0.35, 0.75))
    m = geri(dilim(t_alt, 0.8, 1.2))
    dx, dy = R.sarsinti(t_alt, [0.35, 0.75, 1.2], guc=10)
    ctx.save()
    ctx.translate(dx, dy)
    ctx.save()
    ctx.translate(0, (1 - r) * 1100)
    raylar(ctx, ust=900)
    ctx.restore()
    if k > 0:
        ctx.save()
        ctx.translate((1 - k) * 900, 0)
        kabin(ctx, ZEMIN - 20, halat=False)
        ctx.restore()
    if m > 0:
        ctx.save()
        ctx.translate(0, -(1 - m) * 600 + (900 - UST) - 40)
        makine(ctx)
        ctx.restore()
    ctx.restore()
    R.ust_bant(ctx, L_, 4, t)


def asansor_yuku():
    def ciz(c, xd, yd):
        for i in range(4):
            kutu(c, xd + 70 + i * 220, yd - 14, 46, 14, a2.renk("#9C7A4F"))
        for j in range(3):   # kılavuz ray demeti
            kutu(c, xd + 40, yd - 24 - j * 14, 760, 10, C["antrasit"])
        x = xd + 220
        kutu(c, x, yd - 250, 360, 200, a2.renk("#F6EFE4"), a=0.6)
        for d in (0, 346):
            kutu(c, x + d, yd - 260, 14, 220, C["turuncu"])
        kutu(c, x - 6, yd - 266, 372, 22, C["turuncu_k"], r=3)
        kutu(c, x - 6, yd - 62, 372, 18, C["turuncu_k"], r=3)
        kutu(c, x + 120, yd - 262, 120, 18, C["beyaz"], r=3)
        yazi(c, "beta", x + 180, yd - 248, 18, C["antrasit"], kalin=True, hiza="orta")
        for xs in (x + 60, x + 300):
            cizgi(c, [(xs, yd - 266), (xs - 20, yd)], C["kirmizi"], lw=5, a=0.9)
    return ciz


def s_kurulum(ctx, L_, t):
    """0-1.0 raylar ve makine; 1.0-1.6 kabin kuyuya iner; 1.6-2.2 palet (3 t) yüklenir;
    2.2-3.8 kabin 0 → 3. kata yükselir (kat göstergesi); 3.8-4.6 kapı açılır, teslim."""
    R.koyu_zemin(ctx, a2.renk("#2B3036"), C["koyu"])
    bina(ctx)
    ray_p = eio(dilim(t, 0.0, 0.8))
    raylar(ctx, ust=lerp(ZEMIN, UST, ray_p))
    if t > 0.6:
        ctx.save()
        ctx.translate(0, -(1 - eo(dilim(t, 0.6, 1.0))) * 400)
        makine(ctx)
        ctx.restore()
    kab_in = eio(dilim(t, 1.0, 1.6))
    yuk_in = eo(dilim(t, 1.6, 2.2))
    cik = eio(dilim(t, 2.2, 3.8))
    kat = 3 * cik
    yk = lerp(UST + 260, ZEMIN, kab_in) if t < 2.2 else lerp(ZEMIN, kat_y(3), cik)
    kapi = 1.0 - dilim(t, 2.0, 2.2) if t < 3.8 else dilim(t, 3.8, 4.2)
    if t < 1.6:
        kapi = 1.0
    dx, dy = R.sarsinti(t, [1.6, 3.8], guc=12)
    ctx.save()
    ctx.translate(dx, dy)
    if t >= 1.0:
        yuk = (220, "3 t") if t >= 1.6 else None
        if 1.6 <= t < 2.2:
            # palet transpaleti ile içeri itilir
            x = lerp(W + 100, (KX0 + KX1) / 2, yuk_in)
            kutu(ctx, x - 104, ZEMIN - 22, 208, 14, a2.renk("#9C7A4F"))
            kutu(ctx, x - 104, ZEMIN - 130, 208, 108, C["gri"], r=4)
            yazi(ctx, "3 t", x, ZEMIN - 64, 42, C["beyaz"], kalin=True, hiza="orta")
            yuk = None
        kabin(ctx, yk, kapi=kapi, yuk=yuk)
    kat_kapilari(ctx, acik_kat=3 if t >= 3.8 else None, acik=dilim(t, 3.8, 4.2))
    ctx.restore()
    if t >= 2.2:
        gosterge(ctx, kat, a=dilim(t, 2.2, 2.4))
    R.baslik(ctx, L_, L_["b7"], L_["s7"], t, en=L_["e7"])
    p = geri(dilim(t, 4.3, 4.6))
    if p > 0:
        ctx.save()
        ctx.translate(W / 2, 1840)
        ctx.scale(p, p)
        ctx.rotate(-0.08)
        kutu(ctx, -340, -56, 680, 100, C["yesil"], r=20)
        yazi(ctx, L_["tamam"], 0, 16, 48, C["beyaz"], kalin=True, hiza="orta")
        ctx.restore()
    R.ust_bant(ctx, L_, 7, t)


R_s_imalat = R.s_imalat
R.FONK.update(olcu=s_olcu, tasarim=s_tasarim, imalat=s_imalat, kurulum=s_kurulum)
a2.kiris_yuk = lambda uzun=760: asansor_yuku()


def main():
    if sys.argv[1] == "--kare":
        R.kare(float(sys.argv[2]), L).write_to_png(sys.argv[3])
        return
    sys.argv = [sys.argv[0], "asansor", sys.argv[1]]
    R.main()


if __name__ == "__main__":
    main()
