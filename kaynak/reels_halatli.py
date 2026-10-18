"""
Beta Vinç - Instagram Reels: elektrikli halatlı vincin üretimi
(2B motion graphics, 1080x1920, 30 sn, Türkçe + İngilizce tek video).

reels.py altyapısını (başlık, ilerleme bandı, geçiş, müzik, kapanış) kullanır; sahneler üretim adımlarıdır:
tambur, redüktör, motor, halat, montaj, test, sevkiyat.

Kullanım:
    python reels_halatli.py <cikti.mp4>
    python reels_halatli.py --kare <sn> <cikti.png>
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
    kanca1="SIFIRDAN", kanca2="HALATLI VİNÇ",
    kanca3="Bir halatlı vinç nasıl üretilir?", kanca3_en="How is a wire rope hoist made?",
    son1="Sıradaki proje sizin.", son2="Your project is next.", cta="Takip et · Follow   betavinc.com",
    slogan="vinç sistemleri", slogan_en="crane systems", adim="ADIM · STEP",
    onay="ONAYLANDI · APPROVED",
)
R.T["halatli"] = L

ADIM = [  # (TR başlık, EN başlık, alt yazı)
    ("Tornala.", "Turn it.", "Tambur · CNC kanal açma · Drum grooving"),
    ("Dişli.", "Gear it.", "Redüktör · Helisel dişliler · Gearbox"),
    ("Motor.", "Power it.", "Sargı, rotor, fren · Winding & brake"),
    ("Halat sar.", "Wind it.", "Çelik halat · Steel wire rope"),
    ("Birleştir.", "Assemble.", "Gövde, araba, kanca · Frame, trolley, hook"),
    ("Test et.", "Test it.", "%125 yük testi · 125% load test"),
    ("Sevk et.", "Ship it.", "Boyandı, etiketlendi, yola çıktı"),
]

R.SAHNE[:] = [("kanca", 0.0, 2.5)] + [(f"adim{i}", 2.5 + i * 3.5, 6.0 + i * 3.5) for i in range(7)] + \
    [("kapanis", 27.0, 30.0)]

CX, CY = W / 2, 1180     # vinç merkezi
DL, DR_ = 300, 300       # tambur yarı uzunluğu sol/sağ
DRY = 90                 # tambur yarıçapı


# ---------------------------------------------------------------- ortak
def zemin(ctx, ust=a2.renk("#33383F"), alt=C["koyu"], tezgah=True):
    a2.gradyan_kutu(ctx, 0, 0, W, H, ust, alt)
    if tezgah:
        kutu(ctx, 0, 1560, W, 360, a2.renk("#3E444C"))
        kutu(ctx, 0, 1560, W, 8, C["turuncu"], a=0.6)


def baslik(ctx, i, t, koyu=False):
    tr, en, alt = ADIM[i]
    R.kelime_pop(ctx, tr, W / 2, 400, 116, 0.02, t, renk=C["koyu"] if koyu else C["beyaz"])
    R.kelime_pop(ctx, en, W / 2, 476, 60, 0.15, t, renk=C["turuncu_k"] if koyu else C["turuncu"])
    yazi(ctx, alt, W / 2, 540, 30, C["antrasit"] if koyu else C["gri_a"], kalin=True, hiza="orta", a=dilim(t, 0.3, 0.6))
    R.ust_bant(ctx, L, i + 1, t)


def tambur(ctx, x0, x1, y, r, aci=0.0, kanal=1.0, halat=0.0, renk=None):
    """Yandan tambur: silindir gövde, helisel kanallar (kanal: 0..1 açılmış oran), sarılmış halat (halat: 0..1)."""
    c = renk or a2.renk("#9AA0A8")
    a2.gradyan_kutu(ctx, x0, y - r, x1 - x0, 2 * r, a2.lerp_renk(c, C["beyaz"], 0.35), a2.lerp_renk(c, C["koyu"], 0.35))
    adim = 22
    n = int((x1 - x0) / adim)
    faz = (aci / (2 * math.pi)) * adim
    for k in range(n + 1):
        xx = x0 + k * adim + faz % adim
        if xx > x1 or xx < x0:
            continue
        if (xx - x0) / (x1 - x0) <= kanal:
            cizgi(ctx, [(xx, y - r + 4), (xx - 10, y + r - 4)], C["koyu"], lw=3, a=0.45)
        if (xx - x0) / (x1 - x0) <= halat:
            cizgi(ctx, [(xx, y - r - 3), (xx - 10, y + r + 3)], a2.renk("#C9CDD2"), lw=11)
            cizgi(ctx, [(xx - 2, y - r - 3), (xx - 12, y + r + 3)], a2.renk("#6E737B"), lw=2)
    for xf in (x0 - 14, x1):
        kutu(ctx, xf, y - r - 18, 14, 2 * r + 36, C["antrasit"], r=3)


def disli(ctx, x, y, r, dis, aci, renk):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(aci)
    ctx.new_path()
    for k in range(dis * 2):
        a0 = k * math.pi / dis
        rr = r if k % 2 == 0 else r * 0.86
        ctx.line_to(rr * math.cos(a0), rr * math.sin(a0))
        ctx.line_to(rr * math.cos(a0 + math.pi / dis), rr * math.sin(a0 + math.pi / dis))
    ctx.close_path()
    a2.boya(ctx, renk)
    ctx.fill()
    daire(ctx, 0, 0, r * 0.32, C["koyu"])
    daire(ctx, 0, 0, r * 0.12, C["gri_a"])
    ctx.restore()


def motor(ctx, x, y, s=1.0, a=1.0, sargi=1.0, ic=False):
    w, h = 220 * s, 190 * s
    a2.gradyan_kutu(ctx, x - w / 2, y - h / 2, w, h, a2.renk("#4E555E"), a2.renk("#2E3338"), r=26 * s)
    for k in range(9):
        kutu(ctx, x - w / 2 + 14 * s + k * 22 * s, y - h / 2 - 8 * s, 8 * s, h + 16 * s, C["antrasit"], r=3, a=a)
    kutu(ctx, x - w / 2 - 30 * s, y - h / 2 + 20 * s, 34 * s, h - 40 * s, C["turuncu"], r=8 * s, a=a)  # fren
    kutu(ctx, x - 40 * s, y - h / 2 - 50 * s, 80 * s, 46 * s, C["antrasit"], r=6 * s, a=a)           # klemens
    if ic:
        daire(ctx, x, y, 70 * s, C["koyu"])
        for k in range(int(24 * sargi)):
            aa = k * 2 * math.pi / 24
            daire(ctx, x + math.cos(aa) * 54 * s, y + math.sin(aa) * 54 * s, 9 * s, a2.renk("#C97F3A"))


def redukt(ctx, x, y, s=1.0, a=1.0):
    w, h = 190 * s, 250 * s
    kutu(ctx, x - w / 2, y - h / 2, w, h, C["turuncu"], r=24 * s, a=a)
    kutu(ctx, x - w / 2, y - h / 2, w, 30 * s, C["turuncu_k"], r=14 * s, a=a)
    for dy in (-70, 0, 70):
        daire(ctx, x + 50 * s, y + dy * s, 8 * s, C["antrasit"], a=a)
    kutu(ctx, x - 70 * s, y - 24 * s, 110 * s, 48 * s, C["beyaz"], r=6, a=a)
    R.resim(ctx, R.LOGO_K, x - 15 * s, y, 90 * s, a=a, orta=True)


def halatli_vinc(ctx, *a, olcek=0.78, **k):
    """Monte edilmiş vinci dikey kadraja sığacak ölçekte çiz."""
    ctx.save()
    ctx.translate(CX, CY)
    ctx.scale(olcek, olcek)
    ctx.translate(-CX, -CY)
    _halatli_vinc(ctx, *a, **k)
    ctx.restore()


def _halatli_vinc(ctx, parca=("govde", "tambur", "motor", "redukt", "araba", "kanca"), ofs=None, kanca_y=None,
                  halat=1.0, aci=0.0, yuk=None):
    """Monte edilmiş halatlı vinç; ofs: parça adı -> (dx, dy) yerleşme kayması (montaj animasyonu için)."""
    ofs = ofs or {}

    def o(ad):
        return ofs.get(ad, (0, 0))

    x0, x1 = CX - DL, CX + DR_
    if "govde" in parca:
        dx, dy = o("govde")
        for xs in (x0 - 40, x1 + 26):
            kutu(ctx, xs + dx, CY - 170 + dy, 18, 300, C["antrasit"], r=4)
        kutu(ctx, x0 - 40 + dx, CY - 170 + dy, x1 - x0 + 84, 22, C["antrasit"], r=4)
    if "araba" in parca:
        dx, dy = o("araba")
        kutu(ctx, x0 - 60 + dx, CY - 230 + dy, x1 - x0 + 124, 60, C["antrasit"], r=8)
        for xs in (x0 - 10, x0 + 90, x1 - 90, x1 + 10):
            daire(ctx, xs + dx, CY - 236 + dy, 18, C["koyu"])
            daire(ctx, xs + dx, CY - 236 + dy, 7, C["gri_a"])
        kutu(ctx, CX - 260 + dx, CY - 320 + dy, 520, 28, C["gri"], r=4, a=0.8)  # kiriş alt flanşı (ray)
    if "tambur" in parca:
        dx, dy = o("tambur")
        ctx.save()
        ctx.translate(dx, dy)
        tambur(ctx, x0, x1, CY, DRY, aci=aci, kanal=1.0, halat=halat, renk=a2.renk("#8A9099"))
        ctx.restore()
    if "motor" in parca:
        dx, dy = o("motor")
        motor(ctx, x0 - 150 + dx, CY + dy, s=0.9)
    if "redukt" in parca:
        dx, dy = o("redukt")
        redukt(ctx, x1 + 120 + dx, CY + dy, s=0.95)
    if "kanca" in parca:
        dx, dy = o("kanca")
        ky = (kanca_y if kanca_y is not None else CY + 290) + dy
        for xs in (CX - 22, CX + 22):
            cizgi(ctx, [(xs + dx, CY + DRY), (xs + dx, ky)], a2.renk("#C9CDD2"), lw=6)
        kutu(ctx, CX - 70 + dx, ky, 140, 70, C["turuncu"], r=14)
        daire(ctx, CX + dx, ky + 35, 26, C["antrasit"])
        daire(ctx, CX + dx, ky + 35, 10, C["gri_a"])
        ctx.new_sub_path()
        ctx.arc(CX + dx, ky + 120, 30, -math.pi * 0.05, math.pi * 1.25)
        a2.boya(ctx, C["koyu"])
        ctx.set_line_width(14)
        ctx.stroke()
        cizgi(ctx, [(CX + dx, ky + 70), (CX + dx, ky + 92)], C["koyu"], lw=14)
        if yuk:
            yw, yh, metin = yuk
            for d in (-yw / 2 + 16, yw / 2 - 16):
                cizgi(ctx, [(CX + dx, ky + 146), (CX + dx + d, ky + 210)], C["koyu"], lw=4)
            kutu(ctx, CX + dx - yw / 2, ky + 210, yw, yh, C["gri"], r=6)
            yazi(ctx, metin, CX + dx, ky + 210 + yh / 2 + 20, 56, C["beyaz"], kalin=True, hiza="orta")


def talas(ctx, x, y, t, n=18):
    rnd = random.Random(int(t * R.FPS))
    for _ in range(n):
        a = rnd.uniform(-math.pi * 0.9, -math.pi * 0.1)
        v = rnd.uniform(30, 120)
        cizgi(ctx, [(x, y), (x + math.cos(a) * v, y + math.sin(a) * v * 0.6 + 40)], a2.renk("#C9CDD2"), lw=3, a=0.8)


def sayac(ctx, metin, y=760, renk=C["turuncu"]):
    kutu(ctx, W / 2 - 260, y - 92, 520, 130, C["koyu"], r=26, a=0.92)
    yazi(ctx, metin, W / 2, y, 86, renk, kalin=True, hiza="orta")


# ---------------------------------------------------------------- adımlar
def s_tambur(ctx, t):
    zemin(ctx)
    x0, x1 = CX - DL, CX + DR_
    aci = t * 18
    # torna aynası ve punta
    kutu(ctx, x0 - 120, CY - 150, 90, 300, C["antrasit"], r=10)
    for k in range(3):
        a = aci + k * 2 * math.pi / 3
        kutu(ctx, x0 - 60, CY + math.sin(a) * 70 - 14, 40, 28, C["gri_a"], r=4)
    kutu(ctx, x1 + 30, CY - 40, 140, 80, C["antrasit"], r=10)
    cizgi(ctx, [(x1 + 30, CY), (x1 + 10, CY)], C["gri_a"], lw=12)
    k = eio(dilim(t, 0.2, 3.0))
    tambur(ctx, x0, x1, CY, DRY, aci=aci, kanal=k)
    # kesici takım
    tx = lerp(x0, x1, k)
    a2.cokgen(ctx, [(tx - 10, CY + DRY + 2), (tx + 10, CY + DRY + 2), (tx + 30, CY + DRY + 120), (tx - 30, CY + DRY + 120)],
              C["turuncu"])
    kutu(ctx, tx - 60, CY + DRY + 120, 120, 50, C["antrasit"], r=6)
    if 0 < k < 1:
        talas(ctx, tx, CY + DRY, t)
    sayac(ctx, f"{int(k * 48)} / 48", y=780)
    yazi(ctx, "kanal · grooves", W / 2, 840, 28, C["gri_a"], hiza="orta")
    baslik(ctx, 0, t)


def s_redukt(ctx, t):
    zemin(ctx)
    aci = t * 4
    ac = 1 - eio(dilim(t, 2.2, 3.0))   # kapak açık oranı
    disli(ctx, CX - 120, CY, 160, 28, aci, a2.renk("#B9BEC4"))
    disli(ctx, CX + 110, CY - 120, 80, 14, -aci * 2 + 0.11, a2.renk("#D9DCE0"))
    disli(ctx, CX + 150, CY + 130, 100, 18, -aci * 1.55, a2.renk("#9AA0A8"))
    disli(ctx, CX + 150, CY + 130, 46, 9, -aci * 1.55, a2.renk("#E99A2A"))
    if ac < 1:
        ctx.save()
        ctx.translate(0, ac * 900)
        a2.gradyan_kutu(ctx, CX - 320, CY - 260, 640, 520, C["turuncu_a"], C["turuncu_k"], r=40)
        kutu(ctx, CX - 120, CY - 40, 240, 80, C["beyaz"], r=8)
        R.resim(ctx, R.LOGO_K, CX, CY, 190, orta=True)
        for x, y in ((CX - 280, CY - 220), (CX + 280, CY - 220), (CX - 280, CY + 220), (CX + 280, CY + 220)):
            daire(ctx, x, y, 12, C["antrasit"])
        ctx.restore()
    oran = f"i = {lerp(1, 63, eio(dilim(t, 0.2, 2.0))):.0f}:1"
    sayac(ctx, oran, y=780)
    yazi(ctx, "çevrim oranı · gear ratio", W / 2, 840, 28, C["gri_a"], hiza="orta")
    baslik(ctx, 1, t)


def s_motor(ctx, t):
    zemin(ctx)
    sargi = eio(dilim(t, 0.1, 1.4))
    kapan = eio(dilim(t, 1.5, 2.0))
    if kapan < 1:
        motor(ctx, CX, CY, s=1.8, ic=True, sargi=sargi, a=1)
    if kapan > 0:
        ctx.save()
        ctx.translate(0, (1 - kapan) * 700)
        motor(ctx, CX, CY, s=1.8)
        ctx.restore()
    # dönüş: fan kapağı izleri
    devir = int(1450 * eio(dilim(t, 2.0, 3.2)))
    if t > 2.0:
        for k in range(6):
            a = t * 40 + k * math.pi / 3
            cizgi(ctx, [(CX + 260, CY), (CX + 260 + math.cos(a) * 60, CY + math.sin(a) * 60)], C["gri_a"], lw=6, a=0.7)
        daire(ctx, CX + 260, CY, 14, C["antrasit"])
    sayac(ctx, f"{devir} d/d", y=780)
    yazi(ctx, "rpm", W / 2, 840, 28, C["gri_a"], hiza="orta")
    baslik(ctx, 2, t)


def s_halat(ctx, t):
    zemin(ctx)
    x0, x1 = CX - DL, CX + DR_
    p = eio(dilim(t, 0.2, 3.0))
    aci = p * 60
    tambur(ctx, x0, x1, CY, DRY, aci=aci, kanal=1.0, halat=p)
    # halat makarası (sağ altta) ve gelen halat
    mx, my = CX + 200, 1420
    daire(ctx, mx, my, 120, C["antrasit"])
    daire(ctx, mx, my, 120 - 70 * p, a2.renk("#8A9099"))
    daire(ctx, mx, my, 30, C["koyu"])
    hx = lerp(x0, x1, p)
    cizgi(ctx, [(mx - 100 + 70 * p, my - 40), (hx, CY + DRY)], a2.renk("#C9CDD2"), lw=9)
    sayac(ctx, f"{int(40 * p)} m", y=780)
    yazi(ctx, "Ø16 çelik halat · steel rope", W / 2, 840, 28, C["gri_a"], hiza="orta")
    baslik(ctx, 3, t)


def s_montaj(ctx, t):
    zemin(ctx)
    sira = [("govde", (0, 900)), ("tambur", (0, -900)), ("motor", (-900, 0)), ("redukt", (900, 0)),
            ("araba", (0, -900)), ("kanca", (0, 900))]
    ofs, gorunen = {}, []
    darbe = []
    for i, (ad, (dx, dy)) in enumerate(sira):
        a0 = 0.15 + i * 0.42
        p = geri(dilim(t, a0, a0 + 0.38))
        if p > 0:
            gorunen.append(ad)
            ofs[ad] = (dx * (1 - p), dy * (1 - p))
            darbe.append(a0 + 0.38)
    sx, sy = R.sarsinti(t, darbe, guc=10)
    ctx.save()
    ctx.translate(sx, sy)
    halatli_vinc(ctx, parca=tuple(gorunen), ofs=ofs)
    ctx.restore()
    baslik(ctx, 4, t)


def s_test(ctx, t):
    zemin(ctx, tezgah=False)
    # test kulesi
    kutu(ctx, 60, 760, 40, 1160, C["antrasit"])
    kutu(ctx, W - 100, 760, 40, 1160, C["antrasit"])
    kutu(ctx, 60, 740, W - 120, 40, C["antrasit"])
    kutu(ctx, 0, 1800, W, 120, a2.renk("#3E444C"))
    for k in range(8):
        cizgi(ctx, [(100, 820 + k * 130), (W - 100, 820 + k * 130)], C["gri"], lw=1, a=0.2)
    kalk = eio(dilim(t, 0.6, 2.4))
    ky = lerp(1480, 1240, kalk)
    ctx.save()
    ctx.translate(0, -120)
    halatli_vinc(ctx, kanca_y=ky, yuk=(260, 180, "12,5 t"), halat=1.0 - 0.3 * kalk)
    ctx.restore()
    yuzde = int(125 * eio(dilim(t, 0.3, 2.4)))
    sayac(ctx, f"%{yuzde}", y=780, renk=C["yesil"] if yuzde >= 125 else C["turuncu"])
    yazi(ctx, "10 t × 1,25 = 12,5 t", W / 2, 840, 28, C["gri_a"], hiza="orta")
    d = dilim(t, 2.6, 2.9)
    if d > 0:
        s = lerp(2.4, 1.0, eo(d))
        ctx.save()
        ctx.translate(W / 2, 1700)
        ctx.rotate(-0.1)
        ctx.scale(s, s)
        kutu(ctx, -300, -50, 600, 90, a2.renk("#FFFFFF", 0.92), r=12, cizgi=C["yesil"], lw=7)
        yazi(ctx, L["onay"], 0, 16, 44, C["yesil"], kalin=True, hiza="orta", a=min(1, d * 2))
        ctx.restore()
    baslik(ctx, 5, t)


def s_sevkiyat(ctx, t):
    a2.gradyan_kutu(ctx, 0, 0, W, H, a2.renk("#7FB6DE"), a2.renk("#D9ECF7"))
    kutu(ctx, 0, 1380, W, 540, C["yol"])
    for k in range(8):
        x = (k * 260 - max(0, t - 1.6) * 2400) % (W + 260) - 130
        kutu(ctx, x, 1620, 150, 16, C["beyaz"], r=4)

    def yuk(c, xd, yd):
        # sandık + vinç
        kutu(c, xd + 220, yd - 360, 420, 360, a2.renk("#B58A5A"), r=6)
        for k in range(5):
            cizgi(c, [(xd + 220, yd - 360 + k * 80), (xd + 640, yd - 360 + k * 80)], a2.renk("#8C6A48"), lw=4)
        kutu(c, xd + 330, yd - 250, 200, 90, C["beyaz"], r=8)
        yazi(c, "beta", xd + 430, yd - 190, 54, C["antrasit"], kalin=True, hiza="orta")
        yazi(c, "↑ ↑", xd + 430, yd - 60, 50, C["antrasit"], kalin=True, hiza="orta")
    x = lerp(1500, 1500 + 1800, eio(dilim(t, 1.6, 3.4)))
    R.dunya(ctx, 0.72, W / 2 + 120, 1240, lambda c: a2.tir(c, x, a2.ZEMIN, teker=t * 18, yuk=yuk))
    # paketleme: önce sandık kapanır
    if t < 1.6:
        p = eo(dilim(t, 0.2, 1.0))
        ctx.save()
        ctx.translate(0, -(1 - p) * 500)
        kutu(ctx, W / 2 - 230, 760, 460, 46, a2.renk("#8C6A48"), r=6, a=p)
        ctx.restore()
    baslik(ctx, 6, t, koyu=True)


ADIM_FN = [s_tambur, s_redukt, s_motor, s_halat, s_montaj, s_test, s_sevkiyat]
for _i, _f in enumerate(ADIM_FN):
    R.FONK[f"adim{_i}"] = (lambda f: (lambda ctx, L_, t: f(ctx, t)))(_f)


def main():
    if sys.argv[1] == "--kare":
        R.kare(float(sys.argv[2]), L).write_to_png(sys.argv[3])
        return
    sys.argv = [sys.argv[0], "halatli", sys.argv[1]]
    R.main()


if __name__ == "__main__":
    main()
