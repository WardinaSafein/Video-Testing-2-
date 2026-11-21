# Usage: python render.py <file.blend> <out_prefix> <start> <end>
import bpy, sys
blend, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for f in range(a, b + 1):
    sc.frame_set(f); sc.render.filepath = f"{out}{f:04d}.png"
    bpy.ops.render.render(write_still=True)
