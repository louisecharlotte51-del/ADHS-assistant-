"""Exportiert aus gartenquartier_bergfrieden.blend: kontext.glb + V1..V5.glb (Phasen als Knoten).
Aufruf: blender -b 3d/gartenquartier_bergfrieden.blend --python blender_glb_export.py"""
import bpy, os
OUT = os.path.join(os.path.dirname(bpy.data.filepath))
def export(datei, colls):
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for c in colls:
        c.hide_viewport = False
        for ch in c.children_recursive:
            ch.hide_viewport = False
        for lc in bpy.context.view_layer.layer_collection.children:
            pass
        for ob in c.all_objects:
            ob.hide_set(False); ob.hide_viewport = False; ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, datei), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("GLB", datei, flush=True)
C = bpy.data.collections
export("kontext.glb", [C["Kontext"], C["Entwurf_Geruest"]])
for v in ("V1", "V2", "V3", "V4", "V5"):
    export(f"{v}.glb", [C[v]])
print("FERTIG")
