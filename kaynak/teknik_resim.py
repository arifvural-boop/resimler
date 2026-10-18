"""
Beta Vinç - portal ve pergel vinç teknik resimleri (A3 pafta, mm).

Ölçüler render_vincler.py'deki 3B görselleştirme modelinden alınmıştır.

Kullanım:
    python teknik_resim.py <cikti_klasoru>
"""
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon, Rectangle  # noqa: E402

plt.rcParams["font.family"] = "DejaVu Sans"

A3 = (420.0, 297.0)
KALIN, ORTA, INCE = 0.9, 0.55, 0.3  # çizgi kalınlıkları (pt)
TURUNCU = "#E99A2A"
ANTRASIT = "#3C424B"
TARIH = "18.10.2026"


# ---------------------------------------------------------------- pafta
class Pafta:
    def __init__(self, baslik, no, olcek_notu, kapasite, notlar):
        self.fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
        self.ax = ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, A3[0])
        ax.set_ylim(0, A3[1])
        ax.set_aspect("equal")
        ax.axis("off")
        # çerçeve (ISO 5457: 20 mm sol cilt payı, 10 mm diğerleri)
        ax.add_patch(Rectangle((20, 10), A3[0] - 30, A3[1] - 20, fill=False, lw=1.2, ec="k"))
        self.baslik_kutusu(baslik, no, olcek_notu, kapasite)
        self.notlar(notlar)

    def baslik_kutusu(self, baslik, no, olcek, kapasite):
        ax = self.ax
        x0, y0, w, h = A3[0] - 10 - 180, 10, 180, 46
        ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.0, ec="k"))
        # logo alanı
        ax.add_patch(Rectangle((x0, y0 + 26), 50, 20, fc=TURUNCU, ec="k", lw=0.8))
        ax.text(x0 + 25, y0 + 36, "beta", ha="center", va="center", fontsize=20, weight="bold", color=ANTRASIT)
        ax.text(x0 + 25, y0 + 28.5, "VİNÇ SİSTEMLERİ", ha="center", va="center", fontsize=5.5, color=ANTRASIT)
        satirlar = [
            ((x0 + 50, y0 + 36, 130, 10), "ÇİZİM ADI", baslik),
            ((x0 + 50, y0 + 26, 130, 10), "KAPASİTE", kapasite),
            ((x0, y0 + 16, 50, 10), "ÖLÇEK", olcek),
            ((x0 + 50, y0 + 16, 45, 10), "ÖLÇÜ BİRİMİ", "mm"),
            ((x0 + 95, y0 + 16, 45, 10), "TARİH", TARIH),
            ((x0 + 140, y0 + 16, 40, 10), "PAFTA NO", no),
            ((x0, y0 + 6, 95, 10), "MALZEME", "S355JR yapı çeliği (taşıyıcılar)"),
            ((x0 + 95, y0 + 6, 85, 10), "YÜZEY", "Boya RAL 1028 tonu / RAL 7016"),
        ]
        for (x, y, ww, hh), et, deger in satirlar:
            ax.add_patch(Rectangle((x, y), ww, hh, fill=False, lw=0.5, ec="k"))
            ax.text(x + 1.2, y + hh - 1.6, et, fontsize=4.2, va="top", color="#444")
            ax.text(x + 1.5, y + 2.0, deger, fontsize=7 if len(deger) < 34 else 6, va="bottom", weight="bold")
        ax.add_patch(Rectangle((x0, y0), w, 6, fill=False, lw=0.5, ec="k"))
        ax.text(x0 + 1.5, y0 + 3, "Görselleştirme modelinden türetilmiştir. İmalat ve statik hesap için onaylı proje esas alınır.",
                fontsize=4.6, va="center", style="italic")

    def notlar(self, notlar):
        ax = self.ax
        x, y = 26, 52
        ax.text(x, y, "NOTLAR", fontsize=6.5, weight="bold", va="top")
        for i, n in enumerate(notlar):
            ax.text(x, y - 4.2 - i * 3.6, f"{i + 1}. {n}", fontsize=5.4, va="top")

    def kaydet(self, pdf, png):
        self.fig.savefig(png, dpi=200)
        pdf.savefig(self.fig)
        plt.close(self.fig)


