"""
Beta Vinç - "Bir vincin yolculuğu" 3B animasyonu: sahne kareleri (Blender EEVEE).

Yazılar/arayüz bu karelere kompozit.py ile (TR/EN) eklenir.

Kullanım:
    python animasyon3b.py <sahne> <cikti_klasoru> [ilk_kare son_kare] [--adim N]
    sahneler: acilis siparis kesif muhendislik imalat sevkiyat nakliye kurulum kapanis
"""
import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_vincler as rv  # noqa: E402

FPS = 25
RX, RY = 1280, 720
KLASOR = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(KLASOR, "logo")

SURE = dict(acilis=4.0, siparis=7.0, kesif=8.0, muhendislik=6.0, imalat=10.0, sevkiyat=8.5, nakliye=8.0,
            kurulum=11.0, kapanis=4.5)


# ---------------------------------------------------------------- temel
def hazirla():
    rv.sifirla()
    rv.MATS.clear()
    rv._CIVATA_MESH.clear()
    rv.FONT = rv.font_yukle()
    M = rv.malzemeler()
    sc = bpy.context.scene
    sc.render.fps = FPS
    return M, sc


def dunya(renk=(0.85, 0.88, 0.92), guc=0.8):
    w = bpy.data.worlds.new("dunya")
    bpy.context.scene.world = w
    nt = rv.node_tree(w)
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*renk, 1)
    bg.inputs["Strength"].default_value = guc


def gunes(aci=(50, 0, 35), guc=3.0, renk=(1.0, 0.96, 0.9), yumusak=2.0):
    ld = bpy.data.lights.new("gunes", "SUN")
    ld.energy = guc
    ld.color = renk
    ld.angle = math.radians(yumusak)
    o = bpy.data.objects.new("gunes", ld)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(a) for a in aci)
    return o


def alan_isigi(loc, hedef, guc, boyut=6, renk=(1, 0.97, 0.92)):
    o = rv.anahtar_isik(loc, hedef, guc, boyut=boyut, renk=renk)
    return o


def zemin(renk=(0.82, 0.8, 0.77), boyut=200, mat=None):
    m = mat or rv.boya("zemin3b", (*renk, 1), rough=0.75, var=0.05)
    return rv.duzlem("zemin", (boyut, boyut), (0, 0, 0), (0, 0, 0), m)


def kamera_yolu(kareler, lens=35):
    """kareler: [(kare, (x,y,z), (hx,hy,hz)), ...] — konum ve bakış noktası anahtar kareleri."""
    cd = bpy.data.cameras.new("kamera")
    cd.lens = lens
    cd.sensor_width = 36
    co = bpy.data.objects.new("kamera", cd)
    bpy.context.scene.collection.objects.link(co)
    hedef = bpy.data.objects.new("kamera_hedef", None)
    bpy.context.scene.collection.objects.link(hedef)
    for f, p, h in kareler:
        co.location = p
        co.keyframe_insert("location", frame=f)
        hedef.location = h
        hedef.keyframe_insert("location", frame=f)
    c = co.constraints.new("TRACK_TO")
    c.target = hedef
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    bpy.context.scene.camera = co
    return co, hedef


def anahtar(o, yol, kareler, interp="BEZIER"):
    """kareler: [(kare, deger), ...]; yol: 'location', 'rotation_euler', 'scale' veya ('location', 2) gibi."""
    if isinstance(yol, tuple):
        yol, idx = yol
    else:
        idx = -1
    for f, v in kareler:
        if idx >= 0:
            getattr(o, yol)[idx] = v
            o.keyframe_insert(yol, index=idx, frame=f)
        else:
            setattr(o, yol, v)
            o.keyframe_insert(yol, frame=f)
    if o.animation_data and o.animation_data.action:
        try:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = interp
        except Exception:
            pass


def gorunur(o, kareler):
    """[(kare, True/False)] — nesne ve çocuklarının render görünürlüğü."""
    hepsi = [o] + list(o.children_recursive)
    for ob in hepsi:
        for f, v in kareler:
            ob.hide_render = not v
            ob.keyframe_insert("hide_render", frame=f)
            ob.hide_viewport = not v
            ob.keyframe_insert("hide_viewport", frame=f)
        if ob.animation_data and ob.animation_data.action:
            try:
                for fc in ob.animation_data.action.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
            except Exception:
                pass


