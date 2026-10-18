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
    """Ray üzerinde baş arabası (Y doğrultusunda): ana kutu + iki tekerlek bloğu, tahrik grubu, tamponlar."""
    L = y1 - y0
    cy = (y0 + y1) / 2
    kutu(name, (0.34, L - 0.5, 0.30), (x, cy, z + 0.47), M["antrasit"], parent, bevel=0.01)
    for sy in (-1, 1):
        yy = cy + sy * (L / 2 - 0.32)
        # tekerlek bloğu: iki yan levha (alt yarıda tekerlek görünür)
        for sx in (-1, 1):
            kutu(f"{name}_blok{sy}{sx}", (0.025, 0.62, 0.36), (x + sx * 0.12, yy, z + 0.40), M["antrasit"], parent, bevel=0.004)
            civata_izgara(f"{name}_blokc{sy}{sx}", (x + sx * 0.133, yy, z + 0.45), (0, 1, 0), (0, 0, 1), 3, 2, 0.2, 0.14,
                          "X" if sx > 0 else "-X", M, parent, r=0.012)
        kutu(f"{name}_blokust{sy}", (0.27, 0.62, 0.025), (x, yy, z + 0.57), M["antrasit"], parent, bevel=0.003)
        silindir(f"{name}_tek{sy}", 0.17, 0.09, (x, yy, z + 0.20), M["celik"], parent, axis="X", bevel=0.004)
        silindir(f"{name}_tekflans{sy}", 0.19, 0.02, (x - 0.05, yy, z + 0.20), M["celik"], parent, axis="X")
        silindir(f"{name}_mil{sy}", 0.05, 0.34, (x, yy, z + 0.20), M["antrasit"], parent, axis="X")
        kutu(f"{name}_tampon_govde{sy}", (0.16, 0.14, 0.16), (x, cy + sy * (L / 2 + 0.03), z + 0.40), M["antrasit"], parent, bevel=0.01)
        silindir(f"{name}_tampon{sy}", 0.07, 0.12, (x, cy + sy * (L / 2 + 0.15), z + 0.40), M["siyah"], parent, axis="Y", bevel=0.01)
    # tahrik grubu (motor + redüktör, tekerlek miline akuple)
    yd = cy + L / 2 - 0.32
    kutu(f"{name}_red", (0.22, 0.30, 0.30), (x + 0.25, yd, z + 0.30), M["turuncu"], parent, bevel=0.02)
    silindir(f"{name}_motor", 0.10, 0.32, (x + 0.25, yd - 0.30, z + 0.36), M["antrasit"], parent, axis="Y", bevel=0.01)
    silindir(f"{name}_fren", 0.105, 0.06, (x + 0.25, yd - 0.48, z + 0.36), M["siyah"], parent, axis="Y", bevel=0.005)


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
    for sy in (-1, 1):
        # alt flanş cıvataları (baş arabasına)
        for i, (dx, dy) in enumerate(((-0.17, -0.17), (0, -0.17), (0.17, -0.17), (0.17, 0), (0.17, 0.17),
                                       (0, 0.17), (-0.17, 0.17), (-0.17, 0))):
            civata(f"{name}_altc{sy}{i}", (x + dx, sy * y_alt + dy, z_alt + 0.031), "Z", M, parent, r=0.016)
        # üst flanş: ayak başlık levhası + cıvatalar (uç kirişe)
        kutu(f"{name}_ustflans{sy}", (0.60, 0.56, 0.035), (x, sy * y_ust, z_ust - 0.0175), M["turuncu"], parent, bevel=0.004)
        for i in range(4):
            for sx in (-1, 1):
                civata(f"{name}_ustc{sy}{sx}{i}", (x + sx * 0.26, sy * y_ust - 0.21 + i * 0.14, z_ust - 0.036), "-Z", M, parent, r=0.016)
        # ara bağlantı guse levhaları + cıvatalar
        yb = sy * (yc - 0.12)
        for sx in (-1, 1):
            kutu(f"{name}_guse{sy}{sx}", (0.014, 0.42, 0.38), (x + sx * 0.118, yb, zc), M["turuncu"], parent, bevel=0.002)
            civata_izgara(f"{name}_gusec{sy}{sx}", (x + sx * 0.126, yb, zc), (0, 1, 0), (0, 0, 1), 2, 2, 0.2, 0.2,
                          "X" if sx > 0 else "-X", M, parent, r=0.014)



# ---------------------------------------------------------------- bağlantı ve donanım detayları
_CIVATA_MESH = {}


def civata(name, loc, eksen, M, parent=None, r=0.014):
    """Pullu altıgen cıvata başı; `eksen` başın baktığı yön ('X','-X','Y','-Y','Z','-Z')."""
    if "m" not in _CIVATA_MESH:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=1.0, radius2=1.0, depth=0.9,
                              matrix=Matrix.Translation((0, 0, 0.75)))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=1.45, radius2=1.45, depth=0.3,
                              matrix=Matrix.Translation((0, 0, 0.15)))
        me = bm_to_mesh(bm, "civata_bas")
        me.materials.append(M["celik"])
        _CIVATA_MESH["m"] = me
    o = bpy.data.objects.new(name, _CIVATA_MESH["m"])
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.scale = (r, r, r)
    rot = {"Z": (0, 0, 0), "-Z": (math.pi, 0, 0), "X": (0, math.pi / 2, 0), "-X": (0, -math.pi / 2, 0),
           "Y": (-math.pi / 2, 0, 0), "-Y": (math.pi / 2, 0, 0)}[eksen]
    o.rotation_euler = rot
    o.parent = parent
    return o


def civata_izgara(name, merkez, u, v, nu, nv, au, av, eksen, M, parent=None, r=0.014):
    """merkez etrafında u, v doğrultularında nu x nv cıvata dizisi."""
    c, u, v = Vector(merkez), Vector(u), Vector(v)
    for i in range(nu):
        for j in range(nv):
            p = c + u * ((i - (nu - 1) / 2) * au) + v * ((j - (nv - 1) / 2) * av)
            civata(f"{name}_{i}_{j}", p, eksen, M, parent, r)