class Gorunus:
    """Pafta üzerinde bir görünüş: dünya (m) -> kağıt (mm)."""

    def __init__(self, pafta, ox, oy, olcek, ad):
        self.ax = pafta.ax
        self.ox, self.oy = ox, oy
        self.k = 1000.0 / olcek  # 1 m kaç mm
        self.ad = ad

    def p(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    def cizgi(self, pts, lw=KALIN, ls="-", c="k", z=3):
        xs, ys = zip(*[self.p(*q) for q in pts])
        self.ax.plot(xs, ys, lw=lw, ls=ls, color=c, zorder=z, solid_capstyle="butt")

    def eksen(self, pts):
        self.cizgi(pts, lw=INCE, ls=(0, (12, 3, 2, 3)), c="#555", z=2)

    def gizli(self, pts):
        self.cizgi(pts, lw=INCE, ls=(0, (4, 2)), c="#333", z=2)

    def dik(self, x0, y0, x1, y1, fc="none", lw=KALIN, z=3, hatch=None):
        a, b = self.p(x0, y0), self.p(x1, y1)
        self.ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]),
                                    fc=fc, ec="k", lw=lw, zorder=z, hatch=hatch))

    def cokgen(self, pts, fc="none", lw=KALIN, z=3):
        self.ax.add_patch(Polygon([self.p(*q) for q in pts], closed=True, fc=fc, ec="k", lw=lw, zorder=z))

    def daire(self, x, y, r, fc="none", lw=KALIN, z=3):
        cx, cy = self.p(x, y)
        self.ax.add_patch(Circle((cx, cy), r * self.k, fc=fc, ec="k", lw=lw, zorder=z))

    def yay(self, x, y, r, a0, a1, ls="--"):
        cx, cy = self.p(x, y)
        self.ax.add_patch(Arc((cx, cy), 2 * r * self.k, 2 * r * self.k, theta1=a0, theta2=a1,
                              lw=INCE, ls=ls, color="#333", zorder=2))

    def yazi(self, x, y, t, fs=5.5, ha="center", va="center", rot=0, w="normal"):
        px, py = self.p(x, y)
        self.ax.text(px, py, t, fontsize=fs, ha=ha, va=va, rotation=rot, weight=w, zorder=6)

    def baslik(self, x, y, olcek_yazi):
        px, py = self.p(x, y)
        self.ax.text(px, py, self.ad, fontsize=7.5, weight="bold", ha="center", va="top")
        self.ax.text(px, py - 3.6, olcek_yazi, fontsize=5.5, ha="center", va="top")
        self.ax.plot([px - 22, px + 22], [py - 6.2, py - 6.2], lw=0.5, color="k")

    def zemin(self, x0, x1, y=0.0):
        a, b = self.p(x0, y), self.p(x1, y)
        self.ax.plot([a[0], b[0]], [a[1], a[1]], lw=KALIN, color="k", zorder=3)
        for i in range(int((b[0] - a[0]) / 2.5)):
            xx = a[0] + i * 2.5
            self.ax.plot([xx, xx - 2], [a[1], a[1] - 2], lw=INCE, color="k", zorder=2)

    # ölçü çizgisi: (x0,y0)-(x1,y1) iki nokta, d: kağıtta mm kaydırma (ölçü çizgisi normal yönde)
    def olcu(self, a, b, d, metin=None, fs=5.3):
        A, B = self.p(*a), self.p(*b)
        dx, dy = B[0] - A[0], B[1] - A[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        A2 = (A[0] + nx * d, A[1] + ny * d)
        B2 = (B[0] + nx * d, B[1] + ny * d)
        s = 1 if d >= 0 else -1
        for P, Q in ((A, A2), (B, B2)):  # uzatma çizgileri
            self.ax.plot([P[0] + nx * s * 1.0, Q[0] + nx * s * 1.5], [P[1] + ny * s * 1.0, Q[1] + ny * s * 1.5],
                         lw=INCE, color="k", zorder=4)
        self.ax.plot([A2[0], B2[0]], [A2[1], B2[1]], lw=INCE, color="k", zorder=4)
        for P, sg in ((A2, 1), (B2, -1)):  # oklar
            t = 2.4
            w = 0.55
            tip = P
            base = (P[0] + ux * t * sg, P[1] + uy * t * sg)
            self.ax.add_patch(Polygon([tip, (base[0] + nx * w, base[1] + ny * w), (base[0] - nx * w, base[1] - ny * w)],
                                      closed=True, fc="k", ec="k", lw=0.1, zorder=5))
        if metin is None:
            metin = f"{round(math.dist(a, b) * 1000):d}"
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        mx, my = (A2[0] + B2[0]) / 2 + nx * 1.6 * (1 if d >= 0 else -1), (A2[1] + B2[1]) / 2 + ny * 1.6 * (1 if d >= 0 else -1)
        self.ax.text(mx, my, metin, fontsize=fs, ha="center", va="center", rotation=ang, zorder=6,
                     bbox=dict(fc="white", ec="none", pad=0.2))

    def etiket(self, x, y, tx, ty, metin, fs=5.2):
        """Kılavuz çizgili parça etiketi (tx, ty kağıtta mm kaydırma)."""
        P = self.p(x, y)
        Q = (P[0] + tx, P[1] + ty)
        self.ax.plot([P[0], Q[0]], [P[1], Q[1]], lw=INCE, color="k", zorder=5)
        self.ax.add_patch(Circle(P, 0.5, fc="k", zorder=5))
        self.ax.plot([Q[0], Q[0] + (12 if tx >= 0 else -12)], [Q[1], Q[1]], lw=INCE, color="k", zorder=5)
        self.ax.text(Q[0] + (1 if tx >= 0 else -1), Q[1] + 0.8, metin, fontsize=fs, ha="left" if tx >= 0 else "right",
                     va="bottom", zorder=6)


# ---------------------------------------------------------------- ortak çizim parçaları
def ipe_kesit(g, x, y, h, b, tf, tw, fc="none"):
    g.cokgen([(x - b / 2, y), (x + b / 2, y), (x + b / 2, y + tf), (x + tw / 2, y + tf), (x + tw / 2, y + h - tf),
              (x + b / 2, y + h - tf), (x + b / 2, y + h), (x - b / 2, y + h), (x - b / 2, y + h - tf),
              (x - tw / 2, y + h - tf), (x - tw / 2, y + tf), (x - b / 2, y + tf)], fc=fc)


def caraskal(g, x, z_ray, yon=1):
    """Monoray araba + 2 t zincirli caraskal + kanca (yan görünüş, şematik)."""
    g.dik(x - 0.17, z_ray - 0.09, x + 0.17, z_ray + 0.15, fc="#ddd", lw=ORTA)  # yan levha
    g.dik(x - 0.11, z_ray + 0.02, x + 0.15, z_ray + 0.17, fc="#bbb", lw=ORTA)  # "2 ton" kutusu
    for sx in (-0.11, 0.11):
        g.daire(x + sx, z_ray + 0.045, 0.045, lw=ORTA)
    g.dik(x - 0.025, z_ray - 0.15, x + 0.025, z_ray - 0.09, lw=ORTA)  # askı kulağı
    zg = z_ray - 0.15
    g.dik(x - 0.30, zg - 0.36, x + 0.30, zg, fc="#f3d9a8", lw=ORTA)  # caraskal gövdesi
    g.dik(x - 0.30, zg - 0.36, x - 0.12, zg, fc="#999", lw=ORTA)  # motor kapağı
    g.dik(x + 0.08, zg - 0.36, x + 0.30, zg, fc="#999", lw=ORTA)  # elektrik kapağı
    g.dik(x - 0.27, zg - 0.95, x - 0.05, zg - 0.40, fc="#bbb", lw=ORTA)  # zincir torbası
    g.cizgi([(x + 0.02, zg - 0.36), (x + 0.02, zg - 0.86)], lw=ORTA)  # zincir
    g.dik(x - 0.015, zg - 0.93, x + 0.055, zg - 0.86, fc="#666", lw=ORTA)  # kanca bloğu
    kanca_cizimi(g, x + 0.02, zg - 0.93, 0.07)
    return zg - 0.93 - 0.14


def kanca_cizimi(g, x, z, r):
    pts = [(x, z), (x, z - r * 0.6)]
    for i in range(1, 25):
        t = math.radians(-235 * i / 24)
        pts.append((x - r + r * math.cos(t), z - r * 0.6 + r * math.sin(t)))
    g.cizgi(pts, lw=KALIN)


# ---------------------------------------------------------------- paftalar
def duvar_pergel(pdf, klasor):
    P = Pafta("DUVAR TİPİ PERGEL VİNÇ", "BV-PV-01", "1:40 / 1:100 / 1:10", "2 t (zincirli caraskal)", [
        "Bom IPE 300 (S355JR), üstten gergili; alt flanş caraskal yürüyüş yolu olarak serbesttir.",
        "Konsol: 30 mm taban levhası, her mafsalda 25 mm alt/üst kulak levhası + guse, Ø70 dikey pim.",
        "Gergi Ø84 boru, gerdirme manşonlu; bom üst flanşında pimli kulak (x = 3450).",
        "Dönme açısı 180°. Festoon C rayı bom yanında, üst flanş altında.",
        "Bina kolonu 600x600 betonarme; konsol 8 adet ankraj cıvatası ile bağlanır (ölçüler projede).",
    ])
    # ön görünüş 1:50
    g = Gorunus(P, 62, 72, 40, "ÖN GÖRÜNÜŞ")
    XP, zb = 0.22, 4.30
    g.zemin(-1.0, 5.0)
    g.dik(-0.6, 0, 0, 6.6, fc="#e6e6e6")  # betonarme kolon
    g.dik(-0.6, 0, 0, 6.6, fc="none", hatch="////")
    g.dik(0, 3.75, 0.03, 5.75, fc="#888")  # taban levhası
    for z in (4.14, 5.55):
        for sz in (-1, 1):
            g.dik(0.03, z + sz * 0.085 - 0.0125, XP + 0.10, z + sz * 0.085 + 0.0125, fc="#888", lw=ORTA)
        g.dik(XP - 0.035, z - 0.135, XP + 0.035, z + 0.135, fc="#ccc", lw=ORTA)  # pim
    g.eksen([(XP, 3.5), (XP, 6.2)])
    # bom
    ipe_x0, ipe_x1 = XP + 0.11, XP + 4.30
    g.dik(XP + 0.11 - 0.025, zb - 0.32, XP + 0.11, zb - 0.02, fc="#ccc", lw=ORTA)  # alın levhası
    g.dik(XP - 0.058, 4.07, XP + 0.058, 4.21, fc=TURUNCU, lw=ORTA)  # kök göbeği
    g.dik(ipe_x0, zb - 0.30, ipe_x1, zb, fc="#f6cf91")
    g.cizgi([(ipe_x0, zb - 0.022), (ipe_x1, zb - 0.022)], lw=INCE)
    g.cizgi([(ipe_x0, zb - 0.278), (ipe_x1, zb - 0.278)], lw=INCE)
    g.dik(ipe_x1, zb - 0.32, ipe_x1 + 0.02, zb + 0.02, fc="#888", lw=ORTA)
    # gergi
    p0, p1 = (XP + 0.06, 5.54), (XP + 3.45, zb + 0.10)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    nx, ny = -math.sin(ang) * 0.042, math.cos(ang) * 0.042
    g.cokgen([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)],
             fc="#f6cf91", lw=ORTA)
    g.dik(XP - 0.05, 5.48, XP + 0.05, 5.62, fc=TURUNCU, lw=ORTA)
    g.dik(XP + 3.36, zb, XP + 3.54, zb + 0.14, fc="#888", lw=ORTA)
    g.daire(XP + 3.45, zb + 0.10, 0.022, lw=ORTA)
    # caraskal
    kanca = caraskal(g, XP + 3.25, zb - 0.30 + 0.022)
    # ölçüler
    g.olcu((XP, zb), (ipe_x1 + 0.02, zb), 72, "4300 (erişim)")
    g.olcu((XP, 5.55), (XP + 3.45, 5.55), 22, "3450")
    g.olcu((5.0, 0), (5.0, zb), 12)
    g.olcu((5.3, 0), (5.3, 5.55), 12)
    g.olcu((-1.0, 4.14), (-1.0, 5.55), -6, "1410")
    g.olcu((XP + 3.25, 0), (XP + 3.25, kanca), -16, f"≈{round(kanca * 1000)}")
    g.etiket(1.6, zb - 0.15, 8, -20, "IPE 300 bom")
    g.etiket(XP + 2.4, 4.81, 14, 6, "Gergi Ø84")
    g.etiket(-0.3, 2.0, -10, -8, "Betonarme kolon 600x600")
    g.etiket(XP + 3.4, kanca + 0.6, 14, -10, "2 t zincirli caraskal")
    g.baslik(2.0, -0.45, "Ölçek 1:40")
    # plan 1:100
    pl = Gorunus(P, 262, 190, 100, "PLAN")
    pl.dik(-0.6, -0.3, 0, 0.3, fc="#e6e6e6")
    pl.dik(-0.6, -0.3, 0, 0.3, fc="none", hatch="////")
    pl.yay(XP, 0, 4.30, -90, 90)
    pl.dik(XP + 0.11, -0.075, XP + 4.30, 0.075, fc="#f6cf91", lw=ORTA)
    pl.eksen([(XP, -4.6), (XP, 4.6)])
    for a in (-90, 90):
        pl.cizgi([(XP, 0), (XP + 4.30 * math.cos(math.radians(a)), 4.30 * math.sin(math.radians(a)))], lw=INCE, ls="--")
    pl.yazi(XP + 3.4, 2.6, "180°", fs=6)
    pl.olcu((XP, 0), (XP + 4.30, 0), -10, "R 4300")
    pl.baslik(2.2, -4.9, "Ölçek 1:100")
    # A-A kesiti 1:10
    k = Gorunus(P, 345, 100, 10, "A-A KESİTİ (BOM)")
    ipe_kesit(k, 0, 0, 0.30, 0.15, 0.0107, 0.0071, fc="#f6cf91")
    k.olcu((-0.075, 0.30), (0.075, 0.30), 6, "150")
    k.olcu((-0.075, 0), (-0.075, 0.30), 8, "300")
    k.yazi(0.0, -0.035, "IPE 300  tf=10,7  tw=7,1", fs=5.2)
    k.baslik(0.0, -0.06, "Ölçek 1:10")
    g.yazi(XP + 1.9, zb - 0.15, "A", fs=7, w="bold")
    P.kaydet(pdf, os.path.join(klasor, "duvar_pergel_teknik.png"))


