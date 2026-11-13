"""Path-traced "postcards": one Cycles render per region, shown when it unlocks.

Each postcard shows the archipelago as it stands at that moment (regions 0..i),
with Clawd posed at the new landmark, through a shallow-focus "miniature" lens.

    python blender/postcards.py <out_dir> [first] [last] [--samples N] [--size WxH]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
import clawd as clawd_mod  # noqa: E402
from lib.voxel import Builder, ensure_sky, reset_scene  # noqa: E402
from regions import REGIONS  # noqa: E402

SUN_DIR = Vector((0.42, -0.62, 0.66)).normalized()  # towards the sun (Blender coords)


def render_material(m):
    """Swap the export material for a render one: _pbr drives roughness/metal, glow emits."""
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "_pbr"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(attr.outputs["Vector"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Y"], bsdf.inputs["Metallic"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.5


def glow_material():
    m = bpy.data.materials.new("glow")
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(vc.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    return m


def build_world(upto):
    roots = []
    for i in range(upto + 1):
        b = Builder(f"region_{i:02d}", seed=1000 + i)
        b.uv = False
        meta = REGIONS[i]["fn"](b)
        root = b.build()
        roots.append((root, meta))
    return roots


def place_clawd(meta):
    arm = clawd_mod.make_armature()
    body = clawd_mod.build_mesh()
    clawd_mod.merged_body(body, arm)
    accs = {}
    for name, (ab, bone) in clawd_mod.build_accessories().items():
        accs[name] = clawd_mod.acc_mesh(name, ab, bone, arm)
    clawd_mod.make_actions(arm)
    for name, ob in accs.items():
        ob.hide_render = name != meta.get("acc")
    sx, sy, sz = meta["spot"]
    lx, ly, _ = meta["look"]
    arm.location = (sx, sy, sz)
    # Clawd's front is -Y; turn to face the look point
    arm.rotation_euler = (0, 0, math.atan2(-(lx - sx), (ly - sy)) + math.pi)
    act = bpy.data.actions.get(meta.get("action") or "idle")
    if act:
        arm.animation_data.action = act
        if hasattr(arm.animation_data, "action_slot") and act.slots:
            arm.animation_data.action_slot = act.slots[0]
        bpy.context.scene.frame_set(int(act.frame_range[1] * 0.3))
    return arm


def setup_render(samples, w, h):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.view_settings.exposure = -0.35
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 86
    ensure_sky(elevation_deg=42, strength=0.16)
    sun_data = bpy.data.lights.new("sun", "SUN")
    sun_data.energy = 4.6
    sun_data.angle = math.radians(3.0)
    sun_data.color = (1.0, 0.94, 0.86)
    sun = bpy.data.objects.new("sun", sun_data)
    sun.rotation_euler = SUN_DIR.to_track_quat("Z", "Y").to_euler()
    sc.collection.objects.link(sun)


def aim_camera(target, dist):
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 42
    cam_data.sensor_width = 36
    cam_data.clip_end = 400
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 1.1  # very shallow: reads as a photographed miniature
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    t = Vector(target)
    d = Vector((0.55, -0.95, 0.68)).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.dof.focus_distance = (t - cam.location).length
    sc.camera = cam


def prep_scene(upto, samples, w, h):
    reset_scene()
    setup_render(samples, w, h)
    roots = build_world(upto)
    for m in bpy.data.materials:
        if m.name.startswith("voxel"):
            render_material(m)
    gm = glow_material()
    for root, _ in roots:
        for ob in root.children:
            if ob.get("part") == "glow" or ob.get("glow"):
                ob.data.materials[0] = gm
            if ob.get("night"):
                ob.hide_render = True  # aurora/stars are night-only
    return roots


def render_hero(out, samples, w, h):
    """The whole finished archipelago, wide."""
    roots = prep_scene(len(REGIONS) - 1, samples, w, h)
    place_clawd(roots[0][1])
    aim_camera((-2.0, 2.0, 2.5), 78.0)
    cam = bpy.context.scene.camera
    cam.data.lens = 50
    cam.data.dof.aperture_fstop = 2.8
    bpy.context.scene.render.filepath = str(out / "hero.jpg")
    bpy.ops.render.render(write_still=True)
    print("hero ->", bpy.context.scene.render.filepath, flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    nums = []
    skip = False
    for a in argv[1:]:
        if skip:
            skip = False
        elif a in ("--samples", "--size"):
            skip = True
        elif not a.startswith("--"):
            nums.append(a)
    first = int(nums[0]) if nums else 0
    last = int(nums[1]) if len(nums) > 1 else len(REGIONS) - 1
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 160
    size = argv[argv.index("--size") + 1] if "--size" in argv else "960x600"
    w, h = (int(v) for v in size.split("x"))
    if "--hero" in argv:
        render_hero(out, samples, w, h)
        return
    for i in range(first, last + 1):
        roots = prep_scene(i, samples, w, h)
        meta = roots[i][1]
        place_clawd(meta)
        # frame the new region with Clawd in it
        sx, sy, sz = meta["spot"]
        # keep the region's own bounds in shot
        b = Builder("tmp")
        REGIONS[i]["fn"](b)
        xs = [v[0] for p in b.parts.values() for v in p.verts]
        ys = [v[1] for p in b.parts.values() for v in p.verts]
        zs = [v[2] for p in b.parts.values() for v in p.verts]
        size_r = min(max(max(xs) - min(xs), max(ys) - min(ys), (max(zs) - min(zs)) * 0.8), 26)
        target = ((sx * 2 + (min(xs) + max(xs)) / 2) / 3, (sy * 2 + (min(ys) + max(ys)) / 2) / 3, sz + 0.8)
        aim_camera(target, max(12.0, size_r * 2.1))
        bpy.context.scene.render.filepath = str(out / f"region_{i:02d}.jpg")
        bpy.ops.render.render(write_still=True)
        print(f"postcard {i:02d} -> {bpy.context.scene.render.filepath}", flush=True)


if __name__ == "__main__":
    main()