def kablo(name, noktalar, r, mat, parent=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(noktalar) - 1)
    for pt, q in zip(sp.points, noktalar):
        pt.co = (q[0], q[1], q[2], 1.0)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    o.parent = parent
    return o


def festoon(name, x0, x1, y, z, x_sabit, x_araba, M, parent, n=6, L=1.7, y_konsol=None, z_konsol=None, aralik=1.4):
    """C raylı festoon kablo sistemi: ray, konsollar, kablo arabaları ve sarkan yassı kablolar.

    x_sabit: kabloların sabit (besleme) ucu, x_araba: vinç arabasının yanındaki çekme arabası.
    y_konsol/z_konsol: konsolların kirişe/boma bağlandığı nokta.
    """
    L_ray = x1 - x0
    kutu(f"{name}_ray", (L_ray, 0.05, 0.05), ((x0 + x1) / 2, y, z), M["galvaniz"], parent, bevel=0.004)
    kutu(f"{name}_ray_yarik", (L_ray, 0.012, 0.006), ((x0 + x1) / 2, y, z - 0.024), M["siyah"], parent, bevel=0.0)
    if y_konsol is not None:
        k = max(2, int(L_ray / aralik) + 1)
        for i in range(k):
            xk = x0 + 0.1 + i * (L_ray - 0.2) / (k - 1)
            yk_, zk = y_konsol, z_konsol
            # dikey ayak + yatay kol + rayı tutan kelepçe
            kutu(f"{name}_konsol_ayak{i}", (0.05, 0.05, abs(z + 0.06 - zk)), (xk, yk_, (z + 0.06 + zk) / 2), M["antrasit"], parent, bevel=0.003)
            kutu(f"{name}_konsol_kol{i}", (0.05, abs(yk_ - y) + 0.05, 0.05), (xk, (yk_ + y) / 2, z + 0.06), M["antrasit"], parent, bevel=0.003)
            kutu(f"{name}_kelepce{i}", (0.07, 0.07, 0.02), (xk, y, z + 0.035), M["galvaniz"], parent, bevel=0.002)
            civata(f"{name}_konsol_c{i}", (xk, y, z + 0.047), "Z", M, parent, r=0.009)
    # kablo arabaları
    yon = 1 if x_araba > x_sabit else -1
    xs = [x_sabit + yon * 0.12 + i * (x_araba - x_sabit - yon * 0.12) / (n - 1) for i in range(n)]
    for i, xa in enumerate(xs):
        kutu(f"{name}_araba{i}", (0.10, 0.07, 0.05), (xa, y, z - 0.055), M["galvaniz"], parent, bevel=0.006)
        kutu(f"{name}_tutucu{i}", (0.05, 0.12, 0.05), (xa, y, z - 0.105), M["siyah"], parent, bevel=0.008)
    # sarkan kablolar (parabolik sehim, kablo boyu L sabit)
    for i in range(n - 1):
        a, b = xs[i], xs[i + 1]
        s_ = abs(b - a)
        d = math.sqrt(max(0.0, 3 * s_ * (L - s_) / 8))
        for k, dy in enumerate((-0.035, 0.0, 0.035)):
            pts = []
            for t in range(17):
                tt = t / 16
                pts.append((a + (b - a) * tt, y + dy, z - 0.13 - 4 * d * tt * (1 - tt) * (1 - 0.06 * k)))
            kablo(f"{name}_kablo{i}_{k}", pts, 0.011, M["siyah"], parent)
    # sabit uçta buat kutusu
    kutu(f"{name}_buat", (0.22, 0.12, 0.28), (x_sabit, y, z - 0.30), M["antrasit"], parent, bevel=0.01)
    return xs


def merdiven(name, p_alt, p_ust, genislik, M, parent, yan=Vector((0, 1, 0)), adim=0.3):
    p0, p1 = Vector(p_alt), Vector(p_ust)
    yan = Vector(yan).normalized() * (genislik / 2)
    for sy in (-1, 1):
        boru(f"{name}_dikme{sy}", p0 + yan * sy, p1 + yan * sy, 0.022, M["sari"], parent, seg=12)
    n = int((p1 - p0).length / adim)
    for i in range(1, n):
        q = p0 + (p1 - p0) * (i / n)
        boru(f"{name}_basamak{i}", q - yan, q + yan, 0.014, M["sari"], parent, seg=10)


def kablo_tamburu(name, loc, M, parent, eksen="X"):
    x, y, z = loc
    silindir(f"{name}_flans1", 0.55, 0.02, (x - 0.12, y, z), M["antrasit"], parent, axis=eksen, bevel=0.004)
    silindir(f"{name}_flans2", 0.55, 0.02, (x + 0.12, y, z), M["antrasit"], parent, axis=eksen, bevel=0.004)
    silindir(f"{name}_sarim", 0.42, 0.22, (x, y, z), M["siyah"], parent, axis=eksen)
    silindir(f"{name}_gobek", 0.08, 0.40, (x, y, z), M["celik"], parent, axis=eksen)
    kutu(f"{name}_motor", (0.28, 0.26, 0.26), (x + 0.30, y, z), M["turuncu"], parent, bevel=0.02)
    kutu(f"{name}_konsol", (0.08, 0.10, 0.75), (x - 0.18, y, z - 0.25), M["antrasit"], parent, bevel=0.004)
    # kablo tamburun altından zemindeki kablo kanalına iner
    kablo(f"{name}_kablo", [(x, y, z - 0.42), (x, y, 0.35), (x, y - 0.15, 0.08), (x, y - 0.6, 0.02), (x, y - 5.0, 0.02)],
          0.018, M["siyah"], parent)
    kutu(f"{name}_kanal", (0.16, 7.0, 0.012), (x, y - 3.2, -0.115), M["antrasit"], parent, bevel=0.002)


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
YAN = BEYAZ and os.environ.get("GORUNUS", "yan") == "yan"  # orijinal çizimler gibi tam yandan görünüş
RAY = 6.0 if BEYAZ else 30.0
FOTOLAR = []  # (dosya, nesne, yerel_nokta, yukseklik_m, yatay_capa)