def kolon_pergel(pdf, klasor):
    P = Pafta("KOLON TİPİ PERGEL VİNÇ", "BV-PV-02", "1:40 / 1:100 / 1:20", "2 t (zincirli caraskal)", [
        "Kolon Ø340 boru (S355JR), taban levhası 900x900x40, 8 guse, 4 ankraj (M42) 720x720 aks.",
        "Dönen başlık Ø430, üstünde Ø220 gergi direği; gergi Ø84, bom üst flanşında pimli kulak.",
        "Bom IPE 300, üstten gergili; alt flanş caraskal yürüyüş yolu olarak serbesttir.",
        "Dönme açısı 360°. Festoon C rayı bom yanında.",
        "Temel boyutları zemin etüdüne göre statik projede belirlenir.",
    ])
    g = Gorunus(P, 70, 76, 40, "ÖN GÖRÜNÜŞ")
    H = 4.3
    zb = H + 0.48
    zd = zb + 1.35
    g.zemin(-1.2, 5.2)
    g.dik(-0.7, -0.04, 0.7, 0.0, fc="#e6e6e6", lw=ORTA)
    g.dik(-0.45, 0.0, 0.45, 0.04, fc="#888")
    for sx in (-1, 1):
        g.cokgen([(sx * 0.17, 0.04), (sx * 0.43, 0.04), (sx * 0.17, 0.5)], fc="#999", lw=ORTA)
    g.dik(-0.17, 0.04, 0.17, H + 0.06, fc="#cfd3d8")
    g.dik(-0.20, H - 0.02, 0.20, H + 0.14, fc="#888", lw=ORTA)
    g.dik(-0.215, H + 0.12, 0.215, H + 0.48, fc="#888")
    g.dik(-0.11, zb + 0.04, 0.11, zd, fc="#cfd3d8")
    g.dik(-0.14, zd, 0.14, zd + 0.05, fc="#888", lw=ORTA)
    g.eksen([(0, -0.3), (0, zd + 0.4)])
    g.dik(0.18, zb - 0.30, 4.4, zb, fc="#f6cf91")
    g.cizgi([(0.18, zb - 0.022), (4.4, zb - 0.022)], lw=INCE)
    g.cizgi([(0.18, zb - 0.278), (4.4, zb - 0.278)], lw=INCE)
    g.dik(4.4, zb - 0.32, 4.42, zb + 0.02, fc="#888", lw=ORTA)
    p0, p1 = (0.2, zd - 0.06), (3.45, zb + 0.10)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    nx, ny = -math.sin(ang) * 0.042, math.cos(ang) * 0.042
    g.cokgen([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)],
             fc="#f6cf91", lw=ORTA)
    g.dik(3.36, zb, 3.54, zb + 0.14, fc="#888", lw=ORTA)
    kanca = caraskal(g, 3.45, zb - 0.30 + 0.022)
    g.olcu((0, zb), (4.42, zb), 30, "4420 (erişim)")
    g.olcu((0, zd), (3.45, zd), 10, "3450")
    g.olcu((5.0, 0), (5.0, zb), 12)
    g.olcu((5.35, 0), (5.35, zd + 0.05), 12)
    g.olcu((-0.45, -0.04), (0.45, -0.04), -9, "900")
    g.olcu((3.45, 0), (3.45, kanca), -16, f"≈{round(kanca * 1000)}")
    g.etiket(0.0, 2.2, -12, 6, "Kolon Ø340")
    g.etiket(1.6, zb - 0.15, 8, -18, "IPE 300 bom")
    g.etiket(0.0, zd - 0.4, -12, 4, "Gergi direği Ø220")
    g.etiket(3.4, kanca + 0.6, 14, -10, "2 t zincirli caraskal")
    g.baslik(2.0, -0.55, "Ölçek 1:40")
    # plan 1:100
    pl = Gorunus(P, 285, 200, 100, "PLAN")
    pl.yay(0, 0, 4.42, 0, 360)
    pl.daire(0, 0, 0.215, fc="#888", lw=ORTA)
    pl.dik(0.18, -0.075, 4.4, 0.075, fc="#f6cf91", lw=ORTA)
    pl.eksen([(-4.7, 0), (4.7, 0)])
    pl.eksen([(0, -4.7), (0, 4.7)])
    pl.olcu((0, 0), (4.42, 0), -8, "R 4420")
    pl.yazi(-3.3, 3.5, "360°", fs=6)
    pl.baslik(0, -4.75, "Ölçek 1:100")
    # taban levhası detayı 1:20
    d = Gorunus(P, 372, 100, 20, "TABAN LEVHASI")
    d.dik(-0.45, -0.45, 0.45, 0.45, fc="#ddd")
    d.daire(0, 0, 0.17, fc="#cfd3d8")
    for a in range(8):
        t = math.radians(a * 45)
        c, s_ = math.cos(t), math.sin(t)
        d.cokgen([(0.17 * c - 0.01 * s_, 0.17 * s_ + 0.01 * c), (0.43 * c - 0.01 * s_, 0.43 * s_ + 0.01 * c),
                  (0.43 * c + 0.01 * s_, 0.43 * s_ - 0.01 * c), (0.17 * c + 0.01 * s_, 0.17 * s_ - 0.01 * c)],
                 fc="#999", lw=INCE)
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.daire(sx * 0.36, sy * 0.36, 0.023, fc="white", lw=ORTA)
    d.olcu((-0.45, 0.45), (0.45, 0.45), 5, "900")
    d.olcu((-0.36, -0.45), (0.36, -0.45), -5, "720")
    d.olcu((0.45, -0.36), (0.45, 0.36), -5, "720")
    d.yazi(0, -0.62, "4 x M42 ankraj", fs=5.2)
    d.baslik(0, -0.7, "Ölçek 1:20")
    P.kaydet(pdf, os.path.join(klasor, "kolon_pergel_teknik.png"))


