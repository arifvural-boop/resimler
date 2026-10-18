"""
Beta Vinç - Instagram Reels: vinç kumanda sistemleri
(2B motion graphics, 1080x1920, 30 sn, Türkçe + İngilizce tek video).

reels.py altyapısını (başlık, ilerleme bandı, geçiş, müzik, kapanış) kullanır; sahneler kumanda zinciridir:
butonyer, telsiz kumanda, pano, frekans invertörü, PLC, güvenlik, devreye alma.

Kullanım:
    python reels_kumanda.py <cikti.mp4>
    python reels_kumanda.py --kare <sn> <cikti.png>
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
    kanca1="AKILLI", kanca2="KUMANDA",
    kanca3="Bir vinç nasıl kumanda edilir?", kanca3_en="How is a crane controlled?",
    son1="Sıradaki proje sizin.", son2="Your project is next.", cta="Takip et · Follow   betavinc.com",
    slogan="vinç sistemleri", slogan_en="crane systems", adim="ADIM · STEP",
    onay="ONAYLANDI · APPROVED",
)
R.T["kumanda"] = L

ADIM = [  # (TR başlık, EN başlık, alt yazı)
    ("Bas.", "Press.", "Butonyer · Pendant control"),
    ("Uzaktan.", "Go wireless.", "Telsiz kumanda · Radio remote"),
    ("Kablola.", "Wire it.", "Kumanda panosu · Control panel"),
    ("Yumuşat.", "Smooth it.", "Frekans invertörü · VFD soft start"),
    ("Programla.", "Program it.", "PLC · Akıllı yazılım · Smart logic"),
    ("Koru.", "Protect it.", "Aşırı yük · Limit · Acil stop · Safety"),
    ("Devreye al.", "Commission.", "Test ve teslim · Test & handover"),
]

R.SAHNE[:] = [("kanca", 0.0, 2.5)] + [(f"adim{i}", 2.5 + i * 3.5, 6.0 + i * 3.5) for i in range(7)] + \
    [("kapanis", 27.0, 30.0)]

CX, CY = W / 2, 1220
LED = a2.renk("#5BE38A")


# ---------------------------------------------------------------- ortak
def zemin(ctx, ust=a2.renk("#33383F"), alt=C["koyu"]):
    a2.gradyan_kutu(ctx, 0, 0, W, H, ust, alt)
    for k in range(0, W, 60):   # ince ızgara: elektrik/teknik his
        cizgi(ctx, [(k, 600), (k, H)], C["beyaz"], lw=1, a=0.03)
    for k in range(600, H, 60):
        cizgi(ctx, [(0, k), (W, k)], C["beyaz"], lw=1, a=0.03)


def baslik(ctx, i, t, koyu=False):
    tr, en, alt = ADIM[i]
    R.kelime_pop(ctx, tr, W / 2, 400, 116, 0.02, t, renk=C["koyu"] if koyu else C["beyaz"])
    R.kelime_pop(ctx, en, W / 2, 476, 60, 0.15, t, renk=C["turuncu_k"] if koyu else C["turuncu"])
    yazi(ctx, alt, W / 2, 540, 30, C["antrasit"] if koyu else C["gri_a"], kalin=True, hiza="orta", a=dilim(t, 0.3, 0.6))
    R.ust_bant(ctx, L, i + 1, t)


def sayac(ctx, metin, y=760, renk=C["turuncu"], alt=None):
    kutu(ctx, W / 2 - 280, y - 92, 560, 130, C["koyu"], r=26, a=0.92)
    yazi(ctx, metin, W / 2, y, 80, renk, kalin=True, hiza="orta")
    if alt:
        yazi(ctx, alt, W / 2, y + 66, 28, C["gri_a"], hiza="orta")


def kismi(pts, p):
    """Çoklu çizginin baştan p (0..1) oranı kadarlık kısmı (kablo çekme animasyonu)."""
    if p <= 0:
        return []
    boy = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    hedef, out = sum(boy) * min(1, p), [pts[0]]
    for (a, b), d in zip(zip(pts, pts[1:]), boy):
        if hedef >= d:
            out.append(b)
            hedef -= d
        else:
            k = hedef / d if d else 0
            out.append((lerp(a[0], b[0], k), lerp(a[1], b[1], k)))
            break
    return out


def isik(ctx, x, y, r, c, yan):
    """Yanan buton / LED: halo + parlak çekirdek."""
    if yan > 0:
        daire(ctx, x, y, r * 1.8, c, a=0.25 * yan)
    daire(ctx, x, y, r, a2.lerp_renk(a2.renk("#4A5058"), c, yan))


def acil_stop(ctx, x, y, s, basik=0.0):
    daire(ctx, x, y, 64 * s, a2.renk("#F2C230"))
    daire(ctx, x, y + 6 * s * basik, 44 * s, a2.renk("#B8261C"))
    daire(ctx, x, y - 6 * s * (1 - basik) + 6 * s * basik, 40 * s, C["kirmizi"])


def butonyer(ctx, x, y, s=1.0, basili=None, basik=0.0):
    """Sarkıt butonyer: üst kablo, sarı gövde, yön butonları, acil stop."""
    w, h = 300 * s, 620 * s
    cizgi(ctx, [(x, 600), (x, y - h / 2)], C["koyu"], lw=14 * s)
    kutu(ctx, x - 40 * s, y - h / 2 - 50 * s, 80 * s, 60 * s, C["antrasit"], r=10 * s)
    a2.gradyan_kutu(ctx, x - w / 2, y - h / 2, w, h, a2.renk("#F5C43A"), a2.renk("#D9A21C"), r=60 * s)
    kutu(ctx, x - w / 2 + 26 * s, y - h / 2 + 150 * s, w - 52 * s, h - 190 * s, a2.renk("#2E3338"), r=34 * s)
    acil_stop(ctx, x, y - h / 2 + 78 * s, s * 0.85, basik)
    basili = basili or {}
    oklar = [(0, -1, 1), (0, 1, 1), (-1, 0, 1), (1, 0, 1), (-1, 0, 2), (1, 0, 2)]  # (yön x, yön y, ok sayısı)
    for k, (ox, oy, adet) in enumerate(oklar):
        bx = x + (-62 if k % 2 == 0 else 62) * s
        by = y - h / 2 + 220 * s + (k // 2) * 120 * s
        yan = basili.get(k, 0.0)
        isik(ctx, bx, by, 44 * s, C["turuncu"], yan)
        c = C["koyu"] if yan > 0.5 else C["gri_a"]
        for n in range(adet):
            m = (n - (adet - 1) / 2) * 18 * s
            px, py = bx + ox * m, by + oy * m
            u, v = 18 * s, 16 * s   # uç uzunluğu, taban yarı genişliği
            a2.cokgen(ctx, [(px + ox * u + (0 if ox else 0), py + oy * u),
                            (px - ox * u * 0.6 - oy * v, py - oy * u * 0.6 + ox * v),
                            (px - ox * u * 0.6 + oy * v, py - oy * u * 0.6 - ox * v)], c)
    R.resim(ctx, R.LOGO_K, x, y + h / 2 - 22 * s, 110 * s, orta=True)


# ---------------------------------------------------------------- adımlar
def s_butonyer(ctx, t):
    zemin(ctx)
    sira = [(0, "KALDIR · HOIST"), (1, "İNDİR · LOWER"), (3, "ARABA · TROLLEY"), (5, "KÖPRÜ · BRIDGE")]
    basili, etiket = {}, "IP65"
    for n, (k, ad) in enumerate(sira):
        a0 = 0.4 + n * 0.65
        p = dilim(t, a0, a0 + 0.12) * (1 - dilim(t, a0 + 0.5, a0 + 0.62))
        if p > 0:
            basili[k] = p
        if a0 <= t:
            etiket = ad
    sal = math.sin(t * 2.2) * 0.025
    ctx.save()
    ctx.translate(W / 2, 600)
    ctx.rotate(sal)
    ctx.translate(-W / 2, -600)
    butonyer(ctx, W / 2, 1290, s=1.0, basili=basili)
    ctx.restore()
    if etiket == "IP65":
        sayac(ctx, etiket, y=780, alt="toz ve suya dayanıklı · dust & water proof")
    else:
        kutu(ctx, W / 2 - 330, 688, 660, 130, C["koyu"], r=26, a=0.92)
        yazi(ctx, etiket, W / 2, 776, 52, C["turuncu"], kalin=True, hiza="orta")
    baslik(ctx, 0, t)


def telsiz(ctx, x, y, s, joy=(0.0, 0.0), yan=1.0):
    w, h = 460 * s, 300 * s
    kutu(ctx, x + 140 * s, y - h / 2 - 150 * s, 22 * s, 160 * s, C["koyu"], r=10 * s)   # anten
    a2.gradyan_kutu(ctx, x - w / 2, y - h / 2, w, h, a2.renk("#F5C43A"), a2.renk("#D9A21C"), r=50 * s)
    kutu(ctx, x - w / 2 + 20 * s, y - h / 2 + 20 * s, w - 40 * s, h - 40 * s, a2.renk("#2E3338"), r=36 * s)
    for k, jx in enumerate((x - 120 * s, x + 120 * s)):
        daire(ctx, jx, y + 20 * s, 66 * s, C["koyu"])
        dx = joy[k] * 34 * s
        cizgi(ctx, [(jx, y + 20 * s), (jx + dx, y - 40 * s)], C["gri"], lw=16 * s)
        daire(ctx, jx + dx, y - 44 * s, 26 * s, C["turuncu"])
    acil_stop(ctx, x, y - 70 * s, 0.55 * s)
    isik(ctx, x - 40 * s, y + 90 * s, 9 * s, LED, yan)
    isik(ctx, x + 40 * s, y + 90 * s, 9 * s, C["turuncu"], 0.4 + 0.6 * (math.sin(yan * 30) > 0))


def s_telsiz(ctx, t):
    zemin(ctx)
    # alıcı (vinç üzerinde): sağ üst
    rx, ry = W - 230, 1020
    kutu(ctx, rx - 120, ry - 70, 240, 140, C["antrasit"], r=14)
    kutu(ctx, rx + 70, ry - 160, 16, 90, C["koyu"], r=6)
    alindi = dilim(t, 1.0, 1.2)
    isik(ctx, rx - 60, ry, 14, LED, alindi * (0.6 + 0.4 * math.sin(t * 20)))
    yazi(ctx, "RX", rx + 20, ry + 14, 36, C["gri_a"], kalin=True, hiza="orta")
    # verici
    tx, ty = 380, 1380
    jx = math.sin(dilim(t, 1.2, 3.4) * math.pi * 3) * eo(dilim(t, 1.2, 1.5))
    telsiz(ctx, tx, ty, 1.15, joy=(jx, -jx * 0.6), yan=dilim(t, 0.3, 0.5))
    # sinyal dalgaları antenden alıcıya
    ax, ay = tx + 170, ty - 340
    for k in range(6):
        f = (t * 1.4 - k * 0.18) % 1.0
        if t < 0.5 + k * 0.1:
            continue
        r = 40 + f * 620
        ctx.new_sub_path()
        ctx.arc(ax, ay, r, -math.pi * 0.42, -math.pi * 0.08)
        a2.boya(ctx, C["turuncu"], a=(1 - f) * 0.8)
        ctx.set_line_width(8)
        ctx.stroke()
    menzil = int(100 * eio(dilim(t, 0.4, 2.6)))
    sayac(ctx, f"{menzil} m", y=780, alt="menzil · range  ·  433 MHz")
    baslik(ctx, 1, t)


def s_pano(ctx, t):
    zemin(ctx)
    x0, y0, w, h = 150, 900, 780, 840
    kutu(ctx, x0 - 20, y0 - 20, w + 40, h + 40, a2.renk("#9AA0A8"), r=18)
    kutu(ctx, x0, y0, w, h, a2.renk("#E9E6E0"), r=8)
    kanal = a2.renk("#B9BEC4")
    for yy in (y0 + 30, y0 + 300, y0 + 570):
        kutu(ctx, x0 + 30, yy, w - 60, 40, kanal, r=4)   # kablo kanalları
    for yy in (y0 + 110, y0 + 380, y0 + 650):
        kutu(ctx, x0 + 30, yy + 70, w - 60, 14, C["gri"])  # DIN rayı
    # cihazlar sırayla takılır
    cihaz = []
    for r_, yy in enumerate((y0 + 110, y0 + 380, y0 + 650)):
        for k in range(4):
            cihaz.append((x0 + 70 + k * 170, yy, r_))
    n = 0
    for i, (cx, cy, r_) in enumerate(cihaz):
        a0 = 0.15 + i * 0.13
        p = geri(dilim(t, a0, a0 + 0.2))
        if p <= 0:
            continue
        n += 1
        dy = (1 - p) * -60
        renk = C["antrasit"] if r_ != 1 else a2.renk("#4E555E")
        kutu(ctx, cx, cy + dy, 120, 150, renk, r=8)
        kutu(ctx, cx + 20, cy + 20 + dy, 80, 34, C["gri_a"], r=4)
        isik(ctx, cx + 60, cy + 110 + dy, 9, LED if r_ != 2 else C["turuncu"], dilim(t, 2.4, 2.6))
    # kablolar
    pk = dilim(t, 1.0, 2.6)
    renkler = [C["kirmizi"], C["mavi_a"], C["koyu"], C["turuncu"]]
    for k in range(4):
        x = x0 + 130 + k * 170
        yol = [(x, y0 + 260), (x, y0 + 340), (x + 40, y0 + 340), (x + 40, y0 + 530), (x, y0 + 530), (x, y0 + 650)]
        pts = kismi(yol, dilim(pk, k * 0.15, k * 0.15 + 0.7))
        if len(pts) > 1:
            cizgi(ctx, pts, renkler[k], lw=7)
    sayac(ctx, f"{n} / 12", y=780, alt="modül · modules  ·  24 V DC")
    baslik(ctx, 2, t)


def s_inverter(ctx, t):
    zemin(ctx)
    # invertör gövdesi (solda)
    ix, iy = 270, 1300
    a2.gradyan_kutu(ctx, ix - 170, iy - 330, 340, 660, a2.renk("#4E555E"), a2.renk("#2E3338"), r=22)
    for k in range(7):
        kutu(ctx, ix - 120, iy + 120 + k * 26, 240, 10, C["koyu"], r=4)
    p = dilim(t, 0.4, 2.0)
    s_egri = p * p * (3 - 2 * p)   # S rampası
    hz = 50 * s_egri
    kutu(ctx, ix - 130, iy - 290, 260, 130, a2.renk("#0F2A1B"), r=10)
    yazi(ctx, f"{hz:4.1f}", ix - 20, iy - 195, 72, LED, kalin=True, hiza="orta")
    yazi(ctx, "Hz", ix + 92, iy - 195, 26, LED, hiza="orta")
    for k in range(4):
        daire(ctx, ix - 90 + k * 60, iy - 100, 18, C["gri"])
    R.resim(ctx, R.LOGO_K, ix, iy + 40, 140, orta=True)
    # hız grafiği (sağda)
    gx, gy, gw, gh = 500, 1500, 500, 520
    kutu(ctx, gx - 30, gy - gh - 40, gw + 60, gh + 110, C["koyu"], r=18, a=0.9)
    cizgi(ctx, [(gx, gy - gh), (gx, gy), (gx + gw, gy)], C["gri"], lw=3)
    yazi(ctx, "v", gx - 14, gy - gh + 10, 28, C["gri_a"], kalin=True, hiza="orta")
    yazi(ctx, "t", gx + gw + 4, gy + 40, 28, C["gri_a"], kalin=True, hiza="orta")
    # direkt yol verme (kırmızı, sert) vs. invertör (turuncu, yumuşak)
    cizgi(ctx, [(gx, gy), (gx + 10, gy - gh * 0.85), (gx + gw, gy - gh * 0.85)], C["kirmizi"], lw=4, a=0.55,
          kesik=[14, 10])
    egri = []
    for k in range(61):
        u = k / 60
        v = min(1, u / 0.6)
        v = v * v * (3 - 2 * v)
        egri.append((gx + u * gw, gy - gh * 0.85 * v))
    pts = kismi(egri, dilim(t, 0.4, 2.6))
    if len(pts) > 1:
        cizgi(ctx, pts, C["turuncu"], lw=9)
        daire(ctx, pts[-1][0], pts[-1][1], 14, C["turuncu_a"])
    yazi(ctx, "DOL", gx + 60, gy - gh * 0.85 - 18, 24, C["kirmizi"], kalin=True, hiza="orta")
    yazi(ctx, "VFD", gx + gw - 60, gy - gh * 0.85 + 46, 24, C["turuncu"], kalin=True, hiza="orta")
    sayac(ctx, f"{hz:4.1f} Hz", y=780, alt="yumuşak kalkış · soft start")
    baslik(ctx, 3, t)


def s_plc(ctx, t):
    zemin(ctx)
    # PLC modülü
    px, py = 140, 900
    kutu(ctx, px, py, 800, 240, a2.renk("#D9DCE0"), r=14)
    kutu(ctx, px, py, 220, 240, a2.renk("#4E555E"), r=14)
    yazi(ctx, "PLC", px + 110, py + 140, 56, C["beyaz"], kalin=True, hiza="orta")
    for k in range(16):
        x = px + 260 + (k % 8) * 80
        y = py + 70 + (k // 8) * 100
        yan = 1.0 if math.sin(t * 9 + k * 1.7) > 0.2 and t > 0.4 else 0.0
        isik(ctx, x, y, 12, LED if k < 8 else C["turuncu"], yan)
        yazi(ctx, f"{'I' if k < 8 else 'Q'}{k % 8}", x, y + 46, 20, C["antrasit"], hiza="orta")
    # merdiven diyagramı (ekran)
    ex, ey, ew = 110, 1200, 860
    kutu(ctx, ex, ey, ew, 600, a2.renk("#11161C"), r=18)
    cizgi(ctx, [(ex + 50, ey + 40), (ex + 50, ey + 560)], C["gri"], lw=4)
    cizgi(ctx, [(ex + ew - 50, ey + 40), (ex + ew - 50, ey + 560)], C["gri"], lw=4)
    satir = [("ileri", "yük<%100", "MOTOR"), ("limit", "kapı", "ARABA"), ("yük≥%110", "", "STOP")]
    for k, (a, b, q) in enumerate(satir):
        p = dilim(t, 0.4 + k * 0.6, 0.9 + k * 0.6)
        if p <= 0:
            continue
        y = ey + 120 + k * 170
        x1 = lerp(ex + 50, ex + ew - 50, eo(p))
        akim = t > 2.4
        c = LED if akim and k < 2 else (C["kirmizi"] if k == 2 and akim else C["gri_a"])
        cizgi(ctx, [(ex + 50, y), (x1, y)], c, lw=4)
        for n, metin in enumerate((a, b)):
            if not metin:
                continue
            kx = ex + 170 + n * 220
            if x1 > kx:
                kutu(ctx, kx - 16, y - 34, 32, 68, a2.renk("#11161C"))
                cizgi(ctx, [(kx - 16, y - 34), (kx - 16, y + 34)], c, lw=5)
                cizgi(ctx, [(kx + 16, y - 34), (kx + 16, y + 34)], c, lw=5)
                yazi(ctx, metin, kx, y - 48, 24, C["gri_a"], hiza="orta")
        bx = ex + ew - 170
        if x1 > bx:
            ctx.new_sub_path()
            ctx.arc(bx, y, 34, 0, 2 * math.pi)
            a2.boya(ctx, a2.renk("#11161C"))
            ctx.fill_preserve()
            a2.boya(ctx, c)
            ctx.set_line_width(5)
            ctx.stroke()
            yazi(ctx, q, bx, y - 48, 24, C["turuncu"], kalin=True, hiza="orta")
    satirlar = int(1280 * eio(dilim(t, 0.3, 2.8)))
    sayac(ctx, f"{satirlar} satır", y=780, alt="kod satırı · lines of code")
    baslik(ctx, 4, t)


def s_guvenlik(ctx, t):
    zemin(ctx)
    yuk = lerp(0, 112, eio(dilim(t, 0.3, 1.9)))
    kirmizi = yuk >= 110
    # yük göstergesi (yay)
    gx, gy, r = W / 2, 1330, 330
    ctx.new_sub_path()
    ctx.arc(gx, gy, r, math.pi, 2 * math.pi)
    a2.boya(ctx, C["antrasit"])
    ctx.set_line_width(56)
    ctx.stroke()
    for (a0, a1, c) in ((0, 100, C["yesil"]), (100, 110, C["turuncu"]), (110, 125, C["kirmizi"])):
        ctx.new_sub_path()
        ctx.arc(gx, gy, r, math.pi + math.pi * a0 / 125, math.pi + math.pi * a1 / 125)
        a2.boya(ctx, c, a=0.85)
        ctx.set_line_width(40)
        ctx.stroke()
    aci = math.pi + math.pi * min(yuk, 125) / 125
    cizgi(ctx, [(gx, gy), (gx + math.cos(aci) * (r - 50), gy + math.sin(aci) * (r - 50))], C["beyaz"], lw=12)
    daire(ctx, gx, gy, 30, C["beyaz"])
    yazi(ctx, f"%{yuk:.0f}", gx, gy + 110, 90, C["kirmizi"] if kirmizi else C["beyaz"], kalin=True, hiza="orta")
    yazi(ctx, "yük · load", gx, gy + 160, 28, C["gri_a"], hiza="orta")
    # acil stop + limit şalteri
    bas = dilim(t, 1.9, 2.05)
    sx, sy = R.sarsinti(t, [1.95], guc=16)
    ctx.save()
    ctx.translate(sx, sy)
    acil_stop(ctx, W / 2, 1650, 1.25, basik=bas)
    ctx.restore()
    for k, (ad, x) in enumerate((("LİMİT ↑", 170), ("LİMİT ↓", W - 170))):
        yan = dilim(t, 2.2 + k * 0.2, 2.35 + k * 0.2)
        kutu(ctx, x - 90, 1580, 180, 150, C["antrasit"], r=14)
        isik(ctx, x, 1640, 20, C["kirmizi"], yan)
        yazi(ctx, ad, x, 1705, 26, C["gri_a"], kalin=True, hiza="orta")
    if kirmizi:
        fl = 0.5 + 0.5 * math.sin(t * 24)
        kutu(ctx, 0, 0, W, H, C["kirmizi"], a=0.08 * fl)
        sayac(ctx, "STOP", y=780, renk=C["kirmizi"], alt="%110 aşırı yük · overload cut-off")
    else:
        sayac(ctx, f"%{yuk:.0f}", y=780, renk=C["yesil"], alt="yük sensörü · load cell")
    baslik(ctx, 5, t)


def s_devreye(ctx, t):
    zemin(ctx, ust=a2.renk("#3A4048"))
    # hol: kolonlar + ray
    yr = 960
    for x in (90, W - 90):
        kutu(ctx, x - 26, yr, 52, 760, a2.renk("#5A626B"))
    kutu(ctx, 0, 1720, W, 200, a2.renk("#4A5058"))
    kutu(ctx, 0, 1720, W, 8, C["turuncu"], a=0.6)
    # vinç: kumandaya göre araba sağa-sola, kanca iner-çıkar
    p1 = eio(dilim(t, 0.3, 1.3))
    p2 = eio(dilim(t, 1.3, 2.2))
    cx = lerp(300, 700, p1) - 200 * p2
    ky = lerp(1380, 1140, eio(dilim(t, 0.5, 1.1))) + 120 * p2
    a2.kopru_vinc(ctx, 130, W - 130, yr, cx=cx, kanca_y=ky, yuk=(150, 110, "5 t"))
    # telsiz kumanda (sağ alt, küçük)
    joy = (1.0 if 0.3 < t < 1.3 else (-1.0 if 1.3 < t < 2.2 else 0.0))
    telsiz(ctx, W - 250, 1800, 0.5, joy=(joy, 0.0), yan=1.0)
    sayac(ctx, "✓  %100", y=780, renk=C["yesil"] if t > 2.3 else C["turuncu"], alt="fonksiyon testi · function test")
    d = dilim(t, 2.5, 2.8)
    if d > 0:
        s = lerp(2.4, 1.0, eo(d))
        ctx.save()
        ctx.translate(W / 2, 1610)
        ctx.rotate(-0.1)
        ctx.scale(s, s)
        kutu(ctx, -300, -50, 600, 90, a2.renk("#FFFFFF", 0.92), r=12, cizgi=C["yesil"], lw=7)
        yazi(ctx, L["onay"], 0, 16, 44, C["yesil"], kalin=True, hiza="orta", a=min(1, d * 2))
        ctx.restore()
    baslik(ctx, 6, t)


ADIM_FN = [s_butonyer, s_telsiz, s_pano, s_inverter, s_plc, s_guvenlik, s_devreye]
for _i, _f in enumerate(ADIM_FN):
    R.FONK[f"adim{_i}"] = (lambda f: (lambda ctx, L_, t: f(ctx, t)))(_f)


def main():
    if sys.argv[1] == "--kare":
        R.kare(float(sys.argv[2]), L).write_to_png(sys.argv[3])
        return
    sys.argv = [sys.argv[0], "kumanda", sys.argv[1]]
    R.main()


if __name__ == "__main__":
    main()
