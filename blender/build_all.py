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
from lib.voxel import Builder, export_glb, reset_scene  # noqa: E402
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
    only = int(sys.argv[3]) if len(sys.argv) > 3 else None
    out.mkdir(parents=True, exist_ok=True)
    regions = []
    for i, r in enumerate(REGIONS):
        b = Builder(f"region_{i:02d}", seed=1000 + i)
        meta = r["fn"](b)
        lo, hi = bounds(b)
        if only is None or only == i:
            reset_scene()
            root = b.build()
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