def ortam(M, **kw):
    """Gölgesiz düz beyaz arka plan veya fabrika holü."""
    if not BEYAZ:
        return hol(M, **kw)
    return None  # zemin yok: düz beyaz arka plan, gölge yok


def foto_vinc(dosya, nesne, nokta, yukseklik, capa=0.5, dikey=0.0, arkasinda=(), halat=None,
              eksen=None, genislik_carpani=1.0, kirp_ust=0.0):
    """Gerçek ürün fotoğrafını sahnedeki bir düzleme perspektifli olarak yerleştir.

    Fotoğraf gerçek ölçüsünde (yükseklik m) bir düzleme oturtulur; dört köşesi kameraya
    izdüşürülüp homografi ile bükülür. eksen=None: düzlem kameraya diktir (fotoğraf kendi
    perspektifini taşır; sahne kamerası fotoğrafın çekim açısına göre ayarlanır).
    eksen verilirse düzlem `nesne` yerel `eksen` (yatay) ve Z doğrultularındadır; fotoğraf aynı açıdan
    çekilmişse genislik_carpani=1/cos(açı) kendi kısalmasını telafi eder (perspektif iki kez uygulanmaz).
    kirp_ust: fotoğrafın üstten bu oranı atılır (ör. arabası 3B modellenen caraskalda yalnız gövde kalır);
    yukseklik kırpılmamış fotoğrafın yüksekliğidir.
    nokta: fotoğrafın yatayda `capa`, düşeyde `dikey` oranına (0 = üst kenar) denk gelen nokta,
    arkasinda: fotoğrafın önünde kalacak nesnelerin ad önekleri (ör. ön kiriş),
    halat: (ust_oran, alt_oran, kanca_z) - yalnız halat bandını uzatıp kancayı kanca_z'ye indirir.
    """
    FOTOLAR.append((os.path.join(FOTO_KLASOR, dosya), nesne, Vector(nokta), yukseklik, capa, dikey,
                    tuple(arkasinda), halat, None if eksen is None else Vector(eksen).normalized(), genislik_carpani,
                    kirp_ust))


def _homografi(hedef, kaynak):
    """PIL PERSPECTIVE katsayıları: çıktı (hedef) noktası -> girdi (kaynak) noktası."""
    import numpy as np

    A, B = [], []
    for (x, y), (u, v) in zip(hedef, kaynak):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def maske_render(onekler, yol):
    """Yalnızca verilen nesnelerin kapsama maskesini (alfa) render et."""
    sc = bpy.context.scene
    for o in sc.objects:
        if o.type in {"MESH", "CURVE", "FONT"} and not o.name.startswith(onekler):
            o.hide_render = True
    beyaz = bpy.data.materials.new("maske")
    nt = node_tree(beyaz)
    nt.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 1, 1, 1)
    nt.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.0
    bpy.context.view_layer.material_override = beyaz
    sc.cycles.samples = 4
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.render.film_transparent = True
    sc.render.filepath = yol
    bpy.ops.render.render(write_still=True)


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
    taban = img.copy()

    def ekran(p):
        q = world_to_camera_view(sc, sc.camera, p)
        return (q.x * W, (1 - q.y) * H)

    yerlesim = []
    for dosya, nesne, nokta, yuk, capa, dikey, arkasinda, halat, eksen, gcarp, kirp in FOTOLAR:
        foto = Image.open(dosya).convert("RGBA")
        if kirp:
            foto = foto.crop((0, round(kirp * foto.height), foto.width, foto.height))
            yuk *= 1 - kirp
        fw, fh = foto.size
        gen = yuk * fw / fh * gcarp
        if halat:
            r1, r2, kanca_z = halat
            a, b = round(r1 * fh), round(r2 * fh)
            kanca_alt = (nesne.matrix_world @ nokta).z - (1 - dikey) * yuk
            ek_m = max(0.0, kanca_alt - kanca_z)
            orta = foto.crop((0, a, fw, b)).resize((fw, round(b - a + ek_m * fh / yuk)), Image.BICUBIC)
            yeni = Image.new("RGBA", (fw, a + orta.height + fh - b), (0, 0, 0, 0))
            yeni.paste(foto.crop((0, 0, fw, a)), (0, 0))
            yeni.paste(orta, (0, a))
            yeni.paste(foto.crop((0, b, fw, fh)), (0, a + orta.height))
            ust_m = dikey * yuk
            foto, fh = yeni, yeni.height
            yuk = yuk + ek_m
            dikey = ust_m / yuk
        mw = nesne.matrix_world
        A = mw @ nokta
        if eksen is None:
            cm = sc.camera.matrix_world.to_3x3()
            eksen = (cm @ Vector((1, 0, 0))).normalized()
            z = (cm @ Vector((0, 1, 0))).normalized()
        else:
            eksen = (mw.to_3x3() @ eksen).normalized()
            z = Vector((0, 0, 1))

        def kose(fx, fy, u=eksen):
            return ekran(A + u * ((fx - capa) * gen) + z * ((dikey - fy) * yuk))

        # fotoğraf ayna görüntüsü olmasın: sol kenar ekranda solda kalsın
        if kose(0, dikey)[0] > kose(1, dikey)[0]:
            eksen = -eksen
        hedef = [kose(0, 0, eksen), kose(1, 0, eksen), kose(1, 1, eksen), kose(0, 1, eksen)]
        katsayi = _homografi(hedef, [(0, 0), (fw, 0), (fw, fh), (0, fh)])
        bukulmus = foto.transform((W, H), Image.PERSPECTIVE, katsayi, Image.BICUBIC)
        yerlesim.append((bukulmus, 0, 0, arkasinda))
    for foto, x, y, _ in yerlesim:
        img.alpha_composite(foto, (x, y))
    onekler = tuple(sorted({o for *_, a in yerlesim for o in a}))
    if onekler:
        yol = os.path.splitext(cikti)[0] + "_maske.png"
        maske_render(onekler, yol)
        m = Image.open(yol).convert("RGBA").getchannel("A")
        os.remove(yol)
        on = taban.copy()
        on.putalpha(m)
        img.alpha_composite(on)
    img.convert("RGB").save(cikti)


