"""Tiny voxel/box mesh builder for headless Blender (bpy).

Everything in ClawdStudy is built from axis-aligned boxes. Boxes are
accumulated into a handful of merged meshes per region (static, glow and
named animated parts) so the web renderer gets very few draw calls.

Coordinates are Blender's: X right, Y back, Z up. The glTF exporter converts
to Y-up for three.js.

Per-corner data written to every mesh:
  * colour attribute "Col"   - flat colour with contact darkening (cheap fake AO)
  * attribute "_drop"        - per-box reveal delay in [0,1] (bottom boxes first),
                               consumed by the reveal shader in the web app
"""
import math
import random

import bpy

# Palette: warm cream/terracotta, matching the Claude effort-video look.
P = {
    "grass": (0.66, 0.72, 0.53),
    "grass2": (0.58, 0.67, 0.47),
    "grass3": (0.74, 0.78, 0.58),
    "leaf": (0.43, 0.56, 0.35),
    "leaf2": (0.36, 0.49, 0.31),
    "leaf3": (0.55, 0.64, 0.38),
    "path": (0.86, 0.78, 0.64),
    "sand": (0.91, 0.84, 0.69),
    "rock": (0.73, 0.65, 0.56),
    "rock2": (0.60, 0.53, 0.45),
    "rock3": (0.48, 0.42, 0.37),
    "cream": (0.94, 0.90, 0.83),
    "cream2": (0.88, 0.83, 0.74),
    "white": (0.97, 0.96, 0.93),
    "roof": (0.79, 0.44, 0.31),
    "roof2": (0.66, 0.35, 0.26),
    "clay": (0.85, 0.47, 0.34),   # Clawd orange
    "wood": (0.60, 0.42, 0.29),
    "wood2": (0.47, 0.32, 0.22),
    "dark": (0.23, 0.21, 0.19),
    "charcoal": (0.32, 0.30, 0.28),
    "steel": (0.55, 0.57, 0.60),
    "water": (0.56, 0.72, 0.79),
    "water2": (0.66, 0.80, 0.86),
    "blue": (0.43, 0.55, 0.72),
    "sky": (0.75, 0.82, 0.89),
    "yellow": (0.93, 0.76, 0.36),
    "mustard": (0.85, 0.66, 0.27),
    "red": (0.78, 0.33, 0.29),
    "pink": (0.90, 0.62, 0.62),
    "lilac": (0.70, 0.62, 0.80),
    "teal": (0.37, 0.62, 0.60),
    "snow": (0.97, 0.97, 0.98),
    "chalk": (0.22, 0.30, 0.26),
    "glow": (1.00, 0.84, 0.52),
    "glowblue": (0.62, 0.85, 1.00),
    "glowgreen": (0.55, 1.00, 0.75),
    "glowpink": (0.95, 0.60, 1.00),
}


def col(c):
    return P[c] if isinstance(c, str) else c


class Part:
    """A merged mesh under construction."""

    def __init__(self, name, pivot=(0.0, 0.0, 0.0), extras=None):
        self.name = name
        self.pivot = pivot
        self.extras = extras or {}
        self.verts = []
        self.faces = []
        self.cols = []   # per face corner
        self.drops = []  # per face corner

    def empty(self):
        return not self.faces


