# Soft 3D dachshund — builds the whole scene in Blender from code.
# Usage: python build_scene.py [preview]   (needs the official `bpy` module: pip install bpy)
import bpy, bmesh, math, sys
from mathutils import Vector

PREVIEW = 'preview' in sys.argv
FPS, SECONDS = 24, 4
FRAMES = FPS * SECONDS

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
sc = bpy.context.scene

def hexcol(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c] + [a]

def mat(name, color, rough=0.5, coat=0.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = hexcol(color)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.25
    if sss:
        p.inputs['Subsurface Weight'].default_value = sss
        p.inputs['Subsurface Radius'].default_value = (0.4, 0.2, 0.15)
        p.inputs['Subsurface Scale'].default_value = 0.15
    return m

M = dict(
    fur=mat('Fur', '#E2722F', 0.55, 0.15, 0.25), ear=mat('Ear', '#6B2E14', 0.6, 0.1),
    black=mat('Gloss', '#141414', 0.12, 0.6), white=mat('White', '#FFFFFF', 0.3),
    blush=mat('Blush', '#FF8E86', 0.6), collar=mat('Collar', '#1FA7C9', 0.35, 0.4),
    gold=mat('Gold', '#F5C542', 0.25, 0.5), ball=mat('Ball', '#FF6F61', 0.35, 0.5, 0.1),
    bush=mat('Bush', '#5CC97A', 0.6, 0.1, 0.1), floor=mat('Floor', '#F6DEC6', 0.8),
    belly=mat('Belly', '#F2C08E', 0.6, 0.1, 0.2),
)

def link(o): sc.collection.objects.link(o); return o

def sphere(name, loc, scale, m, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    if parent: o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def metaball(name, base_mat=None, res=0.04):
    mb = bpy.data.metaballs.new(name); mb.render_resolution = res; mb.resolution = 0.1
    o = link(bpy.data.objects.new(name, mb))
    if base_mat: mb.materials.append(base_mat)
    return o

def el(o, kind, co, r, sx=1, sy=1, sz=1):
    e = o.data.elements.new(type=kind); e.co = co; e.radius = r
    e.size_x, e.size_y, e.size_z = sx, sy, sz; return e

# ---------- backdrop (cyclorama) ----------
bm = bmesh.new(); prof = []
for i in range(12): prof.append((-30 + i * 2.5, 0))
for i in range(17):
    a = math.radians(i * 90 / 16); prof.append((math.sin(a) * 8, 8 - math.cos(a) * 8))
for i in range(1, 6): prof.append((8, 8 + i * 4))
cols = []
for x in (-40, 40):
    cols.append([bm.verts.new((x, y, z)) for (y, z) in prof])
for i in range(len(prof) - 1):
    bm.faces.new((cols[0][i], cols[1][i], cols[1][i + 1], cols[0][i + 1]))
me = bpy.data.meshes.new('Backdrop'); bm.to_mesh(me); bm.free()
bd = link(bpy.data.objects.new('Backdrop', me)); me.materials.append(M['floor'])
for p in me.polygons: p.use_smooth = True
bd.location.y = 2

# ---------- dog body (metaball family "Dog") ----------
dog = metaball('Dog', M['fur'])
el(dog, 'CAPSULE', (0, 0, 1.15), 1.25, sx=1.5)          # long sausage body
el(dog, 'BALL', (1.55, 0, 1.45), 1.35)                   # chest
el(dog, 'BALL', (-1.5, 0, 1.2), 1.2)                     # rump
for x in (1.45, -1.35):
    for y in (0.5, -0.5):
        el(dog, 'CAPSULE', (x, y, 0.42), 0.6, sx=0.12)  # stubby legs
for x in (1.55, -1.25):
    for y in (0.52, -0.52):
        el(dog, 'ELLIPSOID', (x + 0.18, y, 0.2), 0.62, sx=1.25, sy=0.9, sz=0.55)  # paws

head = metaball('Dog.001')            # same family -> merges smoothly with body
head.location = (2.15, 0, 2.35); head.rotation_euler = (0, 0, math.radians(-62))
el(head, 'BALL', (0, 0, 0), 1.35)                        # skull
el(head, 'ELLIPSOID', (0.95, 0, -0.22), 1.0, sx=1.3, sy=0.75, sz=0.72)  # snout
el(head, 'BALL', (-0.55, 0, -0.75), 1.0)                 # neck

def child(o):
    o.parent = head; o.matrix_parent_inverse.identity(); return o

# --- find the real metaball surface by ray-casting, so features sit ON the head ---
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
HM = head.matrix_world.copy(); HMi = HM.inverted()
def surf(d, center=(0, 0, 0), inset=0.0):
    """Hit point (head-local) of a ray shot from outside toward `center` along direction d."""
    d = Vector(d).normalized(); c = Vector(center)
    o_w = HM @ (c + d * 6); dir_w = (HM.to_3x3() @ -d).normalized()
    ok, loc, nrm, *_ = sc.ray_cast(dg, o_w, dir_w)
    assert ok, d
    return HMi @ (loc - nrm * inset), (HMi.to_3x3() @ nrm).normalized()

def place(o, loc, nrm=None):
    child(o); o.location = loc
    if nrm is not None: o.rotation_euler = nrm.to_track_quat('Z', 'Y').to_euler()
    return o

nose_loc, nose_n = surf((1, 0, 0.05), center=(0.9, 0, -0.2))
for s in (1, -1):
    loc, n = surf((0.75, 0.48 * s, 0.42), inset=0.07)
    place(sphere('Eye', (0, 0, 0), (0.17, 0.17, 0.19), M['black']), loc, n)
    place(sphere('Spark', (0, 0, 0), (0.05, 0.05, 0.03), M['white']), loc + n * 0.14 + Vector((0, 0.05 * s, 0.07)), n)
    loc, n = surf((0.55, 0.85 * s, -0.15), inset=0.02)
    place(sphere('Blush', (0, 0, 0), (0.2, 0.13, 0.04), M['blush']), loc, n)
    loc, n = surf((0.55, 0.42 * s, 0.85), inset=0.0)
    place(sphere('Brow', (0, 0, 0), (0.15, 0.05, 0.04), M['ear']), loc, n)
nose = place(sphere('Nose', (0, 0, 0), (0.26, 0.21, 0.24), M['black']), nose_loc - Vector((0.08, 0, 0)))

# smile: a tube that follows the snout surface
pts = []
for i in range(17):
    u = -1 + i / 8
    loc, n = surf((1, 0, 0), center=(0.9, 0.36 * u, -0.48 + 0.16 * u * u), inset=-0.01)
    pts.append(loc)
cu = bpy.data.curves.new('Smile', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.035; cu.bevel_resolution = 4
sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
for pt, v in zip(sp.points, pts): pt.co = (*v, 1)
cu.use_fill_caps = True; cu.materials.append(M['black'])
mouth = child(link(bpy.data.objects.new('Smile', cu)))

ears = []
for s in (1, -1):
    loc, n = surf((-0.15, 0.75 * s, 0.65), inset=0.1)
    pivot = bpy.data.objects.new('EarPivot', None); link(pivot); child(pivot); pivot.location = loc
    e = sphere('Ear', (0, 0, 0), (0.5, 0.16, 0.95), M['ear'])
    e.parent = pivot; e.location = (0.0, 0.18 * s, -0.75); e.rotation_euler = (math.radians(-14 * s), math.radians(8), 0)
    ears.append((pivot, s))

# collar: shoot a ring of rays out from inside the neck and run a tube through the hits,
# so the collar hugs whatever shape the blended neck actually has
from mathutils import Euler, Matrix
nc_w = Vector((1.8, 0, 1.95)); ax = Vector((0.5, 0, 0.87)).normalized()
u = ax.orthogonal().normalized(); v = ax.cross(u)
hits = []
for i in range(48):
    a = 2 * math.pi * i / 48; d = (u * math.cos(a) + v * math.sin(a)).normalized()
    ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, nc_w, d)
    hits.append((loc - nc_w).length if ok and ob.name.startswith('Dog') else None)
good = sorted(h for h in hits if h); med = good[len(good) // 2]
hits = [min(h, med * 1.35) if h else med for h in hits]
for _ in range(3):  # smooth the radius profile
    hits = [(hits[i - 1] + 2 * hits[i] + hits[(i + 1) % len(hits)]) / 4 for i in range(len(hits))]
cu = bpy.data.curves.new('Collar', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.12; cu.bevel_resolution = 6
sp = cu.splines.new('NURBS'); sp.points.add(len(hits) - 1); sp.use_cyclic_u = True; sp.order_u = 4
ring = []
for i, (pt, h) in enumerate(zip(sp.points, hits)):
    a = 2 * math.pi * i / 48; w = nc_w + (u * math.cos(a) + v * math.sin(a)) * (h + 0.06)
    ring.append(w); pt.co = (*(HMi @ w), 1)
cu.materials.append(M['collar'])
collar = child(link(bpy.data.objects.new('Collar', cu)))
# hang the tag from the point of the collar that faces the camera and points down most
tag_w = max(ring, key=lambda w: (w - nc_w).normalized().dot(Vector((0.35, -0.6, -0.7)).normalized()))
low = None
tagpivot = bpy.data.objects.new('TagPivot', None); link(tagpivot); child(tagpivot)
tagpivot.location = HMi @ tag_w
bpy.ops.mesh.primitive_cylinder_add(radius=0.24, depth=0.08, vertices=48)
tag = bpy.context.object; tag.name = 'Tag'; bpy.ops.object.shade_smooth(); tag.data.materials.append(M['gold'])
bevel = tag.modifiers.new('b', 'BEVEL'); bevel.width = 0.03; bevel.segments = 4
tag.parent = tagpivot; tag.rotation_euler = (HMi.to_3x3() @ Vector((-0.45, -0.9, 0.1))).to_track_quat('Z', 'Y').to_euler()
tag.location = (HMi.to_3x3() @ Vector((0.05, -0.12, -0.27)))

# tail
tailpivot = bpy.data.objects.new('TailPivot', None); link(tailpivot); tailpivot.location = (-2.35, 0, 1.6)
tail = sphere('Tail', (0, 0, 0), (0.17, 0.17, 0.75), M['fur']); tail.parent = tailpivot
tail.location = (-0.35, 0, 0.55); tail.rotation_euler = (0, math.radians(-35), 0)

# ---------- props ----------
ball = sphere('Ball', (4.5, -2.9, 0.45), (0.55, 0.55, 0.55), M['ball'])
bush = metaball('Bush', M['bush'], res=0.06)
for (x, y, z, r) in [(-3.6, 2.2, 0.6, 1.8), (-2.5, 2.6, 0.4, 1.3), (-4.4, 1.6, 0.3, 1.2), (-3.2, 3.0, 1.5, 1.3),
                     (5.0, 2.8, 0.5, 1.7), (6.0, 2.4, 0.3, 1.2), (4.2, 3.3, 0.3, 1.1), (5.2, 3.2, 1.4, 1.1)]:
    el(bush, 'BALL', (x, y, z), r)

# ---------- camera + lights ----------
target = bpy.data.objects.new('Target', None); link(target); target.location = (1.25, -0.4, 1.75)
cam = link(bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))); cam.location = (6.2, -11.5, 3.4)
cam.data.lens = 40; cam.data.dof.use_dof = True; cam.data.dof.focus_object = target; cam.data.dof.aperture_fstop = 4.0
c = cam.constraints.new('TRACK_TO'); c.target = target
sc.camera = cam

def area(name, loc, energy, size, color='#FFFFFF'):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = hexcol(color)[:3]
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    t = o.constraints.new('TRACK_TO'); t.target = target; return o
area('Key', (-6, -8, 9), 2600, 7, '#FFF3E6')
area('Fill', (9, -6, 3), 700, 6, '#FFE3F0')
area('Rim', (3, 7, 7), 1400, 4, '#FFFFFF')
w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = hexcol('#FBE9D7')
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55

# ---------- animation (seamless 4 s loop) ----------
sc.frame_start, sc.frame_end = 1, FRAMES; sc.render.fps = FPS
TAU = 2 * math.pi
def key(o, path): o.keyframe_insert(data_path=path)
for f in range(1, FRAMES + 1):
    t = (f - 1) / FPS; sc.frame_set(f)
    br = math.sin(TAU * t / 2)
    dog.scale = (1, 1 + 0.015 * br, 1 + 0.025 * br); key(dog, 'scale')
    head.rotation_euler = (math.radians(9 * math.sin(TAU * t / 4)), math.radians(-4 + 4 * math.sin(TAU * t / 2)),
                           math.radians(-62 + 6 * math.sin(TAU * t / 4 + 0.6)))
    head.location = (2.15, 0, 2.35 + 0.04 * br); key(head, 'rotation_euler'); key(head, 'location')
    for (p, s) in ears:
        p.rotation_euler = (math.radians(14 * s * math.sin(TAU * t / 4 - 0.9) + 5 * s), math.radians(8 * math.sin(TAU * t / 2 - 0.8)), 0)
        key(p, 'rotation_euler')
    tailpivot.rotation_euler = (math.radians(28 * math.sin(TAU * t * 2.5)), 0, 0); key(tailpivot, 'rotation_euler')
    tagpivot.rotation_euler = (math.radians(14 * math.sin(TAU * t / 2 - 1.2)), 0, 0); key(tagpivot, 'rotation_euler')
    tb = t % 2; blink = 0.08 if 1.25 < tb < 1.37 else 1.0
    for o in head.children:
        if o.name.startswith(('Eye', 'Spark')):
            base = 0.17 if o.name.startswith('Eye') else 0.05
            o.scale.y = base * blink; key(o, 'scale')
    nose.scale = (0.26, 0.21, 0.24 * (1 + (0.12 * abs(math.sin(TAU * t * 3)) if 2.6 < t < 3.4 else 0))); key(nose, 'scale')
    # bouncing ball with squash & stretch, 4 bounces per loop
    p = t % 1.0; hgt = 1.4 * 4 * p * (1 - p)
    vel = abs(1 - 2 * p)
    if p < 0.06 or p > 0.94:
        sq = 1 - 0.32 * (1 - min(p, 1 - p) / 0.06); sx, sz = 1 / math.sqrt(sq), sq
    else:
        sz = 1 + 0.18 * vel; sx = 1 / math.sqrt(sz)
    r = 0.45
    ball.scale = (r * sx, r * sx, r * sz); ball.location = (4.5, -2.9, r * sz + hgt)
    ball.rotation_euler = (0, TAU * t / 2, 0)
    key(ball, 'scale'); key(ball, 'location'); key(ball, 'rotation_euler')

# ---------- render settings ----------
r = sc.render; r.engine = 'CYCLES'; sc.cycles.device = 'CPU'
r.resolution_x, r.resolution_y = 864, 1080
r.resolution_percentage = 40 if PREVIEW else 100
sc.cycles.samples = 24 if PREVIEW else 32
sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = True
sc.cycles.max_bounces = 6
r.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
r.image_settings.file_format = 'PNG'
sc.frame_set(1)
import os; bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "soft3d_dog_preview.blend" if PREVIEW else "soft3d_dog.blend"))
