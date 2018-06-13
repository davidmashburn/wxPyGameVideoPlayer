# coding: utf-8

from __future__ import print_function

import numpy as np
import cv2

try:
    import pydub
except ImportError:
    print('\n'.join(('Warning, pydub is not installed!',
                     '"mp4_to_array" cannot be used!')))

def get_msec_to_frame(frame_rate):
    '''Get the function to convert from frame time (ms) to frame number'''
    return lambda msec: msec * frame_rate / 1000.

def get_frame_to_msec(frame_rate):
    '''Get the function to convert from frame number to frame time (ms)'''
    return lambda frame_number: 1000. * frame_number / frame_rate

def get_frame_rate(video_file):
    '''Get the frame rate for a video file'''
    cap = cv2.VideoCapture(video_file)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return frame_rate

def get_opencv_position(cap, frame_rate=None):
    '''Get the frame position in the OpenCV video'''
    frame_time = cap.get(cv2.CAP_PROP_POS_MSEC)
    frame_rate = (frame_rate if frame_rate is not None else
                  cap.get(cv2.CAP_PROP_FPS))
    return get_msec_to_frame(frame_rate)(frame_time)

def set_opencv_position(cap, frame_number, frame_rate=None):
    '''Set the frame number in the OpenCV video.
       
       This is not as simple as it sounds and requires converting the
       frame number to a frame time.
       
       THIS WILL ONLY WORK ONE TIME FOR SOME REASON.
       After that it reverts to the original position!
       I assume this is some kind of OpenCV bug.'''
    frame_rate = (frame_rate if frame_rate is not None else
                  cap.get(cv2.CAP_PROP_FPS))
    frame_time = get_frame_to_msec(frame_rate)(frame_number)
    return cap.set(cv2.CAP_PROP_POS_MSEC, frame_time)

def get_opencv_frame(video_file, frame_number, frame_rate=None):
    '''Get a single frame from a video file using OpenCV'''
    cap = cv2.VideoCapture(video_file)
    set_opencv_position(cap, frame_number, frame_rate)
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
    return (np.array(frame)[:, :, ::-1] if ret else frame)

def mp4_to_array(f):
    '''Read audio straight from a movie file using pydub (and indirectly ffmpeg)
       Returns the frame rate and the actual array with shape (#frames, #channels)'''
    aud = pydub.AudioSegment.from_file(f)
    frame_rate = aud.frame_rate
    frame_count = aud.frame_count()
    new_shape = aud.frame_count(), aud.channels
    arr = np.frombuffer(aud._data, dtype=np.int16).reshape(new_shape)
    return frame_rate, arr
