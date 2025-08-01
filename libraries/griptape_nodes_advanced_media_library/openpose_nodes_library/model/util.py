import math
from typing import Any

import cv2  # type: ignore[reportMissingImports]
import matplotlib as mpl  # type: ignore[reportMissingImports]
import matplotlib.pyplot as plt  # type: ignore[reportMissingImports]
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas  # type: ignore[reportMissingImports]
from matplotlib.figure import Figure  # type: ignore[reportMissingImports]


def padRightDownCorner(img: np.ndarray, stride: int, pad_value: int) -> tuple[np.ndarray, list[int]]:
    """Pad image to right and down corner."""
    h = img.shape[0]
    w = img.shape[1]

    pad: list[int] = [0, 0, 0, 0]
    pad[0] = 0  # up
    pad[1] = 0  # left
    pad[2] = 0 if (h % stride == 0) else stride - (h % stride)  # down
    pad[3] = 0 if (w % stride == 0) else stride - (w % stride)  # right

    img_padded = img
    pad_up = np.tile(img_padded[0:1, :, :] * 0 + pad_value, (pad[0], 1, 1))
    img_padded = np.concatenate((pad_up, img_padded), axis=0)
    pad_left = np.tile(img_padded[:, 0:1, :] * 0 + pad_value, (1, pad[1], 1))
    img_padded = np.concatenate((pad_left, img_padded), axis=1)
    pad_down = np.tile(img_padded[-2:-1, :, :] * 0 + pad_value, (pad[2], 1, 1))
    img_padded = np.concatenate((img_padded, pad_down), axis=0)
    pad_right = np.tile(img_padded[:, -2:-1, :] * 0 + pad_value, (1, pad[3], 1))
    img_padded = np.concatenate((img_padded, pad_right), axis=1)

    return img_padded, pad


# transfer caffe model to pytorch which will match the layer name
def transfer(model: Any, model_weights: dict[str, Any]) -> dict[str, Any]:
    """Transfer caffe model to pytorch which will match the layer name."""
    transferred_model_weights = {}
    body25_split_threshold = 4
    for weights_name in model.state_dict():
        if len(weights_name.split(".")) > body25_split_threshold:  # body25
            transferred_model_weights[weights_name] = model_weights[".".join(weights_name.split(".")[3:])]
        else:
            transferred_model_weights[weights_name] = model_weights[".".join(weights_name.split(".")[1:])]
    return transferred_model_weights


