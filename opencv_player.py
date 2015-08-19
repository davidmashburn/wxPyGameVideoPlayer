'''Just a really simple video player that uses OpenCV, wxPython, and PyGame

Uses OpenCV to load frames from the video file
Uses PyGame (in a non-blocking thread) to acheive fast frame rendering
and matplotlib for plotting metrics
A separate wxPython window handles the GUI events

This is forked from a previous project, ca. 4/2007
'''

import os
import time
import threading
import Queue

import attrdict
import numpy as np
import wx
import pygame

import matplotlib
matplotlib.use('WxAgg')
matplotlib.interactive(False)
import matplotlib.pyplot as plt

from wx_video_ui import VideoPlayerFrame

USE_MPL = False
USE_PYGAME = True

import cv2_utils
import pygame_interface

class OpenCVDataInterface(object):
    def __init__(self, gui_app, pygame_plot_object, pygame_thread):
        self.gui_app = gui_app
        self.filename = None
        self._video_frame_rate = None
        self.num_frames = None
        self.pygame_plot_object = pygame_plot_object
        self.pygame_thread = pygame_thread
    
    def plot(self, frame_num):
        self.frame_data = cv2_utils.get_opencv_frame_as_array(self.filename, frame_num)
        if USE_MPL:
            plt.imshow(self.frame_data)
            plt.draw()
        if USE_PYGAME:
            pygame_plot_object.imshowT(self.frame_data)
    def update(self):
        frame_num = self.gui_app.get_frame_number()
        self.plot(frame_num)
    
    def play(self, start_frame, playback_speed, reverse=False, skip_frames=False):
        if USE_PYGAME:
            self.pygame_thread.putQueue(dict(
                id_string='Start',
                skip_frames=skip_frames,
                speed=playback_speed,
                frame_num=start_frame,
                num_frames=self.get_number_of_frames(),
                reverse=reverse,
                filename=self.filename,
                plot_function=self.plot
            ))
    
    def stop(self):
        if USE_PYGAME:
            self.pygame_thread.putQueue({'id_string': 'Stop'})
    
    def load_new_file(self, filename=None):
        filename = wx.FileSelector() if filename is None else filename
        print filename
        if filename == self.filename:    # already loaded
            return
        if not os.path.exists(filename): # file does not exist
            return
        
        self.filename = filename
        self._video_frame_rate = cv2_utils.get_frame_rate(self.filename)
        self.get_number_of_frames(rebuild=True) # search for the number of frames
        self.frame = cv2_utils.get_opencv_frame_as_array(self.filename, 0) # load the first frame
        self.gui_app.set_filename(self.filename)
        self.update()
    
    def update_traces(self):
        pass
    
    def get_number_of_frames(self, rebuild=False):
        if rebuild or self.num_frames is None:
            self.num_frames = cv2_utils.binary_search_end(self.filename) + 1
        return self.num_frames

class VideoApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.video_frame = VideoPlayerFrame(None, -1, "")
        self.video_frame.Move(wx.Point(wx.DisplaySize()[0] - self.video_frame.GetSize()[0] - 20, 20))
        self.SetTopWindow(self.video_frame)
        self.video_frame.Show()
        return 1

    def set_filename(self, filename):
        self.video_frame.file_name_textbox.SetValue(filename)
    
    def get_frame_number(self):
        return self.video_frame.get_frame_number()
    
    def set_frame_number(self, i):
        return self.video_frame.set_frame_number(i)

if __name__ == "__main__":
    #test_video = ''
    
    image_fig = plt.figure(1)
    plot_fig = plt.figure(2)
    
    gui_app = VideoApp(0)
    pygame_plot_object = pygame_interface.PygamePlotObject()
    pygame_thread = pygame_interface.PygameThread(gui_app.set_frame_number)
    pygame_thread.start()
    
    dat = OpenCVDataInterface(gui_app, pygame_plot_object, pygame_thread)
    gui_app.video_frame.set_data(dat)
    #dat.load_new_file(test_video)
    gui_app.MainLoop()
    plt.show()
