SPRITE_STATES = {
    "neutral": {"column": 0, "row": 0},
    "blink": {"column": 1, "row": 0},
    "speaking": {"column": 0, "row": 1},
    "happy": {"column": 1, "row": 1},
}


def avatar_manifest(sprite_url: str) -> dict:
    return {
        "type": "2d_sprite",
        "version": "1.1",
        "sprite_url": sprite_url,
        "grid": {"columns": 2, "rows": 2},
        "states": SPRITE_STATES,
        "ai_generated": True,
    }