# draw the body keypoint and lims
def draw_bodypose(
    canvas: np.ndarray, candidate: np.ndarray, subset: np.ndarray, model_type: str = "coco"
) -> np.ndarray:
    """Draw the body keypoint and limbs."""
    stick_width = 4
    stickwidth = stick_width
    if model_type == "body25":
        limb_seq = [
            [1, 0],
            [1, 2],
            [2, 3],
            [3, 4],
            [1, 5],
            [5, 6],
            [6, 7],
            [1, 8],
            [8, 9],
            [9, 10],
            [10, 11],
            [8, 12],
            [12, 13],
            [13, 14],
            [0, 15],
            [0, 16],
            [15, 17],
            [16, 18],
            [11, 24],
            [11, 22],
            [14, 21],
            [14, 19],
            [22, 23],
            [19, 20],
        ]
        njoint = 25
    else:
        limb_seq = [
            [1, 2],
            [1, 5],
            [2, 3],
            [3, 4],
            [5, 6],
            [6, 7],
            [1, 8],
            [8, 9],
            [9, 10],
            [1, 11],
            [11, 12],
            [12, 13],
            [1, 0],
            [0, 14],
            [14, 16],
            [0, 15],
            [15, 17],
            [2, 16],
            [5, 17],
        ]
        njoint = 18

    colors = [
        [255, 0, 0],
        [255, 85, 0],
        [255, 170, 0],
        [255, 255, 0],
        [170, 255, 0],
        [85, 255, 0],
        [0, 255, 0],
        [0, 255, 85],
        [0, 255, 170],
        [0, 255, 255],
        [0, 170, 255],
        [0, 85, 255],
        [0, 0, 255],
        [85, 0, 255],
        [170, 0, 255],
        [255, 0, 255],
        [255, 0, 170],
        [255, 0, 85],
        [255, 255, 0],
        [255, 255, 85],
        [255, 255, 170],
        [255, 255, 255],
        [170, 255, 255],
        [85, 255, 255],
        [0, 255, 255],
    ]

    for i in range(njoint):
        for n in range(len(subset)):
            index = int(subset[n][i])
            if index == -1:
                continue
            x, y = candidate[index][0:2]
            cv2.circle(canvas, (int(x), int(y)), 4, colors[i], thickness=-1)
    for i in range(njoint - 1):
        for n in range(len(subset)):
            index = subset[n][np.array(limb_seq[i])]
            if -1 in index:
                continue
            cur_canvas = canvas.copy()
            y_coords = candidate[index.astype(int), 0]
            x_coords = candidate[index.astype(int), 1]
            m_x = np.mean(x_coords)
            m_y = np.mean(y_coords)
            length = ((x_coords[0] - x_coords[1]) ** 2 + (y_coords[0] - y_coords[1]) ** 2) ** 0.5
            angle = math.degrees(math.atan2(x_coords[0] - x_coords[1], y_coords[0] - y_coords[1]))
            polygon = cv2.ellipse2Poly((int(m_y), int(m_x)), (int(length / 2), stickwidth), int(angle), 0, 360, 1)
            cv2.fillConvexPoly(cur_canvas, polygon, colors[i])
            canvas = cv2.addWeighted(canvas, 0.4, cur_canvas, 0.6, 0)
    return canvas


def draw_handpose(canvas: np.ndarray, all_hand_peaks: list[Any], *, show_number: bool = False) -> np.ndarray:
    """Draw hand pose."""
    edges = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 4],
        [0, 5],
        [5, 6],
        [6, 7],
        [7, 8],
        [0, 9],
        [9, 10],
        [10, 11],
        [11, 12],
        [0, 13],
        [13, 14],
        [14, 15],
        [15, 16],
        [0, 17],
        [17, 18],
        [18, 19],
        [19, 20],
    ]
    fig = Figure(figsize=plt.figaspect(canvas))

    fig.subplots_adjust(0, 0, 1, 1)
    fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
    bg = FigureCanvas(fig)
    ax = fig.subplots()
    ax.axis("off")
    ax.imshow(canvas)

    width, height = ax.figure.get_size_inches() * ax.figure.get_dpi()

    for peaks in all_hand_peaks:
        for ie, e in enumerate(edges):
            if np.sum(np.all(peaks[e], axis=1) == 0) == 0:
                x1, y1 = peaks[e[0]]
                x2, y2 = peaks[e[1]]
                ax.plot([x1, x2], [y1, y2], color=mpl.colors.hsv_to_rgb([ie / float(len(edges)), 1.0, 1.0]))

        for i, keyponit in enumerate(peaks):
            x, y = keyponit
            ax.plot(x, y, "r.")
            if show_number:
                ax.text(x, y, str(i))
    bg.draw()
    canvas = np.frombuffer(bg.buffer_rgba(), dtype="uint8").reshape(int(height), int(width), 4)[:, :, :3]
    return canvas


