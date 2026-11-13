"""Build every region of Clawd's Archipelago and export it.

Usage (headless, bpy as a Python module):
    python blender/build_all.py <raw_out_dir> <manifest_path> [only_index]

Writes region_XX.glb (unoptimised) into raw_out_dir and world.json (Y-up three.js
coordinates) to manifest_path. scripts/build-world.sh then compresses the glbs.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.voxel import Builder, bake_lightmap, export_glb, reset_scene, surface_area  # noqa: E402
from regions import REGIONS  # noqa: E402


def to3(p):
    """Blender (x, y, z) -> three.js (x, z, -y), rounded."""
    x, y, z = p
    return [round(x, 3), round(z, 3), round(-y, 3)]


def bounds(b):
    # verts are world-space (the pivot is subtracted only at build time)
    xs = [v[0] for p in b.parts.values() for v in p.verts]
    ys = [v[1] for p in b.parts.values() for v in p.verts]
    zs = [v[2] for p in b.parts.values() for v in p.verts]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    return lo, hi


def main():
    out = Path(sys.argv[1])
    manifest = Path(sys.argv[2])
    only = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    lm_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else None  # bake lightmaps when given
    out.mkdir(parents=True, exist_ok=True)
    old = {}
    if manifest.exists():
        old = {r["id"]: r for r in json.loads(manifest.read_text())["regions"]}
    regions = []
    for i, r in enumerate(REGIONS):
        b = Builder(f"region_{i:02d}", seed=1000 + i)
        meta = r["fn"](b)
        lo, hi = bounds(b)
        lm = old.get(i, {}).get("lm")
        if only is None or only == i:
            reset_scene()
            root = b.build()
            static = next((o for o in root.children if o.get("part") == "static"), None)
            if lm_dir and static is not None:
                lm_dir.mkdir(parents=True, exist_ok=True)
                area = surface_area(static)
                res = 1024 if area > 900 else 512 if area > 160 else 256
                scale = bake_lightmap(static, str(lm_dir / f"region_{i:02d}.webp"), res)
                lm = dict(file=f"world/lm/region_{i:02d}.webp", scale=scale, res=res)
                print(f"   lightmap {res}px area={area:.0f} scale={scale}")
            export_glb(root, str(out / f"region_{i:02d}.glb"))
        # focus: centre of the region's footprint, ignoring far-flung sky items
        c = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        regions.append(dict(
            id=i,
            file=f"world/region_{i:02d}.glb",
            chapter=r["chapter"],
            title=r["title"],
            blurb=r["blurb"],
            parent=meta["parent"],
            door=to3(meta["door"]),
            spot=to3(meta["spot"]),
            look=to3(meta["look"]),
            via=[to3(p) for p in meta["via"]],
            action=meta["action"],
            acc=meta["acc"],
            focus=to3(meta["spot"]) if size > 30 else to3(c),
            radius=round(min(size, 30) / 2 + 2, 2),
            boxes=b.stats,
            lm=lm,
        ))
        print(f"region {i:02d} {r['title']:<24} boxes={b.stats}")
    lo = [min(r["focus"][k] for r in regions) for k in range(3)]
    hi = [max(r["focus"][k] for r in regions) for k in range(3)]
    manifest.write_text(json.dumps(dict(
        version=1,
        regions=regions,
        center=[round((lo[k] + hi[k]) / 2, 2) for k in range(3)],
        extent=round(max(hi[k] - lo[k] for k in range(3)) / 2, 2),
    ), indent=1))
    print("manifest ->", manifest)


if __name__ == "__main__":
    main()
