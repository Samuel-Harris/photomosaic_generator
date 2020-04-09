import numpy as np


def MSE_match_images(target_tile, input_image):
    return -abs(np.linalg.norm(target_tile - input_image))
