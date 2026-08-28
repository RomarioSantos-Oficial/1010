"""Build Luna's reproducible adult 3D base inside Blender.

Run this file with the portable Blender bundled in ``tools/blender``. The
result is a neutral-gray technical mannequin, not the final identity mesh.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "assets" / "avatar" / "3d"
BLEND_PATH = OUTPUT_DIR / "luna_base_v0_1.blend"
GLB_PATH = OUTPUT_DIR / "luna_base_v0_1.glb"
PREVIEW_PATH = OUTPUT_DIR / "luna_base_v0_1_preview.png"
REPORT_PATH = OUTPUT_DIR / "luna_base_v0_1_report.json"


def enable_extensions() -> None:
    for module in ("bl_ext.blender_org.mpfb", "bl_ext.blender_org.vrm"):
        if module not in bpy.context.preferences.addons:
            result = bpy.ops.preferences.addon_enable(module=module)
            if "FINISHED" not in result:
                raise RuntimeError(f"Falha ao ativar a extensao {module}: {result}")


def clear_scene() -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def create_adult_body() -> bpy.types.Object:
    scene = bpy.context.scene
    settings = {
        "MPFB_NH_add_phenotype": True,
        "MPFB_NH_add_breast": True,
        "MPFB_NH_breast_influence": 0.12,
        "MPFB_NH_detailed_helpers": True,
        "MPFB_NH_extra_vertex_groups": True,
        "MPFB_NH_mask_helpers": True,
        "MPFB_NH_phenotype_age": "young",
        "MPFB_NH_phenotype_gender": "female",
        "MPFB_NH_phenotype_height": "average",
        "MPFB_NH_phenotype_influence": 1.0,
        "MPFB_NH_phenotype_muscle": "averagemuscle",
        "MPFB_NH_phenotype_proportions": "average",
        "MPFB_NH_phenotype_race": "universal",
        "MPFB_NH_phenotype_weight": "averageweight",
        "MPFB_NH_preselect_group": "body",
        "MPFB_NH_scale_factor": "METER",
    }
    for name, value in settings.items():
        if not hasattr(scene, name):
            raise RuntimeError(f"Propriedade MPFB ausente: {name}")
        setattr(scene, name, value)

    result = bpy.ops.mpfb.create_human()
    if "FINISHED" not in result:
        raise RuntimeError(f"MPFB nao criou o corpo: {result}")

    body = bpy.context.active_object
    if body is None or body.type != "MESH":
        raise RuntimeError("MPFB nao deixou um corpo 3D ativo")

    body.name = "Luna_BaseBody"
    body.data.name = "Luna_BaseBody_Mesh"
    body["luna_character"] = "Luna"
    body["luna_adult"] = True
    body["luna_declared_age"] = 25
    body["luna_ai_generated"] = True
    body["luna_stage"] = "generic_adult_base_v0_1"
    body["luna_identity_status"] = "pending_reference_sculpt"
    return body


def apply_neutral_material(body: bpy.types.Object) -> None:
    material = bpy.data.materials.new("Luna_Technical_Neutral_Gray")
    material.diffuse_color = (0.31, 0.34, 0.38, 1.0)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.31, 0.34, 0.38, 1.0)
        principled.inputs["Roughness"].default_value = 0.72
        principled.inputs["Metallic"].default_value = 0.0

    body.data.materials.clear()
    body.data.materials.append(material)
    for polygon in body.data.polygons:
        polygon.material_index = 0


def add_full_rig(body: bpy.types.Object) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body

    scene = bpy.context.scene
    scene.MPFB_ADR_standard_rig = "default"
    scene.MPFB_ADR_import_weights = True
    result = bpy.ops.mpfb.add_standard_rig()
    if "FINISHED" not in result:
        raise RuntimeError(f"MPFB nao criou o rig: {result}")

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError(f"Esperado um armature, encontrados {len(armatures)}")
    armature = armatures[0]
    armature.name = "Luna_FullBody_Rig"
    armature.data.name = "Luna_FullBody_Armature"
    armature.show_in_front = True
    armature["luna_humanoid_rig"] = True
    armature["luna_vrm_status"] = "mapping_pending"
    return armature


def find_side_bone(armature: bpy.types.Object, side: str) -> str:
    side = side.lower()
    exact_candidates = {
        "left": ("hand.L", "hand_l", "l_hand", "wrist.L", "wrist_l"),
        "right": ("hand.R", "hand_r", "r_hand", "wrist.R", "wrist_r"),
    }[side]
    by_lower_name = {bone.name.lower(): bone.name for bone in armature.data.bones}
    for candidate in exact_candidates:
        if candidate.lower() in by_lower_name:
            return by_lower_name[candidate.lower()]

    markers = (".l", "_l", "left") if side == "left" else (".r", "_r", "right")
    for bone in armature.data.bones:
        lowered = bone.name.lower()
        if ("hand" in lowered or "wrist" in lowered) and any(marker in lowered for marker in markers):
            return bone.name
    raise RuntimeError(f"Osso da mao {side} nao encontrado")


def create_grip_anchor(armature: bpy.types.Object, side: str, bone_name: str) -> bpy.types.Object:
    anchor = bpy.data.objects.new(f"Luna_{side.title()}Hand_Grip", None)
    anchor.empty_display_type = "PLAIN_AXES"
    anchor.empty_display_size = 0.06
    bpy.context.scene.collection.objects.link(anchor)
    anchor.matrix_world = armature.matrix_world @ armature.data.bones[bone_name].matrix_local
    anchor.parent = armature
    anchor.parent_type = "BONE"
    anchor.parent_bone = bone_name
    anchor["luna_interaction_anchor"] = "product_grip"
    anchor["luna_hand"] = side
    return anchor


def export_glb(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    result = bpy.ops.export_scene.gltf(
        filepath=str(GLB_PATH),
        export_format="GLB",
        use_selection=True,
        export_animations=False,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Falha ao exportar GLB: {result}")


def point_camera(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def create_preview(body: bpy.types.Object) -> None:
    world_corners = [body.matrix_world @ Vector(corner) for corner in body.bound_box]
    min_z = min(point.z for point in world_corners)
    max_z = max(point.z for point in world_corners)
    center = sum(world_corners, Vector()) / len(world_corners)
    height = max_z - min_z

    camera_data = bpy.data.cameras.new("Luna_Preview_Camera")
    camera = bpy.data.objects.new("Luna_Preview_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (center.x, center.y - height * 1.72, min_z + height * 0.52)
    camera_data.lens = 54
    point_camera(camera, Vector((center.x, center.y, min_z + height * 0.52)))

    for name, location, energy, size in (
        ("Key", (2.6, -3.8, max_z + 0.7), 1150, 3.0),
        ("Fill", (-2.4, -2.5, min_z + height * 0.58), 800, 2.5),
        ("Rim", (1.5, 2.0, max_z), 900, 2.0),
    ):
        light_data = bpy.data.lights.new(f"Luna_Preview_{name}", "AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(f"Luna_Preview_{name}", light_data)
        bpy.context.scene.collection.objects.link(light)
        light.location = location
        point_camera(light, Vector((center.x, center.y, min_z + height * 0.52)))

    bpy.ops.mesh.primitive_plane_add(size=8, location=(center.x, center.y, min_z - 0.004))
    floor = bpy.context.active_object
    floor.name = "Luna_Preview_Floor"
    floor_material = bpy.data.materials.new("Luna_Preview_Floor_Material")
    floor_material.diffuse_color = (0.055, 0.07, 0.09, 1.0)
    floor.data.materials.append(floor_material)

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW_PATH)
    scene.render.film_transparent = False
    scene.world.color = (0.018, 0.025, 0.035)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    enable_extensions()
    clear_scene()
    body = create_adult_body()
    apply_neutral_material(body)
    armature = add_full_rig(body)

    left_bone = find_side_bone(armature, "left")
    right_bone = find_side_bone(armature, "right")
    left_anchor = create_grip_anchor(armature, "left", left_bone)
    right_anchor = create_grip_anchor(armature, "right", right_bone)

    bone_names = [bone.name for bone in armature.data.bones]
    finger_bones = [
        name
        for name in bone_names
        if any(
            marker in name.lower()
            for marker in ("finger", "metacarpal", "thumb", "index", "middle", "ring", "pinky")
        )
    ]
    if len(armature.data.bones) < 50:
        raise RuntimeError("O rig nao contem ossos suficientes para um corpo completo")

    body.modifiers.update()
    export_glb([body, armature, left_anchor, right_anchor])
    create_preview(body)

    readme = bpy.data.texts.new("LUNA_3D_BASE_README")
    readme.write(
        "Base 3D tecnica da personagem adulta ficticia Luna.\n"
        "Status: corpo e rig completos; identidade facial, roupas, blendshapes e mapeamento VRM pendentes.\n"
        "Ancora de produtos: Luna_LeftHand_Grip e Luna_RightHand_Grip.\n"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)

    report = {
        "character": "Luna",
        "ai_generated": True,
        "adult_character": True,
        "declared_age": 25,
        "stage": "generic_adult_base_v0_1",
        "identity_status": "pending_reference_sculpt",
        "blender_version": bpy.app.version_string,
        "mesh": body.name,
        "vertices": len(body.data.vertices),
        "polygons": len(body.data.polygons),
        "armature": armature.name,
        "bones": len(armature.data.bones),
        "finger_bones_detected": len(finger_bones),
        "hand_bones": {"left": left_bone, "right": right_bone},
        "grip_anchors": [left_anchor.name, right_anchor.name],
        "blend_file": BLEND_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "glb_file": GLB_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "preview_file": PREVIEW_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "vrm_status": "mapping_pending",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("LUNA_3D_REPORT", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LUNA_3D_ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
