"""Repara apenas buracos transparentes fechados no sprite segmentado."""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "avatar" / "luna_sprite_source_v1.png"
SEGMENTED = ROOT / "assets" / "avatar" / "luna_sprite_v1.png"
OUTPUT = ROOT / "assets" / "avatar" / "luna_sprite_v1_1.png"


def repair_alpha_holes(source_path: Path, segmented_path: Path, output_path: Path) -> None:
    source = np.asarray(Image.open(source_path).convert("RGBA")).copy()
    segmented = np.asarray(Image.open(segmented_path).convert("RGBA")).copy()
    height, width = segmented.shape[:2]

    for y0, y1 in ((0, height // 2), (height // 2, height)):
        for x0, x1 in ((0, width // 2), (width // 2, width)):
            alpha = segmented[y0:y1, x0:x1, 3]
            foreground = alpha > 16
            holes = binary_fill_holes(foreground) & ~foreground
            region = segmented[y0:y1, x0:x1]
            source_region = source[y0:y1, x0:x1]
            region[holes, :3] = source_region[holes, :3]
            region[holes, 3] = 255

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(segmented, mode="RGBA").save(output_path)


if __name__ == "__main__":
    repair_alpha_holes(SOURCE, SEGMENTED, OUTPUT)