def bos(ad, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(ad, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.parent = parent
    return e


def isik_mat(ad, renk, guc=5.0):
    m = bpy.data.materials.new(ad)
    nt = rv.node_tree(m)
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*renk[:3], 1)
    b.inputs["Emission Color"].default_value = (*renk[:3], 1)
    b.inputs["Emission Strength"].default_value = guc
    return m


def resim_mat(ad, dosya, isik=0.0):
    m = bpy.data.materials.new(ad)
    nt = rv.node_tree(m)
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(dosya)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"])
    if isik:
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = isik
    b.inputs["Roughness"].default_value = 0.6
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m, tx.image.size[:]


def logo_levha(ad, dosya, gen, loc, rot, parent=None, isik=0.0):
    m, (w, h) = resim_mat(ad, dosya, isik)
    o = rv.duzlem(ad, (gen, gen * h / w), loc, rot, m)
    # UV haritası (dokunun düzleme oturması için)
    me = o.data
    uv = me.uv_layers.new(name="UV")
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        uv.data[li].uv = ((co.x - min(xs)) / (max(xs) - min(xs)), (co.y - min(ys)) / (max(ys) - min(ys)))
    o.parent = parent
    return o


def logo_3b(ad="logo3b", olcek=1.0 / 1000, kalinlik=0.08, mat=None):
    """potrace ile izlenmiş 'beta' işaretinden kabartma 3B logo (eğri dolgu + ekstrüzyon + pah)."""
    g = json.load(open(os.path.join(LOGO_DIR, "beta_isaret.geojson")))
    cu = bpy.data.curves.new(ad, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = kalinlik
    cu.bevel_depth = 0.008
    cu.bevel_resolution = 3
    xs = [p[0] for f in g["features"] for r in f["geometry"]["coordinates"] for p in r]
    ys = [p[1] for f in g["features"] for r in f["geometry"]["coordinates"] for p in r]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    for f in g["features"]:
        for ring in f["geometry"]["coordinates"]:
            sp = cu.splines.new("POLY")
            pts = ring[:-1] if ring[0] == ring[-1] else ring
            sp.points.add(len(pts) - 1)
            for p, q in zip(sp.points, pts):
                p.co = ((q[0] - cx) * olcek, (q[1] - cy) * olcek, 0, 1)
            sp.use_cyclic_u = True
    o = bpy.data.objects.new(ad, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat or rv.boya("logo_koyu", rv.BETA_ANTRASIT, rough=0.3, metal=0.4))
    return o


def eevee(sc, ornek=16):
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = RX
    sc.render.resolution_y = RY
    sc.render.resolution_percentage = int(os.environ.get("YUZDE", "100"))
    try:
        sc.eevee.taa_render_samples = ornek
    except Exception:
        pass
    for k, v in (("use_shadows", True), ("use_raytracing", False), ("shadow_ray_count", 1), ("shadow_step_count", 4)):
        try:
            setattr(sc.eevee, k, v)
        except Exception:
            pass
    sc.render.film_transparent = False
    vs = sc.view_settings
    vs.view_transform = "AgX"
    try:
        vs.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"


# ---------------------------------------------------------------- 3B nesneler
def insan3b(ad, loc, M, yuz=0.0, baret=True, govde=rv.BETA_ANTRASIT, yelek=True, kol_aci=0.0):
    g = bos(ad, loc)
    g.rotation_euler = (0, 0, yuz)
    ten = rv.boya("ten", rv.srgb("#E8B48E"), rough=0.6, var=0)
    kum = rv.boya(ad + "_govde", govde, rough=0.7, var=0)
    pant = rv.boya("pantolon", rv.srgb("#262A30"), rough=0.7, var=0)
    for sy in (-1, 1):
        rv.silindir(f"{ad}_bacak{sy}", 0.075, 0.85, (0, sy * 0.1, 0.43), pant, g, seg=16)
        rv.kutu(f"{ad}_ayak{sy}", (0.26, 0.11, 0.07), (0.05, sy * 0.1, 0.035), M["siyah"], g, bevel=0.02)
    rv.kutu(f"{ad}_govde", (0.24, 0.42, 0.62), (0, 0, 1.17), kum, g, bevel=0.08)
    if yelek:
        sari = rv.boya("yelek_serit", rv.srgb("#F7E36A"), rough=0.4, var=0)
        for z in (1.05, 1.25):
            rv.kutu(f"{ad}_serit{z}", (0.25, 0.43, 0.04), (0, 0, z), sari, g, bevel=0.01)
    rv.silindir(f"{ad}_kol_sol", 0.06, 0.6, (0, 0.27, 1.15), kum, g, seg=16)
    kol = bos(f"{ad}_omuz", (0, -0.27, 1.42), g)
    kol.rotation_euler = (0, math.radians(90) - kol_aci, 0)
    rv.silindir(f"{ad}_kol_sag", 0.06, 0.6, (0, 0, 0.3), kum, kol, seg=16)
    el = bos(f"{ad}_el", (0, 0, 0.62), kol)
    rv.silindir(f"{ad}_bas", 0.13, 0.2, (0, 0, 1.68), ten, g, seg=24, bevel=0.06)
    if baret:
        rv.silindir(f"{ad}_baret", 0.155, 0.1, (0, 0, 1.8), M["turuncu"], g, seg=32, r2=0.11, bevel=0.03)
        rv.silindir(f"{ad}_siper", 0.19, 0.015, (0.03, 0, 1.75), M["turuncu"], g, seg=32)
    return g, kol, el


def kopru_vinc3b(ad, x0, x1, y, z_ray, M, cx=None, kanca_z=None, parcalar=("kiris", "bas", "caraskal")):
    """Tek kirişli köprülü vinç: X boyunca kiriş, Y=y düzleminde; ray kotu z_ray. Döner: grup ve alt gruplar."""
    g = bos(ad)
    L = x1 - x0
    zk = z_ray + 0.62  # kiriş üst kotu
    kiris = bos(ad + "_kiris", (0, 0, 0), g)
    if "kiris" in parcalar:
        rv.kutu(ad + "_kutu", (L + 0.4, 0.42, 0.62), ((x0 + x1) / 2, y, zk - 0.31), M["turuncu"], kiris, bevel=0.012)
        rv.kutu(ad + "_ust", (L + 0.4, 0.46, 0.02), ((x0 + x1) / 2, y, zk - 0.01), M["turuncu"], kiris, bevel=0.004)
        rv.kutu(ad + "_alt", (L + 0.4, 0.46, 0.02), ((x0 + x1) / 2, y, zk - 0.61), M["turuncu"], kiris, bevel=0.004)
        n = int(L / 1.2)
        for i in range(1, n):
            for sy in (-1, 1):
                rv.kutu(f"{ad}_dikme{i}{sy}", (0.012, 0.006, 0.56), (x0 + i * L / n, y + sy * 0.213, zk - 0.31),
                        M["turuncu"], kiris, bevel=0.002)
        rv.kutu(ad + "_logozemin", (1.6, 0.004, 0.36), ((x0 + x1) / 2, y - 0.226, zk - 0.31), M["beyaz"], kiris, bevel=0.002)
        logo_levha(ad + "_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 1.3,
                   ((x0 + x1) / 2, y - 0.230, zk - 0.31), (math.pi / 2, 0, 0), kiris)
    bas = bos(ad + "_bas", (0, 0, 0), g)
    if "bas" in parcalar:
        for xb in (x0, x1):
            rv.kutu(f"{ad}_bas{xb:g}", (0.36, 2.4, 0.32), (xb, y, z_ray + 0.19), M["antrasit"], bas, bevel=0.01)
            for sy in (-1, 1):
                rv.silindir(f"{ad}_tek{xb:g}{sy}", 0.12, 0.08, (xb, y + sy * 0.95, z_ray + 0.12), M["celik"], bas, axis="X")
            rv.kutu(f"{ad}_red{xb:g}", (0.22, 0.26, 0.26), (xb + (0.28 if xb > x0 else -0.28), y - 0.75, z_ray + 0.22),
                    M["turuncu"], bas, bevel=0.02)
            rv.silindir(f"{ad}_mot{xb:g}", 0.08, 0.3, (xb + (0.28 if xb > x0 else -0.28), y - 1.05, z_ray + 0.22),
                        M["antrasit"], bas, axis="Y")
    car = bos(ad + "_caraskal", ((x0 + x1) / 2 if cx is None else cx, y, 0), g)
    kanca = None
    if "caraskal" in parcalar:
        za = zk - 0.62
        rv.kutu(ad + "_car_levha", (0.4, 0.5, 0.2), (0, 0, za - 0.06), M["antrasit"], car, bevel=0.01)
        rv.kutu(ad + "_car_govde", (0.62, 0.34, 0.36), (0, 0, za - 0.38), M["turuncu"], car, bevel=0.04)
        rv.silindir(ad + "_car_motor", 0.15, 0.2, (-0.38, 0, za - 0.38), M["antrasit"], car, axis="X", bevel=0.01)
        rv.kutu(ad + "_car_kapak", (0.22, 0.36, 0.38), (0.32, 0, za - 0.38), M["antrasit"], car, bevel=0.03)
        rv.kutu(ad + "_car_etiket", (0.14, 0.004, 0.06), (0.32, -0.183, za - 0.34), M["beyaz"], car, bevel=0.001)
        kanca = bos(ad + "_kanca", (0, 0, (kanca_z or za - 1.6)), car)
        rv.kutu(ad + "_blok", (0.16, 0.12, 0.16), (0, 0, 0.08), M["turuncu"], kanca, bevel=0.02)
        rv.kanca(ad + "_k", (0, 0, 0.0), 1.2, M, kanca)
        # zincir: caraskaldan kanca bloğuna (Stretch To)
        zn = rv.silindir(ad + "_zincir", 0.012, 1.0, (0, 0, 0), M["galvaniz"], None, seg=8)
        zn.location = (0, 0, 0)
        zp = bos(ad + "_zincir_bas", (0, 0, za - 0.56), car)
        zn.parent = None
        c = zn.constraints.new("COPY_LOCATION")
        c.target = zp
        s = zn.constraints.new("STRETCH_TO")
        s.target = kanca
        s.rest_length = 1.0
        zn.rotation_euler = (0, 0, 0)
        # Stretch To silindirin Y eksenini uzatır: geometriyi Y'ye çevir
        me = zn.data
        for v in me.vertices:
            v.co = Vector((v.co.x, v.co.z + 0.5, -v.co.y))
    return g, kiris, bas, car, kanca


def tir3b(ad, M, yuk_fn=None):
    """Beta logolu çekici + low-bed dorse. Orijin: çekici ön tamponu altı, +X yönüne gider."""
    g = bos(ad)
    beyaz_logo = os.path.join(LOGO_DIR, "beta_isaret_beyaz.png")
    # çekici
    rv.kutu(ad + "_sasi", (6.0, 0.9, 0.25), (-3.0, 0, 0.75), M["siyah"], g, bevel=0.02)
    rv.kutu(ad + "_kabin", (2.1, 2.45, 2.5), (-1.15, 0, 2.15), M["antrasit"], g, bevel=0.12)
    rv.kutu(ad + "_kabin_serit", (2.12, 2.47, 0.32), (-1.15, 0, 2.95), M["turuncu"], g, bevel=0.02)
    rv.kutu(ad + "_kabin_alt", (2.12, 2.47, 0.22), (-1.15, 0, 1.15), M["turuncu"], g, bevel=0.02)
    cam = rv.boya("tir_cam", (0.25, 0.35, 0.42, 1), rough=0.08, metal=0.3, var=0)
    rv.kutu(ad + "_cam_on", (0.04, 2.2, 0.85), (-0.08, 0, 2.55), cam, g, bevel=0.03)
    for sy in (-1, 1):
        rv.kutu(f"{ad}_cam_yan{sy}", (0.9, 0.04, 0.7), (-0.6, sy * 1.235, 2.6), cam, g, bevel=0.02)
        logo_levha(f"{ad}_kapi_logo{sy}", beyaz_logo, 1.2, (-1.3, sy * 1.24, 1.75), (math.pi / 2, 0, 0 if sy < 0 else math.pi), g)
    rv.kutu(ad + "_izgara", (0.05, 1.8, 0.6), (-0.07, 0, 1.6), M["siyah"], g, bevel=0.02)
    for sy in (-1, 1):
        rv.kutu(f"{ad}_far{sy}", (0.04, 0.35, 0.16), (-0.08, sy * 0.95, 1.25), isik_mat("far", (1, 0.97, 0.85), 2), g)
    rv.kutu(ad + "_tampon", (0.25, 2.45, 0.3), (-0.1, 0, 0.85), M["antrasit"], g, bevel=0.03)
    teker = []
    for x in (-1.1, -4.2, -5.6):
        for sy in (-1, 1):
            t = rv.silindir(f"{ad}_t{x}{sy}", 0.52, 0.35, (x, sy * 1.05, 0.52), M["siyah"], g, axis="Y", bevel=0.05)
            rv.silindir(f"{ad}_j{x}{sy}", 0.28, 0.36, (x, sy * 1.05, 0.52), M["gri"], g, axis="Y")
            teker.append(t)
    rv.kutu(ad + "_beşinci", (1.2, 1.2, 0.12), (-4.8, 0, 1.0), M["siyah"], g, bevel=0.02)
    # dorse (low-bed)
    rv.kutu(ad + "_dorse_boyun", (2.0, 2.5, 0.35), (-5.6, 0, 1.38), M["antrasit"], g, bevel=0.03)
    rv.kutu(ad + "_dorse", (12.0, 2.5, 0.25), (-12.4, 0, 1.05), M["antrasit"], g, bevel=0.02)
    rv.kutu(ad + "_dorse_ust", (12.0, 2.52, 0.04), (-12.4, 0, 1.19), rv.boya("dorse_ahsap", (0.42, 0.3, 0.18, 1), rough=0.8), g)
    for x in (-15.0, -16.3, -17.6):
        for sy in (-1, 1):
            rv.silindir(f"{ad}_dt{x}{sy}", 0.45, 0.3, (x, sy * 1.0, 0.45), M["siyah"], g, axis="Y", bevel=0.04)
            rv.silindir(f"{ad}_dj{x}{sy}", 0.24, 0.31, (x, sy * 1.0, 0.45), M["gri"], g, axis="Y")
    if yuk_fn:
        yuk_fn(g)
    return g


def tasima_kirisi(ad, M, parent, x=-12.4, z=1.21, L=11.0):
    """Tır üstündeki vinç kirişi (takozlar + spanzetler)."""
    k = bos(ad, (x, 0, z), parent)
    ahsap = rv.boya("takoz", (0.42, 0.3, 0.18, 1), rough=0.8)
    for i in range(4):
        rv.kutu(f"{ad}_takoz{i}", (0.25, 0.8, 0.14), (-L / 2 + 1 + i * (L - 2) / 3, 0, 0.07), ahsap, k, bevel=0.01)
    rv.kutu(ad + "_kutu", (L, 0.42, 0.62), (0, 0, 0.45), M["turuncu"], k, bevel=0.012)
    rv.kutu(ad + "_logozemin", (1.6, 0.004, 0.36), (0, -0.215, 0.45), M["beyaz"], k, bevel=0.002)
    logo_levha(ad + "_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 1.3, (0, -0.219, 0.45), (math.pi / 2, 0, 0), k)
    kirmizi = rv.boya("spanzet", rv.srgb("#E5483B"), rough=0.6)
    for xs in (-L / 3, L / 3):
        rv.kutu(f"{ad}_spanzet{xs:g}", (0.06, 0.44, 0.02), (xs, 0, 0.77), kirmizi, k)
        for sy in (-1, 1):
            rv.kutu(f"{ad}_spanzet{xs:g}{sy}", (0.06, 0.02, 0.8), (xs, sy * 0.23, 0.37), kirmizi, k)
    return k


def agac(ad, loc, s=1.0):
    gov = rv.boya("agac_govde", (0.3, 0.22, 0.15, 1), rough=0.9)
    yap = rv.boya("agac_yaprak", rv.srgb("#5E9A63"), rough=0.8)
    g = bos(ad, loc)
    rv.silindir(ad + "_g", 0.15 * s, 1.6 * s, (0, 0, 0.8 * s), gov, g, seg=10)
    rv.silindir(ad + "_y", 1.3 * s, 3.2 * s, (0, 0, 3.0 * s), yap, g, seg=12, r2=0.05)
    return g


def hol3b(M, x0=-1.0, x1=13.0, uzun=24.0, z_ray=6.5, cati=True):
    """Müşteri holü: beton kolonlar, konsollar, yürüyüş yolu kirişleri, duvarlar, çatı."""
    beton = rv.beton_dokusu()
    duvar = rv.boya("hol_duvar", (0.78, 0.78, 0.76, 1), rough=0.85, var=0.05)
    zemin(mat=rv.boya("hol_zemin", (0.62, 0.62, 0.6, 1), rough=0.55, var=0.1, bump=0.05), boyut=120)
    for x in (x0 - 0.6, x1 + 0.6):
        for i, y in enumerate((-6, 0, 6)):
            rv.kutu(f"kolon{x:g}{i}", (0.6, 0.6, 9.0), (x, y, 4.5), beton, bevel=0.02)
            rv.kutu(f"konsol{x:g}{i}", (0.6, 0.6, 0.6), (x + (0.5 if x < 0 else -0.5), y, z_ray - 0.55), beton, bevel=0.01)
        rv.ipe(f"yolkirisi{x:g}", -9, 9, z_ray - 0.25, 0.5, 0.3, M["antrasit"], None, tf=0.025, tw=0.014)
        yk = bpy.data.objects[f"yolkirisi{x:g}"]
        yk.rotation_euler = (0, 0, math.pi / 2)
        yk.location = (x + (0.5 if x < 0 else -0.5), 0, 0)
        rv.kutu(f"yolrayi{x:g}", (0.06, 18, 0.05), (x + (0.5 if x < 0 else -0.5), 0, z_ray - 0.225), M["ray"])
    rv.duzlem("arka_duvar", (40, 10), ((x0 + x1) / 2, 7.5, 5), (math.pi / 2, 0, 0), duvar)
    if cati:
        for i in range(-3, 4):
            rv.kutu(f"cati_kiris{i}", (x1 - x0 + 3, 0.2, 0.4), ((x0 + x1) / 2, i * 3, 9.2), M["gri"], bevel=0.005)
    return beton


def mobil_vinc3b(ad, loc, M, bom_uzun=14.0, bom_aci=55.0, don=0.0):
    """Mobil vinç: taşıyıcı + döner üst yapı + teleskopik bom. Döner: (grup, döner, bom, uç boş)."""
    g = bos(ad, loc)
    acik = rv.boya("mv_govde", (0.85, 0.86, 0.86, 1), rough=0.4, var=0.03)
    rv.kutu(ad + "_sasi", (9.0, 2.6, 1.1), (0, 0, 1.25), acik, g, bevel=0.05)
    rv.kutu(ad + "_serit", (9.02, 2.62, 0.18), (0, 0, 1.6), M["turuncu"], g, bevel=0.01)
    rv.kutu(ad + "_kabin", (1.8, 2.4, 1.6), (3.8, 0, 2.6), acik, g, bevel=0.1)
    rv.kutu(ad + "_kabin_cam", (0.04, 2.0, 0.8), (4.71, 0, 2.9), rv.boya("tir_cam", (0.25, 0.35, 0.42, 1), rough=0.08, metal=0.3, var=0), g)
    for x in (-3.0, -1.5, 1.5, 3.0):
        for sy in (-1, 1):
            rv.silindir(f"{ad}_t{x}{sy}", 0.6, 0.45, (x, sy * 1.15, 0.6), M["siyah"], g, axis="Y", bevel=0.05)
    for x in (-4.0, 4.0):
        for sy in (-1, 1):
            rv.kutu(f"{ad}_ayak{x}{sy}", (0.3, 1.4, 0.2), (x, sy * 1.9, 0.9), M["antrasit"], g)
            rv.kutu(f"{ad}_ped{x}{sy}", (0.6, 0.6, 0.1), (x, sy * 2.5, 0.05), M["antrasit"], g)
            rv.kutu(f"{ad}_ayakd{x}{sy}", (0.25, 0.25, 0.9), (x, sy * 2.5, 0.5), M["antrasit"], g)
    dn = bos(ad + "_doner", (-1.0, 0, 1.8), g)
    dn.rotation_euler = (0, 0, math.radians(don))
    rv.kutu(ad + "_ust", (3.4, 2.4, 1.2), (-0.6, 0, 0.6), acik, dn, bevel=0.06)
    rv.kutu(ad + "_kar", (1.4, 2.4, 1.0), (-2.0, 0, 0.6), M["antrasit"], dn, bevel=0.04)
    rv.kutu(ad + "_ust_kabin", (1.3, 0.9, 1.2), (0.7, 1.0, 1.0), acik, dn, bevel=0.06)
    bom = bos(ad + "_bom", (0.6, 0, 1.4), dn)
    bom.rotation_euler = (0, -math.radians(bom_aci), 0)
    for i, (w, h, ofs) in enumerate(((0.8, 0.7, 0.0), (0.62, 0.55, 0.32), (0.46, 0.42, 0.64))):
        Lb = bom_uzun * (1 - ofs * 0.5)
        rv.kutu(f"{ad}_bom{i}", (Lb, w, h), (Lb / 2 + ofs * bom_uzun * 0.3, 0, 0), [M["turuncu_k"] if "turuncu_k" in M else M["turuncu"], M["turuncu"], M["turuncu"]][i],
                bom, bevel=0.03)
    uc = bos(ad + "_uc", (bom_uzun, 0, 0), bom)
    rv.silindir(ad + "_makara", 0.3, 0.3, (bom_uzun, 0, 0), M["antrasit"], bom, axis="Y")
    return g, dn, bom, uc


def halat_kanca(ad, uc, M, kanca_z0):
    """uc boşundan aşağı inen halat + kanca bloğu; kanca konumu dünya koordinatında anahtarlanır."""
    kb = bos(ad + "_kanca")
    c = kb.constraints.new("COPY_LOCATION")
    c.target = uc
    c.use_z = False
    kb.location = (0, 0, kanca_z0)
    rv.kutu(ad + "_blok", (0.4, 0.3, 0.5), (0, 0, 0.25), M["antrasit"], kb, bevel=0.04)
    rv.kanca(ad + "_k", (0, 0, 0), 2.2, M, kb)
    h = rv.silindir(ad + "_halat", 0.02, 1.0, (0, 0, 0), M["halat"], None, seg=8)
    for v in h.data.vertices:
        v.co = Vector((v.co.x, v.co.z + 0.5, -v.co.y))
    cl = h.constraints.new("COPY_LOCATION")
    cl.target = uc
    s = h.constraints.new("STRETCH_TO")
    s.target = kb
    s.rest_length = 1.0
    return kb


def sapan(ad, kb, M, yuk_gen=8.0, yuk_z=-1.6):
    """Kancadan yüke iki sapan (kanca boşuna bağlı)."""
    for sx in (-1, 1):
        rv.boru(f"{ad}_sapan{sx}", (0, 0, -0.25), (sx * yuk_gen / 2, 0, yuk_z), 0.025, rv.boya("sapan", rv.srgb("#F2C200"), rough=0.7), kb, seg=8)


# ---------------------------------------------------------------- sahneler
def s_acilis(M, sc, n):
    dunya((0.05, 0.055, 0.065), 0.5)
    zm = rv.boya("stud_zemin", (0.12, 0.13, 0.15, 1), rough=0.35, var=0.03)
    zemin(mat=zm)
    logo = logo_3b(mat=rv.boya("logo_metal", (0.85, 0.86, 0.88, 1), rough=0.22, metal=0.9, var=0.03))
    logo.rotation_euler = (math.pi / 2, 0, 0)
    logo.location = (0, 0, 0.6)
    anahtar(logo, ("rotation_euler", 2), [(1, math.radians(-75)), (int(n * 0.55), 0.0)])
    anahtar(logo, ("location", 2), [(1, 0.2), (int(n * 0.55), 0.62)])
    # turuncu ışık çizgisi
    cizgi = rv.kutu("cizgi", (3.2, 0.02, 0.03), (0, -0.1, 0.18), isik_mat("turuncu_isik", (0.91, 0.6, 0.16), 8))
    anahtar(cizgi, ("scale", 0), [(int(n * 0.35), 0.001), (int(n * 0.7), 1.0)])
    alan_isigi((-3, -4, 4), (0, 0, 0.6), 900, boyut=3)
    alan_isigi((3, -2, 2), (0, 0, 0.6), 300, boyut=2, renk=(1.0, 0.75, 0.4))
    alan_isigi((0, 3, 3), (0, 0, 0.6), 600, boyut=4)
    kamera_yolu([(1, (0.6, -6.5, 1.4), (0, 0, 0.55)), (n, (0, -4.6, 1.0), (0, 0, 0.6))], lens=50)


def s_siparis(M, sc, n):
    dunya((0.95, 0.93, 0.9), 0.9)
    zemin(mat=rv.boya("ofis_zemin", (0.55, 0.45, 0.36, 1), rough=0.5, var=0.08))
    duvar = rv.boya("ofis_duvar", (0.93, 0.91, 0.87, 1), rough=0.9, var=0.03)
    rv.duzlem("duvar", (20, 6), (0, 3.0, 3), (math.pi / 2, 0, 0), duvar)
    cam = isik_mat("pencere", (0.85, 0.92, 1.0), 2.5)
    rv.duzlem("pencere", (3.2, 2.0), (-2.2, 2.97, 2.1), (math.pi / 2, 0, 0), cam)
    for x in (-3.8, -2.2, -0.6):
        rv.kutu(f"pc{x}", (0.06, 0.04, 2.1), (x, 2.95, 2.1), M["beyaz"])
    logo_levha("duvar_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 2.0, (1.8, 2.96, 2.4), (math.pi / 2, 0, 0))
    ahsap = rv.boya("masa", (0.5, 0.36, 0.24, 1), rough=0.45, var=0.08)
    rv.kutu("masa", (2.4, 1.1, 0.05), (0, 0, 0.75), ahsap, bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rv.kutu(f"masa_ayak{sx}{sy}", (0.05, 0.05, 0.73), (sx * 1.1, sy * 0.48, 0.365), M["antrasit"])
    # dizüstü
    lp = bos("laptop", (0.1, 0.05, 0.775))
    rv.kutu("lp_alt", (0.34, 0.24, 0.015), (0, 0, 0.0075), M["gri"], lp, bevel=0.004)
    ekran = bos("lp_ekran", (0, 0.12, 0.015), lp)
    ekran.rotation_euler = (math.radians(-105), 0, 0)
    rv.kutu("lp_kapak", (0.34, 0.24, 0.01), (0, -0.12, 0.0), M["gri"], ekran, bevel=0.004)
    ui = isik_mat("lp_ui", (0.92, 0.62, 0.2), 1.6)
    rv.kutu("lp_ui", (0.31, 0.21, 0.002), (0, -0.12, 0.006), ui, ekran)
    rv.kutu("kahve", (0.08, 0.08, 0.1), (-0.5, -0.1, 0.83), M["beyaz"], bevel=0.03)
    rv.kutu("telefon", (0.08, 0.16, 0.01), (0.55, -0.2, 0.785), M["siyah"], bevel=0.005)
    rv.kutu("dosya", (0.3, 0.22, 0.03), (-0.2, 0.25, 0.79), M["turuncu"], bevel=0.005)

    alan_isigi((-2.2, 2.5, 2.2), (0, 0, 0.8), 700, boyut=3, renk=(0.92, 0.96, 1.0))
    alan_isigi((2, -2, 3), (0, 0, 0.8), 400, boyut=3)
    kamera_yolu([(1, (1.25, -1.35, 1.35), (0.05, 0.15, 0.9)), (n, (0.85, -0.95, 1.18), (0.05, 0.15, 0.9))], lens=32)


def s_kesif(M, sc, n):
    dunya((0.85, 0.87, 0.9), 0.7)
    hol3b(M)
    gunes((55, 10, 40), 2.5)
    alan_isigi((6, -10, 8), (6, 0, 4), 1600, boyut=10)
    tek, kol, el = insan3b("teknisyen", (1.0, -3.5, 0), M, yuz=0.0, kol_aci=math.radians(-5))
    anahtar(tek, ("location", 1), [(1, -9.0), (int(n * 0.3), -3.5)])
    rv.kutu("lazer", (0.12, 0.06, 0.1), (0.05, 0, 0.0), M["turuncu"], el, bevel=0.01)
    # lazer ışını: ray kotunda açıklık boyunca
    kirmizi = isik_mat("lazer_isin", (1.0, 0.1, 0.05), 12)
    isin = rv.kutu("lazer_isin", (13.0, 0.012, 0.012), (6.0, 0, 6.33), kirmizi)
    anahtar(isin, ("scale", 0), [(int(n * 0.32), 0.001), (int(n * 0.6), 1.0)])
    isin2 = rv.kutu("lazer_isin2", (0.012, 0.012, 6.3), (9.5, 0, 3.15), kirmizi)
    anahtar(isin2, ("scale", 2), [(int(n * 0.62), 0.001), (int(n * 0.82), 1.0)])
    kamera_yolu([(1, (5.0, -13.0, 2.6), (5.5, 0, 3.4)), (n, (5.5, -12.0, 2.4), (5.8, 0, 3.6))], lens=24)
    return dict(aciklik=((-0.5, 0, 6.33), (12.5, 0, 6.33)), yukseklik=((9.5, 0, 0), (9.5, 0, 6.3)))


def s_muhendislik(M, sc, n):
    dunya((0.03, 0.08, 0.14), 0.6)
    gm = rv.boya("blue_zemin", (0.04, 0.12, 0.22, 1), rough=0.3, var=0.02)
    nt = gm.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 0.5
    br.inputs["Mortar Size"].default_value = 0.01
    br.inputs["Color1"].default_value = (0, 0, 0, 1)
    br.inputs["Color2"].default_value = (0, 0, 0, 1)
    br.inputs["Mortar"].default_value = (0.4, 0.7, 1.0, 1)
    br.offset = 0.0
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.6
    zemin(mat=gm, boyut=80)
    tel = isik_mat("tel", (0.55, 0.85, 1.0), 4)
    g, kiris, bas, car, kanca = kopru_vinc3b("vinc", 0, 12, 0, 1.0, M, cx=7.0, kanca_z=-1.2)
    g.location = (-6, 0, 0)
    for ob in g.children_recursive:
        if ob.type in {"MESH", "CURVE", "FONT"}:
            ob.data = ob.data.copy() if ob.type == "MESH" else ob.data
    # tel kafes kopyası
    tg = bos("tel_grup", (-6, 0, 0))
    for ob in list(g.children_recursive):
        if ob.type == "MESH":
            k = ob.copy()
            k.data = ob.data.copy()
            k.modifiers.clear()
            bpy.context.scene.collection.objects.link(k)
            k.parent = None
            k.matrix_world = ob.matrix_world.copy()
            k.parent = tg
            k.matrix_parent_inverse = tg.matrix_world.inverted()
            k.data.materials.clear()
            k.data.materials.append(tel)
            w = k.modifiers.new("tel", "WIREFRAME")
            w.thickness = 0.012
    don = bos("donme", (0, 0, 0))
    g.parent = don
    tg.parent = don
    g.location = (-6, 0, 0)
    tg.location = (-6, 0, 0)
    anahtar(don, ("rotation_euler", 2), [(1, math.radians(-25)), (n, math.radians(20))], interp="LINEAR")
    gorunur(g, [(1, False), (int(n * 0.55), True)])
    gorunur(tg, [(1, True), (int(n * 0.62), False)])
    alan_isigi((-4, -8, 8), (0, 0, 1.5), 2500, boyut=6, renk=(0.85, 0.92, 1.0))
    alan_isigi((6, 4, 5), (0, 0, 1.5), 1200, boyut=5)
    kamera_yolu([(1, (0, -15.5, 6.5), (0, 0, 1.6)), (n, (0, -13.5, 5.2), (0, 0, 1.6))], lens=30)


def s_imalat(M, sc, n):
    dunya((0.85, 0.85, 0.86), 0.4)
    zemin(mat=rv.boya("fab_zemin", (0.5, 0.5, 0.49, 1), rough=0.45, var=0.12, bump=0.05), boyut=120)
    duvar = rv.boya("fab_duvar", (0.75, 0.76, 0.77, 1), rough=0.8, var=0.04)
    rv.duzlem("fab_arka", (60, 12), (0, 8, 6), (math.pi / 2, 0, 0), duvar)
    logo_levha("fab_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 5.0, (3.5, 7.95, 7.2), (math.pi / 2, 0, 0))
    for x in (-12, -4, 4, 12):
        rv.kutu(f"fab_kolon{x}", (0.4, 0.4, 11), (x, 7.6, 5.5), M["antrasit"], bevel=0.01)
    # sehpalar
    for x in (-3.5, 3.5):
        rv.uye(f"sehpa{x}", (x, 0, 0), (x, 0, 0.85), 0.9, 0.5, 0.5, 0.35, M["antrasit"], up=Vector((1, 0, 0)))
    # kiriş: renk ham çelikten turuncuya (boya)
    km = bpy.data.materials.new("kiris_boya")
    b = rv.node_tree(km).nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.45
    ham = (0.42, 0.44, 0.47, 1)
    f_boya0, f_boya1 = int(n * 0.42), int(n * 0.66)
    b.inputs["Base Color"].default_value = ham
    b.inputs["Base Color"].keyframe_insert("default_value", frame=f_boya0)
    b.inputs["Base Color"].default_value = rv.BETA_TURUNCU
    b.inputs["Base Color"].keyframe_insert("default_value", frame=f_boya1)
    b.inputs["Metallic"].default_value = 0.6
    b.inputs["Metallic"].keyframe_insert("default_value", frame=f_boya0)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Metallic"].keyframe_insert("default_value", frame=f_boya1)
    L = 11.0
    rv.kutu("kiris", (L, 0.42, 0.62), (0, 0, 1.16), km, bevel=0.012)
    for i in range(1, 9):
        for sy in (-1, 1):
            rv.kutu(f"dikme{i}{sy}", (0.012, 0.006, 0.56), (-L / 2 + i * L / 9, sy * 0.213, 1.16), km, bevel=0.002)
    lz = rv.kutu("kiris_logozemin", (1.6, 0.004, 0.36), (0, -0.215, 1.16), M["beyaz"], bevel=0.002)
    lg = logo_levha("kiris_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 1.3, (0, -0.219, 1.16), (math.pi / 2, 0, 0))
    gorunur(lz, [(1, False), (f_boya1, True)])
    gorunur(lg, [(1, False), (f_boya1, True)])
    # kaynak: ışık + kıvılcım yayıcı kiriş boyunca
    kn = bos("kaynak_noktasi", (-5, -0.25, 0.86))
    anahtar(kn, ("location", 0), [(int(n * 0.04), -5.0), (int(n * 0.38), 5.0)], interp="LINEAR")
    kl = bpy.data.lights.new("kaynak_isik", "POINT")
    kl.color = (1.0, 0.75, 0.4)
    kl.shadow_soft_size = 0.05
    klo = bpy.data.objects.new("kaynak_isik", kl)
    bpy.context.scene.collection.objects.link(klo)
    klo.parent = kn
    klo.location = (0, -0.25, 0.1)
    rnd = random.Random(3)
    for f in range(1, n + 1):
        kl.energy = (300 + rnd.uniform(-120, 160)) if int(n * 0.04) <= f <= int(n * 0.38) else 0.0
        kl.keyframe_insert("energy", frame=f)
    spr = bpy.data.objects.new("kivilcim_yayici", bpy.data.meshes.new("kv"))
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.03)
    bm.to_mesh(spr.data)
    bm.free()
    bpy.context.scene.collection.objects.link(spr)
    spr.parent = kn
    spr.hide_render = True
    kv = rv.silindir("kivilcim", 0.006, 0.06, (0, 0, -20), isik_mat("kivilcim_m", (1.0, 0.8, 0.35), 25), None, seg=6)
    ps = spr.modifiers.new("kivilcim", "PARTICLE_SYSTEM").particle_system.settings
    ps.count = 1500
    ps.frame_start = int(n * 0.04)
    ps.frame_end = int(n * 0.38)
    ps.lifetime = 12
    ps.lifetime_random = 0.6
    ps.normal_factor = 2.5
    ps.factor_random = 2.5
    ps.render_type = "OBJECT"
    ps.instance_object = kv
    ps.particle_size = 1.0
    ps.use_rotations = True
    ps.rotation_mode = "VEL"
    # kaynakçı
    kay, kol, el = insan3b("kaynakci", (-5.5, -1.3, 0), M, yuz=math.radians(30), kol_aci=math.radians(-35))
    anahtar(kay, ("location", 0), [(int(n * 0.04), -5.6), (int(n * 0.38), 4.4)], interp="LINEAR")
    gorunur(kay, [(1, True), (int(n * 0.42), False)])
    rv.kutu("kaynak_maske", (0.14, 0.3, 0.3), (0.12, 0, 1.68), M["siyah"], kay, bevel=0.03)
    # boya: boyacı + sis
    boyaci, _, _ = insan3b("boyaci", (4.5, -1.6, 0), M, yuz=math.radians(150), baret=False,
                           govde=(0.92, 0.92, 0.92, 1), yelek=False, kol_aci=math.radians(-25))
    anahtar(boyaci, ("location", 0), [(f_boya0, 4.5), (f_boya1, -4.5)], interp="LINEAR")
    gorunur(boyaci, [(1, False), (f_boya0, True), (f_boya1 + 5, False)])
    # montaj: baş arabaları yandan, caraskal yukarıdan
    for sx in (-1, 1):
        ba = bos(f"bas{sx}", (sx * 5.3, 0, 0))
        rv.kutu(f"bas_k{sx}", (0.36, 2.4, 0.32), (0, 0, 0.62), M["antrasit"], ba, bevel=0.01)
        for sy in (-1, 1):
            rv.silindir(f"bas_t{sx}{sy}", 0.12, 0.08, (0, sy * 0.95, 0.55), M["celik"], ba, axis="X")
        anahtar(ba, ("location", 0), [(int(n * 0.7), sx * 11.0), (int(n * 0.82), sx * 5.3)])
    car = bos("caraskal", (1.5, 0, 0))
    rv.kutu("car_govde", (0.62, 0.34, 0.36), (0, 0, 0.0), M["turuncu"], car, bevel=0.04)
    rv.silindir("car_motor", 0.15, 0.2, (-0.38, 0, 0), M["antrasit"], car, axis="X", bevel=0.01)
    rv.kutu("car_kapak", (0.22, 0.36, 0.38), (0.32, 0, 0), M["antrasit"], car, bevel=0.03)
    anahtar(car, ("location", 2), [(int(n * 0.8), 7.0), (int(n * 0.9), 0.6)])
    alan_isigi((-6, -10, 9), (0, 0, 1), 1600, boyut=10)
    alan_isigi((8, -4, 5), (0, 0, 1), 500, boyut=5)
    kamera_yolu([(1, (-7.5, -8.5, 2.6), (-1.5, 0, 1.1)), (int(n * 0.45), (0, -9.5, 2.6), (0, 0, 1.1)),
                 (n, (4.5, -10.5, 3.6), (0, 0, 1.4))], lens=26)


def fabrika_cephe(M):
    cephe = rv.boya("cephe", (0.86, 0.86, 0.85, 1), rough=0.7, var=0.05)
    rv.kutu("fabrika", (40, 20, 11), (8, 22, 5.5), cephe, bevel=0.05)
    rv.kutu("fab_cati", (40.4, 20.4, 0.4), (8, 22, 11.2), M["antrasit"])
    for i in range(6):
        rv.kutu(f"fab_cam{i}", (3.0, 0.05, 1.5), (-6 + i * 5.6, 11.97, 8.0), rv.boya("cam2", (0.35, 0.45, 0.55, 1), rough=0.1, metal=0.5, var=0))
    rv.kutu("fab_kapi", (7, 0.08, 7), (0, 11.96, 3.5), rv.boya("kepenk", (0.6, 0.62, 0.64, 1), rough=0.5, var=0.04))
    rv.kutu("tabela", (9.0, 0.2, 2.4), (13, 11.85, 8.4), M["antrasit"], bevel=0.04)
    logo_levha("tabela_logo", os.path.join(LOGO_DIR, "beta_isaret_beyaz.png"), 7.6, (13, 11.74, 8.4), (math.pi / 2, 0, 0), isik=1.2)


def s_sevkiyat(M, sc, n):
    dunya((0.7, 0.82, 0.95), 0.55)
    zemin(mat=rv.boya("avlu", (0.55, 0.55, 0.54, 1), rough=0.8, var=0.1, bump=0.05), boyut=200)
    fabrika_cephe(M)
    gunes((50, 0, -30), 2.2)
    t = tir3b("tir", M)
    t.location = (8.0, -2.0, 0)
    # kiriş yerde (sol), mobil vinç ortada
    mv, dn, bom, uc = mobil_vinc3b("mvinc", (-6.0, 4.0, 0), M, bom_uzun=15.0, bom_aci=48, don=-60)
    anahtar(dn, ("rotation_euler", 2), [(int(n * 0.35), math.radians(-60)), (int(n * 0.68), math.radians(-0.5))])
    bpy.context.view_layer.update()
    kb = halat_kanca("mv", uc, M, 3.0)
    yuk = bos("yuk", (0, 0, -1.6), kb)
    rv.kutu("yuk_kiris", (11.0, 0.42, 0.62), (0, 0, -0.31), M["turuncu"], yuk, bevel=0.012)
    rv.kutu("yuk_logozemin", (1.6, 0.004, 0.36), (0, -0.215, -0.31), M["beyaz"], yuk, bevel=0.002)
    logo_levha("yuk_logo", os.path.join(LOGO_DIR, "beta_isaret_koyu.png"), 1.3, (0, -0.219, -0.31), (math.pi / 2, 0, 0), yuk)
    sapan("mv", kb, M, yuk_gen=7.0, yuk_z=-1.6)
    # kanca kotu: kirişi yerden kaldır, taşı, dorseye indir
    # dünya Z: yerde kiriş üstü 0.62 => kanca z = 0.62 + 1.6
    anahtar(kb, ("location", 2), [(1, 2.22 + 0.15), (int(n * 0.12), 2.22 + 0.15), (int(n * 0.32), 6.2),
                                   (int(n * 0.7), 6.2), (int(n * 0.88), 1.83 + 1.6 + 0.0)])
    alan_isigi((0, -14, 10), (2, 0, 2), 1500, boyut=12)
    kamera_yolu([(1, (-3.0, -21.0, 5.5), (0.5, 0, 3.0)), (n, (2.0, -19.0, 4.8), (1.5, 0, 2.8))], lens=24)


def s_nakliye(M, sc, n):
    dunya((0.62, 0.78, 0.95), 0.6)
    cim = rv.boya("cim", rv.srgb("#86AE6E"), rough=0.9, var=0.1)
    zemin(mat=cim, boyut=600)
    asf = rv.boya("asfalt", (0.12, 0.12, 0.13, 1), rough=0.75, var=0.1, bump=0.05)
    rv.kutu("yol", (600, 9, 0.04), (0, 0, 0.02), asf)
    for i in range(-150, 150):
        rv.kutu(f"serit{i}", (2.5, 0.15, 0.005), (i * 6, 0, 0.042), M["beyaz"])
    rnd = random.Random(5)
    for i in range(-40, 60):
        for sy in (1,):
            if rnd.random() < 0.7:
                agac(f"agac{i}{sy}", (i * 7 + rnd.uniform(-2, 2), sy * rnd.uniform(9, 22), 0), s=rnd.uniform(0.8, 1.4))
    tepe = rv.boya("tepe", rv.srgb("#A3C48E"), rough=0.95)
    for i in range(12):
        rv.silindir(f"tepe{i}", rnd.uniform(25, 45), rnd.uniform(8, 18), (i * 50 - 250, 90 + rnd.uniform(0, 30), 0), tepe, seg=24, r2=1)
    gunes((45, 0, 60), 2.4)
    t = tir3b("tir", M, yuk_fn=lambda g: tasima_kirisi("tkiris", M, g))
    t.location = (0, -2.0, 0)
    hiz = 14.0  # m/s
    anahtar(t, ("location", 0), [(1, 0.0), (n, hiz * n / FPS)], interp="LINEAR")
    for ob in t.children:
        if ob.name.startswith(("tir_t", "tir_j", "tir_dt", "tir_dj")):
            r = 0.52 if ob.name.startswith(("tir_t", "tir_j")) else 0.45
            anahtar(ob, ("rotation_euler", 1), [(1, 0.0), (n, -(hiz * n / FPS) / r)], interp="LINEAR")
    # kamera tırla birlikte, yan-ön 3/4
    co, hd = kamera_yolu([(1, (6.0, -16.0, 4.0), (-6.0, 0, 1.8)), (n, (6.0 + hiz * n / FPS - 4, -14.0, 3.2),
                                                                 (-6.0 + hiz * n / FPS, 0, 1.8))], lens=28)
    for o in (co, hd):
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def s_kurulum(M, sc, n):
    dunya((0.85, 0.87, 0.9), 0.7)
    z_ray = 6.5
    hol3b(M, z_ray=z_ray)
    gunes((55, 10, 40), 2.5)
    alan_isigi((6, -12, 9), (6, 0, 4), 1800, boyut=12)
    # tır içeri girer, kiriş indirildikten sonra çıkar
    t = tir3b("tir", M)
    t.rotation_euler = (0, 0, 0)
    anahtar(t, ("location", 0), [(1, -12.0), (int(n * 0.2), 12.4 + 6.0), (int(n * 0.5), 12.4 + 6.0), (int(n * 0.62), 40.0)])
    t.location.y = -2.6
    t.keyframe_insert("location", index=1, frame=1)
    # tır üstündeki kiriş (kaldırılınca gizlenir)
    tk = tasima_kirisi("tkiris", M, t)
    gorunur(tk, [(1, True), (int(n * 0.24), False)])
    # kaldırılan kiriş: tır üstünden ray kotuna
    g, kiris, bas, car, kanca = kopru_vinc3b("vinc", 0, 12, 0, z_ray, M, cx=4.0, kanca_z=2.0)
    for ob in [kiris] + list(kiris.children_recursive):
        pass
    kiris_k = bos("kiris_kaldir", (0, 0, 0))
    kiris.parent = kiris_k
    f_al, f_ust, f_otur = int(n * 0.24), int(n * 0.44), int(n * 0.52)
    # tır üstünde kiriş üst kotu = 1.21+0.76=1.97; ray üstündeki kiriş üst kotu = z_ray+0.62
    dz0 = 1.97 - (z_ray + 0.62)
    anahtar(kiris_k, "location", [(1, (0, -2.6, dz0)), (f_al, (0, -2.6, dz0)), (f_ust, (0, -2.6, 0.9)),
                                  (int(n * 0.48), (0, 0, 0.9)), (f_otur, (0, 0, 0))])
    gorunur(kiris_k, [(1, False), (f_al, True)])
    # kaldırma halatları (çatıdan)
    for x in (2.0, 10.0):
        h = rv.boru(f"askı{x}", (x, 0, 9.0), (x, 0, z_ray + 0.62), 0.02, M["halat"], kiris_k, seg=8)
    gorunur(bpy.data.objects["askı2.0"], [(1, False), (f_al, True), (f_otur + 3, False)])
    gorunur(bpy.data.objects["askı10.0"], [(1, False), (f_al, True), (f_otur + 3, False)])
    gorunur(bas, [(1, False), (int(n * 0.55), True)])
    gorunur(car, [(1, False), (int(n * 0.6), True)])
    anahtar(car, ("location", 0), [(int(n * 0.6), -1.0), (int(n * 0.68), 4.0), (int(n * 0.88), 4.0), (n, 8.5)])
    # yük testi: 5 t test ağırlığı
    agirlik = bos("agirlik", (4.0, 0, 0))
    rv.kutu("agirlik_k", (1.2, 1.2, 1.0), (0, 0, 0.5), M["gri"], agirlik, bevel=0.03)
    rv.kutu("agirlik_et", (0.6, 0.004, 0.3), (0, -0.603, 0.55), M["beyaz"], agirlik)
    rv.yazi("agirlik_yazi", "5 t", (0, -0.607, 0.55), 0.22, M["antrasit"], agirlik)
    za = z_ray + 0.62 - 0.62
    # kanca: car içinde yerel z; kanca bloğu dünya kotu = za + yerel
    anahtar(kanca, ("location", 2), [(int(n * 0.62), -1.4), (int(n * 0.72), -(za - 1.25)), (int(n * 0.76), -(za - 1.25)),
                                     (int(n * 0.86), -(za - 3.2))])
    agirlik.parent = None
    anahtar(agirlik, "location", [(1, (4.0, 0, 0)), (int(n * 0.76), (4.0, 0, 0)), (int(n * 0.86), (4.0, 0, 1.95)),
                                  (int(n * 0.88), (4.0, 0, 1.95)), (n, (8.5, 0, 1.95))])
    kamera_yolu([(1, (6.0, -18.0, 3.6), (6.0, 0, 4.2)), (int(n * 0.5), (2.0, -17.0, 4.5), (6.0, 0, 5.0)),
                 (n, (9.5, -15.0, 4.0), (6.0, 0, 4.5))], lens=24)


def s_kapanis(M, sc, n):
    dunya((0.91, 0.6, 0.16), 0.6)
    zm = rv.boya("kap_zemin", (0.75, 0.45, 0.1, 1), rough=0.4, var=0.03)
    zemin(mat=zm)
    rv.duzlem("kap_arka", (40, 20), (0, 6, 5), (math.pi / 2, 0, 0), rv.boya("kap_arka", rv.BETA_TURUNCU, rough=0.8, var=0.02))
    logo = logo_3b(mat=rv.boya("logo_beyaz3b", (0.95, 0.95, 0.95, 1), rough=0.3, var=0.02))
    logo.rotation_euler = (math.pi / 2, 0, 0)
    logo.location = (0, 0, 1.1)
    anahtar(logo, ("rotation_euler", 2), [(1, math.radians(25)), (int(n * 0.5), 0.0)])
    alan_isigi((-3, -5, 5), (0, 0, 1), 1500, boyut=4)
    alan_isigi((3, -3, 2), (0, 0, 1), 500, boyut=3)
    kamera_yolu([(1, (0, -6.5, 1.5), (0, 0, 0.95)), (n, (0, -5.8, 1.35), (0, 0, 0.95))], lens=45)


SAHNELER = dict(acilis=s_acilis, siparis=s_siparis, kesif=s_kesif, muhendislik=s_muhendislik, imalat=s_imalat,
                sevkiyat=s_sevkiyat, nakliye=s_nakliye, kurulum=s_kurulum, kapanis=s_kapanis)


def main():
    argv = sys.argv[1:]
    adim = 1
    if "--adim" in argv:
        i = argv.index("--adim")
        adim = int(argv[i + 1])
        del argv[i:i + 2]
    sahne, klasor = argv[0], argv[1]
    os.makedirs(klasor, exist_ok=True)
    n = int(SURE[sahne] * FPS)
    k0 = int(argv[2]) if len(argv) > 2 else 1
    k1 = min(n, int(argv[3])) if len(argv) > 3 else n
    M, sc = hazirla()
    noktalar = SAHNELER[sahne](M, sc, n) or {}
    eevee(sc, ornek=int(os.environ.get("ORNEK", "12")))
    sc.frame_start, sc.frame_end = 1, n
    # 2B katman için 3B noktaların ekran izdüşümleri (her kare)
    from bpy_extras.object_utils import world_to_camera_view
    izd = {}
    for f in range(k0, k1 + 1, adim):
        sc.frame_set(f)
        if noktalar:
            izd[f] = {ad: [list(world_to_camera_view(sc, sc.camera, Vector(p))[:2]) for p in pts]
                      for ad, pts in noktalar.items()}
        sc.render.filepath = os.path.join(klasor, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    if izd:
        yol = os.path.join(klasor, "noktalar.json")
        eski = json.load(open(yol)) if os.path.exists(yol) else {}
        eski.update({str(k): v for k, v in izd.items()})
        json.dump(eski, open(yol, "w"))
    print("tamam", sahne, k0, k1)


if __name__ == "__main__":
    main()
