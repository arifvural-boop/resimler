"""
Beta Vinç - C raylı festoon kablo sistemi: çift kirişli köprülü vinç üzerinde gerçekçi render (Blender / bpy).

Fotoğraflardaki parçalar modellenir: galvaniz C ray profili (alt yarıklı, içe kıvrık dudaklı), turuncu
kanatlı araba plakası, iki dişli mil ve siyah yarım yuvarlak kablo kelepçesi; yassı kablolar arabalar
arasında ilmek yaparak sarkar. render_vincler.py'nin malzeme, ışık ve render altyapısını kullanır.

Kullanım:
    python render_festoon.py <genel|detay> <cikti.png> [ornek_sayisi]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,I001
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import render_vincler as RV  # noqa: E402

kutu, silindir, boru, obj, bm_to_mesh = RV.kutu, RV.silindir, RV.boru, RV.obj, RV.bm_to_mesh

# ---------------------------------------------------------------- ölçüler (m)
SPAN = 12.0          # köprü açıklığı (X)
YK = 0.48            # kiriş aksları ±Y
KB = 0.42            # kiriş genişliği
KH = 0.9             # kiriş yüksekliği
ZR = 6.2             # yürüyüş yolu ray üst kotu
Z_UST = ZR + 0.62 + KH
RB, RH, RT = 0.07, 0.07, 0.004   # C ray dış genişlik/yükseklik, et kalınlığı
YARIK = 0.026                    # alt yarık
Y_RAY = -(YK + KB / 2 + 0.36)    # festoon rayı ön kirişin dışında
Z_RAY = Z_UST + 0.36             # ray merkez kotu
X_ARABA = 4.9                    # vinç arabası konumu
X_SABIT = 0.35                   # besleme ucu
ETIKET = {}                      # pafta açıklama noktaları: ad -> dünya koordinatı


# ---------------------------------------------------------------- parçalar
def c_ray(name, x0, x1, y, z, M, g):
    """Alt yarıklı C ray: kesit çokgeni X boyunca çekilir, dudaklar içe ve hafif yukarı kıvrık."""
    b, h, t, s = RB / 2, RH / 2, RT, YARIK / 2
    yz = [(-s, -h + 0.006), (-b + 0.010, -h), (-b, -h + 0.010), (-b, h - 0.008), (-b + 0.008, h),
          (b - 0.008, h), (b, h - 0.008), (b, -h + 0.010), (b - 0.010, -h), (s, -h + 0.006),
          (s, -h + 0.006 + t), (b - 0.010 - t * 0.4, -h + t), (b - t, -h + 0.010 + t * 0.3), (b - t, h - 0.008 - t * 0.3),
          (b - 0.008 - t * 0.3, h - t), (-b + 0.008 + t * 0.3, h - t), (-b + t, h - 0.008 - t * 0.3),
          (-b + t, -h + 0.010 + t * 0.3), (-b + 0.010 + t * 0.4, -h + t), (-s, -h + 0.006 + t)]
    bm = bmesh.new()
    vs = [bm.verts.new((x0, y + py, z + pz)) for py, pz in yz]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    yeni = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((x1 - x0, 0, 0)), verts=yeni)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if "c_ray" not in M:
        M["c_ray"] = RV.fircali_celik(RV.boya("c_ray", (0.80, 0.81, 0.83, 1), rough=0.24, metal=1.0, var=0.08))
    return obj(name, bm_to_mesh(bm, name), M["c_ray"], g, bevel=0.0012, seg=2)


def plaka(name, x, y, z, M, g, s=1.0):
    """Turuncu kanatlı araba plakası (üstten bakışta iki yana sivrilen altıgen)."""
    hx, hy, t = 0.055 * s, 0.115 * s, 0.014 * s
    plan = [(-hx, -0.04 * s), (-0.016 * s, -hy), (0.016 * s, -hy), (hx, -0.04 * s),
            (hx, 0.04 * s), (0.016 * s, hy), (-0.016 * s, hy), (-hx, 0.04 * s)]
    bm = bmesh.new()
    alt = [bm.verts.new((x + px, y + py, z - t)) for px, py in plan]
    ust = [bm.verts.new((x + px, y + py, z)) for px, py in plan]
    bm.faces.new(list(reversed(alt)))
    bm.faces.new(ust)
    n = len(plan)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([alt[i], alt[j], ust[j], ust[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm_to_mesh(bm, name), M["turuncu"], g, bevel=0.003, seg=3)


def kelepce(name, x, y, z, M, g, R=0.07, uz=0.10):
    """Siyah yarım yuvarlak kablo kelepçesi (kesit YZ düzleminde D, X boyunca uz); z: taban kotu."""
    bm = bmesh.new()
    n = 24
    halka = [(R * math.cos(math.pi * k / n), R * 0.62 * math.sin(math.pi * k / n)) for k in range(n + 1)]
    on = [bm.verts.new((x - uz / 2, y + py, z + pz)) for py, pz in halka]
    ar = [bm.verts.new((x + uz / 2, y + py, z + pz)) for py, pz in halka]
    bm.faces.new(on)
    bm.faces.new(list(reversed(ar)))
    for i in range(n):
        bm.faces.new([on[i], on[i + 1], ar[i + 1], ar[i]])
    bm.faces.new([on[n], on[0], ar[0], ar[n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj(name, bm_to_mesh(bm, name), M["siyah"], g, smooth=True, bevel=0.004, seg=3)
    # alt tırnak (fotoğraftaki kablo tutma dili)
    kutu(name + "_dil", (uz * 0.5, 0.05, 0.022), (x, y - R * 0.55, z - 0.006), M["siyah"], g, bevel=0.004)
    return o


def araba(name, x, M, g, cek=False):
    """Ray içinde tekerlekli gövde, yarıktan inen boyun, turuncu plaka, iki mil, kelepçe. Kelepçe taban kotunu döndürür."""
    zr_alt = Z_RAY - RH / 2
    # ray içi: gövde + 4 makara (ray ucundan bakınca görünür)
    kutu(name + "_govde", (0.08, YARIK * 0.8, 0.03), (x, Y_RAY, Z_RAY - 0.004), M["galvaniz"], g, bevel=0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            silindir(f"{name}_mak{sx}{sy}", 0.013, 0.012, (x + sx * 0.026, Y_RAY + sy * 0.021, zr_alt + RT + 0.014),
                     M["celik"], g, axis="Y", seg=24)
    kutu(name + "_boyun", (0.03, YARIK * 0.6, 0.035), (x, Y_RAY, zr_alt - 0.004), M["galvaniz"], g, bevel=0.002)
    zp = zr_alt - 0.016
    plaka(name + "_plaka", x, Y_RAY, zp, M, g, s=1.25 if cek else 1.0)
    zk = zp - 0.014 - 0.11            # kelepçe tabanı
    for sy in (-1, 1):
        yy = Y_RAY + sy * 0.042
        silindir(f"{name}_mil{sy}", 0.0045, 0.17, (x, yy, zp - 0.07), M["celik"], g, seg=16)
        silindir(f"{name}_somun{sy}", 0.008, 0.008, (x, yy, zp - 0.012 - 0.004), M["celik"], g, seg=6)
        silindir(f"{name}_somun_alt{sy}", 0.008, 0.008, (x, yy, zk - 0.026), M["celik"], g, seg=6)
    kelepce(name + "_kel", x, Y_RAY, zk, M, g)
    return zk


def serit_kablo(name, pts, gen, kal, mat, g):
    """Yassı kablo: XZ düzleminde çoklu çizgi boyunca dikdörtgen kesitli şerit (genişlik Y'de)."""
    bm = bmesh.new()
    halkalar = []
    for i, p in enumerate(pts):
        a = Vector(pts[max(0, i - 1)])
        b = Vector(pts[min(len(pts) - 1, i + 1)])
        t = (b - a).normalized()
        n = Vector((-t.z, 0, t.x))
        p = Vector(p)
        y = Vector((0, gen / 2, 0))
        k = kal / 2
        halkalar.append([bm.verts.new(p + n * k - y), bm.verts.new(p + n * k + y),
                         bm.verts.new(p - n * k + y), bm.verts.new(p - n * k - y)])
    for r0, r1 in zip(halkalar, halkalar[1:]):
        for j in range(4):
            bm.faces.new([r0[j], r0[(j + 1) % 4], r1[(j + 1) % 4], r1[j]])
    bm.faces.new(halkalar[0])
    bm.faces.new(list(reversed(halkalar[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm_to_mesh(bm, name), mat, g, bevel=0.003, seg=2)


def ilmek(a, b, z, L):
    """a..b arasında boyu L olan sarkık ilmek (U biçimi); derinlik ikiye bölmeyle bulunur."""
    def nokta(D, n=40):
        return [(a + (b - a) * k / n, z - D * math.sin(math.pi * k / n) ** 0.7) for k in range(n + 1)]

    def boy(ps):
        return sum(math.dist(p, q) for p, q in zip(ps, ps[1:]))

    lo, hi = 0.0, L
    for _ in range(40):
        D = (lo + hi) / 2
        if boy(nokta(D)) < L:
            lo = D
        else:
            hi = D
    return nokta(lo)


def festoon_sistemi(M, g, x_ray0, x_ray1, x_sabit, x_cek, n=7, L=1.3):
    c_ray("festoon_ray", x_ray0, x_ray1, Y_RAY, Z_RAY, M, g)
    # rayı ön kirişe bağlayan konsollar (dikme kiriş üst başlığına kaynaklı, kol + ray kelepçesi)
    yk_dis = -(YK + KB / 2 + 0.02)
    k = int((x_ray1 - x_ray0) / 1.5)
    for i in range(k + 1):
        xk = x_ray0 + 0.15 + i * (x_ray1 - x_ray0 - 0.3) / k
        if abs(xk - x_cek) < 0.25:
            continue
        zk = Z_RAY + RH / 2 + 0.035
        kutu(f"festoon_konsol_dikme{i}", (0.06, 0.012, zk - Z_UST + 0.02), (xk, yk_dis, (zk + Z_UST) / 2), M["antrasit"], g,
             bevel=0.002)
        kutu(f"festoon_konsol_kol{i}", (0.06, abs(yk_dis - Y_RAY) + 0.03, 0.012), (xk, (yk_dis + Y_RAY) / 2, zk), M["antrasit"],
             g, bevel=0.002)
        kutu(f"festoon_konsol_tas{i}", (0.06, RB + 0.03, 0.03), (xk, Y_RAY, Z_RAY + RH / 2 + 0.014), M["galvaniz"], g,
             bevel=0.003)
        for sy in (-1, 1):
            silindir(f"festoon_konsol_c{i}{sy}", 0.006, 0.008, (xk, Y_RAY + sy * (RB / 2 + 0.008), Z_RAY + RH / 2 + 0.033),
                     M["celik"], g, seg=6)
    # ray sonu tapaları + ray ucunda beta yazısı
    for xs in (x_ray0, x_ray1):
        kutu(f"festoon_tapa{xs:g}", (0.012, RB + 0.012, RH + 0.012), (xs + (-0.006 if xs == x_ray0 else 0.006), Y_RAY, Z_RAY),
             M["turuncu"], g, bevel=0.002)
    RV.yazi("festoon_logo", "beta", (x_ray0 + 0.22, Y_RAY - RB / 2 - 0.0006, Z_RAY - 0.008), 0.03, M["antrasit"], g,
            extrude=0.0004)
    # arabalar: sabit uçtan çekme arabasına eşit aralık
    xs = [x_sabit + i * (x_cek - x_sabit) / (n - 1) for i in range(n)]
    zk = None
    for i, xa in enumerate(xs):
        zk = araba(f"festoon_araba{i}", xa, M, g, cek=(i == n - 1))
    # kablolar: iki yassı güç/kumanda kablosu, kelepçe üstünde yan yana
    R = 0.07
    for j, (dy, gen, ek) in enumerate(((-0.026, 0.044, 0.0), (0.026, 0.036, 0.06))):
        zt = zk + R * 0.62 * math.sqrt(max(0.0, 1 - (dy / R) ** 2)) + 0.007
        pts = []
        for i in range(n):
            a = xs[i]
            pts += [(a - 0.05, zt), (a + 0.05, zt)]
            if i < n - 1:
                pts += ilmek(a + 0.05, xs[i + 1] - 0.05, zt, L + ek)[1:-1]
        serit_kablo(f"festoon_kablo{j}", [(p[0], 0, p[1]) for p in pts], gen, 0.012, M["siyah"], g)
        o = bpy.data.objects[f"festoon_kablo{j}"]
        o.location.y = Y_RAY + dy
    # besleme ucu: kiriş üstünde buat kutusu; sabit kelepçeden kutuya kısa kablo, kutudan besleme kablosu
    yb = -(YK + KB / 2) + 0.10
    kutu("festoon_buat", (0.30, 0.16, 0.26), (x_sabit - 0.10, yb, Z_UST + 0.13), M["antrasit"], g, bevel=0.012)
    kutu("festoon_buat_kapak", (0.26, 0.004, 0.22), (x_sabit - 0.10, yb - 0.082, Z_UST + 0.13), M["gri"], g, bevel=0.002)
    for k in range(2):
        boru(f"festoon_giris{k}", (x_sabit - 0.12, Y_RAY + (k - 0.5) * 0.052, zk + 0.02),
             (x_sabit - 0.16, yb - 0.08, Z_UST + 0.06), 0.012, M["siyah"], g)
    boru("festoon_besleme", (x_sabit - 0.22, yb, Z_UST + 0.13), (-0.5, yb, Z_UST + 0.13), 0.016, M["siyah"], g)
    return xs


def cekme_kolu(M, g, x, z_araba):
    """Vinç arabasının panosundan çekme arabasına L kol."""
    y_pano = -(YK + 0.25) - 0.21
    zk = Z_RAY + RH / 2 + 0.10
    kutu("festoon_cekme_kol", (0.05, abs(y_pano - (Y_RAY - 0.075)), 0.05), (x, (y_pano + Y_RAY - 0.075) / 2, zk),
         M["antrasit"], g, bevel=0.004)
    kutu("festoon_cekme_dik", (0.05, 0.05, zk - (Z_RAY - RH / 2 - 0.03)), (x, Y_RAY - 0.075, (zk + Z_RAY - RH / 2 - 0.03) / 2),
         M["antrasit"], g, bevel=0.004)
    kutu("festoon_cekme_pabuc", (0.05, 0.075, 0.012), (x, Y_RAY - 0.04, Z_RAY - RH / 2 - 0.03), M["antrasit"], g, bevel=0.002)
    kutu("festoon_cekme_ayak", (0.06, 0.05, zk - z_araba), (x, y_pano + 0.02, (zk + z_araba) / 2), M["antrasit"], g, bevel=0.004)


def kopru_vinc(M):
    g = RV.bos("kopru", (0, 0, 0))
    RV.kutu_kiris("kiris_on", 0, SPAN, -YK, Z_UST, KH, KB, M, g, logo_yuzu=True)
    RV.kutu_kiris("kiris_arka", 0, SPAN, YK, Z_UST, KH, KB, M, g)
    # uç kirişler (baş arabası kutuları) ve kiriş birleşimleri
    for ad, x in (("sol", 0.0), ("sag", SPAN)):
        RV.bas_araba(f"bas_{ad}", x, -1.5, 1.5, M, g, z=ZR)
        for sy in (-1, 1):
            kutu(f"birlesim_{ad}{sy}", (0.42, KB + 0.04, 0.03), (x, sy * YK, ZR + 0.635), M["antrasit"], g, bevel=0.003)
            RV.civata_izgara(f"birlesim_c_{ad}{sy}", (x, sy * YK, ZR + 0.652), (1, 0, 0), (0, 1, 0), 2, 3, 0.3, 0.14,
                             "Z", M, g, r=0.013)
    # yürüyüş yolu: ray, kiriş, betonarme kolon + konsol
    beton = RV.beton_dokusu()
    for ad, x in (("sol", 0.0), ("sag", SPAN)):
        kutu(f"ray_{ad}_mantar", (0.07, 8.6, 0.05), (x, 0, ZR - 0.025), M["ray"], bevel=0.004)
        kutu(f"ray_{ad}_kiris_ust", (0.32, 8.6, 0.025), (x, 0, ZR - 0.0625), M["antrasit"], bevel=0.003)
        kutu(f"ray_{ad}_kiris_govde", (0.016, 8.6, 0.55), (x, 0, ZR - 0.35), M["antrasit"], bevel=0.002)
        kutu(f"ray_{ad}_kiris_alt", (0.32, 8.6, 0.025), (x, 0, ZR - 0.6375), M["antrasit"], bevel=0.003)
        sx = -1 if x == 0 else 1
        for i, y in enumerate((-3.8, 3.8)):
            kutu(f"bina_kolon_{ad}{i}", (0.6, 0.6, ZR + 1.6), (x + sx * 0.75, y, (ZR + 1.6) / 2), beton, bevel=0.01)
            kutu(f"bina_konsol_{ad}{i}", (1.0, 0.6, 0.5), (x + sx * 0.25, y, ZR - 0.9), beton, bevel=0.01)
        for sy in (-1, 1):
            kutu(f"ray_stop_{ad}{sy}", (0.25, 0.2, 0.3), (x, sy * 4.2, ZR + 0.15), M["antrasit"], bevel=0.01)
    RV.halatli_araba("araba", X_ARABA, Z_UST + 0.05, YK, M, g, kanca_z=3.4)
    xs = festoon_sistemi(M, g, 0.15, SPAN - 0.15, X_SABIT, X_ARABA - 0.15)
    cekme_kolu(M, g, X_ARABA - 0.15, Z_UST + 0.11)
    zp = Z_RAY - RH / 2 - 0.03
    ETIKET.update(
        ray=(8.4, Y_RAY, Z_RAY), araba=(xs[2], Y_RAY, zp), kablo=((xs[3] + xs[4]) / 2, Y_RAY, zp - 0.7),
        cekme=(xs[-1], Y_RAY - 0.075, Z_RAY + 0.1), buat=(X_SABIT - 0.10, -(YK + KB / 2) + 0.10, Z_UST + 0.2),
        konsol=(10.6, -(YK + KB / 2 + 0.02), Z_UST + 0.3))
    return g, xs


def sahne_genel(M):
    kopru_vinc(M)
    RV.kamera((SPAN * 0.5 - 2.5, -17.5, 4.2), (SPAN * 0.5 - 0.3, 0, Z_UST - 1.5), lens=37, kaydir=True)
    RV.anahtar_isik((4, -12, 12), (5, 0, 6), 3500, boyut=8)


def sahne_detay(M):
    _, xs = kopru_vinc(M)
    # fotoğraftaki gibi: ray ucunun hemen önünden, hafif alttan, ray boyunca bakış
    hedef = (2.6, Y_RAY + 0.05, Z_RAY - 0.35)
    RV.kamera((-0.75, Y_RAY - 0.95, Z_RAY - 0.42), hedef, lens=30, dof=None)
    RV.anahtar_isik((-2, -4, Z_RAY + 3), hedef, 600, boyut=3)


SAHNELER = {"genel": sahne_genel, "detay": sahne_detay}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sahne, cikti = argv[0], argv[1]
    ornek = int(argv[2]) if len(argv) > 2 else 512
    RV.sifirla()
    RV.MATS.clear()
    RV.FONT = RV.font_yukle()
    M = RV.malzemeler()
    RV.FOTOLAR.clear()
    RV.dunya(0.4)
    SAHNELER[sahne](M)
    RV.studyo_isiklari()
    RV.render_ayarlari(cikti, ornek)
    bpy.ops.render.render(write_still=True)
    RV.fotolari_ekle(cikti)
    # açıklama noktalarının görüntü koordinatları (pafta için)
    import json
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    nok = {}
    for ad, p in ETIKET.items():
        q = world_to_camera_view(sc, sc.camera, Vector(p))
        nok[ad] = (q.x, 1 - q.y)
    with open(os.path.splitext(cikti)[0] + "_noktalar.json", "w") as f:
        json.dump(nok, f, indent=1)


if __name__ == "__main__":
    main()
