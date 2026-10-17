"""
Beta Vinç - portal ve pergel vinç gerçekçi render betiği (Blender / bpy).

Kullanım:
    python render_vincler.py <sahne> <cikti.png> [ornek_sayisi]
    sahne: duvar_pergel | kolon_pergel | yari_portal | portal
"""
import math
import os
import sys

import bpy  # noqa: I001  (bmesh, bpy yüklendikten sonra içe aktarılabilir)
import bmesh
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- marka renkleri
def srgb(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


BETA_TURUNCU = srgb("#E99A2A")
BETA_ANTRASIT = srgb("#3C424B")
BETA_GRI = srgb("#5A626B")
FONT_YOLLARI = [
    "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


# ---------------------------------------------------------------- temel
def sifirla():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def node_tree(mat):
    try:
        mat.use_nodes = True
    except Exception:
        pass
    return mat.node_tree


MATS = {}


def boya(name, color, rough=0.35, metal=0.0, coat=0.0, var=0.08, bump=0.0):
    """Hafif pürüz varyasyonlu endüstriyel boya / metal."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    nt = node_tree(m)
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.15
    if var:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 6.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = max(0.02, rough - var)
        mr.inputs["To Max"].default_value = min(1.0, rough + var)
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
        if bump:
            bp = nt.nodes.new("ShaderNodeBump")
            bp.inputs["Strength"].default_value = bump
            bp.inputs["Distance"].default_value = 0.002
            nz2 = nt.nodes.new("ShaderNodeTexNoise")
            nz2.inputs["Scale"].default_value = 120.0
            nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
            nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"])
            nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    m.diffuse_color = color
    MATS[name] = m
    return m


def malzemeler():
    return dict(
        turuncu=boya("beta_turuncu", BETA_TURUNCU, rough=0.32, coat=0.25, bump=0.05),
        antrasit=boya("beta_antrasit", BETA_ANTRASIT, rough=0.42, bump=0.05),
        gri=boya("beta_gri", BETA_GRI, rough=0.38, bump=0.04),
        celik=boya("celik", (0.62, 0.62, 0.63, 1), rough=0.28, metal=1.0, var=0.1),
        galvaniz=boya("galvaniz", (0.55, 0.56, 0.58, 1), rough=0.35, metal=1.0, var=0.12),
        halat=boya("halat", (0.33, 0.34, 0.35, 1), rough=0.45, metal=1.0, var=0.1),
        siyah=boya("siyah", (0.025, 0.025, 0.028, 1), rough=0.55),
        kanca=boya("kanca", (0.05, 0.055, 0.06, 1), rough=0.38, metal=0.6, var=0.1),
        beyaz=boya("etiket_beyaz", (0.86, 0.86, 0.85, 1), rough=0.3, var=0.02),
        sari=boya("sari_cizgi", srgb("#F2C200"), rough=0.5, var=0.15),
        ray=boya("ray", (0.42, 0.42, 0.43, 1), rough=0.32, metal=1.0, var=0.15),
    )


def obj(name, mesh, mat=None, parent=None, smooth=False, bevel=0.0, seg=3):
    o = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        mesh.materials.append(mat)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
        try:
            mesh.set_sharp_from_angle(angle=math.radians(40))
        except Exception:
            pass
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = seg
        b.limit_method = "ANGLE"
        try:
            b.harden_normals = True
        except Exception:
            pass
    if parent is not None:
        o.parent = parent
    return o


def bm_to_mesh(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def kutu(name, size, loc, mat, parent=None, bevel=0.006, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = obj(name, bm_to_mesh(bm, name), mat, parent, bevel=bevel)
    o.location = loc
    o.rotation_euler = rot
    return o


def silindir(name, r, depth, loc, mat, parent=None, axis="Z", seg=48, bevel=0.0, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    o = obj(name, bm_to_mesh(bm, name), mat, parent, smooth=True, bevel=bevel, seg=2)
    o.location = loc
    if axis == "X":
        o.rotation_euler = (0, math.pi / 2, 0)
    elif axis == "Y":
        o.rotation_euler = (math.pi / 2, 0, 0)
    return o


def uye(name, p1, p2, w1, w2, d1, d2, mat, parent=None, up=Vector((1, 0, 0)), bevel=0.008):
    """p1->p2 arasında konik kutu kesitli taşıyıcı eleman."""
    p1, p2 = Vector(p1), Vector(p2)
    a = (p2 - p1).normalized()
    u = (up - a * up.dot(a)).normalized()
    v = a.cross(u)
    bm = bmesh.new()
    vs = []
    for p, w, d in ((p1, w1, d1), (p2, w2, d2)):
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vs.append(bm.verts.new(p + u * (su * w / 2) + v * (sv * d / 2)))
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    for idx in f:
        bm.faces.new([vs[i] for i in idx])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm_to_mesh(bm, name), mat, parent, bevel=bevel)


def boru(name, p1, p2, r, mat, parent=None, seg=32):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    o = silindir(name, r, d.length, (p1 + p2) / 2, mat, parent, seg=seg)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def ipe(name, x0, x1, z_ust, h, b, mat, parent=None, y=0.0, tf=0.016, tw=0.010):
    """X ekseni boyunca I profil (IPE/HEA)."""
    L = x1 - x0
    cx = (x0 + x1) / 2
    g = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(g)
    g.parent = parent
    kutu(name + "_ust", (L, b, tf), (cx, y, z_ust - tf / 2), mat, g, bevel=0.003)
    kutu(name + "_alt", (L, b, tf), (cx, y, z_ust - h + tf / 2), mat, g, bevel=0.003)
    kutu(name + "_govde", (L, tw, h - 2 * tf), (cx, y, z_ust - h / 2), mat, g, bevel=0.002)
    return g


def font_yukle():
    for p in FONT_YOLLARI:
        try:
            return bpy.data.fonts.load(p)
        except Exception:
            continue
    return None


FONT = None


def yazi(name, text, loc, size, mat, parent=None, rot=(math.pi / 2, 0, 0), extrude=0.002):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    if FONT:
        cu.font = FONT
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_character = 1.02
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    o.parent = parent
    return o


def etiket(name, loc, w, h, M, parent=None, face="-Y", text="beta"):
    """Beyaz plaka üzerinde koyu 'beta' yazısı (orijinal görsellerdeki gibi)."""
    x, y, z = loc
    if face == "-Y":
        kutu(name + "_plaka", (w, 0.004, h), (x, y, z), M["beyaz"], parent, bevel=0.0015)
        yazi(name + "_yazi", text, (x, y - 0.0035, z), h * 0.78, M["antrasit"], parent)
    else:  # +X
        kutu(name + "_plaka", (0.004, w, h), (x, y, z), M["beyaz"], parent, bevel=0.0015)
        yazi(name + "_yazi", text, (x + 0.0035, y, z), h * 0.78, M["antrasit"], parent,
             rot=(math.pi / 2, 0, math.pi / 2))


# ---------------------------------------------------------------- vinç parçaları
def kanca(name, loc, s, M, parent=None):
    """Dövme kanca: gövde + kıvrım + emniyet mandalı."""
    x0, y0, z0 = loc
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.024 * s
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    pts = []
    shank = 0.10 * s
    r = 0.075 * s
    for i in range(6):
        pts.append((0.0, -shank * i / 5, 1.05))
    n = 40
    for i in range(1, n + 1):
        t = math.radians(-235.0 * i / n)
        px = -r + r * math.cos(t)
        pz = -shank + r * math.sin(t)
        rad = 1.25 - 0.65 * (i / n) ** 1.6
        pts.append((px, pz, rad))
    sp.points.add(len(pts) - 1)
    for p, (px, pz, rad) in zip(sp.points, pts):
        p.co = (px, 0.0, pz, 1.0)
        p.radius = rad
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(M["kanca"])
    o.location = (x0, y0, z0)
    o.parent = parent
    # boyun ve somun
    silindir(name + "_boyun", 0.02 * s, 0.06 * s, (x0, y0, z0 + 0.03 * s), M["celik"], parent)
    silindir(name + "_somun", 0.034 * s, 0.03 * s, (x0, y0, z0 + 0.065 * s), M["celik"], parent, seg=6)
    # emniyet mandalı
    tip_t = math.radians(-235.0)
    tip = Vector((x0 - r + r * math.cos(tip_t), y0, z0 - shank + r * math.sin(tip_t)))
    kok = Vector((x0, y0, z0 - 0.015 * s))
    m = boru(name + "_mandal", kok, tip, 0.005 * s, M["celik"], parent, seg=12)
    return o


def zincir(name, x, y, z_ust, z_alt, M, parent=None, pitch=0.042):
    """Halka halka galvaniz yük zinciri."""
    bm = bmesh.new()
    R, r, seg_u, seg_v = 0.016, 0.0055, 24, 10
    rings = []
    for i in range(seg_u):
        a = 2 * math.pi * i / seg_u
        ring = []
        for j in range(seg_v):
            b = 2 * math.pi * j / seg_v
            px = (R + r * math.cos(b)) * math.cos(a)
            pz = (R + r * math.cos(b)) * math.sin(a) * 1.55
            py = r * math.sin(b)
            ring.append(bm.verts.new((px, py, pz)))
        rings.append(ring)
    for i in range(seg_u):
        for j in range(seg_v):
            a, b = rings[i][j], rings[(i + 1) % seg_u][j]
            c, d = rings[(i + 1) % seg_u][(j + 1) % seg_v], rings[i][(j + 1) % seg_v]
            bm.faces.new((a, b, c, d))
    me = bm_to_mesh(bm, name + "_halka")
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(M["galvaniz"])
    n = int((z_ust - z_alt) / pitch)
    for i in range(n):
        o = bpy.data.objects.new(f"{name}_{i}", me)
        bpy.context.scene.collection.objects.link(o)
        o.location = (x, y, z_ust - i * pitch)
        o.rotation_euler = (0, 0, (math.pi / 2) * (i % 2))
        o.parent = parent


def zincirli_palanga(name, x, z_kiris_alt, flange_b, M, parent, kanca_z):
    """Kiriş alt başlığında yürüyen elektrikli zincirli vinç."""
    # araba yan plakaları ve tekerlekler
    zt = z_kiris_alt
    for sy in (-1, 1):
        kutu(f"{name}_yan{sy}", (0.30, 0.014, 0.17), (x, sy * (flange_b / 2 + 0.025), zt - 0.02), M["antrasit"], parent)
        for sx in (-1, 1):
            silindir(f"{name}_tek{sy}{sx}", 0.032, 0.03, (x + sx * 0.09, sy * (flange_b / 2 - 0.012), zt + 0.03),
                     M["siyah"], parent, axis="Y")
    kutu(f"{name}_kopru", (0.12, flange_b + 0.08, 0.04), (x, 0, zt - 0.11), M["antrasit"], parent)
    # gövde
    gz = zt - 0.30
    kutu(f"{name}_govde", (0.36, 0.26, 0.30), (x, 0, gz), M["turuncu"], parent, bevel=0.035)
    silindir(f"{name}_motor", 0.105, 0.13, (x - 0.24, 0, gz), M["antrasit"], parent, axis="X", bevel=0.01)
    for k in range(10):  # soğutma kanatları
        silindir(f"{name}_kanat{k}", 0.112, 0.004, (x - 0.19 - k * 0.011, 0, gz), M["antrasit"], parent, axis="X")
    silindir(f"{name}_kapak", 0.10, 0.07, (x + 0.215, 0, gz), M["antrasit"], parent, axis="X", bevel=0.01)
    etiket(f"{name}_etiket", (x, -0.132, gz + 0.04), 0.17, 0.05, M, parent)
    # kumanda kablosu ve butonyer
    boru(f"{name}_kablo", (x + 0.12, -0.08, gz - 0.15), (x + 0.12, -0.08, kanca_z + 0.25), 0.006, M["siyah"], parent, seg=10)
    kutu(f"{name}_butonyer", (0.07, 0.06, 0.22), (x + 0.12, -0.08, kanca_z + 0.13), M["turuncu"], parent, bevel=0.012)
    for k, zz in enumerate((0.05, 0.0, -0.05)):
        silindir(f"{name}_buton{k}", 0.012, 0.01, (x + 0.12, -0.112, kanca_z + 0.15 + zz), M["siyah"], parent, axis="Y")
    # zincir torbası
    silindir(f"{name}_torba", 0.09, 0.30, (x - 0.08, 0.16, gz - 0.30), M["siyah"], parent, r2=0.11)
    # zincir + kanca bloğu
    zincir(f"{name}_zincir", x + 0.05, 0, gz - 0.16, kanca_z + 0.10, M, parent)
    kutu(f"{name}_blok", (0.11, 0.08, 0.10), (x + 0.05, 0, kanca_z + 0.05), M["turuncu"], parent, bevel=0.02)
    kanca(f"{name}_kanca", (x + 0.05, 0, kanca_z - 0.01), 0.9, M, parent)


def halatli_araba(name, x, z_ray, y_kiris, M, parent, kanca_z):
    """Çift kirişli portal üzerinde yürüyen halatlı vinç arabası."""
    zt = z_ray + 0.06
    ly = y_kiris + 0.25
    # şasi
    for sy in (-1, 1):
        kutu(f"{name}_bas{sy}", (1.5, 0.22, 0.20), (x, sy * y_kiris, zt + 0.10), M["antrasit"], parent)
        for sx in (-1, 1):
            silindir(f"{name}_tek{sy}{sx}", 0.09, 0.07, (x + sx * 0.55, sy * (y_kiris + 0.13), zt + 0.05),
                     M["antrasit"], parent, axis="Y", bevel=0.005)
    for sx in (-1, 1):
        kutu(f"{name}_trav{sx}", (0.22, 2 * ly, 0.18), (x + sx * 0.64, 0, zt + 0.11), M["antrasit"], parent)
    # tambur
    silindir(f"{name}_tambur", 0.24, 1.0, (x - 0.15, 0, zt + 0.52), M["gri"], parent, axis="Y", bevel=0.005)
    for k in range(24):
        silindir(f"{name}_sarim{k}", 0.243, 0.012, (x - 0.15, -0.42 + k * 0.036, zt + 0.52), M["halat"], parent, axis="Y", seg=36)
    for sy in (-1, 1):
        kutu(f"{name}_tamburyan{sy}", (0.62, 0.03, 0.62), (x - 0.15, sy * 0.53, zt + 0.50), M["antrasit"], parent)
    # motor + redüktör (turuncu, beta plakası)
    kutu(f"{name}_reduktor", (0.62, 0.36, 0.56), (x + 0.42, -0.1, zt + 0.48), M["turuncu"], parent, bevel=0.03)
    silindir(f"{name}_motor", 0.15, 0.42, (x + 0.42, 0.42, zt + 0.48), M["antrasit"], parent, axis="Y", bevel=0.01)
    for k in range(12):
        silindir(f"{name}_kanat{k}", 0.158, 0.006, (x + 0.42, 0.28 + k * 0.022, zt + 0.48), M["antrasit"], parent, axis="Y")
    etiket(f"{name}_etiket", (x + 0.42, -0.283, zt + 0.52), 0.34, 0.10, M, parent)
    # pano
    kutu(f"{name}_pano", (0.5, 0.18, 0.40), (x - 0.15, -ly - 0.12, zt + 0.40), M["antrasit"], parent, bevel=0.01)
    # halatlar (4 kol) ve kanca bloğu
    hz = kanca_z + 0.55
    for sx in (-0.07, 0.07):
        for sy in (-0.1, 0.1):
            boru(f"{name}_halat{sx}{sy}", (x - 0.15 + sx, sy, zt + 0.30), (x - 0.15 + sx, sy * 0.9, hz + 0.08),
                 0.009, M["halat"], parent, seg=12)
    bx = x - 0.15
    kutu(f"{name}_blokust", (0.38, 0.30, 0.10), (bx, 0, hz + 0.05), M["antrasit"], parent, bevel=0.01)
    for sy in (-1, 1):
        silindir(f"{name}_blokyan{sy}", 0.22, 0.05, (bx, sy * 0.12, hz - 0.12), M["turuncu"], parent, axis="Y", bevel=0.01)
    silindir(f"{name}_makara", 0.20, 0.19, (bx, 0, hz - 0.12), M["antrasit"], parent, axis="Y")
    silindir(f"{name}_mil", 0.045, 0.30, (bx, 0, hz - 0.12), M["celik"], parent, axis="Y")
    kutu(f"{name}_traverse", (0.22, 0.16, 0.08), (bx, 0, hz - 0.34), M["antrasit"], parent, bevel=0.01)
    kanca(f"{name}_kanca", (bx, 0, hz - 0.46), 2.1, M, parent)


def kutu_kiris(name, x0, x1, y, z_ust, h, b, M, parent, logo_yuzu=False):
    L = x1 - x0
    cx = (x0 + x1) / 2
    kutu(name, (L, b, h), (cx, y, z_ust - h / 2), M["turuncu"], parent, bevel=0.012)
    # alt ve üst başlık kenarları + dikme izleri
    kutu(name + "_ustbas", (L, b + 0.04, 0.02), (cx, y, z_ust - 0.01), M["turuncu"], parent, bevel=0.004)
    kutu(name + "_altbas", (L, b + 0.04, 0.02), (cx, y, z_ust - h + 0.01), M["turuncu"], parent, bevel=0.004)
    n = int(L / 1.2)
    for i in range(1, n):
        for sy in (-1, 1):
            kutu(f"{name}_dikme{i}{sy}", (0.012, 0.006, h - 0.06),
                 (x0 + i * L / n, y + sy * (b / 2 + 0.003), z_ust - h / 2), M["turuncu"], parent, bevel=0.002)
    # ray
    kutu(name + "_ray", (L - 0.1, 0.06, 0.05), (cx, y, z_ust + 0.025), M["ray"], parent, bevel=0.004)
    if logo_yuzu:
        kutu(name + "_logozemin", (2.2, 0.004, h * 0.62), (cx, y - b / 2 - 0.022, z_ust - h / 2), M["beyaz"], parent, bevel=0.002)
        yazi(name + "_logo", "beta", (cx, y - b / 2 - 0.026, z_ust - h / 2 - 0.01), h * 0.5, M["antrasit"], parent)


def bas_araba(name, x, y0, y1, M, parent, z=0.0):
    """Ray üzerinde tekerlekli baş arabası (Y doğrultusunda)."""
    L = y1 - y0
    cy = (y0 + y1) / 2
    kutu(name, (0.34, L, 0.36), (x, cy, z + 0.33), M["antrasit"], parent, bevel=0.01)
    for sy in (-1, 1):
        yy = cy + sy * (L / 2 - 0.28)
        silindir(f"{name}_tek{sy}", 0.17, 0.10, (x, yy, z + 0.20), M["antrasit"], parent, axis="X", bevel=0.006)
        silindir(f"{name}_gobek{sy}", 0.06, 0.38, (x, yy, z + 0.20), M["celik"], parent, axis="X")
        kutu(f"{name}_tampon{sy}", (0.12, 0.10, 0.12), (x, cy + sy * (L / 2 + 0.05), z + 0.33), M["siyah"], parent, bevel=0.02)
    silindir(f"{name}_motor", 0.10, 0.34, (x + 0.30, cy + L / 2 - 0.28, z + 0.36), M["antrasit"], parent, axis="X", bevel=0.01)
    kutu(f"{name}_red", (0.22, 0.28, 0.30), (x + 0.15, cy + L / 2 - 0.28, z + 0.26), M["turuncu"], parent, bevel=0.02)


def portal_ayak(name, x, y_alt, y_ust, z_alt, z_ust, M, parent):
    """A tipi portal ayağı (iki konik kol, Y-Z düzleminde)."""
    for sy in (-1, 1):
        uye(f"{name}_kol{sy}", (x, sy * y_alt, z_alt), (x, sy * y_ust, z_ust), 0.34, 0.42, 0.28, 0.36,
            M["turuncu"], parent, up=Vector((1, 0, 0)), bevel=0.01)
    # alt flanşlar
    for sy in (-1, 1):
        kutu(f"{name}_flans{sy}", (0.44, 0.44, 0.03), (x, sy * y_alt, z_alt + 0.015), M["turuncu"], parent, bevel=0.004)
    # ara bağlantı
    zc = z_alt + (z_ust - z_alt) * 0.45
    yc = y_alt + (y_ust - y_alt) * 0.45
    kutu(f"{name}_bag", (0.22, 2 * yc, 0.18), (x, 0, zc), M["turuncu"], parent, bevel=0.008)


# ---------------------------------------------------------------- hol ortamı
def zemin_beton():
    m = bpy.data.materials.new("beton_zemin")
    nt = node_tree(m)
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35
    nz.inputs["Detail"].default_value = 12
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.16, 0.16, 0.155, 1)
    ramp.color_ramp.elements[1].color = (0.27, 0.265, 0.255, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    # ince lekeler
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 9
    nz2.inputs["Detail"].default_value = 10
    nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(nz2.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.22
    mr.inputs["To Max"].default_value = 0.6
    nt.links.new(nz2.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.08
    nz3 = nt.nodes.new("ShaderNodeTexNoise")
    nz3.inputs["Scale"].default_value = 260
    nt.links.new(tc.outputs["Object"], nz3.inputs["Vector"])
    nt.links.new(nz3.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def trapez_sac(name, color):
    m = bpy.data.materials.new(name)
    nt = node_tree(m)
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Metallic"].default_value = 0.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.wave_profile = "TRI"
    wv.inputs["Scale"].default_value = 0.5
    wv.inputs["Distortion"].default_value = 0.0
    wv.inputs["Detail"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def duzlem(name, size, loc, rot, mat):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=Vector((size[0], size[1], 1)), verts=bm.verts)
    o = obj(name, bm_to_mesh(bm, name), mat)
    o.location = loc
    o.rotation_euler = rot
    return o


def hol(M, arka_y=9.0, sol_x=-14.0, sag_x=18.0, yukseklik=12.0, kolon_aks=6.0):
    zemin = duzlem("zemin", (80, 80), (0, 0, 0), (0, 0, 0), zemin_beton())
    # zemin derzleri
    derz = boya("derz", (0.12, 0.12, 0.12, 1), rough=0.7, var=0)
    for i in range(-6, 7):
        duzlem(f"derzx{i}", (0.012, 80), (i * 6.0, 0, 0.0008), (0, 0, 0), derz)
        duzlem(f"derzy{i}", (80, 0.012), (0, i * 6.0, 0.0008), (0, 0, 0), derz)
    # arka duvar: alt beton blok + üst trapez sac
    blok = boya("duvar_blok", (0.30, 0.30, 0.29, 1), rough=0.8, var=0.1, bump=0.3)
    sac = trapez_sac("duvar_sac", (0.40, 0.43, 0.47, 1))
    duzlem("arka_alt", (80, 2.4), (0, arka_y, 1.2), (math.pi / 2, 0, 0), blok)
    duzlem("arka_ust", (80, yukseklik - 2.4), (0, arka_y, 2.4 + (yukseklik - 2.4) / 2), (math.pi / 2, 0, 0), sac)
    # pencere bandı
    cam = bpy.data.materials.new("pencere")
    nt = node_tree(cam)
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1)
    bs.inputs["Emission Color"].default_value = (0.85, 0.92, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 0.8
    duzlem("pencere", (80, 1.2), (0, arka_y - 0.02, 8.6), (math.pi / 2, 0, 0), cam)
    # yan duvar
    duzlem("sol_duvar", (80, yukseklik), (sol_x, 0, yukseklik / 2), (math.pi / 2, 0, math.pi / 2), sac)
    # çelik hol kolonları (HEA) arka duvar boyunca
    kolon = boya("hol_kolon", (0.20, 0.22, 0.25, 1), rough=0.45)
    for i in range(-3, 5):
        x = i * kolon_aks
        kutu(f"hk{i}_f1", (0.30, 0.02, yukseklik), (x, arka_y - 0.02, yukseklik / 2), kolon, bevel=0.002)
        kutu(f"hk{i}_f2", (0.30, 0.02, yukseklik), (x, arka_y - 0.32, yukseklik / 2), kolon, bevel=0.002)
        kutu(f"hk{i}_w", (0.012, 0.3, yukseklik), (x, arka_y - 0.17, yukseklik / 2), kolon, bevel=0.0)
    # tavan + aydınlatma
    tavan = boya("tavan", (0.22, 0.23, 0.25, 1), rough=0.7, var=0)
    duzlem("tavan", (80, 80), (0, 0, yukseklik), (math.pi, 0, 0), tavan)
    for i in range(-3, 4):
        for j in range(-2, 2):
            ld = bpy.data.lights.new(f"lamba{i}{j}", "AREA")
            ld.shape = "RECTANGLE"
            ld.size, ld.size_y = 1.2, 0.5
            ld.energy = 160
            ld.color = (1.0, 0.97, 0.92)
            lo = bpy.data.objects.new(f"lamba{i}{j}", ld)
            bpy.context.scene.collection.objects.link(lo)
            lo.location = (i * 6.0 + 1.5, j * 6.0 + 1.0, yukseklik - 0.6)
            kutu(f"armatur{i}{j}", (1.25, 0.55, 0.08), (lo.location.x, lo.location.y, yukseklik - 0.55),
                 boya("armatur", (0.8, 0.8, 0.8, 1), rough=0.4, var=0), bevel=0.0)
    # sarı yaya yolu çizgileri
    for x in (sol_x + 2.0, sol_x + 3.5):
        duzlem(f"yaya{x}", (0.10, 60), (x, 0, 0.0015), (0, 0, 0), M["sari"])
    return zemin


BEYAZ = os.environ.get("ORTAM", "beyaz") == "beyaz"
FOTO_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vinc_foto")
RAY = 6.0 if BEYAZ else 30.0
FOTOLAR = []  # (dosya, nesne, yerel_nokta, yukseklik_m, yatay_capa)


def ortam(M, **kw):
    """Gölgesiz düz beyaz arka plan veya fabrika holü."""
    if not BEYAZ:
        return hol(M, **kw)
    return None  # zemin yok: düz beyaz arka plan, gölge yok


def foto_vinc(dosya, nesne, nokta, yukseklik, capa=0.5):
    """Gerçek ürün fotoğrafını, kirişin alt başlığına oturacak şekilde render sonrası ekle."""
    FOTOLAR.append((os.path.join(FOTO_KLASOR, dosya), nesne, Vector(nokta), yukseklik, capa))


def fotolari_ekle(cikti):
    from bpy_extras.object_utils import world_to_camera_view
    from PIL import Image

    sc = bpy.context.scene
    bpy.context.view_layer.update()
    W = int(sc.render.resolution_x * sc.render.resolution_percentage / 100)
    H = int(sc.render.resolution_y * sc.render.resolution_percentage / 100)
    img = Image.open(cikti).convert("RGBA")
    if BEYAZ:
        zemin = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(zemin, img)
    for dosya, nesne, nokta, yuk, capa in FOTOLAR:
        ust = nesne.matrix_world @ nokta
        alt = nesne.matrix_world @ (nokta - Vector((0, 0, yuk)))
        pu = world_to_camera_view(sc, sc.camera, ust)
        pa = world_to_camera_view(sc, sc.camera, alt)
        hpx = (pu.y - pa.y) * H
        foto = Image.open(dosya).convert("RGBA")
        olcek = hpx / foto.height
        foto = foto.resize((max(1, round(foto.width * olcek)), max(1, round(foto.height * olcek))), Image.LANCZOS)
        x = round(pu.x * W - foto.width * capa)
        y = round((1 - pu.y) * H)
        img.alpha_composite(foto, (x, y))
    img.convert("RGB").save(cikti)


def dunya(guc=0.6):
    w = bpy.data.worlds.new("dunya")
    bpy.context.scene.world = w
    nt = node_tree(w)
    bg = nt.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.75, 0.80, 0.88, 1)
    bg.inputs["Strength"].default_value = guc


def kamera(loc, hedef, lens=35, dof=None):
    cd = bpy.data.cameras.new("kamera")
    cd.lens = lens
    cd.sensor_width = 36
    co = bpy.data.objects.new("kamera", cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = Vector(hedef) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = d.length
        cd.dof.aperture_fstop = dof
    return co


def anahtar_isik(loc, hedef, guc, boyut=4.0, renk=(1.0, 0.96, 0.9)):
    ld = bpy.data.lights.new("anahtar", "AREA")
    ld.shape = "DISK"
    ld.size = boyut
    ld.energy = guc
    ld.color = renk
    lo = bpy.data.objects.new("anahtar", ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector(hedef) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def render_ayarlari(cikti, ornek):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = ornek
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 0.5
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = int(os.environ.get("YUZDE", "100"))
    sc.render.film_transparent = BEYAZ
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.filepath = cikti
    vs = sc.view_settings
    try:
        vs.view_transform = "AgX"
        vs.look = "AgX - Punchy" if BEYAZ else "AgX - Medium High Contrast"
    except Exception:
        pass
    vs.exposure = -0.3 if BEYAZ else 0.0
    sc.render.threads_mode = "AUTO"


# ---------------------------------------------------------------- sahneler
def bos(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    return e


def bom_logo(M, g, x, zb):
    """Bom gövdesine beyaz zemin üzerine 'beta' plakası."""
    kutu("bom_logozemin", (0.62, 0.004, 0.17), (x, -0.008, zb - 0.15), M["beyaz"], g, bevel=0.0015)
    yazi("bom_logo", "beta", (x, -0.0105, zb - 0.155), 0.13, M["antrasit"], g)


def sahne_duvar_pergel(M):
    ortam(M, arka_y=7.0)
    # bina betonarme kolonu
    beton = boya("beton_kolon", (0.36, 0.36, 0.345, 1), rough=0.85, var=0.1, bump=0.4)
    kutu("bina_kolon", (0.6, 0.6, 12.0), (-0.3, 0, 6.0), beton, bevel=0.01)
    # dönen grup (mafsal ekseni x=0.12)
    g = bos("pergel", (0.12, 0, 0), (0, 0, math.radians(18)))
    # duvar konsolu (sabit)
    kutu("konsol_plaka", (0.03, 0.42, 2.0), (0.015, 0, 3.4), M["antrasit"], bevel=0.004)
    for z in (4.15, 2.75):
        kutu(f"konsol_kulak{z}", (0.22, 0.30, 0.14), (0.12, 0, z), M["antrasit"], bevel=0.01)
        silindir(f"pim{z}", 0.04, 0.36, (0.16, 0, z), M["celik"])
    for zz in (2.55, 3.0, 3.8, 4.25):
        for yy in (-0.15, 0.15):
            silindir(f"civata{zz}{yy}", 0.018, 0.04, (0.04, yy, zz), M["celik"], axis="X", seg=6)
    # bom (IPE 300)
    zb = 4.30
    ipe("bom", 0.12, 4.2, zb, 0.30, 0.15, M["turuncu"], g, tf=0.018, tw=0.011)
    kutu("bom_kok", (0.24, 0.26, 0.40), (0.14, 0, zb - 0.16), M["turuncu"], g, bevel=0.02)
    kutu("bom_uc", (0.02, 0.22, 0.34), (4.21, 0, zb - 0.15), M["antrasit"], g, bevel=0.004)
    bom_logo(M, g, 1.25, zb)
    for sy in (-1, 1):
        kutu(f"stoper{sy}", (0.05, 0.03, 0.06), (4.12, sy * 0.06, zb - 0.33), M["siyah"], g, bevel=0.01)
    # gergi
    p1 = (0.18, 0, 2.75)
    p2 = (2.3, 0, zb - 0.30)
    boru("gergi", p1, p2, 0.048, M["turuncu"], g)
    kutu("gergi_ust_kulak", (0.16, 0.10, 0.08), (2.3, 0, zb - 0.34), M["antrasit"], g, bevel=0.008)
    silindir("gergi_ust_pim", 0.025, 0.14, (2.3, 0, zb - 0.36), M["celik"], g, axis="Y")
    foto_vinc("zincirli_vinc_2ton.png", g, (3.25, 0, zb - 0.285), 1.25, capa=0.62)
    if not BEYAZ:
        palet(M, (4.6, 0.1, 0), 0.35)
    kamera((4.6, -5.6, 2.6), (2.1, 0.3, 3.05), lens=34, dof=9)
    anahtar_isik((4, -9, 8), (2, 0, 2), 1800, boyut=6)


def sahne_kolon_pergel(M):
    ortam(M, arka_y=7.0)
    # temel ve taban
    temel = boya("temel", (0.30, 0.30, 0.29, 1), rough=0.8, var=0.1, bump=0.3)
    kutu("temel", (1.4, 1.4, 0.04), (0, 0, 0.0), temel, bevel=0.005)
    kutu("taban", (0.9, 0.9, 0.04), (0, 0, 0.04), M["antrasit"], bevel=0.006)
    for a in range(8):
        ang = a * math.pi / 4
        uye(f"guse{a}", (0.30 * math.cos(ang), 0.30 * math.sin(ang), 0.06),
            (0.18 * math.cos(ang), 0.18 * math.sin(ang), 0.50), 0.02, 0.02, 0.26, 0.02,
            M["antrasit"], up=Vector((-math.sin(ang), math.cos(ang), 0)), bevel=0.002)
    for sx in (-1, 1):
        for sy in (-1, 1):
            silindir(f"ankraj{sx}{sy}", 0.022, 0.12, (sx * 0.36, sy * 0.36, 0.11), M["celik"])
            silindir(f"somun{sx}{sy}", 0.04, 0.035, (sx * 0.36, sy * 0.36, 0.075), M["celik"], seg=6)
    # kolon
    H = 4.3
    silindir("kolon", 0.17, H, (0, 0, H / 2 + 0.06), M["gri"], seg=64)
    silindir("kolon_bilezik", 0.20, 0.16, (0, 0, H + 0.06), M["antrasit"], seg=64, bevel=0.01)
    # dönen grup
    g = bos("pergel", (0, 0, 0), (0, 0, math.radians(15)))
    zb = H + 0.48
    silindir("baslik", 0.215, 0.36, (0, 0, H + 0.30), M["antrasit"], g, seg=64, bevel=0.01)
    silindir("baslik_serit", 0.217, 0.05, (0, 0, H + 0.42), M["turuncu"], g, seg=64)
    silindir("baslik_kapak", 0.23, 0.04, (0, 0, H + 0.50), M["antrasit"], g, seg=64, bevel=0.008)
    ipe("bom", 0.18, 4.4, zb, 0.30, 0.15, M["turuncu"], g, tf=0.018, tw=0.011)
    kutu("bom_kok", (0.22, 0.26, 0.40), (0.22, 0, zb - 0.18), M["turuncu"], g, bevel=0.02)
    kutu("bom_uc", (0.02, 0.22, 0.34), (4.41, 0, zb - 0.15), M["antrasit"], g, bevel=0.004)
    bom_logo(M, g, 1.3, zb)
    # gergi (kolon bileziğinden)
    silindir("alt_bilezik", 0.205, 0.14, (0, 0, H - 0.75), M["antrasit"], g, seg=64, bevel=0.01)
    boru("gergi", (0.2, 0, H - 0.75), (2.3, 0, zb - 0.30), 0.048, M["turuncu"], g)
    kutu("gergi_ust_kulak", (0.16, 0.10, 0.08), (2.3, 0, zb - 0.34), M["antrasit"], g, bevel=0.008)
    foto_vinc("kompakt_vinc.png", g, (3.45, 0, zb - 0.285), 1.10, capa=0.66)
    if not BEYAZ:
        palet(M, (4.4, -0.6, 0), 0.3)
    kamera((4.4, -6.6, 2.4), (2.0, 0.3, 2.65), lens=32, dof=9)
    anahtar_isik((3, -9, 8), (1.5, 0, 2), 1800, boyut=6)


def portal_govde(M, g, span, z_ust, h, cift_ayak=True, ray_ust=0.0, kanca_z=1.6, foto=None):
    yk = 0.48  # kiriş aksları
    kutu_kiris("kiris_on", 0, span, -yk, z_ust, h, 0.42, M, g, logo_yuzu=True)
    kutu_kiris("kiris_arka", 0, span, yk, z_ust, h, 0.42, M, g)
    for x in ((0.0, span) if True else ()):
        kutu(f"bas_kirisi{x}", (0.5, 2 * yk + 0.6, h * 0.8), (x, 0, z_ust - h * 0.45), M["turuncu"], g, bevel=0.012)
    # yürüyüş yolu ve korkuluk (arka kiriş üstünde)
    for i in range(int(span / 1.0) + 1):
        kutu(f"korkuluk_dikme{i}", (0.04, 0.04, 1.0), (i * span / int(span), yk + 0.48, z_ust + 0.5), M["sari"], g, bevel=0.004)
    kutu("korkuluk_ust", (span, 0.04, 0.04), (span / 2, yk + 0.48, z_ust + 1.0), M["sari"], g, bevel=0.004)
    kutu("korkuluk_orta", (span, 0.03, 0.03), (span / 2, yk + 0.48, z_ust + 0.5), M["sari"], g, bevel=0.004)
    kutu("yurume_yolu", (span, 0.55, 0.02), (span / 2, yk + 0.24 + 0.05, z_ust - 0.01), M["antrasit"], g, bevel=0.002)
    # ayaklar
    zl = z_ust - h
    portal_ayak("ayak_sol", 0.0, 1.7, 0.55, 0.62, zl, M, g)
    bas_araba("bas_sol", 0.0, -2.2, 2.2, M, g, z=ray_ust)
    if cift_ayak:
        portal_ayak("ayak_sag", span, 1.7, 0.55, 0.62, zl, M, g)
        bas_araba("bas_sag", span, -2.2, 2.2, M, g, z=ray_ust)
        kutu("kumanda_kabin", (0.6, 0.5, 0.9), (span - 0.0, -1.0, 1.6), M["antrasit"], g, bevel=0.01)
    if foto:
        # Beta ürün fotoğrafı: ön kirişin alt başlığında yürüyen vinç
        dosya, yuk, capa = foto
        foto_vinc(dosya, g, (span * 0.47, -yk, z_ust - h + 0.02), yuk, capa=capa)
    else:
        halatli_araba("araba", span * 0.47, z_ust + 0.05, yk, M, g, kanca_z=kanca_z)


def ray(name, x, y0, y1, M):
    L = y1 - y0
    cy = (y0 + y1) / 2
    kutu(name + "_taban", (0.16, L, 0.02), (x, cy, 0.01), M["ray"], bevel=0.003)
    kutu(name + "_govde", (0.03, L, 0.07), (x, cy, 0.055), M["ray"], bevel=0.002)
    kutu(name + "_mantar", (0.07, L, 0.035), (x, cy, 0.105), M["ray"], bevel=0.006)
    for i in range(int(L / 0.8)):
        kutu(f"{name}_klips{i}", (0.24, 0.08, 0.025), (x, y0 + 0.4 + i * 0.8, 0.012), M["antrasit"], bevel=0.004)


def sahne_portal(M):
    ortam(M, arka_y=9.5, sol_x=-9.0, sag_x=22.0)
    span = 11.0
    ray("ray_sol", 0.0, -RAY, RAY, M)
    ray("ray_sag", span, -RAY, RAY, M)
    g = bos("portal", (0, 0, 0.12))
    portal_govde(M, g, span, 6.6, 0.85, cift_ayak=True, kanca_z=1.4,
                 foto=("kompakt_vinc.png", 1.6, 0.66) if BEYAZ else None)
    # yük: çelik sac paketi
    if not BEYAZ:
        yuk_kasa(M, (span * 0.47 - 0.15, -0.0, 0.0))
    kamera((13.4, -11.0, 1.8), (5.4, 0.0, 3.7), lens=24, dof=12)
    anahtar_isik((4, -12, 10), (5, 0, 3), 3500, boyut=8)


def sahne_yari_portal(M):
    ortam(M, arka_y=9.5, sol_x=-9.0)
    span = 11.0
    # sağda betonarme bina kolonları + yürüyüş yolu kirişi
    beton = boya("beton_kolon", (0.36, 0.36, 0.345, 1), rough=0.85, var=0.1, bump=0.4)
    kx = span + 0.75
    for i, y in enumerate((-3.5, 3.5) if BEYAZ else (-12, -6, 0, 6, 12)):
        kutu(f"bina_kolon{i}", (0.6, 0.6, 12), (kx, y, 6), beton, bevel=0.01)
        kutu(f"konsol{i}", (0.6, 0.6, 0.6), (kx - 0.55, y, 6.0), beton, bevel=0.01)
    if not BEYAZ:
        duzlem("sag_duvar", (80, 12), (kx + 0.3, 0, 6), (math.pi / 2, 0, math.pi / 2),
               boya("sag_duvar_boya", (0.42, 0.43, 0.44, 1), rough=0.8, var=0.08, bump=0.2))
    ipe("yol_kirisi", -3.8 if BEYAZ else -12.3, 3.8 if BEYAZ else 30, 6.75, 0.5, 0.3, M["antrasit"], None, tf=0.025, tw=0.014)
    # X boyunca üretildi; Y boyunca döndür ve kolon hizasına taşı
    yk = bpy.data.objects["yol_kirisi"]
    yk.rotation_euler = (0, 0, math.pi / 2)
    yk.location = (span, 0, 0)
    kutu("yol_rayi", (0.06, 7.6 if BEYAZ else 42.3, 0.05), (span, 0 if BEYAZ else 8.85, 6.775), M["ray"], bevel=0.004)
    ray("ray_sol", 0.0, -RAY, RAY, M)
    g = bos("portal", (0, 0, 0.12))
    zust = 7.75
    portal_govde(M, g, span, zust, 0.85, cift_ayak=False, kanca_z=1.4,
                 foto=("zincirli_vinc_2ton.png", 1.8, 0.62) if BEYAZ else None)
    # yol kirişi üzerindeki baş arabası
    bas_araba("bas_sag", span, -1.6, 1.6, M, g, z=6.68)
    kutu("sag_bas_baglanti", (0.5, 1.6, 0.25), (span, 0, zust - 0.85 - 0.12 + 0.0), M["turuncu"], g, bevel=0.01)
    if not BEYAZ:
        yuk_kasa(M, (span * 0.47 - 0.15, 0.0, 0.0))
    kamera((-2.2, -11.6, 1.8), (6.0, 0.4, 4.3), lens=24, dof=12)
    anahtar_isik((8, -12, 10), (6, 0, 3), 3500, boyut=8)


def palet(M, loc, rot):
    ahsap = boya("ahsap", (0.42, 0.30, 0.18, 1), rough=0.75, var=0.12, bump=0.3)
    g = bos("palet", loc, (0, 0, rot))
    for i in range(5):
        kutu(f"palet_ust{i}", (1.2, 0.1, 0.022), (0, -0.4 + i * 0.2, 0.133), ahsap, g, bevel=0.003)
    for i in range(3):
        kutu(f"palet_tak{i}", (1.2, 0.1, 0.09), (0, -0.35 + i * 0.35, 0.067), ahsap, g, bevel=0.003)
        kutu(f"palet_alt{i}", (1.2, 0.1, 0.022), (0, -0.35 + i * 0.35, 0.011), ahsap, g, bevel=0.003)
    # palet üzerinde çelik parçalar
    silindir("mil_parca", 0.14, 0.9, (0, -0.15, 0.29), M["celik"], g, axis="X", bevel=0.006)
    kutu("kasa_parca", (0.5, 0.36, 0.3), (0.2, 0.25, 0.30), M["antrasit"], g, bevel=0.01)


def yuk_kasa(M, loc):
    x, y, z = loc
    # yerde bekleyen sac paketleri
    sac = boya("sac_paket", (0.36, 0.37, 0.39, 1), rough=0.3, metal=1.0, var=0.15)
    for i in range(6):
        kutu(f"sac{i}", (2.4, 1.2, 0.035), (x + 3.6, y - 2.4, 0.11 + i * 0.037), sac, bevel=0.003)
    ahsap = boya("ahsap", (0.42, 0.30, 0.18, 1), rough=0.75, var=0.12, bump=0.3)
    for i in range(3):
        kutu(f"takoz{i}", (0.1, 1.3, 0.09), (x + 2.6 + i * 1.0, y - 2.4, 0.045), ahsap, bevel=0.003)


SAHNELER = {
    "duvar_pergel": sahne_duvar_pergel,
    "kolon_pergel": sahne_kolon_pergel,
    "yari_portal": sahne_yari_portal,
    "portal": sahne_portal,
}


def main():
    global FONT
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sahne, cikti = argv[0], argv[1]
    ornek = int(argv[2]) if len(argv) > 2 else 160
    sifirla()
    MATS.clear()
    FONT = font_yukle()
    M = malzemeler()
    FOTOLAR.clear()
    dunya(0.4 if BEYAZ else 0.12)
    SAHNELER[sahne](M)
    if BEYAZ:
        # stüdyo dolgu ışığı
        anahtar_isik((-6, -8, 7), (2, 0, 2), 900, boyut=8, renk=(0.95, 0.97, 1.0))
    render_ayarlari(cikti, ornek)
    bpy.ops.render.render(write_still=True)
    fotolari_ekle(cikti)


if __name__ == "__main__":
    main()