def portal_ortak(P, cift, ad_on, ad_yan):
    span, h, yk, b = 11.0, 1.0 if cift else 0.85, 1.1, 0.5
    z_ust = 6.72 if cift else 7.87
    ya = yk + 1.6
    zl = z_ust - 0.85 * h
    # --- ön görünüş (açıklık) 1:100
    g = Gorunus(P, 42, 95, 100, ad_on)
    x_min = -1.0
    x_max = span + (1.0 if cift else 1.4)
    g.zemin(x_min, x_max)
    g.dik(0, z_ust - h, span, z_ust, fc="#f6cf91")
    for x in (0, span):
        g.dik(x - 0.25, z_ust - 0.85 * h, x + 0.25, z_ust - 0.05 * h, fc=TURUNCU, lw=ORTA)
    g.dik(0, z_ust, span, z_ust + 0.05, fc="#888", lw=INCE)  # ray
    ayaklar = (0.0, span) if cift else (0.0,)
    for x in ayaklar:
        g.cokgen([(x - 0.17, 0.74), (x + 0.17, 0.74), (x + 0.21, zl), (x - 0.21, zl)], fc="#f6cf91")
        g.dik(x - 0.17, 0.12, x + 0.17, 0.74, fc="#777", lw=ORTA)  # baş arabası
    if not cift:
        kx = span + 0.75
        g.dik(kx - 0.3, 0, kx + 0.3, 9.5, fc="#e6e6e6")
        g.dik(kx - 0.3, 0, kx + 0.3, 9.5, fc="none", hatch="////")
        g.dik(kx - 0.85, 5.7, kx - 0.3, 6.3, fc="#e6e6e6", lw=ORTA)  # konsol
        ipe_kesit(g, span, 6.25, 0.5, 0.3, 0.025, 0.014, fc="#999")  # yürüyüş yolu kirişi (kesit)
        g.dik(span - 0.17, 6.75, span + 0.17, z_ust - 0.85 * h, fc="#777", lw=ORTA)  # baş arabası (yol kirişinde)
    # araba (şematik)
    xa = span * (0.36 if cift else 0.58)
    g.dik(xa - 0.55, z_ust + 0.05, xa + 0.55, z_ust + 0.95, fc="#f3d9a8", lw=ORTA)
    g.daire(xa - 0.1, z_ust + 0.6, 0.22, lw=ORTA)
    for xx in (xa - 0.02, xa + 0.02):
        g.cizgi([(xx, z_ust + 0.4), (xx, 2.6)], lw=INCE)
    g.dik(xa - 0.12, 2.35, xa + 0.12, 2.6, fc="#f3d9a8", lw=ORTA)
    kanca_cizimi(g, xa, 2.35, 0.09)
    # ölçüler
    g.olcu((0, z_ust + 1.0), (span, z_ust + 1.0), 6, f"{round(span * 1000)} (açıklık)")
    g.olcu((x_max - 0.3 if cift else span + 2.1, 0), (x_max - 0.3 if cift else span + 2.1, z_ust), -5 if cift else 4, None)
    g.olcu((x_min + 0.3, 0), (x_min + 0.3, z_ust + 0.95), 5, None)
    g.olcu((xa + 0.9, 0), (xa + 0.9, 2.1), -4, "≈2100")
    g.etiket(span * 0.75, z_ust - h / 2, 6, -14, f"Kutu kiriş {round(b * 1000)}x{round(h * 1000)}")
    g.etiket(xa + 0.5, z_ust + 0.5, 22, -9, "Halatlı vinç arabası")
    g.baslik(span / 2, -1.0, "Ölçek 1:100")
    # --- yan görünüş (kiriş doğrultusunda) 1:100
    s = Gorunus(P, 244 + (ya + 0.5) * 10, 95, 100, ad_yan)
    s.zemin(-ya - 1.0, ya + 1.0)
    for sy in (-1, 1):
        s.dik(sy * yk - b / 2, z_ust - h, sy * yk + b / 2, z_ust, fc="#f6cf91")
        s.dik(sy * yk - 0.03, z_ust, sy * yk + 0.03, z_ust + 0.05, fc="#888", lw=INCE)
        s.cokgen([(sy * ya - 0.14, 0.74), (sy * ya + 0.14, 0.74), (sy * yk + 0.18, zl), (sy * yk - 0.18, zl)],
                 fc="#f6cf91")
    s.dik(-yk - 0.55, z_ust - 0.85 * h, yk + 0.55, z_ust - 0.05 * h, fc=TURUNCU, lw=ORTA)
    zc = 0.74 + (zl - 0.74) * 0.45
    yc = ya + (yk - ya) * 0.45
    s.dik(-yc, zc - 0.09, yc, zc + 0.09, fc="#f6cf91", lw=ORTA)
    s.dik(-ya - 0.5, 0.32, ya + 0.5, 0.62, fc="#777")
    for sy in (-1, 1):
        s.daire(sy * (ya + 0.5 - 0.32), 0.20, 0.17, fc="#bbb", lw=ORTA)
    s.dik(-ya - 1.0, 0.0, ya + 1.0, 0.03, fc="#888", lw=INCE)
    # araba (cepheden)
    s.dik(-1.3, z_ust + 0.05, 1.3, z_ust + 0.95, fc="#f3d9a8", lw=ORTA)
    s.dik(-0.9, z_ust + 0.55, 0.6, z_ust + 0.9, fc="#ccc", lw=INCE)  # tambur
    for yy in (-0.15, 0.15):
        s.cizgi([(yy, z_ust + 0.4), (yy, 2.6)], lw=INCE)
    s.dik(-0.22, 2.35, 0.22, 2.6, fc="#f3d9a8", lw=ORTA)
    kanca_cizimi(s, 0.0, 2.35, 0.09)
    s.eksen([(0, -0.3), (0, z_ust + 1.3)])
    s.olcu((-yk, z_ust + 1.0), (yk, z_ust + 1.0), 5, f"{round(2 * yk * 1000)} (ray açıklığı)")
    s.olcu((-(ya + 0.5 - 0.32), 0.0), ((ya + 0.5 - 0.32), 0.0), -6, f"{round(2 * (ya + 0.5 - 0.32) * 1000)} (dingil açıklığı)")
    s.etiket(ya * 0.75, 3.0, 6, 6, "A tipi ayak")
    s.etiket(-ya + 0.2, 0.47, -6, 8, "Baş arabası")
    s.baslik(0, -1.45, "Ölçek 1:100")
    # --- plan 1:200
    pl = Gorunus(P, 335, 225, 200, "PLAN")
    for sy in (-1, 1):
        pl.dik(0, sy * yk - b / 2, span, sy * yk + b / 2, fc="#f6cf91", lw=ORTA)
    for x in ayaklar:
        pl.dik(x - 0.25, -yk - 0.3, x + 0.25, yk + 0.3, fc=TURUNCU, lw=ORTA)
        pl.cizgi([(x, -6), (x, 6)], lw=ORTA)  # ray
        pl.dik(x - 0.17, -ya - 0.5, x + 0.17, ya + 0.5, fc="#777", lw=INCE)
    if not cift:
        pl.cizgi([(span, -3.8), (span, 3.8)], lw=KALIN)
        pl.dik(span + 0.45, -3.8, span + 1.05, -3.2, fc="#e6e6e6", lw=ORTA)
        pl.dik(span + 0.45, 3.2, span + 1.05, 3.8, fc="#e6e6e6", lw=ORTA)
    pl.dik(xa - 0.55, -1.3, xa + 0.55, 1.3, fc="#f3d9a8", lw=ORTA)
    pl.olcu((0, -6), (span, -6), -5, f"{round(span * 1000)}")
    pl.yazi(span / 2, 6.6, "Yürüyüş yönü (raylar boyunca) ↕", fs=5.2)
    pl.baslik(span / 2, -8.2, "Ölçek 1:200")


