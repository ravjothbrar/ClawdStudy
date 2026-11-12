"""Clawd's Archipelago: 31 regions (0 = start, 1..30 = one per completed pomodoro).

Each region function draws into a Builder and returns metadata used by the app:
  title, blurb, chapter
  door   - where this region joins the walking graph (Blender coords)
  parent - region whose door we connect to
  via    - extra waypoints between the parent's door and our door
  spot   - where Clawd stands to "use" the landmark
  look   - point Clawd faces while there
  action - Clawd animation clip, acc - accessory to wear

Animated sub-parts carry glTF extras that the web app interprets:
  anim="spin"  axis=x|y|z (three.js axes) speed=rad/s
  anim="bob"   amp, speed
  anim="pulse" speed (glow flicker)
"""
import math

from lib.voxel import P

REGIONS = []


def region(chapter, title, blurb):
    def deco(fn):
        REGIONS.append(dict(fn=fn, chapter=chapter, title=title, blurb=blurb))
        return fn
    return deco


def M(door, spot, look, action="look", acc=None, parent=None, via=()):
    return dict(door=door, spot=spot, look=look, action=action, acc=acc, parent=parent,
                via=list(via))


def fence(b, x0, y0, x1, y1, z=0.0, c="wood"):
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.6))
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        b.box(x - 0.06, y - 0.06, z, x + 0.06, y + 0.06, z + 0.55, c)
    if x0 == x1:
        b.box(x0 - 0.03, y0, z + 0.3, x0 + 0.03, y1, z + 0.38, c)
        b.box(x0 - 0.03, y0, z + 0.45, x0 + 0.03, y1, z + 0.5, c)
    else:
        b.box(x0, y0 - 0.03, z + 0.3, x1, y0 + 0.03, z + 0.38, c)
        b.box(x0, y0 - 0.03, z + 0.45, x1, y0 + 0.03, z + 0.5, c)


def stones(b, pts, z=0.0, s=0.45):
    for (x, y) in pts:
        b.box(x - s / 2, y - s / 2, z, x + s / 2, y + s / 2, z + 0.06, "path", jitter=0.06)


def note(b, key, x, y, z):
    """A floating music note (eighth note)."""
    b.box(x, y - 0.05, z, x + 0.22, y + 0.05, z + 0.16, "dark", part=key)
    b.box(x + 0.16, y - 0.04, z + 0.16, x + 0.22, y + 0.04, z + 0.7, "dark", part=key)
    b.box(x + 0.22, y - 0.04, z + 0.55, x + 0.4, y + 0.04, z + 0.7, "dark", part=key)


# =============================================================== 0. START
@region("Start", "Clawd's Hut", "Where it all begins: a desk, a radio tuned to Claude FM, and a plant.")
def r00(b):
    b.plot(-3, -3, 3, 3, depth=4.5)
    # hut
    b.house(-1.0, 1.2, 2.6, 2.2, 1.8, wall="cream", roof="roof")
    b.box(-2.05, 0.05, 0, -1.8, 0.1, 0.9, "wood2")  # shutter
    b.box(0.05, 2.3, 2.0, 0.45, 2.6, 2.9, "rock2")  # chimney
    # desk (front, facing camera)
    b.box(0.35, -1.95, 0.62, 2.15, -1.25, 0.7, "wood")
    for lx in (0.42, 2.0):
        for ly in (-1.88, -1.35):
            b.box(lx, ly, 0, lx + 0.1, ly + 0.08, 0.62, "wood2")
    # laptop
    b.box(0.6, -1.85, 0.7, 1.3, -1.45, 0.74, "steel")
    b.box(0.6, -1.5, 0.74, 1.3, -1.44, 1.18, "charcoal")
    b.box(0.65, -1.52, 0.78, 1.25, -1.5, 1.14, "glowblue", part="glow")
    # the radio (Claude FM)
    b.box(1.45, -1.9, 0.7, 2.05, -1.55, 1.05, "clay")
    b.box(1.5, -1.92, 0.76, 1.72, -1.9, 0.99, "dark")
    b.box(1.8, -1.93, 0.86, 1.98, -1.9, 0.94, "glow", part="glow")
    b.box(1.95, -1.65, 1.05, 1.98, -1.62, 1.6, "dark")
    # desk lamp + mug
    b.box(0.4, -1.4, 0.7, 0.5, -1.3, 1.2, "dark")
    b.box(0.32, -1.48, 1.2, 0.62, -1.24, 1.3, "glow", part="glow")
    # stool
    b.box(1.0, -0.95, 0, 1.5, -0.6, 0.35, "wood2")
    # potted plant (from the effort video)
    b.box(-2.65, -2.65, 0, -2.05, -2.05, 0.45, "roof")
    for dx, dy, h in ((0, 0, 0.9), (-0.15, 0.1, 0.7), (0.15, -0.1, 0.75), (0.1, 0.15, 0.6)):
        b.box(-2.4 + dx, -2.4 + dy, 0.45, -2.3 + dx, -2.3 + dy, 0.45 + h, "leaf")
    # bits
    b.bush(2.5, 2.4, s=0.6)
    b.bush(-2.6, 2.6, s=0.5)
    for (x, y) in ((2.2, 0.8), (2.6, 0.4), (-2.6, -0.6)):
        b.flower(x, y)
    stones(b, [(0, -2.6), (-0.5, -2.2), (-0.9, -1.4), (-0.95, -0.5)])
    # floating notes above the radio
    b.part("notes", pivot=(1.8, -1.7, 1.6), anim="bob", amp=0.12, speed=1.6)
    note(b, "notes", 1.9, -1.7, 1.8)
    note(b, "notes", 2.4, -1.7, 2.3)
    return M(door=(0, -2.3, 0), spot=(-0.35, -1.3, 0), look=(-0.35, -6, 0), action="dance",
             acc="headphones")


# =============================================================== 1. VILLAGE
@region("Village", "Lamplit Path", "A winding path east, with lamps for late-night sessions.")
def r01(b):
    b.plot(3, -3, 9, 3, depth=3.5)
    stones(b, [(3.4 + i * 0.62, -0.8 + 0.25 * math.sin(i)) for i in range(9)])
    for x in (4.2, 6.6, 8.6):
        b.lamp(x, 0.1)
    # signpost
    b.box(7.4, -2.2, 0, 7.52, -2.08, 1.5, "wood2")
    b.box(7.0, -2.2, 1.15, 8.1, -2.1, 1.38, "cream")
    b.box(7.6, -2.2, 0.85, 8.4, -2.1, 1.05, "roof")
    # bench
    b.box(4.6, 1.6, 0.35, 5.9, 2.0, 0.42, "wood")
    b.box(4.6, 1.95, 0.42, 5.9, 2.05, 0.8, "wood")
    for x in (4.65, 5.75):
        b.box(x, 1.65, 0, x + 0.1, 1.95, 0.35, "dark")
    b.tree(8.2, 2.2)
    b.tree(3.8, -2.3, kind="pine")
    for (x, y) in ((6.2, 2.4), (7.2, 1.2), (5.2, -2.4), (8.5, -1.2)):
        b.flower(x, y)
    return M(door=(5, -0.8, 0), spot=(6.0, -0.9, 0), look=(6.0, -6, 0), action="wave",
             parent=0)


@region("Village", "Second Coffee Café", "Books, red string, a second coffee. Clawd's favourite table.")
def r02(b):
    b.plot(3, 3, 9, 9, depth=3.2)
    # café building
    x0, x1, y0, y1 = 4.2, 8.6, 5.8, 8.6
    b.box(x0, y0, 0, x1, y1, 2.3, "cream")
    b.box(x0 - 0.1, y0 - 0.1, 2.3, x1 + 0.1, y1 + 0.1, 2.55, "roof2")
    # striped awning
    for i in range(11):
        xa = x0 + i * (x1 - x0) / 11
        b.box(xa, y0 - 0.9, 1.7 - 0.0, xa + (x1 - x0) / 11, y0, 1.85,
              "roof" if i % 2 == 0 else "cream")
    b.box(x0, y0 - 0.95, 1.5, x1, y0 - 0.85, 1.7, "roof")
    # big windows + door
    b.box(4.6, y0 - 0.03, 0.4, 5.9, y0, 1.5, "glow", part="glow")
    b.box(7.0, y0 - 0.03, 0.4, 8.2, y0, 1.5, "glow", part="glow")
    b.box(6.15, y0 - 0.06, 0, 6.75, y0, 1.2, "wood2")
    # giant mug sign on the roof
    b.box(5.8, 6.8, 2.55, 7.0, 7.8, 3.7, "white")
    b.box(7.0, 7.1, 2.85, 7.35, 7.5, 3.4, "white")
    b.box(5.9, 6.9, 3.6, 6.9, 7.7, 3.72, "wood2")
    b.part("steam", pivot=(6.4, 7.3, 4.0), anim="bob", amp=0.15, speed=1.2)
    for k in range(3):
        b.box(6.1 + k * 0.25, 7.25, 3.85 + k * 0.3, 6.25 + k * 0.25, 7.35, 4.1 + k * 0.3,
              "white", part="steam")
    # outdoor tables with umbrellas
    for (tx, ty, uc) in ((4.4, 4.0, "yellow"), (6.4, 3.8, "roof"), (8.2, 4.2, "teal")):
        b.box(tx - 0.35, ty - 0.35, 0.55, tx + 0.35, ty + 0.35, 0.6, "white")
        b.box(tx - 0.05, ty - 0.05, 0, tx + 0.05, ty + 0.05, 1.7, "dark")
        b.box(tx - 0.8, ty - 0.8, 1.7, tx + 0.8, ty + 0.8, 1.8, uc)
        b.box(tx - 0.5, ty - 0.5, 1.8, tx + 0.5, ty + 0.5, 1.9, uc)
        b.box(tx - 0.08, ty - 0.08, 0.6, tx + 0.08, ty + 0.08, 0.72, "white")
    # chalkboard menu
    b.box(3.5, 5.2, 0, 4.1, 5.3, 1.0, "wood2")
    b.box(3.55, 5.17, 0.35, 4.05, 5.2, 0.95, "chalk")
    b.bush(8.7, 8.7, s=0.5)
    return M(door=(5, 2.6, 0), spot=(5.4, 4.2, 0), look=(5.4, -3, 0), action="sip", acc="mug",
             parent=1)


