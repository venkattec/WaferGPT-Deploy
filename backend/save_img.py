import os
import numpy as np
from PIL import Image
from matplotlib import cm
from pathlib import Path


def cnv(npyy):
    # Load the wafer map
    wafer_map = np.load(Path(npyy))

    # Normalize the wafer map values to [0, 255]
    wafer_map_normalized = (255 * (wafer_map - wafer_map.min()) / (wafer_map.max() - wafer_map.min())).astype(np.uint8)

    # Apply a color map (e.g., 'viridis')
    color_mapped_wafer = cm.viridis(wafer_map_normalized / 255)  # Map values to [0, 1] for color map
    color_mapped_wafer = (color_mapped_wafer[:, :, :3] * 255).astype(np.uint8)  # Remove alpha channel and scale to [0, 255]

    # Convert to an image and enlarge
    wafer_map_image = Image.fromarray(color_mapped_wafer)
    new_size = (wafer_map_image.width * 10, wafer_map_image.height * 10)
    wafer_map_image_enlarged = wafer_map_image.resize(new_size, Image.NEAREST)

    # Save the color image
    wafer_map_image_enlarged.save("output/output.png")

    return "output/output.png"