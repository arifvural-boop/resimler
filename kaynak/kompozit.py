"""
Beta Vinç 3B animasyonu: 3B sahne kareleri + 2B kurumsal katman (TR / EN) -> MP4.

Kullanım:
    python kompozit.py <kareler_klasoru> <dil: tr|en> <cikti.mp4>
    python kompozit.py <kareler_klasoru> <dil> --kare <sn> <cikti.png>
"""
import json
import math
import os
import subprocess
import sys

import cairo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animasyon as a2  # noqa: E402  (2B çizim yardımcıları ve marka renkleri)

W, H = 1920, 1080
FPS = 25
C = a2.C
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")

SAHNELER = [("acilis", 4.0), ("siparis", 7.0), ("kesif", 8.0), ("muhendislik", 6.0), ("imalat", 10.0),
            ("sevkiyat", 8.5), ("nakliye", 8.0), ("kurulum", 11.0), ("kapanis", 4.5)]
GECIS = 0.5

METIN = {
    "tr": dict(
        slogan="vinç sistemleri", baslik="Bir vincin yolculuğu", alt="Tek kirişli köprülü vinç  ·  siparişten kuruluma",
        adimlar=["Sipariş", "Keşif ve Ölçü", "Mühendislik", "İmalat", "Sevkiyat", "Nakliye", "Kurulum ve Test"],
        siparis=("Sipariş", "İhtiyaç dinlenir, teklif ve sipariş netleşir"),
        form="SİPARİŞ FORMU", onay="ONAYLANDI",
        alanlar=[("Ürün", "Tek kirişli köprülü vinç"), ("Kapasite", "5 ton"), ("Açıklık", "12 m"),
                 ("Kaldırma yüksekliği", "6 m"), ("Kumanda", "Butonyer + uzaktan kumanda"), ("Teslim", "Kurulum dahil")],
        kesif=("Keşif ve Ölçü", "Sahada ray açıklığı ve kotlar ölçülür"),
        rapor="Keşif raporu", rapor_m=["Ray açıklığı 12.000 mm", "Ray kotu 6.500 mm", "Yürüyüş yolu kontrolü", "Enerji beslemesi"],
        muh=("Mühendislik", "Statik hesap, 3B model ve imalat resimleri"), muh_baslik="TEK KİRİŞLİ KÖPRÜLÜ VİNÇ  ·  5 t",
        muh_m=["Statik hesap", "3B model", "İmalat resimleri"],
        imalat=("İmalat", ["Kesim ve kaynak", "Boya", "Montaj", "Kalite kontrol"]), kk=("KALİTE", "KONTROL"),
        sevk=("Sevkiyat", "Ürün güvenle tıra yüklenir ve sabitlenir"), hazir="Sevkiyata hazır",
        nakliye=("Nakliye", "Planlı rota, sigortalı ve takipli taşıma"), rota=("Beta Üretim Merkezi", "Müşteri tesisi"),
        kurulum=("Kurulum ve Test", ["Kiriş montajı", "Baş arabaları ve caraskal", "Yük testi", "Devreye alma"]),
        test="Yük testi tamam", kapanis="Siparişten kuruluma, tek elden.",
    ),
    "en": dict(
        slogan="crane systems", baslik="The journey of a crane", alt="Single girder overhead crane  ·  from order to installation",
        adimlar=["Order", "Site Survey", "Engineering", "Manufacturing", "Dispatch", "Transport", "Installation & Test"],
        siparis=("Order", "We listen to your needs; quote and order are finalized"),
        form="ORDER FORM", onay="APPROVED",
        alanlar=[("Product", "Single girder overhead crane"), ("Capacity", "5 tonnes"), ("Span", "12 m"),
                 ("Lifting height", "6 m"), ("Control", "Pendant + radio remote"), ("Delivery", "Installation included")],
        kesif=("Site Survey", "Runway span and heights are measured on site"),
        rapor="Survey report", rapor_m=["Runway span 12,000 mm", "Rail height 6,500 mm", "Runway inspection", "Power supply"],
        muh=("Engineering", "Structural analysis, 3D model and shop drawings"), muh_baslik="SINGLE GIRDER OVERHEAD CRANE  ·  5 t",
        muh_m=["Structural analysis", "3D model", "Shop drawings"],
        imalat=("Manufacturing", ["Cutting and welding", "Painting", "Assembly", "Quality control"]), kk=("QUALITY", "CONTROL"),
        sevk=("Dispatch", "Loaded onto the truck and secured"), hazir="Ready for dispatch",
        nakliye=("Transport", "Planned route, insured and tracked delivery"), rota=("Beta Production Center", "Customer site"),
        kurulum=("Installation & Test", ["Girder erection", "End carriages and hoist", "Load test", "Commissioning"]),
        test="Load test passed", kapanis="From order to installation, all from one source.",
    ),
}