@region("Village", "The Library", "Stacks of books in every colour. Sketch the problem first.")
def r03(b):
    b.plot(-3, 3, 3, 9, depth=3.8)
    x0, x1, y0, y1 = -2.3, 2.3, 5.4, 8.5
    # steps
    for k in range(3):
        b.box(x0 + 0.6 + k * 0.1, y0 - 0.9 + k * 0.3, k * 0.15, x1 - 0.6 - k * 0.1, y0, (k + 1) * 0.15,
              "cream2")
    b.box(x0, y0, 0.45, x1, y1, 3.0, "cream")
    # columns
    for i in range(5):
        cx = x0 + 0.35 + i * (x1 - x0 - 0.7) / 4
        b.box(cx - 0.17, y0 - 0.5, 0.45, cx + 0.17, y0 - 0.16, 3.0, "white")
    # pediment
    b.box(x0 - 0.2, y0 - 0.65, 3.0, x1 + 0.2, y1 + 0.2, 3.3, "cream2")
    for k in range(4):
        w = (x1 - x0) / 2 + 0.2 - k * 0.55
        b.box(-w, y0 - 0.65, 3.3 + k * 0.25, w, y1 + 0.2 - k * 0.3, 3.55 + k * 0.25,
              "roof" if k % 2 == 0 else "roof2")
    b.box(-0.45, y0 - 0.04, 0.45, 0.45, y0, 1.9, "wood2")
    b.box(-1.9, y0 - 0.03, 1.2, -0.9, y0, 2.4, "glow", part="glow")
    b.box(0.9, y0 - 0.03, 1.2, 1.9, y0, 2.4, "glow", part="glow")
    # book stacks outside
    cols = ["roof", "blue", "yellow", "teal", "lilac", "red", "cream2", "leaf"]
    for (sx, sy, n) in ((-2.5, 3.6, 7), (-1.9, 3.5, 5), (2.3, 3.7, 6), (2.7, 4.6, 4)):
        z = 0
        for k in range(n):
            w = 0.5 + ((k * 37) % 5) * 0.04
            h = 0.12 + ((k * 13) % 3) * 0.03
            off = ((k * 7) % 3 - 1) * 0.04
            b.box(sx - w / 2 + off, sy - 0.2, z, sx + w / 2 + off, sy + 0.2, z + h, cols[(k + n) % len(cols)])
            z += h
    # reading lamp + pile of open books
    b.lamp(-2.6, 4.9)
    return M(door=(0, 3.9, 0), spot=(0.7, 4.1, 0), look=(0.7, -3, 0), action="read",
             acc="book", parent=0, via=[(2.6, -2.2, 0), (2.6, 3.9, 0)])


@region("Village", "Lily Pond", "A little arched bridge over a quiet pond. Good for thinking.")
def r04(b):
    b.plot(-9, -3, -3, 3, depth=3.6)
    # pond (water slightly below grass)
    b.box(-8.3, -2.2, -0.25, -4.3, 1.8, 0.03, "water", jitter=0.0, top="water2")
    b.box(-8.4, -2.3, -0.02, -4.2, -2.2, 0.06, "rock")
    b.box(-8.4, 1.8, -0.02, -4.2, 1.9, 0.06, "rock")
    b.box(-8.4, -2.2, -0.02, -8.3, 1.8, 0.06, "rock")
    b.box(-4.3, -2.2, -0.02, -4.2, 1.8, 0.06, "rock")
    # arched bridge along x at y=-0.2
    for i in range(9):
        x = -8.6 + i * 0.6
        h = 0.08 + 0.35 * math.sin(math.pi * i / 8)
        b.box(x, -0.75, h - 0.08, x + 0.6, 0.35, h, "wood")
        b.box(x, -0.8, h, x + 0.6, -0.7, h + 0.45, "roof2")
        b.box(x, 0.3, h, x + 0.6, 0.4, h + 0.45, "roof2")
    # lily pads + reeds
    for (x, y) in ((-7.6, 1.1), (-5.0, -1.6), (-5.6, 1.2), (-7.3, -1.5)):
        b.box(x - 0.2, y - 0.2, 0.03, x + 0.2, y + 0.2, 0.06, "leaf3")
    b.flower(-5.6, 1.2, z=0.0)
    for (x, y) in ((-8.6, -2.6), (-8.7, 2.3), (-3.6, 2.4), (-3.5, -2.5)):
        for k in range(3):
            b.box(x + k * 0.12, y, 0, x + k * 0.12 + 0.05, y + 0.05, 0.6 + k * 0.15, "leaf")
    # duck
    b.part("duck", pivot=(-6.6, 1.0, 0), anim="bob", amp=0.05, speed=2.0)
    b.box(-6.85, 0.85, 0.03, -6.35, 1.15, 0.25, "white", part="duck")
    b.box(-6.45, 0.9, 0.2, -6.25, 1.1, 0.4, "white", part="duck")
    b.box(-6.27, 0.95, 0.27, -6.15, 1.05, 0.33, "yellow", part="duck")
    b.tree(-8.5, 2.6, kind="round")
    return M(door=(-3.6, -0.5, 0), spot=(-6.2, -0.2, 0.45), look=(-6.2, -6, 0), action="look",
             parent=0)


@region("Village", "Flower Garden", "Rows of flowers and a little fountain. Take a breath.")
def r05(b):
    b.plot(-9, 3, -3, 9, depth=3.2)
    # fountain
    b.disc(-6, 6.4, 0, 0.35, 1.3, "cream2")
    b.disc(-6, 6.4, 0.3, 0.36, 1.05, "water", jitter=0.0)
    b.box(-6.15, 6.25, 0.3, -5.85, 6.55, 1.2, "cream2")
    b.disc(-6, 6.4, 1.2, 1.3, 0.5, "cream2")
    b.part("spray", pivot=(-6, 6.4, 1.3), anim="bob", amp=0.06, speed=3.0)
    b.box(-6.08, 6.32, 1.3, -5.92, 6.48, 1.75, "water2", part="spray")
    # flowerbeds
    for row in range(3):
        y = 4.0 + row * 0.55
        for i in range(9):
            b.flower(-8.6 + i * 0.3 + (row % 2) * 0.15, y if i % 2 else y + 0.1)
    for row in range(2):
        y = 8.0 + row * 0.5
        b.box(-8.7, y - 0.15, 0, -3.3, y + 0.15, 0.4, "leaf2")
    b.tree(-3.6, 8.6)
    b.tree(-8.6, 6.3, kind="pine")
    # arch trellis
    b.box(-4.2, 4.3, 0, -4.05, 4.45, 1.9, "white")
    b.box(-4.2, 5.55, 0, -4.05, 5.7, 1.9, "white")
    b.box(-4.25, 4.25, 1.9, -4.0, 5.75, 2.05, "white")
    for k in range(6):
        b.flower(-4.12, 4.4 + k * 0.2, z=1.95)
    return M(door=(-3.6, 4.4, 0), spot=(-5.2, 4.6, 0), look=(-5.2, -3, 0), action="wave",
             parent=3)


