import numpy as np

def centroid(box):
    """
    Calculate the center point of a bounding box.

    Input:
        box = [x1, y1, x2, y2]

    Returns:
        (cx, cy)
    """

    x1, y1, x2, y2 = box

    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)

    return (cx, cy)