def dunya(guc=0.6):
    w = bpy.data.worlds.new("dunya")
    bpy.context.scene.world = w
    nt = node_tree(w)
    bg = nt.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.75, 0.80, 0.88, 1)
    bg.inputs["Strength"].default_value = guc


def kamera(loc, hedef, lens=35, dof=None, kaydir=False):
    cd = bpy.data.cameras.new("kamera")
    cd.lens = lens
    cd.sensor_width = 36
    co = bpy.data.objects.new("kamera", cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = Vector(hedef) - Vector(loc)
    if kaydir:
        # mimari kamera: yatay bakış + mercek kaydırma, dikeyler dik kalır (ürün fotoğrafları gibi)
        yatay = Vector((d.x, d.y, 0))
        cd.shift_y = d.z / yatay.length * lens / cd.sensor_width
        d = yatay
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


def foto_kamera(g, nokta, sapma, yukseklik, uzaklik, hedef, lens):
    """Kamerayı ürün fotoğrafının çekim açısına koy: `nokta`dan (bom ekseni hizası) bom normaline göre
    `sapma` derece sola ve `yukseklik` derece yukarı. Fotoğraflarda araba üst kenarı yatay olduğundan
    kamera bom hizasındadır (yukseklik=0); uzaklaşan bom da böylece yatay görünür. Kadraj `hedef` noktasına mercek kaydırmayla ortalanır."""
    bpy.context.view_layer.update()
    m = g.matrix_world
    H = m @ Vector(nokta)
    n = (m.to_3x3() @ Vector((0, -1, 0))).normalized()  # bomun kameraya bakan yüzünün normali
    yon = Matrix.Rotation(math.radians(-sapma), 3, "Z") @ n
    t = math.radians(yukseklik)
    cam = H + (yon * math.cos(t) + Vector((0, 0, math.sin(t)))) * uzaklik
    hedef = Vector(hedef)
    # yatay bakış hedefin yönünde; düşeyde mercek kaydırma
    kamera(tuple(cam), (hedef.x, hedef.y, hedef.z), lens=lens, kaydir=True)


def monoray_araba(name, x, z_alt, b, tf, M, g):
    """Bomun alt flanşında yürüyen elektrikli caraskal arabası (Beta 2 ton arabasına benzer).

    z_alt: bom alt yüzü, b: flanş genişliği, tf: flanş kalınlığı. Askı kulağının alt kotunu döndürür.
    """
    zf = z_alt + tf  # flanş üst yüzü = tekerlek basma kotu
    r = 0.045
    yp = b / 2 + 0.035  # yan levhalar flanşın dışında
    for sy in (-1, 1):
        kutu(f"{name}_levha{sy}", (0.34, 0.016, 0.24), (x, sy * yp, zf + 0.03), M["antrasit"], g, bevel=0.004)
        for sx in (-1, 1):
            # tekerlek flanş üstünde, web ile yan levha arasında
            silindir(f"{name}_tek{sy}{sx}", r, 0.032, (x + sx * 0.11, sy * (b / 4 + 0.012), zf + r), M["celik"], g, axis="Y", bevel=0.003)
            silindir(f"{name}_tekflans{sy}{sx}", r + 0.008, 0.006, (x + sx * 0.11, sy * (b / 2 - 0.004), zf + r), M["celik"], g, axis="Y")
            silindir(f"{name}_aks{sy}{sx}", 0.012, 0.06, (x + sx * 0.11, sy * (yp - 0.02), zf + r), M["celik"], g, axis="Y")
            civata(f"{name}_akssomun{sy}{sx}", (x + sx * 0.11, sy * (yp + 0.008), zf + r), "Y" if sy > 0 else "-Y", M, g, r=0.012)
        civata_izgara(f"{name}_levhac{sy}", (x, sy * (yp + 0.008), zf - 0.06), (1, 0, 0), (0, 0, 1), 3, 1, 0.08, 0.0,
                      "Y" if sy > 0 else "-Y", M, g, r=0.010)
    # alt travers (iki levhayı flanşın altından bağlar) + askı kulağı
    kutu(f"{name}_travers", (0.14, 2 * yp + 0.04, 0.05), (x, 0, z_alt - 0.055), M["antrasit"], g, bevel=0.006)
    for sy in (-1, 1):
        civata(f"{name}_traversc{sy}", (x, sy * (yp + 0.028), z_alt - 0.055), "Y" if sy > 0 else "-Y", M, g, r=0.013)
    kutu(f"{name}_kulak", (0.06, 0.03, 0.09), (x, 0, z_alt - 0.12), M["antrasit"], g, bevel=0.004)
    silindir(f"{name}_askipim", 0.016, 0.07, (x, 0, z_alt - 0.13), M["celik"], g, axis="Y")
    # ön levhada "2 ton" kutusu, arka levhada yürütme motoru
    kutu(f"{name}_kutu", (0.26, 0.10, 0.15), (x + 0.02, -(yp + 0.06), zf + 0.06), M["antrasit"], g, bevel=0.012)
    yazi(f"{name}_kapasite", "2\nton", (x + 0.06, -(yp + 0.111), zf + 0.065), 0.045, M["beyaz"], g)
    for k, dz in enumerate((0.03, -0.01)):
        silindir(f"{name}_tapa{k}", 0.012, 0.01, (x - 0.06, -(yp + 0.112), zf + 0.06 + dz), M["siyah"], g, axis="Y")
    kutu(f"{name}_red", (0.12, 0.10, 0.12), (x - 0.12, yp + 0.06, zf + 0.04), M["antrasit"], g, bevel=0.01)
    silindir(f"{name}_motor", 0.05, 0.14, (x - 0.12, yp + 0.13, zf + 0.04), M["antrasit"], g, axis="Y", bevel=0.005)
    return z_alt - 0.15


def bom_logo(M, g, x, zb):
    """Bom gövdesine beyaz zemin üzerine 'beta' plakası."""
    kutu("bom_logozemin", (0.62, 0.004, 0.17), (x, -0.008, zb - 0.15), M["beyaz"], g, bevel=0.0015)
    yazi("bom_logo", "beta", (x, -0.0105, zb - 0.155), 0.13, M["antrasit"], g)


def sahne_duvar_pergel(M):
    ortam(M, arka_y=7.0)
    # bina betonarme kolonu
    beton = boya("beton_kolon", (0.36, 0.36, 0.345, 1), rough=0.85, var=0.1, bump=0.4)
    kutu("bina_kolon", (0.6, 0.6, 12.0), (-0.3, 0, 6.0), beton, bevel=0.01)
    zb = 4.30  # bom üst kotu (IPE 300)
    z_alt, z_ust = zb - 0.16, 5.55  # mafsal kotları: alt = bom kökü, üst = gergi başı
    XP = 0.22  # mafsal (pim) ekseni = dönme ekseni
    # dönen grup: orijini pim ekseninde
    SAPMA, YUKSEKLIK = 10, 0  # zincirli vinç fotoğrafının çekim açısı (soldan, yukarıdan; derece)
    g = bos("pergel", (XP, 0, 0), (0, 0, math.radians(SAPMA if YAN else 18)))
    # --- duvar konsolu (sabit): taban levhası, her mafsalda alt/üst kulak levhaları + guse, dikey pim
    kutu("konsol_plaka", (0.03, 0.42, 2.0), (0.015, 0, 4.75), M["antrasit"], bevel=0.004)
    for zz in (3.85, 4.45, 5.25, 5.68):
        for yy in (-0.15, 0.15):
            civata(f"ankraj{zz}{yy}", (0.03, yy, zz), "X", M, None, r=0.018)
    for z in (z_alt, z_ust):
        for sz in (-1, 1):
            zl = z + sz * 0.085
            kutu(f"kulak{z}{sz}", (XP - 0.03, 0.20, 0.025), ((0.03 + XP) / 2, 0, zl), M["antrasit"], None, bevel=0.003)
            silindir(f"kulak_uc{z}{sz}", 0.10, 0.025, (XP, 0, zl), M["antrasit"], None, seg=48, bevel=0.003)
            # guse: kulağı duvar levhasına bağlar (kulağın dış yüzünde)
            uye(f"kulak_guse{z}{sz}", (0.03, 0, zl + sz * 0.075), (XP - 0.02, 0, zl + sz * 0.018), 0.02, 0.02, 0.13, 0.012,
                M["antrasit"], None, up=Vector((0, 1, 0)), bevel=0.002)
        silindir(f"pim{z}", 0.035, 0.27, (XP, 0, z), M["celik"], None, seg=32)
        silindir(f"pim_pul{z}", 0.05, 0.012, (XP, 0, z + 0.104), M["celik"], None, seg=32)
        silindir(f"pim_somun{z}", 0.045, 0.03, (XP, 0, z + 0.125), M["celik"], None, seg=6)
        silindir(f"pim_bas{z}", 0.05, 0.02, (XP, 0, z - 0.107), M["celik"], None, seg=32)
    # --- bom (dönen): kök göbeği pimin etrafında, guselerle bom alın levhasına
    x0 = 0.11  # bom alın levhası (yerel)
    silindir("kok_gobek", 0.058, 0.14, (0, 0, z_alt), M["turuncu"], g, seg=48, bevel=0.004)
    for sy in (-1, 1):
        kutu(f"kok_guse{sy}", (x0 - 0.03, 0.02, 0.30), ((x0 + 0.03) / 2, sy * 0.045, zb - 0.15), M["turuncu"], g, bevel=0.003)
    kutu("bom_alin", (0.025, 0.22, 0.34), (x0, 0, zb - 0.15), M["turuncu"], g, bevel=0.003)
    civata_izgara("bom_alin_c", (x0 + 0.016, 0, zb - 0.15), (0, 1, 0), (0, 0, 1), 2, 3, 0.15, 0.11, "X", M, g, r=0.012)
    ipe("bom", x0 + 0.012, 4.3, zb, 0.30, 0.15, M["turuncu"], g, tf=0.022, tw=0.011)
    kutu("bom_uc", (0.02, 0.22, 0.34), (4.31, 0, zb - 0.15), M["antrasit"], g, bevel=0.004)
    bom_logo(M, g, 1.25, zb)
    for sy in (-1, 1):
        kutu(f"stoper{sy}", (0.05, 0.03, 0.06), (4.22, sy * 0.06, zb - 0.33), M["siyah"], g, bevel=0.01)
    # --- gergi: üst göbek (pim etrafında) + çatal, gerdirme, bom üst flanşındaki kulak
    xg = 3.45
    silindir("gergi_gobek", 0.05, 0.14, (0, 0, z_ust), M["turuncu"], g, seg=48, bevel=0.004)
    p0 = Vector((0.06, 0, z_ust - 0.01))
    p1 = Vector((xg, 0, zb + 0.10))
    aci = math.atan2(p0.z - p1.z, p1.x - p0.x)
    kutu("gergi_bas_catal", (0.16, 0.07, 0.06), (0.07, 0, z_ust - 0.005), M["turuncu"], g, bevel=0.008, rot=(0, aci, 0))
    boru("gergi", p0, p1, 0.042, M["turuncu"], g)
    pg = p0 + (p1 - p0) * 0.42
    kutu("gergi_gerdirme", (0.22, 0.09, 0.09), tuple(pg), M["antrasit"], g, bevel=0.01, rot=(0, aci, 0))
    kutu("gergi_bom_kulak", (0.18, 0.03, 0.14), (xg, 0, zb + 0.07), M["antrasit"], g, bevel=0.006)
    silindir("gergi_bom_pim", 0.022, 0.12, (xg, 0, zb + 0.10), M["celik"], g, axis="Y")
    kutu("gergi_uc_catal", (0.14, 0.09, 0.07), (xg - 0.08, 0, zb + 0.13), M["antrasit"], g, bevel=0.01, rot=(0, aci, 0))
    # festoon bomun yanında, üst flanşın altında (bom üstü gergi kulağına serbest)
    festoon("festoon", 0.3, 4.1, -0.23, zb - 0.09, 0.4, 3.25 - 0.42, M, g, n=5, L=1.1,
            y_konsol=-0.02, z_konsol=zb - 0.022, aralik=1.2)
    # caraskal arabası 3B: tekerlekler bomun alt flanşında (ray); caraskal gövdesi ürün fotoğrafı, askıya asılı
    z_askı = monoray_araba("araba", 3.25, zb - 0.30, 0.15, 0.022, M, g)
    foto_vinc("zincirli_vinc_2ton.png", g, (3.25, 0, z_askı), 1.25, capa=0.60, dikey=0.0,
              arkasinda=("festoon",), eksen=(1, 0, 0), kirp_ust=0.215,
              genislik_carpani=1 / math.cos(math.radians(SAPMA)))  # bomla aynı perspektif
    if not BEYAZ:
        palet(M, (4.6, 0.1, 0), 0.35)
    if YAN:
        foto_kamera(g, (3.25, 0, zb - 0.15), SAPMA, YUKSEKLIK, 12.5, (2.0, 0.6, 3.3), lens=42)
    else:
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
    SAPMA, YUKSEKLIK = 40, 0  # kompakt vinç fotoğrafının çekim açısı (soldan, yukarıdan; derece)
    g = bos("pergel", (0, 0, 0), (0, 0, math.radians(SAPMA if YAN else 15)))
    zb = H + 0.48
    silindir("baslik", 0.215, 0.36, (0, 0, H + 0.30), M["antrasit"], g, seg=64, bevel=0.01)
    silindir("baslik_serit", 0.217, 0.05, (0, 0, H + 0.42), M["turuncu"], g, seg=64)
    silindir("baslik_kapak", 0.23, 0.04, (0, 0, H + 0.50), M["antrasit"], g, seg=64, bevel=0.008)
    ipe("bom", 0.18, 4.4, zb, 0.30, 0.15, M["turuncu"], g, tf=0.022, tw=0.011)
    kutu("bom_kok", (0.22, 0.26, 0.40), (0.22, 0, zb - 0.18), M["turuncu"], g, bevel=0.02)
    kutu("bom_uc", (0.02, 0.22, 0.34), (4.41, 0, zb - 0.15), M["antrasit"], g, bevel=0.004)
    bom_logo(M, g, 1.3, zb)
    # üstten gergi: dönen başlık üstünde direk, tepesinden bomun üst flanşına (alt flanş serbest)
    zd = zb + 1.35
    silindir("direk", 0.11, zd - (H + 0.52), (0, 0, (zd + H + 0.52) / 2), M["gri"], g, seg=48)
    silindir("direk_kapak", 0.14, 0.05, (0, 0, zd + 0.025), M["antrasit"], g, seg=48, bevel=0.006)
    kutu("direk_kulak", (0.20, 0.03, 0.16), (0.14, 0, zd - 0.06), M["antrasit"], g, bevel=0.006)
    silindir("direk_pim", 0.022, 0.12, (0.2, 0, zd - 0.06), M["celik"], g, axis="Y")
    xg = 3.45
    boru("gergi", (0.2, 0, zd - 0.06), (xg, 0, zb + 0.10), 0.042, M["turuncu"], g)
    kutu("gergi_bom_kulak", (0.18, 0.03, 0.14), (xg, 0, zb + 0.07), M["antrasit"], g, bevel=0.006)
    silindir("gergi_bom_pim", 0.022, 0.12, (xg, 0, zb + 0.10), M["celik"], g, axis="Y")
    kutu("gergi_gerdirme", (0.22, 0.09, 0.09), (1.7, 0, zd - 0.06 - (zd - 0.16 - zb) * (1.5 / 3.25)), M["antrasit"], g, bevel=0.01,
         rot=(0, math.atan2(zd - 0.16 - zb, 3.25), 0))
    for i in range(6):  # direk - başlık flanşı
        a_ = i * math.pi / 3
        civata(f"direk_c{i}", (0.17 * math.cos(a_), 0.17 * math.sin(a_), H + 0.52), "Z", M, g, r=0.011)
    civata_izgara("bom_kok_c", (0.22, -0.132, zb - 0.18), (1, 0, 0), (0, 0, 1), 2, 3, 0.11, 0.11, "-Y", M, g, r=0.013)
    for i in range(10):
        a_ = i * 2 * math.pi / 10
        civata(f"bilezik_c{i}", (0.192 * math.cos(a_), 0.192 * math.sin(a_), H + 0.14), "Z", M, None, r=0.012)
    festoon("festoon", 0.35, 4.3, -0.23, zb - 0.09, 0.45, 3.45 - 0.45, M, g, n=5, L=1.1,
            y_konsol=-0.02, z_konsol=zb - 0.022, aralik=1.2)
    foto_vinc("kompakt_vinc.png", g, (3.45, 0, zb - 0.282), 1.10, capa=0.66, dikey=0.235,
              arkasinda=("festoon", "bom_alt"), eksen=(1, 0, 0),
              genislik_carpani=1 / math.cos(math.radians(SAPMA)))  # bomla aynı perspektif
    if not BEYAZ:
        palet(M, (4.4, -0.6, 0), 0.3)
    if YAN:
        foto_kamera(g, (3.45, 0, zb - 0.15), SAPMA, YUKSEKLIK, 12.5, (1.5, 0.9, 3.0), lens=38)
    else:
        kamera((4.4, -6.6, 2.4), (2.0, 0.3, 2.65), lens=32, dof=9)
    anahtar_isik((3, -9, 8), (1.5, 0, 2), 1800, boyut=6)


def portal_ayak_x(name, xc, z_alt, z_ust, M, g, derinlik):
    """Orijinal çizimdeki gibi açıklık düzleminde A tipi ayak (iki konik kol + ara bağ)."""
    alt, ust = 0.75, 0.18
    for sx in (-1, 1):
        uye(f"{name}_kol{sx}", (xc + sx * alt, 0, z_alt), (xc + sx * ust, 0, z_ust), derinlik, derinlik,
            0.30, 0.40, M["turuncu"], g, up=Vector((0, 1, 0)), bevel=0.01)
        kutu(f"{name}_flans{sx}", (0.46, derinlik + 0.04, 0.03), (xc + sx * alt, 0, z_alt + 0.015), M["turuncu"], g, bevel=0.004)
    t = 0.42
    zc = z_alt + (z_ust - z_alt) * t
    yar = alt - (alt - ust) * t
    kutu(f"{name}_bag", (2 * yar, derinlik * 0.9, 0.16), (xc, 0, zc), M["turuncu"], g, bevel=0.008)


def bas_araba_x(name, xc, z, M, g, derinlik):
    """X doğrultusunda yürüyen baş arabası; tekerlekler yandan görünür."""
    L = 2.3
    kutu(name, (L, derinlik, 0.36), (xc, 0, z + 0.33), M["antrasit"], g, bevel=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            yy = sy * (derinlik / 2 + 0.05)
            silindir(f"{name}_tek{sx}{sy}", 0.17, 0.10, (xc + sx * 0.8, yy, z + 0.20), M["antrasit"], g, axis="Y", bevel=0.006)
            silindir(f"{name}_gobek{sx}{sy}", 0.06, 0.13, (xc + sx * 0.8, yy + sy * 0.02, z + 0.20), M["celik"], g, axis="Y")
        kutu(f"{name}_tampon{sx}", (0.10, 0.14, 0.12), (xc + sx * (L / 2 + 0.05), 0, z + 0.33), M["siyah"], g, bevel=0.02)
    kutu(f"{name}_red", (0.30, 0.22, 0.28), (xc + 0.35, -derinlik / 2 - 0.13, z + 0.42), M["turuncu"], g, bevel=0.02)
    silindir(f"{name}_motor", 0.10, 0.34, (xc + 0.75, -derinlik / 2 - 0.13, z + 0.42), M["antrasit"], g, axis="X", bevel=0.01)


def ray_x(name, x0, x1, y, M):
    L = x1 - x0
    cx = (x0 + x1) / 2
    kutu(name + "_taban", (L, 0.16, 0.02), (cx, y, 0.01), M["ray"], bevel=0.003)
    kutu(name + "_govde", (L, 0.03, 0.07), (cx, y, 0.055), M["ray"], bevel=0.002)
    kutu(name + "_mantar", (L, 0.07, 0.035), (cx, y, 0.105), M["ray"], bevel=0.006)


def portal_govde(M, g, span, z_ust, h, cift_ayak=True, ray_ust=0.0, kanca_z=1.6, foto=None, yan=None, yakin_x=None):
    """Çift kirişli portal. yan=False: gerçek yapı (ayaklar kirişe dik düzlemde A, raylar kirişe dik)."""
    yan = YAN if yan is None else yan
    # kiriş aksları: fotoğraftaki arabanın tekerlek açıklığına (~2,2 m) göre
    yk = 1.1 if (foto and not yan) else 0.48
    kutu_kiris("kiris_on", 0, span, -yk, z_ust, h, 0.5 if yk > 1 else 0.42, M, g, logo_yuzu=True)
    kutu_kiris("kiris_arka", 0, span, yk, z_ust, h, 0.5 if yk > 1 else 0.42, M, g)
    for x in (0.0, span):
        kutu(f"bas_kirisi{x:g}", (0.5, 2 * yk + 0.6, h * 0.8), (x, 0, z_ust - h * 0.45), M["turuncu"], g, bevel=0.012)
        if not yan:
            # uç kirişlerde siyah ikaz şeritleri
            sx = 1 if x > 0 else -1
            for k in range(3):
                kutu(f"bas_kirisi{x:g}_serit{k}", (0.006, 0.07, h * 0.75), (x + sx * 0.253, 0.35 + k * 0.16, z_ust - h * 0.45),
                     M["siyah"], g, bevel=0.0, rot=(math.radians(35), 0, 0))
    # yürüyüş yolu ve korkuluk (arka kirişin dış yanında)
    ky = yk + (0.25 if yk > 1 else 0.48)
    if not yan:
        for i in range(int(span / 1.0) + 1):
            kutu(f"korkuluk_dikme{i}", (0.04, 0.04, 1.0), (i * span / int(span), ky + 0.5, z_ust + 0.5), M["sari"], g, bevel=0.004)
        kutu("korkuluk_ust", (span, 0.04, 0.04), (span / 2, ky + 0.5, z_ust + 1.0), M["sari"], g, bevel=0.004)
        kutu("korkuluk_orta", (span, 0.03, 0.03), (span / 2, ky + 0.5, z_ust + 0.5), M["sari"], g, bevel=0.004)
        kutu("yurume_yolu", (span, 0.6, 0.03), (span / 2, ky + 0.25, z_ust - 0.015), M["antrasit"], g, bevel=0.002)
    # ayaklar
    zl = z_ust - h
    if yan:
        der = 2 * yk + 0.42
        for i, xa in enumerate((1.6, span - 1.6) if cift_ayak else (1.6,)):
            portal_ayak_x(f"ayak{i}", xa, 0.62, zl, M, g, der)
            bas_araba_x(f"bas{i}", xa, ray_ust, M, g, der)
            for sy in (-1, 1):
                ray_x(f"ray{i}{sy}", xa - 2.2, xa + 2.2, sy * (der / 2 + 0.05), M)
    else:
        ya = yk + 1.6 if yk > 1 else 1.7
        yu = yk if yk > 1 else 0.55
        z_ayak = z_ust - 0.85 * h  # uç kirişin alt yüzü
        for ad, x in (("sol", 0.0), ("sag", span)) if cift_ayak else (("sol", 0.0),):
            portal_ayak(f"ayak_{ad}", x, ya, yu, 0.62, z_ayak, M, g)
            bas_araba(f"bas_{ad}", x, -ya - 0.5, ya + 0.5, M, g, z=ray_ust)
        # uç kiriş - ana kiriş birleşimi: alın cıvataları ve yan ek levhaları
        bkal = 0.5 if yk > 1 else 0.42
        for x in (0.0, span):
            sx = 1 if x > 0 else -1
            for sy in (-1, 1):
                civata_izgara(f"uc_birlesim{x:g}{sy}", (x + sx * 0.252, sy * yk, z_ust - h * 0.45), (0, 1, 0), (0, 0, 1),
                              3, 5, 0.14, h * 0.15, "X" if sx > 0 else "-X", M, g, r=0.015)
                yy = sy * (yk + bkal / 2 + 0.008)
                kutu(f"ek_levha{x:g}{sy}", (0.36, 0.014, h * 0.82), (x - sx * 0.43, yy, z_ust - h / 2), M["turuncu"], g, bevel=0.003)
                civata_izgara(f"ek_levhac{x:g}{sy}", (x - sx * 0.43, yy + sy * 0.008, z_ust - h / 2), (1, 0, 0), (0, 0, 1),
                              2, 5, 0.2, h * 0.15, "Y" if sy > 0 else "-Y", M, g, r=0.014)
        # ray sonu tamponları
        for x in ((0.0, span) if cift_ayak else (0.0,)):
            for sy in (-1, 1):
                kutu(f"ray_stop{x:g}{sy}", (0.3, 0.25, 0.35), (x, sy * (RAY - 0.1), 0.175), M["antrasit"], bevel=0.01)
                silindir(f"ray_tampon{x:g}{sy}", 0.09, 0.14, (x, sy * (RAY - 0.3), 0.3), M["siyah"], axis="Y", bevel=0.01)
        if yakin_x is not None:
            # yakın uçtaki ön ayakta merdiven, yakın ayakta besleme kablo tamburu
            sxn = 1 if yakin_x > 0 else -1
            dis = sxn * 0.28
            merdiven("merdiven", (yakin_x + dis, -ya + 0.15, 0.9), (yakin_x + dis, -yu - 0.1, z_ayak - 0.2), 0.42, M, g,
                     yan=Vector((1, 0, 0)))
            kablo_tamburu("tambur", (yakin_x + sxn * 0.55, ya * 0.62, 2.4), M, g)
        # festoon (ön kirişin dış yanında): sabit uç uzak kiriş başında, çekme arabası vinç arabasının yanında
        if foto:
            yf = -(yk + bkal / 2 + 0.32)
            x_tr = span * (0.36 if (yakin_x or 0) > 0 else 0.58)
            x_sabit = 0.35 if (yakin_x or 0) > 0 else span - 0.35
            festoon("festoon", 0.2, span - 0.2, yf, z_ust + 0.22, x_sabit, x_tr + (-0.75 if x_tr > x_sabit else 0.75),
                    M, g, n=6, L=1.8, y_konsol=-(yk + bkal / 2 + 0.03), z_konsol=z_ust)
    if foto:
        # Beta halatlı vinç arabası fotoğrafı: iki kirişin raylarına basar
        dosya, yuk, capa, dikey = foto
        onunde = ["kiris_on", "festoon", "ek_levha"]
        if yakin_x is not None:
            onunde += [f"bas_kirisi{yakin_x:g}", "ayak_sag" if yakin_x > 0 else "ayak_sol"]
        xa = span * (0.36 if (yakin_x or 0) > 0 else 0.58)
        foto_vinc(dosya, g, (xa, 0, z_ust + 0.05), yuk, capa=capa, dikey=dikey,
                  arkasinda=tuple(onunde), halat=(0.45, 0.60, kanca_z),
                  eksen=None if yan else (0, 1, 0))
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
    portal_govde(M, g, span, 6.6, 1.0, cift_ayak=True, kanca_z=2.4, yan=False, yakin_x=span,
                 foto=("halatli_vinc_araba.png", 2.3, 0.5, 0.44) if BEYAZ else None)
    # yük: çelik sac paketi
    if not BEYAZ:
        yuk_kasa(M, (span * 0.47 - 0.15, -0.0, 0.0))
    if BEYAZ:
        # araba fotoğrafı gibi: kiriş doğrultusuna yakın (~20° yandan), ~9° yukarıdan
        a = math.radians(25)
        d = 30.0
        kamera((span / 2 + d * math.cos(a), -d * math.sin(a), 7.8 + d * math.tan(math.radians(9))),
               (span / 2 + 3.6, 0, 3.4), lens=48, kaydir=True)
    else:
        kamera((13.4, -11.0, 1.8), (5.4, 0.0, 3.7), lens=24, dof=12)
    anahtar_isik((4, -12, 10), (5, 0, 3), 3500, boyut=8)


def sahne_yari_portal(M):
    ortam(M, arka_y=9.5, sol_x=-9.0)
    span = 11.0
    # sağda betonarme bina kolonları + yürüyüş yolu kirişi
    beton = boya("beton_kolon", (0.36, 0.36, 0.345, 1), rough=0.85, var=0.1, bump=0.4)
    kx = span + 0.75
    KH = 9.5 if BEYAZ else 12
    for i, y in enumerate((-3.5, 3.5) if BEYAZ else (-12, -6, 0, 6, 12)):
        kutu(f"bina_kolon{i}", (0.6, 0.6, KH), (kx, y, KH / 2), beton, bevel=0.01)
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
    portal_govde(M, g, span, zust, 0.85, cift_ayak=False, kanca_z=2.4, yan=False, yakin_x=0.0,
                 foto=("halatli_vinc_araba.png", 2.3, 0.5, 0.44) if BEYAZ else None)
    # yol kirişi üzerindeki baş arabası
    bas_araba("bas_sag", span, -1.9, 1.9, M, g, z=6.68)
    kutu("sag_bas_baglanti", (0.5, 2.8, 0.25), (span, 0, zust - 0.85 - 0.12 + 0.0), M["turuncu"], g, bevel=0.01)
    if not BEYAZ:
        yuk_kasa(M, (span * 0.47 - 0.15, 0.0, 0.0))
    if BEYAZ:
        a = math.radians(25)
        d = 30.0
        kamera((span / 2 - d * math.cos(a), -d * math.sin(a), 8.9 + d * math.tan(math.radians(9))),
               (span / 2 - 1.2, 0, 4.0), lens=48, kaydir=True)
    else:
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
