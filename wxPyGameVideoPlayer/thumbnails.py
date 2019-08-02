import os
import skimage

import numpy as np

from np_utils import makeifnotexists

from . import cv2_utils

if os.system("ffmpeg -h") != 0:
    print("Warning: ffmpeg not found on system, fast thumbnail functions will work")


def thumbnail(im, max_shape):
    """Resize the image to at most N x N
    
    DEPRECATED -- VERY MEMORY INTENSIVE
    Use create_thumbnails_video_using_ffmpeg and
    thumbstrip_from_video_frames instead
    """
    scale = max_shape / max(im.shape[:2])
    new_shape = [int(scale * i) for i in im.shape[:2]]
    return skimage.transform.resize(im, new_shape)


def create_thumbnails_video_using_ffmpeg(filename, output_dir, max_shape):
    """Create a "thumbnail" version of each frame in a new video file.
    
    Make a system call to ffmpeg that creates a downsized version of
    the video that fits into a box of max_shape and preserves the
    original aspect ratio.
    
    Using ffmpeg is both faster and yeilds higher compression ratios
    than using OpenCV and saving frames using numpy.
    """
    makeifnotexists(output_dir)

    max_w, max_h = (
        max_shape if hasattr(max_shape, "__len__") else (max_shape, max_shape)
    )

    fn, ext = os.path.splitext(os.path.split(filename)[1])
    add = "_fit_to_{}_{}".format(max_w, max_h)
    output_filename = os.path.join(output_dir, fn + add + ext)

    cmd_template = (
        'ffmpeg -i "{}" -vf "scale={}:{}:force_original_aspect_ratio=decrease" "{}"'
    )
    cmd = cmd_template.format(filename, max_w, max_h, output_filename)
    if os.system(cmd) != 0:
        raise Exception("ffmpeg command failed creating file for {}".format(filename))

    return output_filename


def thumbstrip(arr, orientation="horizontal"):
    """Make a filmstrip from an array of images"""
    assert orientation in ["horizontal", "vertical"]

    arr_t = arr if orientation == "vertical" else arr.swapaxes(1, 2)
    s = arr_t.shape
    arr_strip = arr_t.reshape((s[0] * s[1],) + s[2:])

    return arr_strip if orientation == "vertical" else arr_strip.swapaxes(0, 1)


def thumbstrip_from_video_frames(filename, frame_numbers, orientation="horizontal"):
    """Create a thumbstrip by loading spcified frames from a video file
    """
    frame_rate = cv2_utils.get_frame_rate(filename)
    frames_arr = np.array(
        [
            cv2_utils.get_opencv_frame(filename, frame_number, frame_rate=frame_rate)[1]
            for frame_number in frame_numbers
        ]
    )
    return thumbstrip(frames_arr, orientation=orientation)


def image_grid(images_2d_grid):
    a = np.array(images_2d_grid)
    new_shape = (a.shape[0] * a.shape[2], a.shape[1] * a.shape[3]) + a.shape[4:]
    return a.swapaxes(1, 2).reshape(new_shape)


def thumb_grid_from_video_frames(filename, frame_numbers_grid):
    """Create a thumbstrip grid by loading specified frames from a video file
    """
    frame_rate = cv2_utils.get_frame_rate(filename)
    frames_arr = np.array(
        [
            [
                cv2_utils.get_opencv_frame(
                    filename, frame_number, frame_rate=frame_rate
                )[1]
                for frame_number in frame_numbers
            ]
            for frame_numbers in frame_numbers_grid
        ]
    )
    return image_grid(frames_arr)
