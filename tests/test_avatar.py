from avatar.avatar_2d import avatar_manifest
from avatar.avatar_3d import full_body_3d_manifest
from avatar.controller import AvatarController
from avatar.expressions import visual_state


def test_avatar_expression_mapping():
    assert visual_state("neutral") == "neutral"
    assert visual_state("happy") == "happy"
    assert visual_state("sad") == "neutral"
    assert visual_state("happy", speaking=True) == "speaking"


def test_avatar_controller_and_manifest():
    controller = AvatarController("/assets/avatar/test.png")
    assert controller.react("happy")["visual_state"] == "happy"
    assert controller.set_speaking(True)["visual_state"] == "speaking"
    assert controller.set_speaking(False)["visual_state"] == "happy"
    manifest = avatar_manifest(controller.sprite_url)
    assert manifest["grid"] == {"columns": 2, "rows": 2}
    assert set(manifest["states"]) == {"neutral", "blink", "speaking", "happy"}
    manifest_3d = full_body_3d_manifest()
    assert manifest_3d["body"] == "full_body"
    assert {"swimwear", "lingerie", "shoes"}.issubset(manifest_3d["garment_slots"])
    assert manifest_3d["rig"]["finger_bones"] is True