class Builder:
    """Collects boxes for one region (or for Clawd) and turns them into objects."""

    def __init__(self, name, seed=0, z_min=-6.0, z_max=24.0):
        self.name = name
        self.rng = random.Random(seed)
        self.parts = {"static": Part(name + "_static"), "glow": Part(name + "_glow")}
        self.z_min, self.z_max = z_min, z_max
        self.stats = 0

    # ------------------------------------------------------------------ parts
    def part(self, key, pivot=(0, 0, 0), **extras):
        if key not in self.parts:
            self.parts[key] = Part(f"{self.name}_{key}", pivot, extras)
        return key

    # ------------------------------------------------------------------ boxes
    def box(self, x0, y0, z0, x1, y1, z1, c, part="static", jitter=0.025,
            ao=0.80, drop=None, top=None, skip_bottom=False):
        """Axis-aligned box from corner (x0,y0,z0) to (x1,y1,z1)."""
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        if z0 > z1:
            z0, z1 = z1, z0
        p = self.parts[part]
        base = col(c)
        j = 1.0 + self.rng.uniform(-jitter, jitter)
        cc = tuple(min(1.0, v * j) for v in base)
        tc = col(top) if top else cc
        if drop is None:
            # bottom-up reveal order with a little shuffle; normalised per region in build()
            drop = ("z", z0, self.rng.uniform(0, 1))
        i = len(p.verts)
        p.verts += [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        faces = [
            ((4, 5, 6, 7), "top"),
            ((0, 3, 2, 1), "bottom"),
            ((0, 1, 5, 4), "side"),
            ((1, 2, 6, 5), "side"),
            ((2, 3, 7, 6), "side"),
            ((3, 0, 4, 7), "side"),
        ]
        dark = tuple(v * ao for v in cc)
        for f, kind in faces:
            if kind == "bottom" and skip_bottom:
                continue
            p.faces.append(tuple(i + k for k in f))
            for k in f:
                if kind == "top":
                    p.cols.append(tc)
                elif kind == "bottom":
                    p.cols.append(dark)
                else:
                    p.cols.append(dark if k < 4 else cc)
                p.drops.append(drop)
        self.stats += 1
        return self

    def cube(self, x, y, z, s, c, **kw):
        """Cube of size s whose bottom-centre sits at (x, y, z)."""
        h = s / 2
        return self.box(x - h, y - h, z, x + h, y + h, z + s, c, **kw)

    def disc(self, cx, cy, z0, z1, r, c, step=0.5, **kw):
        """Voxelised cylinder: one box per row of `step`."""
        n = max(1, int(round(r / step)))
        for i in range(-n, n):
            yc = (i + 0.5) * step
            if abs(yc) > r:
                continue
            w = math.sqrt(max(0.0, r * r - yc * yc))
            w = max(step / 2, round(w / step * 2) / 2 * step)
            self.box(cx - w, cy + i * step, z0, cx + w, cy + (i + 1) * step, z1, c, **kw)
        return self

    def dome(self, cx, cy, z, r, c, layers=6, step=0.5, **kw):
        """Stack of shrinking discs."""
        h = r / layers
        for k in range(layers):
            rr = r * math.cos((k / layers) * math.pi / 2)
            self.disc(cx, cy, z + k * h, z + (k + 1) * h, max(rr, step), c, step=step, **kw)
        return self

    def cone(self, cx, cy, z, r, h, c, layers=5, step=0.5, **kw):
        lh = h / layers
        for k in range(layers):
            rr = r * (1 - k / layers)
            self.disc(cx, cy, z + k * lh, z + (k + 1) * lh, max(rr, step * 0.5), c, step=step, **kw)
        return self

    # ------------------------------------------------------------- landscape
    def plot(self, x0, y0, x1, y1, z=0.0, c="grass", depth=4.0, rock=True, edge="grass2",
             thick=0.6, seed_off=0):
        """A floating piece of land: grass slab plus a stepped rocky underside."""
        self.box(x0, y0, z - thick, x1, y1, z, c, jitter=0.0, top=c, drop=0.0)
        # grassy lip
        self.box(x0 - 0.05, y0 - 0.05, z - thick - 0.25, x1 + 0.05, y1 + 0.05, z - thick, edge,
                 jitter=0.0, drop=0.0)
        if not rock:
            return self
        rng = random.Random(hash((x0, y0, x1, y1, seed_off)) & 0xffff)
        layers = max(2, int(depth / 0.9))
        zz = z - thick - 0.25
        ax0, ay0, ax1, ay1 = x0, y0, x1, y1
        for k in range(layers):
            inset = 0.45 + rng.uniform(0.1, 0.55)
            ax0 += inset * rng.uniform(0.6, 1.2)
            ay0 += inset * rng.uniform(0.6, 1.2)
            ax1 -= inset * rng.uniform(0.6, 1.2)
            ay1 -= inset * rng.uniform(0.6, 1.2)
            if ax1 - ax0 < 0.6 or ay1 - ay0 < 0.6:
                break
            lh = rng.uniform(0.7, 1.1)
            shade = ("rock", "rock2", "rock3")[min(2, k * 3 // layers)]
            self.box(ax0, ay0, zz - lh, ax1, ay1, zz, shade, jitter=0.04, drop=0.0)
            # a few hanging boulders for character
            if rng.random() < 0.6:
                bx = rng.uniform(ax0, ax1 - 0.6)
                by = rng.uniform(ay0, ay1 - 0.6)
                bs = rng.uniform(0.4, 0.9)
                self.box(bx, by, zz - lh - bs * 0.6, bx + bs, by + bs, zz - lh, "rock2", drop=0.0)
            zz -= lh
        return self

    def tree(self, x, y, z=0.0, h=None, kind="round"):
        rng = self.rng
        h = h or rng.uniform(1.4, 2.4)
        self.box(x - 0.15, y - 0.15, z, x + 0.15, y + 0.15, z + h * 0.55, "wood")
        leaf = rng.choice(["leaf", "leaf2", "leaf3"])
        if kind == "round":
            r = h * 0.42
            self.box(x - r, y - r, z + h * 0.45, x + r, y + r, z + h * 0.45 + r * 1.5, leaf)
            self.box(x - r * 0.65, y - r * 0.65, z + h * 0.45 + r * 1.5, x + r * 0.65,
                     y + r * 0.65, z + h * 0.45 + r * 2.1, leaf)
        else:  # pine
            for k in range(3):
                r = h * (0.42 - k * 0.11)
                zz = z + h * 0.35 + k * h * 0.33
                self.box(x - r, y - r, zz, x + r, y + r, zz + h * 0.38, leaf)
        return self

    def bush(self, x, y, z=0.0, s=0.5, c=None):
        c = c or self.rng.choice(["leaf", "leaf3", "leaf2"])
        return self.box(x - s / 2, y - s / 2, z, x + s / 2, y + s / 2, z + s * 0.8, c)

    def flower(self, x, y, z=0.0):
        c = self.rng.choice(["red", "yellow", "pink", "lilac", "white"])
        self.box(x - 0.03, y - 0.03, z, x + 0.03, y + 0.03, z + 0.25, "leaf")
        return self.box(x - 0.09, y - 0.09, z + 0.25, x + 0.09, y + 0.09, z + 0.4, c)

    def lamp(self, x, y, z=0.0, h=1.6):
        self.box(x - 0.06, y - 0.06, z, x + 0.06, y + 0.06, z + h, "dark")
        self.box(x - 0.18, y - 0.18, z + h, x + 0.18, y + 0.18, z + h + 0.05, "dark")
        self.box(x - 0.14, y - 0.14, z + h + 0.05, x + 0.14, y + 0.14, z + h + 0.33, "glow",
                 part="glow")
        self.box(x - 0.18, y - 0.18, z + h + 0.33, x + 0.18, y + 0.18, z + h + 0.4, "dark")
        return self

    def windows(self, x0, x1, y, z0, z1, n, rows=1, face="-y", w=0.35, h=0.45, inset=0.02):
        """Glowing windows on a wall plane."""
        for r in range(rows):
            zc = z0 + (z1 - z0) * (r + 0.5) / rows
            for i in range(n):
                xc = x0 + (x1 - x0) * (i + 0.5) / n
                if face == "-y":
                    self.box(xc - w / 2, y - inset - 0.04, zc - h / 2, xc + w / 2, y + 0.01, zc + h / 2,
                             "glow", part="glow")
                elif face == "+y":
                    self.box(xc - w / 2, y - 0.01, zc - h / 2, xc + w / 2, y + inset + 0.04, zc + h / 2,
                             "glow", part="glow")
                elif face == "-x":
                    self.box(y - inset - 0.04, xc - w / 2, zc - h / 2, y + 0.01, xc + w / 2, zc + h / 2,
                             "glow", part="glow")
                elif face == "+x":
                    self.box(y - 0.01, xc - w / 2, zc - h / 2, y + inset + 0.04, xc + w / 2, zc + h / 2,
                             "glow", part="glow")
        return self

    def house(self, x, y, w, d, h, wall="cream", roof="roof", door_face="-y", win=2, z=0.0):
        """Simple house: walls + stepped gable roof + door + glowing windows."""
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - d / 2, y + d / 2
        self.box(x0, y0, z, x1, y1, z + h, wall)
        # stepped roof along x
        steps = 4
        for k in range(steps):
            t = k / steps
            iy = d / 2 * t
            self.box(x0 - 0.15, y0 - 0.15 + iy, z + h + k * 0.32, x1 + 0.15, y1 + 0.15 - iy,
                     z + h + (k + 1) * 0.32, roof if k % 2 == 0 else "roof2")
        if door_face == "-y":
            self.box(x - 0.25, y0 - 0.06, z, x + 0.25, y0 + 0.01, z + 0.95, "wood2")
            if win:
                self.windows(x0 + 0.1, x - 0.35, y0, z + 0.4, z + h - 0.3, 1)
                self.windows(x + 0.35, x1 - 0.1, y0, z + 0.4, z + h - 0.3, 1)
        else:
            self.box(x - 0.25, y1 - 0.01, z, x + 0.25, y1 + 0.06, z + 0.95, "wood2")
        return self

    # ------------------------------------------------------------- output
    def build(self, collection=None):
        """Create Blender objects for all non-empty parts. Returns root empty."""
        autos = [d[1] for p in self.parts.values() for d in p.drops if isinstance(d, tuple)]
        lo, hi = (min(autos), max(autos)) if autos else (0.0, 1.0)
        span = max(hi - lo, 0.5)
        for p in self.parts.values():
            p.drops = [d if not isinstance(d, tuple) else
                       min(1.0, 0.12 + (d[1] - lo) / span * 0.72 + d[2] * 0.16) for d in p.drops]
        root = bpy.data.objects.new(self.name, None)
        (collection or bpy.context.scene.collection).objects.link(root)
        for key, p in self.parts.items():
            if p.empty():
                continue
            px, py, pz = p.pivot
            verts = [(v[0] - px, v[1] - py, v[2] - pz) for v in p.verts]
            me = bpy.data.meshes.new(p.name)
            me.from_pydata(verts, [], p.faces)
            me.update()
            ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
            for li, c in enumerate(p.cols):
                ca.data[li].color = (c[0], c[1], c[2], 1.0)
            da = me.attributes.new("_drop", "FLOAT", "CORNER")
            da.data.foreach_set("value", p.drops)
            me.color_attributes.active_color = ca
            me.color_attributes.render_color_index = 0
            me.materials.append(shared_material())
            ob = bpy.data.objects.new(p.name, me)
            ob.location = p.pivot
            ob.parent = root
            ob["part"] = key
            ob["pivot"] = [round(px, 4), round(pz, 4), round(-py, 4)]  # three.js coords
            for k, v in p.extras.items():
                ob[k] = v
            (collection or bpy.context.scene.collection).objects.link(ob)
        return root


_MAT = None


def shared_material():
    """One material that reads the colour attribute (so the exporter keeps it)."""
    global _MAT
    if _MAT and _MAT.name in bpy.data.materials:
        return _MAT
    m = bpy.data.materials.new("voxel")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    _MAT = m
    return m


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global _MAT
    _MAT = None


def export_glb(root, path, animations=False):
    """Export `root` and its descendants as GLB."""
    bpy.ops.object.select_all(action="DESELECT")
    stack = [root]
    while stack:
        o = stack.pop()
        o.select_set(True)
        stack.extend(o.children)
    bpy.context.view_layer.objects.active = root
    kw = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_extras=True,
        export_attributes=True,
        export_vertex_color="ACTIVE",
        export_normals=True,
        export_texcoords=False,
        export_tangents=False,
        export_cameras=False,
        export_lights=False,
        export_animations=animations,
    )
    if animations:
        kw.update(export_animation_mode="ACTIONS", export_force_sampling=True,
                  export_frame_step=1, export_anim_single_armature=True,
                  export_skins=True, export_def_bones=False)
    bpy.ops.export_scene.gltf(**kw)