# image drawn by opencv is not good.
def draw_handpose_by_opencv(canvas: np.ndarray, peaks: np.ndarray, *, show_number: bool = False) -> np.ndarray:
    """Draw hand pose by OpenCV (image quality is not good)."""
    edges = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 4],
        [0, 5],
        [5, 6],
        [6, 7],
        [7, 8],
        [0, 9],
        [9, 10],
        [10, 11],
        [11, 12],
        [0, 13],
        [13, 14],
        [14, 15],
        [15, 16],
        [0, 17],
        [17, 18],
        [18, 19],
        [19, 20],
    ]
    for ie, e in enumerate(edges):
        if np.sum(np.all(peaks[e], axis=1) == 0) == 0:
            x1, y1 = peaks[e[0]]
            x2, y2 = peaks[e[1]]
            cv2.line(
                canvas,
                (x1, y1),
                (x2, y2),
                mpl.colors.hsv_to_rgb([ie / float(len(edges)), 1.0, 1.0]) * 255,
                thickness=2,
            )

    for i, keyponit in enumerate(peaks):
        x, y = keyponit
        cv2.circle(canvas, (x, y), 4, (0, 0, 255), thickness=-1)
        if show_number:
            cv2.putText(canvas, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), lineType=cv2.LINE_AA)
    return canvas


# detect hand according to body pose keypoints
# please refer to https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/src/openpose/hand/handDetector.cpp
def handDetect(candidate: np.ndarray, subset: np.ndarray, ori_img: np.ndarray) -> list[list[int | bool]]:
    """Detect hand according to body pose keypoints."""
    # right hand: wrist 4, elbow 3, shoulder 2
    # left hand: wrist 7, elbow 6, shoulder 5
    ratio_wrist_elbow = 0.33
    detect_result = []
    image_height, image_width = ori_img.shape[0:2]
    for person in subset.astype(int):
        # if any of three not detected
        has_left = np.sum(person[[5, 6, 7]] == -1) == 0
        has_right = np.sum(person[[2, 3, 4]] == -1) == 0
        if not (has_left or has_right):
            continue
        hands = []
        # left hand
        if has_left:
            left_shoulder_index, left_elbow_index, left_wrist_index = person[[5, 6, 7]]
            x1, y1 = candidate[left_shoulder_index][:2]
            x2, y2 = candidate[left_elbow_index][:2]
            x3, y3 = candidate[left_wrist_index][:2]
            hands.append([x1, y1, x2, y2, x3, y3, True])
        # right hand
        if has_right:
            right_shoulder_index, right_elbow_index, right_wrist_index = person[[2, 3, 4]]
            x1, y1 = candidate[right_shoulder_index][:2]
            x2, y2 = candidate[right_elbow_index][:2]
            x3, y3 = candidate[right_wrist_index][:2]
            hands.append([x1, y1, x2, y2, x3, y3, False])

        for x1, y1, x2, y2, x3, y3, is_left in hands:
            x = x3 + ratio_wrist_elbow * (x3 - x2)
            y = y3 + ratio_wrist_elbow * (y3 - y2)
            distance_wrist_elbow = math.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2)
            distance_elbow_shoulder = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            width = 1.5 * max(distance_wrist_elbow, 0.9 * distance_elbow_shoulder)
            # x-y refers to the center --> offset to topLeft point
            # handRectangle.x -= handRectangle.width / 2.f;
            # handRectangle.y -= handRectangle.height / 2.f;
            x -= width / 2
            y -= width / 2  # width = height
            # overflow the image
            x = max(x, 0)
            y = max(y, 0)
            width1 = width
            width2 = width
            if x + width > image_width:
                width1 = image_width - x
            if y + width > image_height:
                width2 = image_height - y
            width = min(width1, width2)
            # the max hand box value is 20 pixels
            min_hand_box_size = 20
            if width >= min_hand_box_size:
                detect_result.append([int(x), int(y), int(width), is_left])

    """
    return value: [[x, y, w, True if left hand else False]].
    width=height since the network require squared input.
    x, y is the coordinate of top left
    """
    return detect_result


# get max index of 2d array
def npmax(array: np.ndarray) -> tuple[int, float]:
    """Get max index of 2d array."""
    arrayindex = array.argmax(1)
    arrayvalue = array.max(1)
    i = arrayvalue.argmax()
    j = arrayindex[i]
    return i, j
