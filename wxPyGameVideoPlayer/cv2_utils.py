'''Utilities for loading specific frames from videos using OpenCV'''

import numpy as np
import cv2

def get_msec_to_frame(frame_rate):
    '''Get the function to convert from frame time (ms) to frame number'''
    return lambda msec: msec * frame_rate / 1000.

def get_frame_to_msec(frame_rate):
    '''Get the function to convert from frame number to frame time (ms)'''
    return lambda frame_number: 1000. * frame_number / frame_rate

def get_frame_rate(video_file):
    cap = cv2.VideoCapture(video_file)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return frame_rate

def get_opencv_frame(video_file, frame_number, frame_rate=None):
    '''Get a single frame from a video file using OpenCV
       This is not as simple as it sounds and requires converting the
       frame number to a frame time.'''
    cap = cv2.VideoCapture(video_file)
    frame_rate = (frame_rate if frame_rate is not None else
                  cap.get(cv2.CAP_PROP_FPS))
    frame_time = get_frame_to_msec(frame_rate)(frame_number)
    cap.set(cv2.CAP_PROP_POS_MSEC, frame_time)
    ret, frame = cap.read()
    cap.release()
    return ret, frame

def binary_search_end(video_file, max_time=2**22, n_extra = 2):
    '''Find the last frame number that returns a valid frame
       The maximum possible length is 18 hours at 60 fps.
       Yes, it's overkill. Whatever.'''
    bottom, top = 0, max_time
    max_iters = int(np.ceil(np.log(max_time)/np.log(2))) + n_extra
    frame_rate = get_frame_rate(video_file)
    for ms in range(max_iters):
        middle = (bottom + top) / 2
        ret, _ = get_opencv_frame(video_file, middle, frame_rate) # Do a frame grab at the middle
        bottom, top = ((middle, top) if ret else
                       (bottom, middle))
    return bottom

def get_opencv_frame_as_array(video_file, frame_number, frame_rate=None):
    '''If this is a valid frame, return it as a numpy array'''
    ret, frame = get_opencv_frame(video_file, frame_number,
                                  frame_rate=frame_rate)
    return (np.array(frame) if ret else frame)
