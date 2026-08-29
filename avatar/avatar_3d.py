GARMENT_SLOTS = (
    "full_body",
    "upper_body",
    "lower_body",
    "swimwear",
    "lingerie",
    "shoes",
    "accessories",
)


def full_body_3d_manifest() -> dict:
    return {
        "current_formats": ["BLEND", "GLB"],
        "target_format": "VRM 1.0",
        "status": "base_rigged_identity_pending",
        "body": "full_body",
        "identity": "luna",
        "ai_generated": True,
        "adult_character": True,
        "declared_age": 25,
        "assets": {
            "blend": "/assets/avatar/3d/luna_base_v0_1.blend",
            "glb": "/assets/avatar/3d/luna_base_v0_1.glb",
            "preview": "/assets/avatar/3d/luna_base_v0_1_preview.png",
        },
        "rig": {
            "humanoid": True,
            "hands": True,
            "finger_bones": True,
            "feet": True,
            "bone_count": 163,
            "finger_bones_detected": 38,
            "face_blendshapes": {
                "status": "pending",
                "planned": ["blink", "happy", "sad", "surprised", "mouth_open"],
            },
        },
        "garment_slots": list(GARMENT_SLOTS),
        "product_interaction": {
            "hand_grip_anchors": ["left_hand", "right_hand"],
            "adult_product_explanation": "age_gate_required",
        },
        "pipeline": {
            "turntable": "complete",
            "base_mesh": "complete",
            "base_rig": "complete",
            "identity_sculpt": "pending",
            "retopology": "pending",
            "outfit_fitting": "pending",
            "blendshapes": "pending",
            "vrm_mapping_and_export": "pending",
        },
    }