def png(ad):
    return cairo.ImageSurface.create_from_png(os.path.join(LOGO, ad))


class Katman:
    def __init__(self, kare_dir, dil):
        self.dir = kare_dir
        self.T = METIN[dil]
        self.dil = dil
        self.logo_koyu = png("beta_isaret_koyu.png")
        self.logo_beyaz = png("beta_isaret_beyaz.png")
        self.nokta = {}
        for s, _ in SAHNELER:
            p = os.path.join(kare_dir, s, "noktalar.json")
            if os.path.exists(p):
                self.nokta[s] = json.load(open(p))

    # ----- yardımcılar
    def resim(self, ctx, surf, x, y, gen, a=1.0):
        s = gen / surf.get_width()
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s, s)
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint_with_alpha(a)
        ctx.restore()
        return surf.get_height() * s

    def kose_logo(self, ctx):
        a2.kutu(ctx, 54, 40, 210, 74, C["beyaz"], r=12, a=0.92)
        self.resim(ctx, self.logo_koyu, 72, 56, 174)

    def kart(self, ctx, no, baslik, alt, t):
        p = a2.ease_out(a2.dilim(t, 0.15, 0.9))
        x = a2.lerp(-640, 54, p)
        y = 136
        gen = max(600, 196 + 11.5 * max(len(alt), len(baslik) * 1.8))
        a2.kutu(ctx, x, y, gen, 120, C["koyu"], r=18, a=0.86 * p)
        a2.kutu(ctx, x, y, 12, 120, C["turuncu"], r=6, a=p)
        a2.yazi(ctx, f"{no:02d}", x + 36, y + 84, 70, C["turuncu"], kalin=True, a=p)
        a2.yazi(ctx, baslik, x + 156, y + 56, 38, C["beyaz"], kalin=True, a=p)
        a2.yazi(ctx, alt, x + 156, y + 96, 22, C["gri_a"], a=p)

    def cubuk(self, ctx, adim, oran):
        a2.kutu(ctx, 0, 968, W, 112, C["beyaz"], a=0.86)
        y, x0, x1 = 1010, 160, W - 160
        n = 7
        a2.kutu(ctx, x0, y - 3, x1 - x0, 6, C["koyu"], r=3, a=0.18)
        o = (adim + a2.sinir(oran)) / (n - 1) if adim < n - 1 else 1.0
        a2.kutu(ctx, x0, y - 3, (x1 - x0) * a2.sinir(o), 6, C["turuncu"], r=3)
        for i, ad in enumerate(self.T["adimlar"]):
            xx = x0 + i * (x1 - x0) / (n - 1)
            a2.daire(ctx, xx, y, 13 if i == adim else 9, C["turuncu"] if i <= adim else C["gri_a"])
            if i == adim:
                a2.daire(ctx, xx, y, 5, C["beyaz"])
            a2.yazi(ctx, ad, xx, y + 44, 21 if i == adim else 18, C["koyu"] if i == adim else C["gri"],
                    kalin=i == adim, hiza="orta")

    def ekran(self, sahne, kare, ad):
        d = self.nokta.get(sahne, {})
        if not d:
            return None
        ks = sorted(int(k) for k in d)
        k = min(ks, key=lambda v: abs(v - kare))
        return [(p[0] * W, (1 - p[1]) * H) for p in d[str(k)][ad]]

    # ----- sahne katmanları
    def acilis(self, ctx, t, n):
        T = self.T
        a = a2.dilim(t, 2.0, 2.6)
        a2.yazi(ctx, T["slogan"], W / 2, 735, 40, C["gri_a"], hiza="orta", a=a, aralik=16)
        b = a2.dilim(t, 2.6, 3.2)
        a2.yazi(ctx, T["baslik"], W / 2, 860, 60, C["beyaz"], kalin=True, hiza="orta", a=b)
        a2.yazi(ctx, T["alt"], W / 2, 912, 30, C["turuncu"], hiza="orta", a=b)

    def siparis(self, ctx, t, n):
        T = self.T
        self.kart(ctx, 1, *T["siparis"], t)
        k = a2.ease_out(a2.dilim(t, 1.0, 1.9))
        kx, ky = a2.lerp(W + 50, 1180, k), 150
        a2.kutu(ctx, kx, ky, 680, 600, C["beyaz"], r=18, a=0.97)
        a2.kutu(ctx, kx, ky, 680, 90, C["antrasit"], r=18)
        a2.kutu(ctx, kx, ky + 60, 680, 30, C["antrasit"])
        self.resim(ctx, self.logo_beyaz, kx + 28, ky + 26, 130)
        a2.yazi(ctx, T["form"], kx + 650, ky + 58, 26, C["turuncu"], kalin=True, hiza="sag", aralik=2)
        for i, (et, deger) in enumerate(T["alanlar"]):
            yy = ky + 150 + i * 70
            p = a2.dilim(t, 1.8 + i * 0.45, 2.4 + i * 0.45)
            a2.yazi(ctx, et, kx + 40, yy, 22, C["gri"])
            a2.yazi(ctx, deger[:int(len(deger) * p)], kx + 300, yy, 26, C["koyu"], kalin=True)
            a2.cizgi(ctx, [(kx + 40, yy + 18), (kx + 640, yy + 18)], C["gri_a"], lw=1.5)
        d = a2.dilim(t, 5.2, 5.8)
        if d > 0:
            s = a2.lerp(2.2, 1.0, a2.ease_out(d))
            ctx.save()
            ctx.translate(kx + 480, ky + 545)
            ctx.rotate(-0.18)
            ctx.scale(s, s)
            a2.kutu(ctx, -165, -42, 330, 72, (0, 0, 0, 0), r=10, cizgi=C["yesil"], lw=6)
            a2.yazi(ctx, T["onay"], 0, 12, 40, C["yesil"], kalin=True, hiza="orta", a=a2.sinir(d * 2))
            ctx.restore()

    def kesif(self, ctx, t, n):
        T = self.T
        self.kart(ctx, 2, *T["kesif"], t)
        kare = int(t * FPS) + 1
        p = a2.ease_io(a2.dilim(kare, n * 0.32, n * 0.6))
        pts = self.ekran("kesif", kare, "aciklik")
        if pts and p > 0:
            (ax, ay), (bx, by) = pts
            mx, my = (ax + bx) / 2, min(ay, by) - 60
            deger = f"{int(12000 * p):,} mm".replace(",", ".") if self.dil == "tr" else f"{int(12000 * p):,} mm"
            a2.kutu(ctx, mx - 130, my - 36, 260, 50, C["beyaz"], r=10, a=0.94)
            a2.yazi(ctx, deger, mx, my, 32, C["kirmizi"], kalin=True, hiza="orta")
        p2 = a2.ease_io(a2.dilim(kare, n * 0.62, n * 0.82))
        pts = self.ekran("kesif", kare, "yukseklik")
        if pts and p2 > 0:
            (ax, ay), (bx, by) = pts
            mx, my = ax + 30, (ay + by) / 2
            deger = f"{int(6500 * p2):,} mm".replace(",", ".") if self.dil == "tr" else f"{int(6500 * p2):,} mm"
            a2.kutu(ctx, mx, my - 30, 220, 50, C["beyaz"], r=10, a=0.94)
            a2.yazi(ctx, deger, mx + 18, my + 6, 32, C["kirmizi"], kalin=True)
        tb = a2.ease_out(a2.dilim(t, 6.4, 7.0))
        if tb > 0:
            tx0, ty0 = a2.lerp(W + 40, 1420, tb), 470
            a2.kutu(ctx, tx0, ty0, 440, 330, C["antrasit"], r=22)
            a2.kutu(ctx, tx0 + 16, ty0 + 16, 408, 298, C["beyaz"], r=12)
            a2.yazi(ctx, T["rapor"], tx0 + 40, ty0 + 66, 28, C["koyu"], kalin=True)
            for i, m in enumerate(T["rapor_m"]):
                yy = ty0 + 118 + i * 50
                a2.onay(ctx, tx0 + 56, yy - 8, 15, a2.dilim(t, 6.9 + i * 0.25, 7.4 + i * 0.25))
                a2.yazi(ctx, m, tx0 + 84, yy, 22, C["koyu"])

    def muhendislik(self, ctx, t, n):
        T = self.T
        self.kart(ctx, 3, *T["muh"], t)
        a = a2.dilim(t, 0.8, 1.6)
        a2.yazi(ctx, T["muh_baslik"], W / 2 + 260, 210, 38, renk_acik(), kalin=True, hiza="orta", a=a, aralik=2)
        for i, s in enumerate(T["muh_m"]):
            x = 560 + i * 380
            a2.onay(ctx, x, 920, 20, a2.dilim(t, 3.4 + i * 0.4, 4.0 + i * 0.4))
            a2.yazi(ctx, s, x + 32, 930, 28, renk_acik(), a=a2.dilim(t, 3.4 + i * 0.4, 3.9 + i * 0.4))

    def imalat(self, ctx, t, n):
        T = self.T
        bas, alts = T["imalat"]
        i = 0 if t < 4.2 else 1 if t < 6.6 else 2 if t < 8.4 else 3
        self.kart(ctx, 4, bas, alts[i], t)
        q = a2.dilim(t, 8.4, 9.2)
        if q > 0:
            s = a2.geri(q)
            ctx.save()
            ctx.translate(1690, 520)
            ctx.scale(s, s)
            a2.daire(ctx, 0, 0, 120, C["yesil"])
            ctx.arc(0, 0, 104, 0, 2 * math.pi)
            a2.boya(ctx, C["beyaz"])
            ctx.set_line_width(4)
            ctx.stroke()
            a2.yazi(ctx, T["kk"][0], 0, -18, 30, C["beyaz"], kalin=True, hiza="orta")
            a2.yazi(ctx, T["kk"][1], 0, 20, 30, C["beyaz"], kalin=True, hiza="orta")
            a2.onay(ctx, 0, 62, 18, 1.0, c=C["beyaz"])
            ctx.restore()

    def sevkiyat(self, ctx, t, n):
        T = self.T
        self.kart(ctx, 5, *T["sevk"], t)
        if t > 7.2:
            a2.kutu(ctx, 1260, 820, 560, 96, C["beyaz"], r=16, a=0.92 * a2.dilim(t, 7.2, 7.6))
            a2.onay(ctx, 1316, 868, 30, a2.dilim(t, 7.2, 7.9))
            a2.yazi(ctx, T["hazir"], 1366, 882, 36, C["koyu"], kalin=True, a=a2.dilim(t, 7.3, 7.8))

    def nakliye(self, ctx, t, n):
        T = self.T
        self.kart(ctx, 6, *T["nakliye"], t)
        a = a2.ease_out(a2.dilim(t, 0.5, 1.3))
        kx, ky = a2.lerp(W + 40, 1380, a), 60
        a2.kutu(ctx, kx, ky, 480, 300, C["beyaz"], r=18, a=0.95)
        pts = [(kx + 70, ky + 230), (kx + 160, ky + 150), (kx + 260, ky + 190), (kx + 330, ky + 110), (kx + 410, ky + 90)]
        a2.cizgi(ctx, pts, C["gri_a"], lw=8)
        pr = a2.ease_io(a2.dilim(t, 1.0, 7.6))
        L = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        d = pr * sum(L)
        q = [pts[0]]
        for i, s in enumerate(L):
            if d >= s:
                q.append(pts[i + 1])
                d -= s
            else:
                q.append((a2.lerp(pts[i][0], pts[i + 1][0], d / s), a2.lerp(pts[i][1], pts[i + 1][1], d / s)))
                break
        a2.cizgi(ctx, q, C["turuncu"], lw=8)
        a2.daire(ctx, *pts[0], 12, C["antrasit"])
        a2.daire(ctx, *pts[-1], 12, C["yesil"] if pr >= 1 else C["gri"])
        a2.daire(ctx, *q[-1], 14, C["turuncu"])
        a2.yazi(ctx, T["rota"][0], kx + 40, ky + 272, 20, C["koyu"], kalin=True)
        a2.yazi(ctx, T["rota"][1], kx + 440, ky + 60, 20, C["koyu"], kalin=True, hiza="sag")

    def kurulum(self, ctx, t, n):
        T = self.T
        bas, alts = T["kurulum"]
        i = 0 if t < 5.8 else 1 if t < 7.5 else 2 if t < 10.0 else 3
        self.kart(ctx, 7, bas, alts[i], t)
        if t > 9.8:
            a2.kutu(ctx, 1260, 820, 560, 96, C["beyaz"], r=16, a=0.92 * a2.dilim(t, 9.8, 10.2))
            a2.onay(ctx, 1316, 868, 30, a2.dilim(t, 9.8, 10.5))
            a2.yazi(ctx, T["test"], 1366, 882, 36, C["koyu"], kalin=True, a=a2.dilim(t, 9.9, 10.4))

    def kapanis(self, ctx, t, n):
        T = self.T
        a = a2.dilim(t, 1.0, 1.6)
        a2.yazi(ctx, T["slogan"], W / 2, 735, 40, C["beyaz"], hiza="orta", a=a, aralik=16)
        b = a2.dilim(t, 1.6, 2.3)
        a2.yazi(ctx, T["kapanis"], W / 2, 860, 54, C["koyu"], kalin=True, hiza="orta", a=b)
        a2.yazi(ctx, "www.betavinc.com", W / 2, 930, 38, C["beyaz"], kalin=True, hiza="orta", a=a2.dilim(t, 2.2, 2.9))

    # ----- kare
    def sahne(self, i, t):
        ad, sure = SAHNELER[i]
        n = int(sure * FPS)
        kare = min(n, max(1, int(round(t * FPS)) + 1))
        yol = os.path.join(self.dir, ad, f"{kare:04d}.png")
        yuzey = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(yuzey)
        if os.path.exists(yol):
            src = cairo.ImageSurface.create_from_png(yol)
            ctx.save()
            ctx.scale(W / src.get_width(), H / src.get_height())
            ctx.set_source_surface(src, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_BEST)
            ctx.paint()
            ctx.restore()
        else:
            a2.kutu(ctx, 0, 0, W, H, C["koyu"])
        getattr(self, ad)(ctx, t, n)
        adim = {"siparis": 0, "kesif": 1, "muhendislik": 2, "imalat": 3, "sevkiyat": 4, "nakliye": 5, "kurulum": 6}.get(ad)
        if adim is not None:
            self.kose_logo(ctx)
            self.cubuk(ctx, adim, t / sure)
        return yuzey

    def kare(self, tg):
        bas = 0.0
        for i, (_, sure) in enumerate(SAHNELER):
            son = bas + sure
            if tg < son or i == len(SAHNELER) - 1:
                t = tg - bas
                y1 = self.sahne(i, t)
                if i + 1 < len(SAHNELER) and t > sure - GECIS:
                    k = a2.yumusak((t - (sure - GECIS)) / GECIS)
                    y2 = self.sahne(i + 1, t - (sure - GECIS))
                    c = cairo.Context(y1)
                    c.set_source_surface(y2, 0, 0)
                    c.paint_with_alpha(k)
                return y1
            bas = son - GECIS


def renk_acik():
    return a2.renk("#DDEBFA")


TOPLAM = sum(s for _, s in SAHNELER) - GECIS * (len(SAHNELER) - 1)


def main():
    kare_dir, dil = sys.argv[1], sys.argv[2]
    K = Katman(kare_dir, dil)
    if sys.argv[3] == "--kare":
        K.kare(float(sys.argv[4])).write_to_png(sys.argv[5])
        return
    cikti = sys.argv[3]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
    n = int(TOPLAM * FPS)
    for i in range(n):
        ff.stdin.write(bytes(K.kare(i / FPS).get_data()))
    ff.stdin.close()
    ff.wait()
    print(cikti, n, "kare", round(TOPLAM, 1), "sn")


if __name__ == "__main__":
    main()