def portal(pdf, klasor):
    P = Pafta("ÇİFT KİRİŞLİ PORTAL VİNÇ", "BV-PV-03", "1:100 / 1:200", "— (projeye göre)", [
        "Ana kirişler 2 x kutu kiriş 500x1000 (S355JR), uç kirişlerle alın levhalı cıvatalı birleşim.",
        "Her uçta kirişe dik düzlemde A tipi iki ayak; ayak-uç kiriş ve ayak-baş arabası flanşları cıvatalı.",
        "Baş arabaları tekerlek bloklu, motor-redüktör-fren tahrikli; raylar kirişe dik doğrultudadır.",
        "Halatlı vinç arabası iki kirişin üstündeki raylarda yürür; enerji festoon sistemiyle.",
        "Yakın ayakta merdiven ve besleme kablo tamburu; ray sonlarında stoper ve tampon.",
    ])
    portal_ortak(P, True, "ÖN GÖRÜNÜŞ", "YAN GÖRÜNÜŞ")
    P.kaydet(pdf, os.path.join(klasor, "portal_teknik.png"))


def yari_portal(pdf, klasor):
    P = Pafta("ÇİFT KİRİŞLİ YARI PORTAL VİNÇ", "BV-PV-04", "1:100 / 1:200", "— (projeye göre)", [
        "Bir uç A tipi ayaklarla zemin rayında, diğer uç bina kolonu konsolundaki yürüyüş yolu kirişinde.",
        "Ana kirişler 2 x kutu kiriş 500x850 (S355JR), uç kirişlerle cıvatalı birleşim.",
        "Yürüyüş yolu kirişi bina kolonu konsollarına oturur; kolon ve konsol ölçüleri bina projesinde.",
        "Halatlı vinç arabası iki kirişin üstündeki raylarda yürür; enerji festoon sistemiyle.",
        "Ray sonlarında stoper ve tampon; ayakta merdiven ve kablo tamburu.",
    ])
    portal_ortak(P, False, "ÖN GÖRÜNÜŞ", "YAN GÖRÜNÜŞ (AYAK TARAFI)")
    P.kaydet(pdf, os.path.join(klasor, "yari_portal_teknik.png"))


def main():
    klasor = sys.argv[1] if len(sys.argv) > 1 else "teknik"
    os.makedirs(klasor, exist_ok=True)
    with PdfPages(os.path.join(klasor, "beta_vinc_teknik_resimler.pdf")) as hepsi:
        for f in (duvar_pergel, kolon_pergel, yari_portal, portal):
            with PdfPages(os.path.join(klasor, f.__name__ + "_teknik.pdf")) as tek:
                class Iki:
                    def savefig(self, fig):
                        hepsi.savefig(fig)
                        tek.savefig(fig)
                f(Iki(), klasor)
    print("tamam:", klasor)


if __name__ == "__main__":
    main()
