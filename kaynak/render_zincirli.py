"""
Beta Vinç - elektrikli zincirli vinç ürün fotoğrafları (Blender / bpy, Cycles, beyaz stüdyo zemin).

Kapasiteler: 500 kg, 1 t, 2 t, 3 t (3 t çift halat düşüşlü: kanca bloğunda makara).
Tipler: sabit (üst askı kancalı) ve monoray (I profil alt başlığında yürüyen elektrikli araba).
Zincir torbası: yumuşak kumaş (PVC kaplı branda) - drape kıvrımları, alt kısımda zincir ağırlığıyla
şişkinlik, köşe biyeleri, üst dikiş bandı ve dokuma kumaş dokusu.

Kullanım:
    python render_zincirli.py <500kg|1t|2t|3t> <sabit|monoray> <cikti.png> [ornek_sayisi]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,I001
import bmesh  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

import render_vincler as RV  # noqa: E402

kutu, silindir, boru, obj, bm_to_mesh, kablo = RV.kutu, RV.silindir, RV.boru, RV.obj, RV.bm_to_mesh, RV.kablo
KLASOR = os.path.dirname(os.path.abspath(__file__))

# kapasite -> (genel ölçek, motor boyu, torba boyu, zincir tel çapı, etiket, düşüş sayısı)
KAPASITE = {
    "500kg": (0.86, 0.22, 0.30, 0.0063, "500 kg", 1),
    "1t": (1.00, 0.26, 0.36, 0.0071, "1 t", 1),
    "2t": (1.12, 0.30, 0.42, 0.0090, "2 t", 1),
    "3t": (1.22, 0.32, 0.46, 0.0090, "3 t", 2),
}


# ---------------------------------------------------------------- malzemeler
def kumas_mat():
    """PVC kaplı branda: dokuma bump + büyük ölçekli kırışık bump, satenimsi parlaklık."""
    if "kumas" in RV.MATS:
        return RV.MATS["kumas"]
    m = bpy.data.materials.new("kumas")
    nt = RV.node_tree(m)
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = RV.srgb("#D88C1F")
    b.inputs["Roughness"].default_value = 0.62
    for ad, v in (("Sheen Weight", 0.35), ("Sheen Roughness", 0.5)):
        try:
            b.inputs[ad].default_value = v
        except Exception:
            pass
    tc = nt.nodes.new("ShaderNodeTexCoord")
    dalga = []
    for yon in ("X", "Z"):
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = yon
        w.inputs["Scale"].default_value = 260.0
        w.inputs["Distortion"].default_value = 1.5
        nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
        dalga.append(w)
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    nt.links.new(dalga[0].outputs["Fac"], mx.inputs[0])
    nt.links.new(dalga[1].outputs["Fac"], mx.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.22
    bp.inputs["Distance"].default_value = 0.0006
    nt.links.new(mx.outputs["Value"], bp.inputs["Height"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp2 = nt.nodes.new("ShaderNodeBump")
    bp2.inputs["Strength"].default_value = 0.18
    bp2.inputs["Distance"].default_value = 0.004
    nt.links.new(nz.outputs["Fac"], bp2.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bp2.inputs["Normal"])
    nt.links.new(bp2.outputs["Normal"], b.inputs["Normal"])
    # hafif renk dalgalanması (kumaşta solma/kirlenme)
    mr = nt.nodes.new("ShaderNodeMixRGB")
    mr.blend_type = "MULTIPLY"
    mr.inputs["Fac"].default_value = 0.12
    mr.inputs["Color1"].default_value = RV.srgb("#D88C1F")
    nt.links.new(nz.outputs["Color"], mr.inputs["Color2"])
    nt.links.new(mr.outputs["Color"], b.inputs["Base Color"])
    m.diffuse_color = RV.srgb("#D88C1F")
    RV.MATS["kumas"] = m
    return m


def malzemeler():
    M = RV.malzemeler()
    M["kumas"] = kumas_mat()
    M["plastik"] = RV.boya("plastik_siyah", (0.03, 0.03, 0.032, 1), rough=0.45, var=0.06, bump=0.02)
    M["zincir"] = RV.boya("zincir", (0.06, 0.062, 0.065, 1), rough=0.32, metal=0.85, var=0.1)
    M["sari"] = RV.boya("butonyer_sari", RV.srgb("#F2C200"), rough=0.35, coat=0.2, var=0.05)
    M["kirmizi"] = RV.boya("buton_kirmizi", RV.srgb("#D62B1E"), rough=0.3, coat=0.3, var=0.03)
    M["yesil"] = RV.boya("buton_yesil", RV.srgb("#2FA84F"), rough=0.3, coat=0.3, var=0.03)
    M["aluminyum"] = RV.fircali_celik(RV.boya("aluminyum", (0.78, 0.79, 0.8, 1), rough=0.3, metal=1.0, var=0.05))
    M["profil"] = RV.boya("profil", (0.36, 0.37, 0.39, 1), rough=0.4, metal=0.6, var=0.1, bump=0.04)
    M["beyaz_yazi"] = RV.boya("beyaz_yazi", (0.9, 0.9, 0.9, 1), rough=0.35, var=0.02)
    M["turuncu_yazi"] = RV.boya("turuncu_yazi", RV.BETA_TURUNCU, rough=0.3, var=0.02)
    return M


# ---------------------------------------------------------------- yardımcılar
def logo(name, loc, gen, rot, mat, parent=None, kalinlik=0.0015):
    """Gerçek 'beta' işareti (potrace geojson) kabartma; gen: genişlik (m)."""
    g = json.load(open(os.path.join(KLASOR, "logo", "beta_isaret.geojson")))
    xs = [p[0] for f in g["features"] for r in f["geometry"]["coordinates"] for p in r]
    ys = [p[1] for f in g["features"] for r in f["geometry"]["coordinates"] for p in r]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = gen / (max(xs) - min(xs))
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = kalinlik
    for f in g["features"]:
        for ring in f["geometry"]["coordinates"]:
            sp = cu.splines.new("POLY")
            pts = ring[:-1] if ring[0] == ring[-1] else ring
            sp.points.add(len(pts) - 1)
            for p, q in zip(sp.points, pts):
                p.co = ((q[0] - cx) * k, (q[1] - cy) * k, 0, 1)
            sp.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    o.parent = parent
    return o


def yazi(name, metin, loc, boy, mat, parent, rot):
    o = RV.yazi(name, metin, loc, boy, mat, parent, rot=rot, extrude=0.0008)
    return o


def zincir(name, x, y, z_ust, z_alt, d, M, parent):
    """Kalibre yük zinciri: stadyum biçimli halkalar (tel çapı d, adım 3d), ardışık halkalar 90° döner."""
    p = 3.0 * d
    w = 0.675 * d + d / 2           # merkez çizgisi yarı genişliği
    duz = max(0.0, p - 1.35 * d)    # düz kısım boyu
    rc = w
    merkez = []
    n_yay = 14
    for side in (1, -1):
        for i in range(n_yay + 1):
            a = math.pi * i / n_yay
            merkez.append((side * rc * math.cos(a), 0.0, side * (duz / 2 + rc * math.sin(a))))
    bm = bmesh.new()
    halkalar = []
    seg = 10
    N = len(merkez)
    for i, c in enumerate(merkez):
        c = Vector(c)
        t = (Vector(merkez[(i + 1) % N]) - Vector(merkez[i - 1])).normalized()
        u = Vector((0, 1, 0))
        v = t.cross(u).normalized()
        halkalar.append([bm.verts.new(c + (u * math.cos(2 * math.pi * j / seg) + v * math.sin(2 * math.pi * j / seg)) * d / 2)
                         for j in range(seg)])
    for i in range(N):
        r0, r1 = halkalar[i], halkalar[(i + 1) % N]
        for j in range(seg):
            bm.faces.new((r0[j], r0[(j + 1) % seg], r1[(j + 1) % seg], r1[j]))
    me = bm_to_mesh(bm, name + "_halka")
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(M["zincir"])
    n = int((z_ust - z_alt) / p)
    for i in range(n):
        o = bpy.data.objects.new(f"{name}_{i}", me)
        bpy.context.scene.collection.objects.link(o)
        o.location = (x, y, z_ust - i * p - p / 2)
        o.rotation_euler = (0, 0, (math.pi / 2) * (i % 2))
        o.parent = parent
    return z_ust - n * p


def yay(name, x, y, z_ust, z_alt, r, tel, M, parent, tur=11):
    pts = []
    n = tur * 24
    for i in range(n + 1):
        a = 2 * math.pi * i / 24
        pts.append((x + r * math.cos(a), y + r * math.sin(a), z_ust - (z_ust - z_alt) * i / n))
    return kablo(name, pts, tel, M["plastik"], parent)


def ucgen(name, loc, boy, yon, mat, parent):
    """-Y yüzüne bakan küçük üçgen ok (butonyer düğmeleri için); yon: 'yukari'/'asagi'/'sol'/'sag'."""
    aci = {"yukari": 0, "sag": -math.pi / 2, "asagi": math.pi, "sol": math.pi / 2}[yon]
    bm = bmesh.new()
    pts = [(0, boy * 0.6), (-boy * 0.5, -boy * 0.35), (boy * 0.5, -boy * 0.35)]
    alt = [bm.verts.new((px * math.cos(aci) - pz * math.sin(aci), 0.0, px * math.sin(aci) + pz * math.cos(aci))) for px, pz in pts]
    ust = [bm.verts.new(v.co + Vector((0, -0.002, 0))) for v in alt]
    bm.faces.new(alt)
    bm.faces.new(list(reversed(ust)))
    for i in range(3):
        bm.faces.new((alt[i], alt[(i + 1) % 3], ust[(i + 1) % 3], ust[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj(name, bm_to_mesh(bm, name), mat, parent)
    o.location = loc
    return o


# ---------------------------------------------------------------- zincir torbası
def torba(name, cx, cy, z_ust, boy, en, der, M, parent):
    """Kumaş zincir torbası: yuvarlak köşeli dikdörtgen kesit, drape kıvrımları, altta şişkinlik."""
    rk = 0.032                      # köşe yarıçapı
    nu, nv = 96, 70
    seed = Vector((3.1, 7.7, 1.3))

    def kesit(t):
        """Çevre parametresi t (0..1) -> (x, y, dış normal) yuvarlak köşeli dikdörtgen."""
        a, b = en / 2 - rk, der / 2 - rk
        L = 4 * a + 4 * b + 2 * math.pi * rk
        s = t * L
        parca = [(2 * b, "d"), (math.pi * rk / 2, "k"), (2 * a, "d"), (math.pi * rk / 2, "k")] * 2
        merkez = [(a, 0), (a, b), (0, b), (-a, b), (-a, 0), (-a, -b), (0, -b), (a, -b)]
        aci0 = [0, 0, math.pi / 2, math.pi / 2, math.pi, math.pi, 3 * math.pi / 2, 3 * math.pi / 2]
        s0 = s - b  # sağ kenar ortasından başla
        if s0 < 0:
            s0 += L
        for i, (uz, tip) in enumerate(parca):
            if s0 <= uz or i == len(parca) - 1:
                n_ = (math.cos(aci0[i]), math.sin(aci0[i]))
                if tip == "k":
                    a_ = aci0[i] + s0 / rk
                    mx, my = merkez[i]
                    n_ = (math.cos(a_), math.sin(a_))
                    return mx + rk * n_[0], my + rk * n_[1], n_
                mx, my = merkez[i]
                tx, ty = -n_[1], n_[0]
                pos = s0 - uz / 2
                return mx + rk * n_[0] + tx * pos, my + rk * n_[1] + ty * pos, n_
            s0 -= uz
        return a + rk, 0, (1, 0)

    bm = bmesh.new()
    satir = []
    for j in range(nv + 1):
        v = j / nv                       # 0 üst, 1 alt
        z = z_ust - v * boy
        sis = 1 + 0.16 * math.sin(math.pi * min(1, v / 0.92) * 0.5) ** 2 * (v ** 1.5)    # zincir ağırlığı
        alt_yuv = 1.0 if v < 0.86 else math.cos((v - 0.86) / 0.14 * math.pi / 2) ** 0.55 + 0.02
        ring = []
        for i in range(nu):
            t = i / nu
            px, py, (nx, ny) = kesit(t)
            k = sis * max(0.03, alt_yuv)
            px, py = px * k, py * k
            # drape kıvrımları: üstte sık, aşağıda seyrek ve yumuşak
            kiv = 0.0075 * math.sin(2 * math.pi * t * 14 + 1.6 * noise.noise(Vector((t * 4, v * 3, 0)) + seed)) * \
                math.exp(-v * 4) + 0.0065 * math.sin(2 * math.pi * t * 5 + 2.0 + 0.8 * noise.noise(Vector((t * 2, v, 5)))) * \
                math.sin(math.pi * v) * (1 - 0.6 * v)
            dz = 0.0
            p3 = Vector((px * 18, py * 18, z * 12)) + seed
            yum = noise.noise(p3) * 0.0065 + noise.noise(p3 * 2.7) * 0.0022
            px += nx * (kiv + yum)
            py += ny * (kiv + yum)
            if v > 0.95:
                dz = -0.004 * (v - 0.95) / 0.05
            ring.append(bm.verts.new((cx + px, cy + py, z + dz)))
        satir.append(ring)
    for j in range(nv):
        for i in range(nu):
            a, b_ = satir[j][i], satir[j][(i + 1) % nu]
            c, d = satir[j + 1][(i + 1) % nu], satir[j + 1][i]
            bm.faces.new((a, b_, c, d))
    alt_m = bm.verts.new((cx, cy, z_ust - boy - 0.005))
    for i in range(nu):
        bm.faces.new((satir[nv][(i + 1) % nu], alt_m, satir[nv][i]))
    koord = [[tuple(v.co) for v in r] for r in satir]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj(name, bm_to_mesh(bm, name), M["kumas"], parent, smooth=True)
    for poly in o.data.polygons:
        poly.use_smooth = True
    sub = o.modifiers.new("subsurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    # köşe biyeleri (dikiş kenarları) ve üst dikiş bandı
    for kk, (qx, qy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        i = max(range(nu), key=lambda i: qx * (koord[0][i][0] - cx) / en + qy * (koord[0][i][1] - cy) / der)
        pts = [koord[j][i] for j in range(0, int(nv * 0.9))]
        kablo(f"{name}_biye{kk}", pts, 0.0035, M["kumas"], parent)
    bant = [koord[3][i] for i in range(nu)] + [koord[3][0]]
    kablo(f"{name}_bant", bant, 0.003, M["plastik"], parent)
    return o


# ---------------------------------------------------------------- vinç
def vinc(M, g, kap, monoray):
    s, Lm, torba_boy, d, etiket, dus = KAPASITE[kap]
    T, A, P = M["turuncu"], M["antrasit"], M["plastik"]
    zc = -0.16                              # gövde ekseni kotu
    # orta gövde (yük dişlisi yuvası)
    kutu("vinc_orta", (0.17, 0.23, 0.27), (0, 0, zc + 0.005), T, g, bevel=0.03)
    for sy in (-1, 1):
        kutu(f"vinc_orta_ny{sy}", (0.19, 0.012, 0.022), (0, sy * 0.118, zc + 0.10), T, g, bevel=0.006)
    # redüktör gövdesi (+X) ve alın paneli (logo + kapasite)
    xr = 0.085 + 0.12
    kutu("vinc_red", (0.24, 0.26, 0.31), (xr, 0, zc), T, g, bevel=0.045)
    kutu("vinc_red_kusak", (0.03, 0.272, 0.322), (0.105, 0, zc), T, g, bevel=0.012)
    xe = xr + 0.12
    kutu("vinc_panel", (0.008, 0.19, 0.22), (xe + 0.002, 0, zc + 0.01), P, g, bevel=0.004)
    rot_x = (math.pi / 2, 0, math.pi / 2)
    logo("vinc_logo", (xe + 0.0068, 0.0, zc + 0.055), 0.145, rot_x, M["turuncu_yazi"], g)
    yazi("vinc_kap", etiket, (xe + 0.0066, 0.0, zc - 0.045), 0.05 if len(etiket) > 3 else 0.065, M["beyaz_yazi"], g, rot_x)
    # yan yüz: alüminyum künye plakası, uyarı etiketi, kapasite etiketi
    yk = -0.131
    kutu("vinc_kunye", (0.11, 0.003, 0.07), (xr + 0.02, yk, zc - 0.07), M["aluminyum"], g, bevel=0.001)
    for k in range(4):
        kutu(f"vinc_kunye_c{k}", (0.085, 0.001, 0.003), (xr + 0.02, yk - 0.0018, zc - 0.05 - k * 0.013), A, g, bevel=0)
    yazi("vinc_kunye_y", "beta", (xr - 0.012, yk - 0.002, zc - 0.044), 0.011, A, g, (math.pi / 2, 0, 0))
    kutu("vinc_uyari", (0.05, 0.003, 0.065), (0.0, -0.1165, zc + 0.04), M["sari"], g, bevel=0.001)
    ucgen("vinc_uyari_ok", (0.0, -0.1185, zc + 0.045), 0.03, "yukari", P, g)
    kutu("vinc_kapet", (0.045, 0.003, 0.065), (0.052, -0.1165, zc + 0.04), P, g, bevel=0.001)
    yazi("vinc_kapet_y", etiket.replace(" ", "\n"), (0.052, -0.1185, zc + 0.04), 0.017, M["beyaz_yazi"], g, (math.pi / 2, 0, 0))
    # motor (-X): gövde, eksenel soğutma kanatları, fan kapağı
    xm0 = -0.085
    rm = 0.118
    silindir("vinc_motor", rm, Lm, (xm0 - Lm / 2, 0, zc), T, g, axis="X", bevel=0.006)
    nk = 20
    for k in range(nk):
        a = 2 * math.pi * k / nk
        o = kutu(f"vinc_kanat{k}", (Lm - 0.03, 0.006, 0.02), (xm0 - Lm / 2 - 0.005, 0, 0), T, g, bevel=0.002)
        o.location = (xm0 - Lm / 2 - 0.005, math.cos(a) * (rm + 0.008), zc + math.sin(a) * (rm + 0.008))
        o.rotation_euler = (a - math.pi / 2, 0, 0)
    silindir("vinc_halka", rm + 0.019, 0.014, (xm0 - 0.012, 0, zc), T, g, axis="X", bevel=0.004)
    xf = xm0 - Lm
    silindir("vinc_fan", rm - 0.006, 0.05, (xf - 0.02, 0, zc), T, g, axis="X", bevel=0.012)
    silindir("vinc_fan_kubbe", rm - 0.012, 0.045, (xf - 0.065, 0, zc), T, g, axis="X", bevel=0.012, r2=rm - 0.045)
    # klemens kutusu (motor üstü) + rakor
    kutu("vinc_klemens", (0.15, 0.13, 0.065), (xm0 - Lm * 0.45, 0, zc + rm + 0.03), T, g, bevel=0.014)
    silindir("vinc_rakor", 0.012, 0.03, (xm0 - Lm * 0.45 + 0.06, -0.068, zc + rm + 0.03), P, g, axis="Y")
    # askı kulakları (üstte)
    for sy in (-1, 1):
        kutu(f"vinc_kulak{sy}", (0.11, 0.014, 0.08), (0, sy * 0.032, zc + 0.165), T, g, bevel=0.01)
    silindir("vinc_pim", 0.017, 0.10, (0, 0, zc + 0.18), M["celik"], g, axis="Y")
    # zincir çıkışı + kılavuz
    xz = 0.075
    kutu("vinc_kilavuz", (0.07, 0.06, 0.04), (xz, -0.02, zc - 0.155), P, g, bevel=0.008)
    # zincir torbası (altta, gövde ortasında) + üst plastik çerçeve + taşıma braketi
    tx, ty = -0.075, 0.015
    ten, tder = 0.20 * (0.92 + 0.08 * s), 0.17 * (0.92 + 0.08 * s)
    zt = zc - 0.20
    kutu("torba_braket", (0.03, 0.03, 0.06), (tx + 0.04, ty, zc - 0.16), A, g, bevel=0.004)
    kutu("torba_cerceve", (ten + 0.02, tder + 0.02, 0.05), (tx, ty, zt + 0.005), P, g, bevel=0.012)
    kutu("torba_cerceve_ust", (ten - 0.02, tder - 0.02, 0.02), (tx, ty, zt + 0.035), P, g, bevel=0.008)
    torba("torba", tx, ty, zt - 0.018, torba_boy, ten, tder, M, g)
    # yük zinciri, yay tamponu, kanca bloğu, kanca
    kanca_ust = zc - 0.75 - 0.25 * s
    xs = [xz] if dus == 1 else [xz - 0.032, xz + 0.032]
    for i, x in enumerate(xs):
        zincir(f"vinc_zincir{i}", x, -0.02, zc - 0.175, kanca_ust + 0.04, d, M, g)
    yay("vinc_yay", xz, -0.02, kanca_ust + 0.24, kanca_ust + 0.075, 0.024 if dus == 1 else 0.055, 0.0032, M, g)
    kutu("vinc_yay_pul", (0.05 if dus == 1 else 0.11, 0.05, 0.008), (xz, -0.02, kanca_ust + 0.072), M["celik"], g, bevel=0.002)
    bw = 0.085 if dus == 1 else 0.15
    kutu("blok", (bw, 0.075, 0.11), (xz, -0.02, kanca_ust), T, g, bevel=0.018)
    for sx in (-1, 1):
        kutu(f"blok_kanat{sx}", (0.012, 0.08, 0.09), (xz + sx * (bw / 2 - 0.004), -0.02, kanca_ust), T, g, bevel=0.004)
    if dus == 2:
        silindir("blok_makara_gobek", 0.02, 0.07, (xz, -0.02, kanca_ust + 0.01), M["celik"], g, axis="Y")
    kutu("blok_etiket", (bw * 0.62, 0.003, 0.065), (xz, -0.0585, kanca_ust - 0.005), P, g, bevel=0.001)
    yazi("blok_etiket_y", etiket.replace(" ", "\n"), (xz, -0.0605, kanca_ust - 0.005), 0.02, M["beyaz_yazi"], g,
         (math.pi / 2, 0, 0))
    RV.kanca("kanca", (xz, -0.02, kanca_ust - 0.055), 0.50 + (0.12 if dus == 2 else 0.0), M, g)
    # butonyer kablosu ve butonyer
    xb, yb = xr + 0.06, -0.075
    zb = kanca_ust + 0.05
    pts = []
    for i in range(25):
        t = i / 24
        pts.append((xb + 0.015 * math.sin(t * math.pi), yb - 0.01 * t, lerp(zc - 0.16, zb + 0.17, t)))
    kablo("butonyer_kablo", pts, 0.0065, P, g)
    kablo("butonyer_celik", [(xb + 0.012, yb + 0.004, zc - 0.16), (xb + 0.012, yb + 0.004, zb + 0.17)], 0.0012, M["celik"], g)
    kutu("butonyer_bas", (0.05, 0.05, 0.035), (xb, yb, zb + 0.165), M["plastik"], g, bevel=0.01)
    kutu("butonyer", (0.072, 0.062, 0.30), (xb, yb, zb), M["sari"], g, bevel=0.016)
    kutu("butonyer_alt", (0.06, 0.05, 0.03), (xb, yb, zb - 0.16), M["plastik"], g, bevel=0.01)
    yf = yb - 0.031
    silindir("butonyer_stop", 0.016, 0.014, (xb, yf - 0.004, zb + 0.11), M["kirmizi"], g, axis="Y", bevel=0.004)
    silindir("butonyer_start", 0.011, 0.008, (xb, yf - 0.002, zb + 0.07), M["yesil"], g, axis="Y", bevel=0.002)
    oklar = ["yukari", "asagi"] + (["sol", "sag"] if monoray else [])
    for k, yon in enumerate(oklar):
        z = zb + 0.025 - k * 0.042
        silindir(f"butonyer_b{k}", 0.014, 0.008, (xb, yf - 0.002, z), P, g, axis="Y", bevel=0.002)
        ucgen(f"butonyer_ok{k}", (xb, yf - 0.0065, z), 0.012, yon, M["beyaz_yazi"], g)
    logo("butonyer_logo", (xb, yf - 0.0005, zb - 0.125), 0.045, (math.pi / 2, 0, 0), P, g, kalinlik=0.0006)
    # askı: sabit -> üst kanca, monoray -> elektrikli araba + I profil
    if not monoray:
        e = RV.bos("ust_kanca", (0, 0, zc + 0.205), (0, math.pi, 0))
        e.parent = g
        RV.kanca("ust_kanca_k", (0, 0, 0), 0.50, M, e)
    else:
        araba(M, g, zc + 0.205, s, etiket)
    return kanca_ust


def lerp(a, b, t):
    return a + (b - a) * t


def araba(M, g, z_pim, s, etiket):
    """I profil alt başlığında yürüyen elektrikli araba: yan levhalar, 4 tekerlek, yürütme motoru, pano."""
    T, A, P = M["turuncu"], M["antrasit"], M["plastik"]
    b, tf, h, tw = 0.14 + 0.03 * (s - 0.86) / 0.36, 0.014, 0.26, 0.009
    zb = z_pim + 0.17                     # alt başlık alt yüzü
    L = 2.4
    kutu("profil_alt", (L, b, tf), (0, 0, zb + tf / 2), M["profil"], g, bevel=0.002)
    kutu("profil_ust", (L, b, tf), (0, 0, zb + h - tf / 2), M["profil"], g, bevel=0.002)
    kutu("profil_govde", (L, tw, h - 2 * tf), (0, 0, zb + h / 2), M["profil"], g, bevel=0.001)
    r = 0.05
    yp = b / 2 + 0.03
    for sy in (-1, 1):
        kutu(f"araba_levha{sy}", (0.36, 0.016, 0.25), (0, sy * yp, zb + 0.03), T, g, bevel=0.006)
        for sx in (-1, 1):
            silindir(f"araba_tek{sy}{sx}", r, 0.03, (sx * 0.12, sy * (b / 4 + 0.012), zb + tf + r), M["celik"], g, axis="Y", bevel=0.003)
            silindir(f"araba_tekfl{sy}{sx}", r + 0.008, 0.006, (sx * 0.12, sy * (b / 2 - 0.004), zb + tf + r), M["celik"], g, axis="Y")
            RV.civata(f"araba_aks{sy}{sx}", (sx * 0.12, sy * (yp + 0.008), zb + tf + r), "Y" if sy > 0 else "-Y", M, g, r=0.012)
        RV.civata_izgara(f"araba_levhac{sy}", (0, sy * (yp + 0.008), zb - 0.06), (1, 0, 0), (0, 0, 1), 3, 1, 0.09, 0.0,
                         "Y" if sy > 0 else "-Y", M, g, r=0.009)
    kutu("araba_travers", (0.16, 2 * yp + 0.04, 0.05), (0, 0, zb - 0.07), T, g, bevel=0.008)
    for sy in (-1, 1):
        RV.civata(f"araba_traversc{sy}", (0, sy * (yp + 0.028), zb - 0.07), "Y" if sy > 0 else "-Y", M, g, r=0.012)
    kutu("araba_ayna", (0.06, 0.05, 0.11), (0, 0, z_pim + 0.065), T, g, bevel=0.008)
    # yürütme motoru + redüktör (+Y levha dışında), pano (-Y levha dışında, kameraya dönük)
    kutu("araba_red", (0.13, 0.10, 0.14), (-0.13, yp + 0.06, zb + 0.04), T, g, bevel=0.016)
    silindir("araba_motor", 0.058, 0.15, (-0.13, yp + 0.17, zb + 0.04), T, g, axis="Y", bevel=0.006)
    for k in range(8):
        silindir(f"araba_motor_k{k}", 0.064, 0.006, (-0.13, yp + 0.11 + k * 0.016, zb + 0.04), T, g, axis="Y")
    kutu("araba_pano", (0.26, 0.10, 0.17), (0.02, -(yp + 0.06), zb + 0.06), T, g, bevel=0.014)
    kutu("araba_pano_kapak", (0.24, 0.004, 0.15), (0.02, -(yp + 0.111), zb + 0.06), T, g, bevel=0.004)
    kutu("araba_uyari", (0.045, 0.002, 0.045), (0.11, -(yp + 0.114), zb + 0.1), M["sari"], g, bevel=0.0008)
    ucgen("araba_uyari_ok", (0.11, -(yp + 0.1155), zb + 0.1), 0.022, "yukari", P, g)
    kutu("araba_kunye", (0.10, 0.002, 0.06), (-0.02, -(yp + 0.114), zb + 0.08), P, g, bevel=0.0008)
    yazi("araba_kunye_y", etiket, (-0.02, -(yp + 0.1156), zb + 0.08), 0.022, M["turuncu_yazi"], g, (math.pi / 2, 0, 0))
    for k in range(2):
        silindir(f"araba_rakor{k}", 0.011, 0.025, (-0.05 + k * 0.06, -(yp + 0.06), zb - 0.025), P, g)
    # pano - vinç arası besleme kablosu (sarkık ilmek)
    pts = []
    for i in range(41):
        t = i / 40
        x = lerp(-0.05, -0.19, t)
        y = lerp(-(yp + 0.06), 0.07, t ** 0.6)
        z = lerp(zb - 0.035, z_pim - 0.205 - 0.16 + 0.12 + 0.065, t) - 0.26 * math.sin(math.pi * t) ** 1.3
        pts.append((x, y, z))
    kablo("araba_kablo", pts, 0.008, P, g)


# ---------------------------------------------------------------- sahne
def sahne(M, kap, tip):
    g = RV.bos("vinc", (0, 0, 0))
    kanca_ust = vinc(M, g, kap, tip == "monoray")
    s = KAPASITE[kap][0]
    g.scale = (s, s, s)
    bpy.context.view_layer.update()
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o in bpy.context.scene.objects:
        if o.type in {"MESH", "CURVE", "FONT"} and not o.name.startswith("profil"):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
    if tip == "monoray":
        hi.z += 0.22 * s
    mrk = (lo + hi) / 2
    yuk = hi.z - lo.z
    lens = 85
    fov = 2 * math.atan(18 / lens)
    D = (yuk / 2) / math.tan(fov / 2) / 0.86
    yon = Vector((0.62, -1.0, 0.10)).normalized()
    RV.kamera(tuple(mrk + yon * D), tuple(mrk), lens=lens, kaydir=True)
    RV.anahtar_isik(tuple(mrk + Vector((-2, -3, 3))), tuple(mrk), 300, boyut=2)
    return kanca_ust


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    kap, tip, cikti = argv[0], argv[1], argv[2]
    ornek = int(argv[3]) if len(argv) > 3 else 384
    RV.sifirla()
    RV.MATS.clear()
    RV.FONT = RV.font_yukle()
    M = malzemeler()
    RV.FOTOLAR.clear()
    RV.dunya(0.9)
    sahne(M, kap, tip)
    RV.studyo_isiklari()
    RV.render_ayarlari(cikti, ornek)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 2400, 3200
    bpy.ops.render.render(write_still=True)
    RV.fotolari_ekle(cikti)


if __name__ == "__main__":
    main()
