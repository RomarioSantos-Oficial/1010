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
        "format": "VRM 1.0",
        "status": "references_curated",
        "body": "full_body",
        "identity": "luna",
        "ai_generated": True,
        "rig": {
            "humanoid": True,
            "hands": True,
            "finger_bones": True,
            "feet": True,
            "face_blendshapes": ["blink", "happy", "sad", "surprised", "mouth_open"],
        },
        "garment_slots": list(GARMENT_SLOTS),
        "product_interaction": {
            "hand_grip_anchors": ["left_hand", "right_hand"],
            "adult_product_explanation": "age_gate_required",
        },
        "pipeline": ["turntable", "mesh", "retopology", "rig", "blendshapes", "vrm_export"],
    }
