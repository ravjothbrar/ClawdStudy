"""Clawd: voxel mesh + armature + baked actions, exported to public/world/clawd.glb.

Proportions follow the official sprite (claudecodeicon.webp): a 6x4 block body,
1-block side nubs, tall eye slots and four legs (doubled front/back in 3D).
One unit U = 0.2 world units, so Clawd is 1.6 wide including nubs.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Quaternion

sys.path.insert(0, str(Path(__file__).parent))
from lib.voxel import Builder, export_glb, reset_scene  # noqa: E402

U = 0.2
FPS = 30
LEG_H = 1 * U
BODY_Z0, BODY_Z1 = LEG_H, LEG_H + 4 * U
HALF_W = 3 * U
HALF_D = 1.6 * U
LEG_X = [-2.5 * U, -1.5 * U, 1.0 * U, 2.0 * U]  # left edges, width 0.5U (from sprite)

BONES = {
    # name: (head, parent)
    "root": ((0, 0, 0), None),
    "body": ((0, 0, BODY_Z0), "root"),
    "eyes": ((0, -HALF_D, BODY_Z0 + 2.5 * U), "body"),
    "nub_L": ((-HALF_W, 0, BODY_Z0 + 1.5 * U), "body"),
    "nub_R": ((HALF_W, 0, BODY_Z0 + 1.5 * U), "body"),
}
LEGS = []
for i, lx in enumerate(LEG_X):
    for row, yy in (("F", -HALF_D + 0.35 * U), ("B", HALF_D - 0.35 * U)):
        name = f"leg_{row}{i}"
        LEGS.append(name)
        BONES[name] = ((lx + 0.25 * U, yy, LEG_H), "body")

CLAY = (0.851, 0.467, 0.341)
EYE = (0.10, 0.09, 0.09)


def build_mesh():
    """Return {group: Builder-part-key} and a Builder holding every piece."""
    b = Builder("clawd", seed=7, z_min=0, z_max=1.2)
    # each bone gets its own part so we can assign vertex groups per part
    for key in ["body", "eyes", "nub_L", "nub_R", *LEGS]:
        b.part(key)
    kw = dict(jitter=0.0, ao=0.9, drop=0.0)
    # body (front face carries the eye sockets; eyes are inset boxes)
    b.box(-HALF_W, -HALF_D, BODY_Z0, HALF_W, HALF_D, BODY_Z1, CLAY, part="body", **kw)
    for ex in (-2.0 * U, 1.5 * U):
        b.box(ex, -HALF_D - 0.02, BODY_Z0 + 2.0 * U, ex + 0.5 * U, -HALF_D + 0.05,
              BODY_Z0 + 3.0 * U, EYE, part="eyes", **kw)
    # nubs
    b.box(-HALF_W - 1 * U, -0.8 * U, BODY_Z0 + 1.0 * U, -HALF_W + 0.01, 0.8 * U,
          BODY_Z0 + 2.0 * U, CLAY, part="nub_L", **kw)
    b.box(HALF_W - 0.01, -0.8 * U, BODY_Z0 + 1.0 * U, HALF_W + 1 * U, 0.8 * U,
          BODY_Z0 + 2.0 * U, CLAY, part="nub_R", **kw)
    # legs
    for name in LEGS:
        hx, hy, _ = BONES[name][0]
        b.box(hx - 0.25 * U, hy - 0.3 * U, 0, hx + 0.25 * U, hy + 0.3 * U, LEG_H + 0.02,
              CLAY, part=name, **kw)
    return b


def build_accessories():
    """Accessory meshes, each bound to a single bone. Hidden by default in the app."""
    acc = {}

    def mk(name, bone):
        b = Builder("acc_" + name, seed=3, z_min=0, z_max=1.2)
        acc[name] = (b, bone)
        return b

    kw = dict(jitter=0.0, ao=0.9, drop=0.0)
    # headphones (navy band over the top, cups on the sides) - Claude FM look
    h = mk("headphones", "body")
    navy = (0.24, 0.33, 0.55)
    top = BODY_Z1
    h.box(-HALF_W - 0.06, -0.5 * U, top, HALF_W + 0.06, 0.5 * U, top + 0.08, navy, **kw)
    for s in (-1, 1):
        x = s * (HALF_W + 0.03)
        h.box(x - 0.06, -0.5 * U, top - 0.05, x + 0.06, 0.5 * U, top + 0.08, navy, **kw)
        h.box(x - 0.09 if s < 0 else x - 0.03, -0.9 * U, BODY_Z0 + 2.4 * U,
              x + 0.03 if s < 0 else x + 0.09, 0.9 * U, BODY_Z0 + 3.6 * U, navy, **kw)
    # hard hat
    hh = mk("hardhat", "body")
    yel = (0.92, 0.74, 0.33)
    hh.box(-HALF_W - 0.06, -HALF_D - 0.12, top, HALF_W + 0.06, HALF_D + 0.06, top + 0.05, yel, **kw)
    hh.box(-HALF_W + 0.08, -HALF_D + 0.04, top + 0.05, HALF_W - 0.08, HALF_D - 0.04, top + 0.3,
           yel, **kw)
    hh.box(-0.05, -HALF_D + 0.02, top + 0.05, 0.05, HALF_D - 0.02, top + 0.34, (0.85, 0.66, 0.27), **kw)
    # lab goggles + coat collar (max effort)
    g = mk("goggles", "body")
    gz = BODY_Z0 + 2.5 * U
    g.box(-HALF_W - 0.02, -HALF_D - 0.04, gz - 0.03, HALF_W + 0.02, -HALF_D + 0.02, gz + 0.03,
          (0.2, 0.2, 0.2), **kw)
    for ex in (-1.75 * U, 1.75 * U):
        g.box(ex - 0.13, -HALF_D - 0.1, gz - 0.13, ex + 0.13, -HALF_D - 0.02, gz + 0.13,
              (0.25, 0.25, 0.25), **kw)
        g.box(ex - 0.09, -HALF_D - 0.11, gz - 0.09, ex + 0.09, -HALF_D - 0.09, gz + 0.09,
              (0.85, 0.93, 0.97), **kw)
    g.box(-HALF_W - 0.02, -HALF_D - 0.02, BODY_Z0 - 0.01, HALF_W + 0.02, HALF_D + 0.02,
          BODY_Z0 + 1.2 * U, (0.96, 0.96, 0.94), **kw)  # lab coat hem
    # coffee mug in the right nub
    m = mk("mug", "nub_R")
    mx = HALF_W + 0.8 * U
    mz = BODY_Z0 + 2.0 * U
    m.box(mx - 0.09, -0.09, mz, mx + 0.09, 0.09, mz + 0.22, (0.97, 0.96, 0.93), **kw)
    m.box(mx + 0.09, -0.03, mz + 0.05, mx + 0.14, 0.03, mz + 0.16, (0.97, 0.96, 0.93), **kw)
    m.box(mx - 0.07, -0.07, mz + 0.2, mx + 0.07, 0.07, mz + 0.225, (0.35, 0.22, 0.14), **kw)
    # open book held in front
    bk = mk("book", "body")
    bz = BODY_Z0 + 1.2 * U
    bk.box(-0.32, -HALF_D - 0.3, bz, 0.32, -HALF_D - 0.05, bz + 0.05, (0.36, 0.45, 0.62), **kw)
    bk.box(-0.29, -HALF_D - 0.28, bz + 0.05, -0.01, -HALF_D - 0.07, bz + 0.09, (0.97, 0.95, 0.9), **kw)
    bk.box(0.01, -HALF_D - 0.28, bz + 0.05, 0.29, -HALF_D - 0.07, bz + 0.09, (0.97, 0.95, 0.9), **kw)
    # tiny hammer in the right nub
    hm = mk("hammer", "nub_R")
    hx = HALF_W + 0.5 * U
    hm.box(hx - 0.025, -0.025, mz - 0.05, hx + 0.025, 0.025, mz + 0.42, (0.6, 0.42, 0.29), **kw)
    hm.box(hx - 0.12, -0.07, mz + 0.38, hx + 0.12, 0.07, mz + 0.52, (0.32, 0.3, 0.28), **kw)
    # party hat for celebrations
    ph = mk("partyhat", "body")
    for k in range(5):
        r = 0.16 * (1 - k / 5)
        ph.box(-r, -r, top + k * 0.07, r, r, top + (k + 1) * 0.07,
               (0.85, 0.47, 0.34) if k % 2 == 0 else (0.93, 0.76, 0.36), **kw)
    # sleeping cap
    sc = mk("nightcap", "body")
    for k in range(4):
        r = (HALF_W - 0.05) * (1 - k / 4.5)
        sc.box(-r, -HALF_D + 0.05 + k * 0.03, top + k * 0.07, r, HALF_D - 0.05, top + (k + 1) * 0.07,
               (0.43, 0.55, 0.72), **kw)
    sc.box(HALF_W - 0.25, 0.0, top + 0.2, HALF_W - 0.05, 0.2, top + 0.4, (0.97, 0.96, 0.93), **kw)
    return acc


def make_armature():
    arm_data = bpy.data.armatures.new("ClawdRig")
    arm = bpy.data.objects.new("Clawd", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (head, parent) in BONES.items():
        eb = arm_data.edit_bones.new(name)
        eb.head = head
        eb.tail = (head[0], head[1], head[2] + 0.1)
        eb.roll = 0.0
    for name, (_, parent) in BONES.items():
        if parent:
            arm_data.edit_bones[name].parent = arm_data.edit_bones[parent]
            arm_data.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def skin(obj, arm, groups):
    """groups: list of (bone name, vertex index list)."""
    for bone, idx in groups:
        vg = obj.vertex_groups.new(name=bone)
        vg.add(idx, 1.0, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm


def merged_body(b, arm):
    """Merge body parts into one skinned mesh with one vertex group per bone."""
    import bmesh  # noqa: F401

    from lib.voxel import shared_material

    verts, faces, cols, groups = [], [], [], []
    for key, p in b.parts.items():
        if p.empty():
            continue
        off = len(verts)
        verts += p.verts
        faces += [tuple(i + off for i in f) for f in p.faces]
        cols += p.cols
        groups.append((key, list(range(off, off + len(p.verts)))))
    me = bpy.data.meshes.new("clawd_body")
    me.from_pydata(verts, [], faces)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for i, c in enumerate(cols):
        ca.data[i].color = (*c, 1.0)
    me.materials.append(shared_material())
    ob = bpy.data.objects.new("clawd_body", me)
    bpy.context.scene.collection.objects.link(ob)
    skin(ob, arm, groups)
    return ob


def acc_mesh(name, b, bone, arm):
    from lib.voxel import shared_material

    p = b.parts["static"]
    me = bpy.data.meshes.new("acc_" + name)
    me.from_pydata(p.verts, [], p.faces)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for i, c in enumerate(p.cols):
        ca.data[i].color = (*c, 1.0)
    me.materials.append(shared_material())
    ob = bpy.data.objects.new("acc_" + name, me)
    bpy.context.scene.collection.objects.link(ob)
    skin(ob, arm, [(bone, list(range(len(p.verts))))])
    ob["accessory"] = name
    return ob


# ----------------------------------------------------------------- animation
def q_axis(axis, deg):
    """Quaternion for rotating `deg` about a world axis, expressed in bone space.

    All bones point +Z with zero roll, so bone-local axes are:
      local X = world X, local Y = world Z, local Z = world -Y.
    """
    ax = {"x": (1, 0, 0), "up": (0, 1, 0), "fwd": (0, 0, -1)}[axis]
    return Quaternion(ax, math.radians(deg))


class Anim:
    def __init__(self, arm, name, frames):
        self.arm, self.name, self.frames = arm, name, frames
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act
        self.act = act
        # reset pose
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.scale = (1, 1, 1)

    def key(self, bone, f, loc=None, rot=None, scale=None):
        pb = self.arm.pose.bones[bone]
        if loc is not None:
            # loc in world-ish terms (x, up, fwd) -> bone local (x, y, z)
            pb.location = (loc[0], loc[1], -loc[2] if len(loc) > 2 else 0)
            pb.keyframe_insert("location", frame=f)
        if rot is not None:
            q = Quaternion((1, 0, 0, 0))
            for axis, deg in rot:
                q = q @ q_axis(axis, deg)
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
        if scale is not None:
            pb.scale = scale
            pb.keyframe_insert("scale", frame=f)

    def loop(self, bone, keys, **kw):
        """keys: list of (frame, value) for kw-kind ('loc'|'rot'|'scale')."""
        kind = kw["kind"]
        for f, v in keys:
            self.key(bone, f, **{kind: v})

    def finish(self):
        # ensure every bone keyed at first & last frame so clips don't leak poses
        for pb in self.arm.pose.bones:
            for f in (0, self.frames):
                if not self._has(pb.name, "rotation_quaternion", f):
                    pass
        self.act.frame_range = (0, self.frames)
        self.arm.animation_data.action = None


    def _has(self, bone, prop, f):
        return False


def make_actions(arm):
    legs_a = [n for i, n in enumerate(LEGS) if (i // 2 + i % 2) % 2 == 0]
    legs_b = [n for n in LEGS if n not in legs_a]

    # idle: gentle breathing + blink
    a = Anim(arm, "idle", 90)
    for f, y in [(0, 0), (45, 0.025), (90, 0)]:
        a.key("body", f, loc=(0, y, 0), scale=(1, 1 - y * 1.2, 1))
    for f, s in [(0, 1), (58, 1), (61, 0.1), (64, 1), (90, 1)]:
        a.key("eyes", f, scale=(1, s, 1))
    for f, d in [(0, 0), (45, 6), (90, 0)]:
        a.key("nub_L", f, rot=[("fwd", -d)])
        a.key("nub_R", f, rot=[("fwd", d)])
    a.finish()

    # walk: alternating legs, bouncy body
    a = Anim(arm, "walk", 16)
    for f, d in [(0, 28), (8, -28), (16, 28)]:
        for n in legs_a:
            a.key(n, f, rot=[("x", d)])
        for n in legs_b:
            a.key(n, f, rot=[("x", -d)])
    for f, y in [(0, 0), (4, 0.05), (8, 0), (12, 0.05), (16, 0)]:
        a.key("body", f, loc=(0, y, 0), rot=[("fwd", 4 if f in (4,) else -4 if f == 12 else 0)])
    for f, d in [(0, 12), (8, -12), (16, 12)]:
        a.key("nub_L", f, rot=[("up", d)])
        a.key("nub_R", f, rot=[("up", d)])
    a.finish()

    # dance (Claude FM vibes): hop, sway, nubs pumping
    a = Anim(arm, "dance", 30)
    for f, y, r in [(0, 0, -10), (7, 0.14, 0), (15, 0, 10), (22, 0.14, 0), (30, 0, -10)]:
        a.key("body", f, loc=(0, y, 0), rot=[("fwd", r)])
    for f, d in [(0, 50), (15, -10), (30, 50)]:
        a.key("nub_L", f, rot=[("fwd", -d)])
        a.key("nub_R", f, rot=[("fwd", 40 - d)])
    for f, d in [(0, 0), (7, -20), (15, 0), (22, 20), (30, 0)]:
        for n in legs_a:
            a.key(n, f, rot=[("x", d)])
        for n in legs_b:
            a.key(n, f, rot=[("x", -d)])
    a.finish()

    # read: nubs forward holding a book, slow nod
    a = Anim(arm, "read", 120)
    for f, d in [(0, 0), (60, 6), (100, 6), (120, 0)]:
        a.key("body", f, rot=[("x", d)])
    for f in (0, 120):
        a.key("nub_L", f, rot=[("up", -55), ("fwd", -15)])
        a.key("nub_R", f, rot=[("up", 55), ("fwd", 15)])
    for f, s in [(0, 1), (80, 1), (83, 0.1), (86, 1), (120, 1)]:
        a.key("eyes", f, scale=(1, s, 1))
    a.finish()

    # sip: right nub lifts mug, body leans back
    a = Anim(arm, "sip", 90)
    for f, d in [(0, 0), (20, 75), (55, 75), (75, 0), (90, 0)]:
        a.key("nub_R", f, rot=[("fwd", d)])
    for f, d in [(0, 0), (25, -8), (55, -8), (75, 0), (90, 0)]:
        a.key("body", f, rot=[("x", d)])
    for f, s in [(0, 1), (25, 0.15), (55, 0.15), (60, 1), (90, 1)]:
        a.key("eyes", f, scale=(1, s, 1))
    a.finish()

    # hammer / build
    a = Anim(arm, "hammer", 24)
    for f, d in [(0, 0), (10, 95), (14, 100), (17, -15), (24, 0)]:
        a.key("nub_R", f, rot=[("fwd", d)])
    for f, y, s in [(0, 0, 1), (10, 0.04, 1.02), (17, -0.03, 0.92), (24, 0, 1)]:
        a.key("body", f, loc=(0, y, 0), scale=(1 + (1 - s) * 0.5, s, 1 + (1 - s) * 0.5))
    a.finish()

    # wave hello
    a = Anim(arm, "wave", 40)
    for f, d in [(0, 0), (8, 115), (16, 85), (24, 115), (32, 85), (40, 0)]:
        a.key("nub_R", f, rot=[("fwd", d)])
    for f, r in [(0, 0), (8, -5), (32, -5), (40, 0)]:
        a.key("body", f, rot=[("fwd", r)])
    a.finish()

    # sleep: squashed, eyes shut, slow breathing
    a = Anim(arm, "sleep", 120)
    for f, s in [(0, 0.9), (60, 0.95), (120, 0.9)]:
        a.key("body", f, loc=(0, -0.04, 0), scale=(1.04, s, 1.04))
    for f in (0, 120):
        a.key("eyes", f, scale=(1, 0.08, 1))
        a.key("nub_L", f, rot=[("fwd", 15)])
        a.key("nub_R", f, rot=[("fwd", -15)])
    a.finish()

    # celebrate: big hop with a spin, nubs up
    a = Anim(arm, "celebrate", 40)
    for f, y, yaw in [(0, 0, 0), (6, -0.04, 0), (16, 0.45, 180), (26, 0, 360), (32, -0.03, 360),
                      (40, 0, 360)]:
        a.key("body", f, loc=(0, y, 0), rot=[("up", yaw)],
              scale=(1.06, 0.9, 1.06) if y < 0 else (1, 1, 1))
    for f, d in [(0, 0), (12, 120), (30, 120), (40, 0)]:
        a.key("nub_L", f, rot=[("fwd", -d)])
        a.key("nub_R", f, rot=[("fwd", d)])
    a.finish()

    # look: curious peek left/right (exploring new places)
    a = Anim(arm, "look", 90)
    for f, yaw in [(0, 0), (15, 25), (40, 25), (55, -25), (80, -25), (90, 0)]:
        a.key("body", f, rot=[("up", yaw)])
    for f, d in [(0, 0), (15, 30), (80, 30), (90, 0)]:
        a.key("nub_R", f, rot=[("fwd", d)])
    a.finish()


def main(out):
    reset_scene()
    bpy.context.scene.render.fps = FPS
    arm = make_armature()
    b = build_mesh()
    merged_body(b, arm)
    for name, (ab, bone) in build_accessories().items():
        acc_mesh(name, ab, bone, arm)
    make_actions(arm)
    export_glb(arm, out, animations=True)
    print("clawd exported ->", out)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv[0] if argv else "public/world/clawd.glb")