@region("Village", "Claude FM Tower", "The radio tower that broadcasts Claude FM to every island.")
def r06(b):
    b.plot(-3, -9, 3, -3, depth=4.2)
    cx, cy = 0.8, -6.6
    # lattice tower: 4 legs tapering, stripes
    H = 11.0
    for k in range(22):
        z0, z1 = k * H / 22, (k + 1) * H / 22
        w = 1.2 * (1 - k / 26)
        c = "clay" if (k // 2) % 2 == 0 else "white"
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.box(cx + sx * w - 0.1, cy + sy * w - 0.1, z0, cx + sx * w + 0.1, cy + sy * w + 0.1, z1, c)
        if k % 3 == 0:
            b.box(cx - w, cy - w - 0.05, z1 - 0.08, cx + w, cy - w + 0.05, z1, "steel")
            b.box(cx - w, cy + w - 0.05, z1 - 0.08, cx + w, cy + w + 0.05, z1, "steel")
            b.box(cx - w - 0.05, cy - w, z1 - 0.08, cx - w + 0.05, cy + w, z1, "steel")
            b.box(cx + w - 0.05, cy - w, z1 - 0.08, cx + w + 0.05, cy + w, z1, "steel")
    # dish
    b.box(cx - 0.8, cy - 1.0, 7.2, cx + 0.8, cy - 0.85, 8.4, "white")
    b.box(cx - 0.1, cy - 0.85, 7.7, cx + 0.1, cy - 0.5, 7.9, "steel")
    # beacon
    b.box(cx - 0.05, cy - 0.05, H, cx + 0.05, cy + 0.05, H + 1.2, "dark")
    b.part("beacon", glow=1, pivot=(cx, cy, H + 1.3), anim="pulse", speed=2.5)
    b.box(cx - 0.22, cy - 0.22, H + 1.15, cx + 0.22, cy + 0.22, H + 1.55, "red", part="beacon")
    # broadcast rings
    b.part("rings", glow=1, pivot=(cx, cy, H + 1.3), anim="spin", axis="y", speed=0.6)
    for k in range(8):
        a = k / 8 * math.tau
        r = 1.4
        b.box(cx + r * math.cos(a) - 0.1, cy + r * math.sin(a) - 0.1, H + 1.25,
              cx + r * math.cos(a) + 0.1, cy + r * math.sin(a) + 0.1, H + 1.35, "glowblue",
              part="rings")
    # studio shack with ON AIR sign
    b.box(-2.6, -8.6, 0, -0.6, -6.9, 1.6, "cream")
    b.box(-2.7, -8.7, 1.6, -0.5, -6.8, 1.8, "charcoal")
    b.box(-2.2, -8.63, 1.0, -1.0, -8.6, 1.4, "red", part="glow")
    b.box(-2.3, -8.63, 0.2, -1.9, -8.6, 0.9, "wood2")
    # big speakers
    for x in (-2.5, 2.4):
        b.box(x - 0.35, -4.0, 0, x + 0.35, -3.5, 1.1, "charcoal")
        b.box(x - 0.22, -4.03, 0.55, x + 0.22, -4.0, 0.95, "dark")
        b.box(x - 0.12, -4.03, 0.15, x + 0.12, -4.0, 0.39, "dark")
    b.part("notes", pivot=(0, -4.5, 2.0), anim="bob", amp=0.18, speed=1.3)
    note(b, "notes", -2.5, -3.8, 1.6)
    note(b, "notes", 2.2, -3.7, 1.9)
    note(b, "notes", -0.4, -4.0, 2.4)
    return M(door=(0, -3.6, 0), spot=(-0.4, -4.4, 0), look=(-0.4, -10, 0), action="dance",
             acc="headphones", parent=0)


# =============================================================== 2. HARBOUR
@region("Harbour", "Waterfall Cliffs", "A stream that tumbles off the island's edge.")
def r07(b):
    b.plot(9, -3, 13, 9, depth=5.0)
    # boulders / cliff mound
    b.box(11.4, 4.6, 0, 13.0, 9.0, 1.4, "rock")
    b.box(11.8, 5.2, 1.4, 13.0, 8.6, 2.2, "rock2")
    b.box(9.2, 7.0, 0, 11.4, 9.0, 0.9, "rock")
    # stream through the grass to the east edge
    b.box(9.0, 2.6, -0.2, 13.0, 3.6, 0.03, "water", jitter=0.0, top="water2")
    # the fall (stepped columns to the harbour)
    for k in range(6):
        b.box(13.0, 2.6 - k * 0.05, -0.6 - k * 0.5, 13.35 + k * 0.08, 3.6 + k * 0.05, -0.1 - k * 0.5,
              "water2" if k % 2 else "water", jitter=0.0)
    b.part("foam", pivot=(13.6, 3.1, -3.0), anim="bob", amp=0.06, speed=4.0)
    for (dx, dy) in ((0, 0), (0.4, 0.3), (0.2, -0.4)):
        b.box(13.4 + dx, 2.8 + dy, -3.05, 13.7 + dx, 3.1 + dy, -2.85, "white", part="foam")
    # stepping stones over the stream
    for x in (9.6, 10.3, 11.0):
        b.box(x, 2.9, -0.05, x + 0.4, 3.3, 0.08, "rock")
    b.tree(9.7, 8.4, kind="pine")
    b.tree(10.4, 6.4, kind="pine")
    b.tree(9.6, -2.3)
    b.bush(12.5, -2.3)
    return M(door=(9.6, -0.8, 0), spot=(11.4, 1.8, 0), look=(14, 4, 0), action="look",
             parent=1)


@region("Harbour", "The Harbour", "A sandy lagoon, a wooden pier and two little sailboats.")
def r08(b):
    b.plot(13, -6, 25, 10, z=-3.0, c="sand", edge="sand", depth=3.5)
    # lagoon
    b.box(14.5, -1.0, -3.3, 23.5, 8.5, -2.97, "water", jitter=0.0, top="water2")
    # stairs down from the cliff path
    for k in range(10):
        x = 12.2 + k * 0.26
        z = -0.3 * k
        b.box(x, -2.9, z - 0.3, x + 0.3, -1.9, z, "cream2")
    b.box(12.2, -2.95, -3.0, 15.0, -2.9, 0.0, "rock2")
    # pier
    b.box(17.4, -1.4, -3.05, 18.6, 3.4, -2.85, "wood")
    for (px, py) in ((17.4, 0), (18.5, 0), (17.4, 2), (18.5, 2), (17.4, 3.3), (18.5, 3.3)):
        b.box(px, py, -3.4, px + 0.1, py + 0.1, -2.5, "wood2")
    # boats
    for (bx, by, sail, key) in ((15.8, 5.2, "white", "boatA"), (21.2, 6.2, "roof", "boatB")):
        b.part(key, pivot=(bx, by, -3.1), anim="bob", amp=0.07, speed=1.4 if key == "boatA" else 1.1)
        b.box(bx - 0.8, by - 0.35, -3.2, bx + 0.8, by + 0.35, -2.9, "wood", part=key)
        b.box(bx - 0.6, by - 0.3, -2.9, bx + 0.6, by + 0.3, -2.85, "cream2", part=key)
        b.box(bx - 0.04, by - 0.04, -2.85, bx + 0.04, by + 0.04, -1.2, "wood2", part=key)
        b.box(bx + 0.04, by - 0.02, -2.6, bx + 0.7, by + 0.02, -1.4, sail, part=key)
    # beach umbrella + crates
    b.box(20.4, -4.2, -3, 20.48, -4.12, -1.6, "dark")
    b.box(19.6, -4.95, -1.6, 21.3, -3.35, -1.5, "teal")
    b.box(14.0, -5.6, -3, 14.6, -5.0, -2.4, "wood")
    b.box(14.1, -5.0, -3, 14.6, -4.5, -2.6, "wood2")
    b.tree(24.4, -5.4)
    b.tree(13.6, 9.4, kind="pine")
    return M(door=(15.2, -2.4, -3), spot=(18.0, 2.6, -2.85), look=(18.0, 9, -3), action="look",
             parent=7, via=[(12.2, -2.4, 0), (14.8, -2.4, -3)])


@region("Harbour", "Lighthouse Point", "A striped lighthouse sweeping its beam across the sky.")
def r09(b):
    b.plot(25, 5, 30, 11, z=-3.0, c="rock", edge="rock2", depth=3.0)
    cx, cy = 28.0, 8.8
    for k in range(12):
        r = 1.2 - k * 0.05
        b.disc(cx, cy, -3 + k * 0.7, -3 + (k + 1) * 0.7, r, "white" if k % 2 == 0 else "red", step=0.4)
    top = -3 + 12 * 0.7
    b.disc(cx, cy, top, top + 0.2, 1.1, "charcoal", step=0.4)
    b.disc(cx, cy, top + 0.2, top + 1.0, 0.7, "glow", step=0.35, part="glow")
    b.cone(cx, cy, top + 1.0, 0.9, 0.8, "roof", layers=3, step=0.3)
    b.part("beam", glow=1, pivot=(cx, cy, top + 0.6), anim="spin", axis="y", speed=0.9)
    b.box(cx + 0.6, cy - 0.15, top + 0.45, cx + 5.5, cy + 0.15, top + 0.75, "glow", part="beam")
    b.box(cx - 5.5, cy - 0.15, top + 0.45, cx - 0.6, cy + 0.15, top + 0.75, "glow", part="beam")
    b.box(27.7, cy - 1.25, -3, 28.3, cy - 1.15, -2.0, "wood2")
    # rocks and gulls
    for (x, y, s) in ((25.6, 10.3, 0.7), (29.4, 5.6, 0.6), (26.2, 5.6, 0.5)):
        b.box(x - s / 2, y - s / 2, -3, x + s / 2, y + s / 2, -3 + s * 0.8, "rock2")
    b.part("gulls", pivot=(cx, cy, top + 2.5), anim="spin", axis="y", speed=0.4)
    for a in (0.3, 2.4, 4.4):
        gx, gy = cx + 2.6 * math.cos(a), cy + 2.6 * math.sin(a)
        b.box(gx - 0.25, gy - 0.05, top + 2.5, gx + 0.25, gy + 0.05, top + 2.58, "white", part="gulls")
    return M(door=(25.6, 6.5, -3), spot=(26.6, 6.6, -3), look=(26.6, 0, -3), action="wave",
             parent=8, via=[(24.3, -2.4, -3), (24.3, 6.5, -3)])


@region("Harbour", "Market Street", "Colourful stalls selling fruit, flowers and fresh ideas.")
def r10(b):
    b.plot(13, 10, 21, 16, z=-3.0, c="path", edge="sand", depth=3.2)
    awn = [("roof", "cream"), ("teal", "cream"), ("yellow", "white"), ("blue", "white")]
    for i, (c1, c2) in enumerate(awn):
        x = 13.6 + i * 1.8
        b.box(x, 13.6, -3, x + 1.5, 14.6, -2.2, "wood")
        b.box(x + 0.05, 13.55, -2.2, x + 0.15, 13.65, -1.2, "wood2")
        b.box(x + 1.35, 13.55, -2.2, x + 1.45, 13.65, -1.2, "wood2")
        for k in range(5):
            b.box(x - 0.1 + k * 0.34, 13.3, -1.2, x + 0.24 + k * 0.34, 14.8, -1.05, c1 if k % 2 == 0 else c2)
        # produce
        for k in range(4):
            fc = ["red", "yellow", "leaf3", "lilac", "roof"][(i + k) % 5]
            b.box(x + 0.15 + k * 0.32, 13.65, -2.2, x + 0.4 + k * 0.32, 13.95, -2.0, fc)
    # bunting
    for k in range(14):
        x = 13.4 + k * 0.52
        z = -0.4 - 0.25 * math.sin(math.pi * k / 13)
        b.box(x, 15.4, z - 0.25, x + 0.22, 15.45, z, ["roof", "yellow", "teal", "white"][k % 4])
    b.box(13.2, 15.35, -3, 13.32, 15.47, -0.2, "wood2")
    b.box(20.6, 15.35, -3, 20.72, 15.47, -0.2, "wood2")
    b.lamp(20.4, 11.0, z=-3)
    b.box(18.0, 10.6, -3, 18.6, 11.2, -2.4, "wood")
    b.box(18.7, 10.6, -3, 19.2, 11.1, -2.55, "wood2")
    return M(door=(14.0, 10.6, -3), spot=(16.4, 12.0, -3), look=(16.4, 5, -3), action="wave",
             parent=8, via=[(13.8, -2.4, -3), (13.8, 10.6, -3)])


@region("Harbour", "Seaside Station", "A tiny train loops the station. All aboard the study express.")
def r11(b):
    b.plot(13, -12, 25, -6, z=-3.0, c="grass", depth=3.4)
    # platform + station
    b.box(13.3, -10.8, -3, 16.0, -6.6, -2.75, "cream2")
    b.box(13.5, -10.6, -2.75, 15.2, -9.0, -1.2, "cream")
    b.box(13.4, -10.7, -1.2, 15.3, -8.9, -1.0, "roof")
    b.box(14.0, -9.0, -2.0, 14.8, -8.97, -1.5, "glow", part="glow")
    b.box(13.5, -8.4, -2.75, 13.6, -8.3, -1.3, "dark")
    b.box(13.3, -8.45, -1.4, 15.9, -6.7, -1.3, "roof2")
    # clock
    b.box(15.0, -8.0, -1.3, 15.5, -7.6, -0.8, "white")
    # circular track
    cx, cy, R = 20.4, -9.2, 2.5
    for k in range(32):
        a = k / 32 * math.tau
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        b.box(x - 0.18, y - 0.18, -3.0, x + 0.18, y + 0.18, -2.9, "wood2")
        b.box(x - 0.1, y - 0.1, -2.9, x + 0.1, y + 0.1, -2.86, "steel")
    b.tree(20.4, -9.2)
    # the train (orbits the loop centre)
    b.part("train", pivot=(cx, cy, -2.86), anim="spin", axis="y", speed=0.5)
    for i, c in enumerate(["clay", "cream", "teal"]):
        a = -i * 0.42
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        b.box(x - 0.25, y - 0.35, -2.86, x + 0.25, y + 0.35, -2.36, c, part="train")
        b.box(x - 0.27, y - 0.37, -2.36, x + 0.27, y + 0.37, -2.28, "charcoal", part="train")
    x, y = cx + R, cy
    b.box(x - 0.08, y + 0.15, -2.28, x + 0.08, y + 0.3, -1.95, "dark", part="train")
    b.lamp(16.6, -6.6, z=-3)
    return M(door=(15.2, -6.6, -3), spot=(14.8, -7.4, -2.75), look=(14.8, -14, -3), action="wave",
             parent=8, via=[(15.2, -5.6, -3)])


@region("Harbour", "Windmill Fields", "Golden fields and a windmill turning in the sea breeze.")
def r12(b):
    b.plot(25, -6, 30, 0, z=-3.0, c="grass3", depth=3.0)
    for row in range(5):
        b.box(25.4, -5.6 + row * 0.55, -3, 26.8, -5.3 + row * 0.55, -2.6, "mustard")
    cx, cy = 28.4, -2.8
    for k in range(8):
        r = 1.0 - k * 0.07
        b.disc(cx, cy, -3 + k * 0.55, -3 + (k + 1) * 0.55, r, "cream", step=0.4)
    top = -3 + 8 * 0.55
    b.cone(cx, cy, top, 0.75, 1.0, "roof", layers=4, step=0.3)
    b.box(cx - 0.2, cy - 1.0, -3, cx + 0.2, cy - 0.9, -2.2, "wood2")
    b.box(cx - 0.2, cy - 0.9, top - 0.9, cx + 0.2, cy - 0.85, top - 0.5, "glow", part="glow")
    b.part("blades", pivot=(cx, cy - 1.0, top - 0.2), anim="spin", axis="z", speed=1.1)
    hub = (cx, cy - 1.05, top - 0.2)
    b.box(hub[0] - 0.12, hub[1] - 0.1, hub[2] - 0.12, hub[0] + 0.12, hub[1] + 0.05, hub[2] + 0.12, "dark",
          part="blades")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x0 = hub[0] + (0.12 if dx > 0 else -2.0 if dx < 0 else -0.25)
        x1 = hub[0] + (2.0 if dx > 0 else -0.12 if dx < 0 else 0.25)
        z0 = hub[2] + (0.12 if dz > 0 else -2.0 if dz < 0 else -0.25)
        z1 = hub[2] + (2.0 if dz > 0 else -0.12 if dz < 0 else 0.25)
        b.box(x0, hub[1] - 0.06, z0, x1, hub[1] - 0.02, z1, "white" if dx == 0 else "cream2",
              part="blades")
    b.bush(29.5, -0.5)
    return M(door=(25.6, -3.0, -3), spot=(26.4, -2.0, -3), look=(26.4, -8, -3), action="look",
             parent=8, via=[(24.3, -2.4, -3)])


# =============================================================== 3. SKYLINE
@region("Skyline", "Construction Site", "Clawd's hard hat goes on. Time to build something bigger.")
def r13(b):
    b.plot(-3, 13, 7, 19, depth=4.0)
    # bridge from the library island
    for k in range(7):
        y = 9.0 + k * 0.58
        b.box(1.8, y, -0.12, 3.4, y + 0.5, 0.0, "wood")
    b.box(1.75, 9.0, 0.0, 1.85, 13.0, 0.6, "wood2")
    b.box(3.35, 9.0, 0.0, 3.45, 13.0, 0.6, "wood2")
    # half-built building with scaffolding
    x0, x1, y0, y1 = 3.4, 6.4, 15.0, 18.4
    b.box(x0, y0, 0, x1, y1, 3.2, "cream2")
    b.box(x0, y0, 3.2, x1, y0 + 0.3, 4.4, "cream2")
    b.box(x0, y0, 3.2, x0 + 0.3, y1, 5.6, "cream2")
    for zz in (1.4, 2.8, 4.2):
        b.box(x0 - 0.5, y0 - 0.5, zz - 0.06, x1 + 0.5, y0 - 0.3, zz, "wood")
    for xx in (x0 - 0.45, (x0 + x1) / 2, x1 + 0.35):
        b.box(xx, y0 - 0.5, 0, xx + 0.1, y0 - 0.4, 5.0, "steel")
    b.windows(x0 + 0.2, x1 - 0.2, y0, 0.4, 3.0, 3, rows=2)
    # cones + bricks
    for (x, y) in ((1.0, 13.6), (2.4, 13.8), (6.6, 13.6)):
        b.box(x - 0.15, y - 0.15, 0, x + 0.15, y + 0.15, 0.08, "roof")
        b.box(x - 0.1, y - 0.1, 0.08, x + 0.1, y + 0.1, 0.4, "roof")
        b.box(x - 0.05, y - 0.05, 0.4, x + 0.05, y + 0.05, 0.5, "white")
    for k in range(3):
        b.box(0.4, 17.0 + k * 0.3, 0, 1.4, 17.25 + k * 0.3, 0.25 * (3 - k), "roof2")
    # tower crane
    cx, cy = -1.5, 16.8
    for k in range(14):
        z0 = k * 0.7
        c = "yellow" if k % 2 == 0 else "mustard"
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.box(cx + sx * 0.3 - 0.06, cy + sy * 0.3 - 0.06, z0, cx + sx * 0.3 + 0.06,
                      cy + sy * 0.3 + 0.06, z0 + 0.7, c)
        b.box(cx - 0.36, cy - 0.36, z0 + 0.62, cx + 0.36, cy + 0.36, z0 + 0.7, c)
    top = 14 * 0.7
    b.part("jib", pivot=(cx, cy, top), anim="spin", axis="y", speed=0.15)
    b.box(cx - 0.4, cy - 0.4, top, cx + 0.4, cy + 0.4, top + 0.6, "charcoal", part="jib")
    b.box(cx - 2.5, cy - 0.15, top + 0.6, cx + 6.0, cy + 0.15, top + 0.9, "yellow", part="jib")
    b.box(cx - 2.8, cy - 0.35, top + 0.1, cx - 1.6, cy + 0.35, top + 0.6, "charcoal", part="jib")
    b.box(cx + 4.8, cy - 0.02, top - 2.5, cx + 4.84, cy + 0.02, top + 0.6, "dark", part="jib")
    b.box(cx + 4.4, cy - 0.3, top - 3.1, cx + 5.2, cy + 0.3, top - 2.5, "roof", part="jib")
    return M(door=(2.6, 13.6, 0), spot=(1.6, 14.6, 0), look=(1.6, 8, 0), action="hammer",
             acc="hardhat", parent=3, via=[(2.6, 3.9, 0), (2.6, 9.0, 0)])


@region("Skyline", "Glass Tower", "Fourteen floors of focus. Windows light up as night falls.")
def r14(b):
    b.plot(7, 13, 12, 19, depth=3.6)
    x0, x1, y0, y1 = 8.2, 11.2, 15.2, 18.2
    b.box(x0, y0, 0, x1, y1, 0.8, "charcoal")
    floors = 14
    for k in range(floors):
        z = 0.8 + k * 0.85
        b.box(x0 + 0.1, y0 + 0.1, z, x1 - 0.1, y1 - 0.1, z + 0.85, "cream" if k % 2 == 0 else "cream2")
        b.windows(x0 + 0.2, x1 - 0.2, y0 + 0.1, z + 0.12, z + 0.75, 4, w=0.45, h=0.5)
    top = 0.8 + floors * 0.85
    b.box(x0, y0, top, x1, y1, top + 0.3, "blue")
    b.box(x0 + 1.0, y0 + 1.0, top + 0.3, x1 - 1.0, y1 - 1.0, top + 1.2, "steel")
    b.part("heli", glow=1, pivot=(9.7, 16.7, top + 1.3), anim="pulse", speed=1.5)
    b.box(9.55, 16.55, top + 1.2, 9.85, 16.85, top + 1.45, "red", part="heli")
    b.box(8.4, y0 - 0.06, 0, 9.0, y0, 0.75, "glow", part="glow")
    b.tree(7.6, 18.4)
    b.lamp(11.6, 13.6)
    return M(door=(7.6, 14.0, 0), spot=(8.8, 14.2, 0), look=(8.8, 8, 0), action="look",
             parent=13)


@region("Skyline", "Brick Tower", "A sturdy terracotta tower with a lot of lit windows.")
def r15(b):
    b.plot(-8, 13, -3, 19, depth=3.6)
    x0, x1, y0, y1 = -7.4, -4.0, 14.8, 18.4
    floors = 10
    for k in range(floors):
        z = k * 0.95
        b.box(x0, y0, z, x1, y1, z + 0.95, "roof" if k % 3 else "roof2")
        b.windows(x0 + 0.2, x1 - 0.2, y0, z + 0.15, z + 0.8, 4, w=0.4, h=0.45)
    top = floors * 0.95
    b.box(x0 - 0.1, y0 - 0.1, top, x1 + 0.1, y1 + 0.1, top + 0.2, "cream2")
    # water tank
    b.disc(-6.6, 17.4, top + 0.2, top + 0.9, 0.5, "wood", step=0.3)
    b.cone(-6.6, 17.4, top + 0.9, 0.55, 0.4, "wood2", layers=2, step=0.3)
    b.box(-5.9, y0 - 0.06, 0, -5.3, y0, 0.85, "wood2")
    b.lamp(-3.5, 18.5)
    return M(door=(-3.4, 14.0, 0), spot=(-4.6, 13.9, 0), look=(-4.6, 8, 0), action="look",
             parent=13)


@region("Skyline", "Clawd Spire", "The tallest building in the archipelago. Clawd's own landmark.")
def r16(b):
    b.plot(-3, 19, 7, 26, depth=4.6)
    # plaza
    b.box(-1.0, 19.3, 0, 5.0, 21.4, 0.06, "path")
    b.disc(2.0, 20.4, 0.06, 0.3, 0.7, "cream2", step=0.35)
    b.disc(2.0, 20.4, 0.3, 0.32, 0.55, "water2", step=0.35)
    # stepped art-deco spire
    cx, cy = 2.0, 23.6
    tiers = [(2.0, 6.0), (1.6, 4.0), (1.2, 3.5), (0.8, 3.0), (0.45, 2.5)]
    z = 0
    for i, (w, h) in enumerate(tiers):
        b.box(cx - w, cy - w, z, cx + w, cy + w, z + h, "cream" if i % 2 == 0 else "white")
        b.box(cx - w - 0.06, cy - w - 0.06, z + h - 0.15, cx + w + 0.06, cy + w + 0.06, z + h, "clay")
        n = max(1, int(w * 2))
        b.windows(cx - w + 0.2, cx + w - 0.2, cy - w, z + 0.3, z + h - 0.4, n, rows=max(1, int(h / 1.2)),
                  w=0.22, h=0.6)
        z += h
    # Clawd-shaped crown on top (body + nubs + eye slots)
    b.box(cx - 0.6, cy - 0.3, z, cx + 0.6, cy + 0.3, z + 0.8, "clay")
    b.box(cx - 0.8, cy - 0.2, z + 0.2, cx + 0.8, cy + 0.2, z + 0.4, "clay")
    b.box(cx - 0.4, cy - 0.32, z + 0.4, cx - 0.3, cy - 0.29, z + 0.6, "dark")
    b.box(cx + 0.3, cy - 0.32, z + 0.4, cx + 0.4, cy - 0.29, z + 0.6, "dark")
    for lx in (-0.5, -0.3, 0.2, 0.4):
        b.box(cx + lx, cy - 0.1, z - 0.2, cx + lx + 0.1, cy + 0.1, z, "clay")
    b.box(cx - 0.03, cy - 0.03, z + 0.8, cx + 0.03, cy + 0.03, z + 2.2, "steel")
    b.part("tip", glow=1, pivot=(cx, cy, z + 2.3), anim="pulse", speed=1.2)
    b.box(cx - 0.15, cy - 0.15, z + 2.2, cx + 0.15, cy + 0.15, z + 2.5, "glow", part="tip")
    for x in (-0.6, 4.6):
        b.lamp(x, 21.0)
    b.tree(-2.3, 25.2, kind="pine")
    b.tree(6.3, 25.0, kind="pine")
    return M(door=(2.0, 19.6, 0), spot=(2.0, 19.9, 0.06), look=(2.0, 14, 0), action="celebrate",
             acc="partyhat", parent=13)


@region("Skyline", "Rooftop Park", "A park in the clouds, and a garden on the Brick Tower roof.")
def r17(b):
    b.plot(-8, 19, -3, 26, depth=3.4)
    for (x, y) in ((-7.2, 25.2), (-4.2, 25.4), (-7.4, 21.8), (-3.6, 22.8)):
        b.tree(x, y, kind="round")
    b.box(-6.6, 23.0, 0, -5.0, 23.5, 0.42, "wood")
    b.box(-6.6, 23.45, 0.42, -5.0, 23.55, 0.85, "wood")
    for k in range(10):
        b.flower(-7.6 + k * 0.45, 19.6 + (k % 2) * 0.3)
    # kite (bob)
    b.part("kite", pivot=(-5.6, 22.0, 5.0), anim="bob", amp=0.4, speed=0.7)
    b.box(-5.9, 21.98, 4.7, -5.3, 22.02, 5.4, "roof", part="kite")
    b.box(-5.65, 21.98, 4.4, -5.55, 22.02, 4.7, "yellow", part="kite")
    # rooftop garden on the Brick Tower (r15 top is z=9.5)
    top = 9.7
    b.box(-7.2, 15.0, top, -4.2, 18.2, top + 0.15, "grass")
    b.tree(-6.6, 15.6, z=top + 0.15, h=1.3)
    b.tree(-4.8, 15.6, z=top + 0.15, h=1.1)
    for k in range(5):
        b.flower(-6.8 + k * 0.5, 15.2, z=top + 0.15)
    return M(door=(-3.5, 20.5, 0), spot=(-5.6, 20.8, 0), look=(-5.6, 14, 0), action="wave",
             parent=16)


@region("Skyline", "Rope Bridge", "A swaying rope bridge to the mysterious islands to the west.")
def r18(b):
    x0, x1, y = -8.0, -14.0, 23.0
    n = 16
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * t
        z = 0 + 2 * t - 0.6 * math.sin(math.pi * t)
        b.box(x - 0.18, y - 0.6, z - 0.08, x + 0.18, y + 0.6, z, "wood" if i % 2 else "wood2")
        b.box(x - 0.03, y - 0.66, z, x + 0.03, y - 0.6, z + 0.6, "wood2")
        b.box(x - 0.03, y + 0.6, z, x + 0.03, y + 0.66, z + 0.6, "wood2")
    for (x, zb) in ((x0 + 0.1, 0.0), (x1 - 0.1, 2.0)):
        for s in (-1, 1):
            b.box(x - 0.1, y + s * 0.75 - 0.1, zb - 0.6, x + 0.1, y + s * 0.75 + 0.1, zb + 1.2, "wood2")
        b.box(x - 0.1, y - 0.4, zb + 1.2, x + 0.1, y + 0.4, zb + 1.4, "dark")
        b.box(x - 0.12, y - 0.12, zb + 0.9, x + 0.12, y + 0.12, zb + 1.15, "glow", part="glow")
    # tiny floating rocks under the bridge
    b.part("rocks", pivot=(-11, 23, -2.0), anim="bob", amp=0.25, speed=0.5)
    for (dx, dy, s) in ((0, 0, 0.8), (-1.6, 0.8, 0.5), (1.5, -0.6, 0.6)):
        b.box(-11 + dx - s / 2, 23 + dy - s / 2, -2.4, -11 + dx + s / 2, 23 + dy + s / 2, -2.4 + s, "rock",
              part="rocks")
        b.box(-11 + dx - s / 2, 23 + dy - s / 2, -2.4 + s, -11 + dx + s / 2, 23 + dy + s / 2, -2.3 + s,
              "grass", part="rocks")
    return M(door=(-11.0, 23.0, 0.45), spot=(-11.0, 23.0, 0.45), look=(-11.0, 16, 0.4),
             action="look", parent=17, via=[(-7.6, 23.0, 0)])


# =============================================================== 4. SCIENCE ISLE
@region("Science Isle", "The Lab", "Full lab coat. Chalkboards, a Tesla coil, and a humming atom.")
def r19(b):
    b.plot(-22, 18, -14, 26, z=2.0, c="grass2", depth=5.0)
    Z = 2.0
    x0, x1, y0, y1 = -21.4, -16.6, 21.2, 25.4
    b.box(x0, y0, Z, x1, y1, Z + 3.2, "white")
    b.box(x0 - 0.1, y0 - 0.1, Z + 3.2, x1 + 0.1, y1 + 0.1, Z + 3.45, "charcoal")
    b.box(x0 + 0.4, y0 - 0.03, Z + 0.8, x1 - 1.8, y0, Z + 2.6, "glowblue", part="glow")
    b.box(x1 - 1.4, y0 - 0.06, Z, x1 - 0.6, y0, Z + 2.0, "steel")
    # chalkboard: bug = f(x)
    b.box(-15.9, 19.0, Z, -15.8, 19.1, Z + 1.0, "wood2")
    b.box(-14.4, 19.0, Z, -14.3, 19.1, Z + 1.0, "wood2")
    b.box(-16.0, 19.02, Z + 0.9, -14.2, 19.1, Z + 2.1, "chalk")
    for (x, z, w) in ((-15.8, 1.85, 0.6), (-15.8, 1.6, 0.9), (-15.8, 1.35, 0.5), (-15.0, 1.1, 0.6)):
        b.box(x, 19.0, Z + z, x + w, 19.02, Z + z + 0.06, "white")
    # tesla coil
    tx, ty = -15.0, 24.4
    b.box(tx - 0.4, ty - 0.4, Z, tx + 0.4, ty + 0.4, Z + 0.4, "charcoal")
    for k in range(8):
        b.disc(tx, ty, Z + 0.4 + k * 0.28, Z + 0.4 + k * 0.28 + 0.16, 0.3, "roof" if k % 2 else "mustard",
               step=0.2)
    b.disc(tx, ty, Z + 2.6, Z + 2.8, 0.5, "steel", step=0.25)
    b.part("orb", glow=1, pivot=(tx, ty, Z + 3.1), anim="pulse", speed=6.0)
    b.dome(tx, ty, Z + 2.8, 0.45, "glowblue", layers=3, step=0.2, part="orb")
    # atom
    b.part("atom", pivot=(-18.2, 20.0, Z + 1.8), anim="spin", axis="y", speed=1.4)
    b.cube(-18.2, 20.0, Z + 1.65, 0.3, "red", part="atom")
    for a in (0, 2.1, 4.2):
        b.cube(-18.2 + 0.8 * math.cos(a), 20.0 + 0.8 * math.sin(a), Z + 1.7 + 0.3 * math.sin(a * 2), 0.14,
               "glowblue", part="atom")
    b.box(-18.3, 19.9, Z, -18.1, 20.1, Z + 1.2, "steel")
    b.box(-18.6, 19.6, Z, -17.8, 20.4, Z + 0.15, "charcoal")
    # flasks on a bench
    b.box(-21.2, 19.2, Z + 0.7, -19.4, 19.9, Z + 0.8, "wood")
    for (x, c) in ((-21.0, "glowgreen"), (-20.5, "glowblue"), (-20.0, "glowpink"), (-19.6, "glowgreen")):
        b.box(x, 19.4, Z + 0.8, x + 0.2, 19.6, Z + 1.05, c, part="glow")
        b.box(x + 0.06, 19.46, Z + 1.05, x + 0.14, 19.54, Z + 1.25, "white")
    for x in (-21.1, -19.6):
        b.box(x, 19.3, Z, x + 0.1, 19.4, Z + 0.7, "dark")
    return M(door=(-14.6, 23.0, 2), spot=(-16.0, 20.4, 2), look=(-16.0, 14, 2), action="hammer",
             acc="goggles", parent=18)


@region("Science Isle", "Observatory", "A white dome with a brass telescope pointed at the stars.")
def r20(b):
    b.plot(-28, 12, -22, 18, z=2.0, c="grass2", depth=4.4)
    Z = 2.0
    cx, cy = -25.4, 15.6
    b.disc(cx, cy, Z, Z + 1.6, 2.1, "cream", step=0.4)
    b.dome(cx, cy, Z + 1.6, 2.1, "white", layers=6, step=0.4)
    b.box(cx - 0.3, cy - 2.12, Z + 1.6, cx + 0.3, cy - 1.5, Z + 3.6, "charcoal")
    b.box(cx - 0.35, cy - 2.15, Z, cx + 0.35, cy - 2.0, Z + 1.2, "wood2")
    b.part("scope", pivot=(cx, cy - 1.0, Z + 3.0), anim="spin", axis="y", speed=0.12)
    b.box(cx - 0.15, cy - 2.6, Z + 3.0, cx + 0.15, cy - 0.2, Z + 3.3, "mustard", part="scope")
    b.box(cx - 0.2, cy - 2.7, Z + 2.95, cx + 0.2, cy - 2.5, Z + 3.35, "wood2", part="scope")
    # outdoor telescope on tripod
    b.box(-23.2, 13.0, Z, -23.1, 13.1, Z + 0.9, "dark")
    b.box(-22.9, 13.0, Z, -22.8, 13.1, Z + 0.9, "dark")
    b.box(-23.4, 12.8, Z + 0.9, -22.6, 13.0, Z + 1.1, "mustard")
    b.tree(-27.4, 17.4, kind="pine")
    b.bush(-22.6, 17.4)
    return M(door=(-22.6, 17.0, 2), spot=(-23.6, 13.6, 2), look=(-23.6, 8, 2), action="look",
             parent=19, via=[(-16.0, 19.6, 2), (-21.8, 19.0, 2)])


@region("Science Isle", "Balloon Launch", "A striped hot-air balloon. Look how far you've come.")
def r21(b):
    b.plot(-20, 12, -14, 18, z=2.0, c="grass3", depth=4.0)
    Z = 2.0
    b.disc(-17, 14.6, Z, Z + 0.15, 1.3, "path", step=0.4)
    for (x, y) in ((-18.4, 13.2), (-15.6, 13.2), (-18.4, 16.0), (-15.6, 16.0)):
        b.box(x - 0.08, y - 0.08, Z, x + 0.08, y + 0.08, Z + 0.4, "wood2")
    b.part("balloon", pivot=(-17.0, 14.6, Z + 6.0), anim="bob", amp=0.5, speed=0.6)
    bz = Z + 4.2
    b.box(-17.4, 14.2, bz, -16.6, 15.0, bz + 0.6, "wood", part="balloon")
    for (x, y) in ((-17.35, 14.25), (-16.7, 14.25), (-17.35, 14.9), (-16.7, 14.9)):
        b.box(x, y, bz + 0.6, x + 0.05, y + 0.05, bz + 1.6, "dark", part="balloon")
    rows = [0.8, 1.4, 1.8, 2.0, 2.0, 1.8, 1.4, 0.8]
    cols = ["roof", "cream", "yellow", "roof", "cream", "yellow", "roof", "cream"]
    for k, r in enumerate(rows):
        b.disc(-17.0, 14.6, bz + 1.6 + k * 0.45, bz + 2.05 + k * 0.45, r, cols[k], step=0.4,
               part="balloon")
    b.bush(-14.6, 17.4)
    b.bush(-19.4, 12.6)
    return M(door=(-16.0, 17.4, 2), spot=(-17.0, 13.0, 2.0), look=(-17.0, 8, 2), action="wave",
             parent=19, via=[(-16.0, 19.6, 2)])


@region("Science Isle", "Ancient Ruins", "Mossy columns and a glowing rune stone. Who built these?")
def r22(b):
    b.plot(-28, 18, -22, 27, z=2.0, c="grass2", depth=4.6)
    Z = 2.0
    for (x, y, h) in ((-27.2, 19.0, 2.6), (-27.2, 21.5, 1.4), (-27.2, 24.0, 2.8), (-27.2, 26.2, 0.9),
                      (-23.2, 26.2, 2.4), (-25.2, 26.2, 1.2)):
        b.box(x - 0.3, y - 0.3, Z, x + 0.3, y + 0.3, Z + 0.2, "cream2")
        b.box(x - 0.22, y - 0.22, Z + 0.2, x + 0.22, y + 0.22, Z + h, "cream")
        b.box(x - 0.24, y - 0.24, Z + h - 0.3, x + 0.24, y + 0.24, Z + h - 0.1, "leaf2")
    # arch
    b.box(-27.4, 23.7, Z + 2.8, -23.0, 24.3, Z + 3.3, "cream")
    b.box(-23.4, 23.7, Z, -22.9, 24.3, Z + 2.8, "cream")
    # fallen column
    b.box(-25.6, 19.6, Z, -23.6, 20.0, Z + 0.4, "cream")
    # rune stone
    b.box(-25.4, 22.4, Z, -24.6, 22.9, Z + 1.6, "charcoal")
    b.part("rune", glow=1, pivot=(-25.0, 22.37, Z + 0.9), anim="pulse", speed=1.0)
    b.box(-25.15, 22.36, Z + 0.5, -24.85, 22.4, Z + 1.3, "glowgreen", part="rune")
    for k in range(6):
        b.bush(-27.6 + k * 0.9, 19.0 + (k % 3) * 2.8, z=Z, s=0.45)
    return M(door=(-22.6, 21.5, 2), spot=(-24.0, 21.8, 2), look=(-25, 23.5, 2), action="look",
             parent=19, via=[(-16.0, 19.6, 2), (-22.0, 19.6, 2)])


@region("Science Isle", "Greenhouse", "Giant flowers under a glass dome. Ideas need watering too.")
def r23(b):
    b.plot(-22, 6, -14, 12, z=2.0, c="grass", depth=4.2)
    Z = 2.0
    cx, cy = -18.6, 8.8
    # steel frame dome (ribs) + a few glass panes
    for k in range(6):
        r = 2.4 * math.cos(k / 6 * math.pi / 2)
        z0 = Z + k * 0.45
        for a in range(12):
            ang = a / 12 * math.tau
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            b.box(x - 0.06, y - 0.06, z0, x + 0.06, y + 0.06, z0 + 0.45, "white")
        b.disc(cx, cy, z0 + 0.4, z0 + 0.45, r, "sky", step=0.6) if k == 5 else None
    b.box(cx - 2.5, cy - 2.5, Z, cx + 2.5, cy + 2.5, Z + 0.1, "path")
    # giant flowers inside
    for (dx, dy, h, c) in ((0, 0, 2.0, "pink"), (-1.0, 0.8, 1.4, "yellow"), (1.0, -0.6, 1.6, "lilac"),
                           (0.8, 1.2, 1.1, "red")):
        b.box(cx + dx - 0.06, cy + dy - 0.06, Z, cx + dx + 0.06, cy + dy + 0.06, Z + h, "leaf")
        b.box(cx + dx - 0.35, cy + dy - 0.35, Z + h, cx + dx + 0.35, cy + dy + 0.35, Z + h + 0.15, c)
        b.box(cx + dx - 0.1, cy + dy - 0.1, Z + h + 0.15, cx + dx + 0.1, cy + dy + 0.1, Z + h + 0.25,
              "yellow")
        b.box(cx + dx, cy + dy - 0.03, Z + h * 0.5, cx + dx + 0.35, cy + dy + 0.03, Z + h * 0.5 + 0.12,
              "leaf3")
    # watering can
    b.box(-15.6, 7.0, Z, -15.1, 7.4, Z + 0.4, "teal")
    b.box(-15.1, 7.15, Z + 0.25, -14.8, 7.25, Z + 0.32, "teal")
    for k in range(5):
        b.flower(-21.5 + k * 0.4, 11.4, z=Z)
    return M(door=(-17.0, 11.4, 2), spot=(-15.4, 8.4, 2), look=(-15.4, 2, 2), action="look",
             parent=21)


@region("Science Isle", "Rocket Workshop", "Parts, plans and a prototype. Something big is coming.")
def r24(b):
    b.plot(-28, 4, -22, 12, z=2.0, c="grass2", depth=4.8)
    Z = 2.0
    # hangar (arched roof)
    x0, x1, y0, y1 = -27.6, -24.0, 6.0, 11.4
    for k in range(6):
        w = (x1 - x0) / 2 * math.cos(k / 6 * math.pi / 2)
        cxh = (x0 + x1) / 2
        b.box(cxh - w, y0, Z + k * 0.5, cxh + w, y1, Z + (k + 1) * 0.5, "steel" if k % 2 else "cream2")
    b.box(-26.6, y0 - 0.04, Z, -25.0, y0, Z + 1.8, "glow", part="glow")
    # prototype rocket outside
    rx, ry = -23.0, 9.6
    for k in range(5):
        b.disc(rx, ry, Z + k * 0.5, Z + (k + 1) * 0.5, 0.45, "white" if k != 2 else "clay", step=0.3)
    b.cone(rx, ry, Z + 2.5, 0.45, 0.8, "clay", layers=3, step=0.3)
    for (dx, dy) in ((0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)):
        b.box(rx + dx - 0.08, ry + dy - 0.08, Z, rx + dx + 0.08, ry + dy + 0.08, Z + 0.7, "roof2")
    # crates + blueprint table
    b.box(-24.0, 4.6, Z, -23.4, 5.2, Z + 0.6, "wood")
    b.box(-23.3, 4.6, Z, -22.8, 5.1, Z + 0.45, "wood2")
    b.box(-26.4, 4.4, Z + 0.6, -25.0, 5.4, Z + 0.68, "blue")
    for x in (-26.3, -25.2):
        b.box(x, 4.5, Z, x + 0.1, 5.3, Z + 0.6, "dark")
    return M(door=(-22.4, 8.0, 2), spot=(-23.4, 7.2, 2), look=(-23.4, 1, 2), action="hammer",
             acc="hardhat", parent=23, via=[(-21.5, 11.6, 2)])


# =============================================================== 5. SUMMIT
MTN = (-15.5, -9.5)
MTN_R = 5.5
MTN_LAYERS = 10
MTN_LH = 1.3


def mtn_r(z):
    return MTN_R * (1 - z / (MTN_LAYERS * MTN_LH + 1.2))


def spiral_path():
    pts = []
    n = 26
    for i in range(1, n + 1):
        t = i / n
        z = t * (MTN_LAYERS - 1) * MTN_LH + MTN_LH * 0.0
        a = -0.2 + t * math.tau * 1.15
        r = mtn_r(z) + 0.35
        pts.append((MTN[0] + r * math.cos(a), MTN[1] + r * math.sin(a), z))
    return pts


@region("Summit", "Mountain Trail", "Pine forest and a campfire at the foot of the mountain.")
def r25(b):
    b.plot(-21, -15, -5, -3, depth=5.0)
    # campfire
    b.disc(-7.6, -8.0, 0, 0.12, 0.6, "rock", step=0.3)
    for k in range(3):
        b.box(-8.0 + k * 0.1, -8.2, 0.12, -7.2, -8.1 + k * 0.1, 0.24, "wood2")
    b.part("fire", glow=1, pivot=(-7.6, -8.0, 0.3), anim="pulse", speed=5.0)
    b.box(-7.8, -8.2, 0.24, -7.4, -7.8, 0.55, "glow", part="fire")
    b.box(-7.7, -8.1, 0.55, -7.5, -7.9, 0.8, "yellow", part="fire")
    # tent
    for k in range(4):
        w = 0.9 - k * 0.22
        b.box(-6.6 - w, -11.6, k * 0.3, -6.6 + w, -10.0, (k + 1) * 0.3, "teal" if k % 2 == 0 else "cream")
    b.box(-6.75, -11.62, 0, -6.45, -11.6, 0.6, "dark")
    # logs to sit on
    b.box(-8.8, -7.0, 0, -7.2, -6.7, 0.3, "wood")
    # pine forest avoiding the mountain footprint
    import random as _r
    rng = _r.Random(25)
    placed = 0
    while placed < 22:
        x, y = rng.uniform(-20.6, -5.4), rng.uniform(-14.6, -3.4)
        if math.hypot(x - MTN[0], y - MTN[1]) < MTN_R + 0.9:
            continue
        if abs(x + 7.6) < 1.6 and abs(y + 8.5) < 3.0:
            continue
        if y > -4.4 and x > -9.5:
            continue
        b.tree(x, y, kind="pine", h=rng.uniform(1.2, 2.4))
        placed += 1
    for (x, y) in ((-9.6, -5.0), (-12.0, -3.8), (-20.0, -4.0)):
        b.box(x - 0.3, y - 0.3, 0, x + 0.3, y + 0.3, 0.4, "rock2")
    return M(door=(-6.5, -3.6, 0), spot=(-8.0, -7.0, 0), look=(-7.6, -8.0, 0), action="sleep",
             acc="nightcap", parent=4, via=[(-3.8, -3.2, 0)])


@region("Summit", "The Peak", "A spiral trail to the snowy summit. Every step counts.")
def r26(b):
    cx, cy = MTN
    cols = ["leaf2", "leaf", "rock2", "rock3", "rock2", "rock3", "rock2", "snow", "snow", "snow"]
    for k in range(MTN_LAYERS):
        z0, z1 = k * MTN_LH, (k + 1) * MTN_LH
        r = mtn_r(z0)
        ox, oy = 0.35 * math.sin(k * 1.3), 0.35 * math.cos(k * 1.7)
        b.disc(cx + ox, cy + oy, z0, z1, r, cols[k], step=0.5)
        # craggy outcrops
        for a in (k * 0.9, k * 0.9 + 2.3, k * 0.9 + 4.1):
            rr = r - 0.2
            x, y = cx + ox + rr * math.cos(a), cy + oy + rr * math.sin(a)
            s_ = 0.6 + 0.3 * math.sin(k + a)
            b.box(x - s_, y - s_, z0, x + s_, y + s_, z1 + 0.35, "snow" if k >= 7 else "rock3")
        if k < 3:
            for a in (k * 2.1 + 0.6, k * 2.1 + 3.3):
                rr = r - 0.6
                b.tree(cx + rr * math.cos(a), cy + rr * math.sin(a), z=z1, kind="pine", h=1.3)
    # spiral staircase
    for (x, y, z) in spiral_path():
        b.box(x - 0.38, y - 0.38, z - 0.3, x + 0.38, y + 0.38, z, "wood")
    # summit flag
    top = MTN_LAYERS * MTN_LH
    b.box(cx - 0.05, cy + 0.3, top, cx + 0.05, cy + 0.4, top + 2.0, "dark")
    b.part("flag", pivot=(cx, cy + 0.35, top + 1.8), anim="bob", amp=0.05, speed=3.0)
    b.box(cx + 0.05, cy + 0.33, top + 1.4, cx + 1.0, cy + 0.37, top + 1.95, "clay", part="flag")
    sp = spiral_path()
    return M(door=(cx, cy - 0.4, top), spot=(cx, cy - 0.4, top), look=(cx, cy - 8, top),
             action="celebrate", acc="partyhat", parent=25,
             via=[(-8.0, -5.0, 0), (sp[0][0], sp[0][1] - 0.6, 0)] + [p for p in sp] +
                 [(cx + 0.4, cy - 0.8, top)])


@region("Summit", "Sky Bridge", "A glowing bridge from the peak to a platform among the clouds.")
def r27(b):
    b.plot(-11, -24, -5, -18, z=12.0, c="grass3", depth=3.4)
    Z = 12.0
    ax, ay, az = MTN[0] + 0.6, MTN[1] - 0.9, MTN_LAYERS * MTN_LH
    bx, by, bz = -8.0, -18.0, Z
    n = 18
    for i in range(n):
        t = i / (n - 1)
        x, y, z = ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t - 0.4 * math.sin(math.pi * t)
        b.box(x - 0.35, y - 0.35, z - 0.08, x + 0.35, y + 0.35, z, "white")
        if i % 3 == 0:
            b.box(x - 0.08, y - 0.08, z, x + 0.08, y + 0.08, z + 0.15, "glowblue", part="glow")
    # gazebo
    gx, gy = -8.0, -21.6
    for (dx, dy) in ((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)):
        b.box(gx + dx - 0.1, gy + dy - 0.1, Z, gx + dx + 0.1, gy + dy + 0.1, Z + 1.8, "white")
    b.cone(gx, gy, Z + 1.8, 1.8, 1.0, "roof", layers=4, step=0.4)
    b.box(gx - 0.6, gy + 0.4, Z, gx + 0.6, gy + 0.8, Z + 0.4, "wood")
    # clouds drifting by
    b.part("clouds", pivot=(-8, -21, Z), anim="spin", axis="y", speed=0.05)
    for (dx, dy, dz, s) in ((-6, 2, -1.5, 1.4), (5, -3, 1.0, 1.0), (3, 6, -2.5, 1.6), (-4, -6, 2.0, 1.1)):
        x, y, z = -8 + dx, -21 + dy, Z + dz
        b.box(x - s, y - s * 0.6, z, x + s, y + s * 0.6, z + s * 0.5, "white", part="clouds")
        b.box(x - s * 0.5, y - s * 0.4, z + s * 0.5, x + s * 0.6, y + s * 0.4, z + s * 0.9, "white",
              part="clouds")
    return M(door=(-8.0, -18.8, 12), spot=(-8.0, -19.6, 12), look=(-8.0, -26, 12), action="look",
             parent=26, via=[(ax, ay, az)])


@region("Summit", "Hot Spring Cabin", "A cosy cabin and a steaming hot spring. You've earned it.")
def r28(b):
    b.plot(-28, -11, -21, -3, depth=4.0)
    b.house(-25.4, -8.4, 3.0, 2.4, 1.8, wall="wood", roof="roof2", door_face="-y")
    b.box(-24.0, -7.6, 2.0, -23.6, -7.2, 3.4, "rock2")
    b.part("smoke", pivot=(-23.8, -7.4, 3.6), anim="bob", amp=0.2, speed=0.8)
    for k in range(3):
        s = 0.25 + k * 0.1
        b.box(-23.8 - s / 2 + k * 0.15, -7.4 - s / 2, 3.6 + k * 0.45, -23.8 + s / 2 + k * 0.15, -7.4 + s / 2,
              3.6 + k * 0.45 + s, "cream2", part="smoke")
    # hot spring
    b.disc(-22.8, -5.0, -0.25, 0.1, 1.2, "rock", step=0.4)
    b.disc(-22.8, -5.0, -0.2, 0.06, 0.95, "water2", step=0.4)
    b.part("steam", pivot=(-22.8, -5.0, 0.4), anim="bob", amp=0.15, speed=1.0)
    for (dx, dy) in ((-0.3, 0.2), (0.3, -0.2), (0.0, 0.4)):
        b.box(-22.8 + dx - 0.1, -5.0 + dy - 0.1, 0.4, -22.8 + dx + 0.1, -5.0 + dy + 0.1, 0.65, "white",
              part="steam")
    b.box(-27.6, -4.2, 0, -26.4, -3.6, 0.5, "wood2")  # wood pile
    b.tree(-27.4, -10.4, kind="pine")
    b.tree(-21.6, -10.4, kind="pine")
    return M(door=(-21.6, -4.0, 0), spot=(-22.8, -5.0, 0.0), look=(-22.8, -12, 0), action="sleep",
             acc="nightcap", parent=25, via=[(-9.0, -3.6, 0), (-20.8, -3.6, 0)])


@region("Summit", "Aurora", "Ribbons of light across the night sky. Look up.")
def r29(b):
    b.part("aurora", glow=1, night=1, pivot=(-6, 34, 17), anim="bob", amp=0.6, speed=0.35)
    cols = ["glowgreen", "glowblue", "glowpink"]
    for ri in range(3):
        for k in range(26):
            x = -26 + k * 1.6
            y = 34 + ri * 2.5 + 2.0 * math.sin(k * 0.45 + ri)
            z = 15 + ri * 1.8 + 1.2 * math.sin(k * 0.3 + ri * 1.7)
            h = 1.4 + 0.8 * math.sin(k * 0.7 + ri)
            b.box(x, y - 0.1, z, x + 1.6, y + 0.1, z + h, cols[(ri + k // 9) % 3], part="aurora")
    # stars
    import random as _r
    rng = _r.Random(29)
    b.part("stars", glow=1, night=1, pivot=(0, 0, 30), anim="pulse", speed=0.7)
    for _ in range(60):
        x, y, z = rng.uniform(-40, 40), rng.uniform(-45, 35), rng.uniform(26, 36)
        b.cube(x, y, z, 0.18, "white", part="stars")
    return M(door=(-8.0, -18.8, 12), spot=(-7.0, -19.8, 12), look=(-7.0, 34, 17), action="look",
             parent=27)


@region("Summit", "Moonshot", "The finale: a rocket on the edge of the sky. You did this.")
def r30(b):
    b.plot(-3, -25, 3, -19, z=12.0, c="grass3", depth=3.8)
    Z = 12.0
    # bridge from the sky platform
    for k in range(4):
        b.box(-5.0 + k * 0.5, -21.6, Z - 0.1, -4.55 + k * 0.5, -20.4, Z, "white")
    # launch pad + gantry
    b.disc(0.4, -22.4, Z, Z + 0.25, 1.6, "charcoal", step=0.4)
    for k in range(10):
        b.box(-1.6, -21.6, Z + k * 0.6, -1.3, -21.3, Z + (k + 1) * 0.6, "red" if k % 2 else "white")
        b.box(-1.6, -23.4, Z + k * 0.6, -1.3, -23.1, Z + (k + 1) * 0.6, "red" if k % 2 else "white")
    b.box(-1.6, -23.4, Z + 4.6, -0.5, -21.3, Z + 4.8, "steel")
    # the rocket (Clawd orange)
    b.part("rocket", pivot=(0.4, -22.4, Z + 0.25), anim="bob", amp=0.04, speed=6.0)
    rx, ry = 0.4, -22.4
    for k in range(9):
        r = 0.75 if k < 7 else 0.75 - (k - 6) * 0.2
        b.disc(rx, ry, Z + 0.6 + k * 0.6, Z + 0.6 + (k + 1) * 0.6, r, "clay" if k not in (3, 4) else "white",
               step=0.3, part="rocket")
    b.cone(rx, ry, Z + 6.0, 0.4, 1.2, "clay", layers=4, step=0.2, part="rocket")
    # porthole with Clawd eyes
    b.box(rx - 0.3, ry - 0.78, Z + 3.0, rx + 0.3, ry - 0.74, Z + 3.5, "glowblue", part="rocket")
    b.box(rx - 0.18, ry - 0.8, Z + 3.15, rx - 0.1, ry - 0.78, Z + 3.35, "dark", part="rocket")
    b.box(rx + 0.1, ry - 0.8, Z + 3.15, rx + 0.18, ry - 0.78, Z + 3.35, "dark", part="rocket")
    for (dx, dy) in ((0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8)):
        b.box(rx + dx * 1.05 - 0.12, ry + dy * 1.05 - 0.12, Z + 0.4, rx + dx * 1.05 + 0.12,
              ry + dy * 1.05 + 0.12, Z + 1.8, "roof2", part="rocket")
    b.box(rx - 0.4, ry - 0.4, Z + 0.25, rx + 0.4, ry + 0.4, Z + 0.6, "glow", part="rocket")
    # the moon
    mx, my, mz = 22.0, 48.0, 32.0
    for k in range(-5, 6):
        r = 4.0 * math.cos(k / 6 * math.pi / 2)
        b.disc(mx, my, mz + k * 0.7, mz + (k + 1) * 0.7, r, "white" if k % 3 else "cream", step=0.7,
               part="glow")
    return M(door=(-2.4, -21.0, 12), spot=(-1.0, -20.0, 12), look=(-1.0, -14, 12), action="celebrate",
             acc="partyhat", parent=27, via=[(-5.2, -21.0, 12)])
