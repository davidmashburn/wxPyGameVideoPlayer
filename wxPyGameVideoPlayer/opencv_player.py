'''Just a really simple video player that uses OpenCV, wxPython, and PyGame

Uses OpenCV to load frames from the video file
Uses PyGame (in a non-blocking thread) to acheive fast frame rendering
and matplotlib for plotting metrics
A separate wxPython window handles the GUI events

This is forked from a previous project, ca. 4/2007
'''

from __future__ import absolute_import
from __future__ import print_function

import os
import time
import numpy as np
import wx
import matplotlib
matplotlib.use('WxAgg')
matplotlib.interactive(False)
import matplotlib.pyplot as plt

from .wx_video_ui import VideoPlayerFrame
from . import cv2_utils
from . import pygame_interface

from mpl_utils import plotting_decorator, plot_or_update

class OpenCVDataInterface(object):
    gui_app = None
    filename = None
    _video_frame_rate = None
    num_frames = None
    pygame_plot_object = None
    pygame_thread = None
    mpl_image = None
    time_line = None
    mpl_static_plots_fig = None
    mpl_time_plots_fig = None
    mpl_image_fig = None
    use_mpl = True
    use_pygame = True
    _lock_finished_time = None # Ready to go: use -1 for totally locked
                               #              use a timestamp for temporary locking
    
    def __init__(self, gui_app, use_mpl=True, use_pygame=True):
        self.gui_app = gui_app
        self.use_mpl = use_mpl
        self.use_pygame = use_pygame
    
    def link_pygame(self, pygame_plot_object, pygame_thread):
        self.pygame_plot_object = pygame_plot_object
        self.pygame_thread = pygame_thread
        
    def set_figures(self, mpl_static_plots_fig=None,
                          mpl_time_plots_fig=None,
                          mpl_image_fig=None):
        plt.ion()
        self.mpl_static_plots_fig = (plt.figure(1)
                                     if mpl_static_plots_fig is None else
                                     mpl_static_plots_fig)
        self.mpl_time_plots_fig = (plt.figure(2)
                                   if mpl_time_plots_fig is None else
                                   mpl_time_plots_fig)
        self.mpl_image_fig = (None if not self.use_mpl else
                              plt.figure(3) if mpl_image_fig is None
                              else mpl_image_fig)
        plt.ioff()
    
    @plotting_decorator(draw=True)
    def mpl_imshow(self, *args, **kwds):
        self.mpl_image = plot_or_update(self.mpl_image, plt.imshow, *args, **kwds)
    
    @plotting_decorator(draw=True)
    def _update_vline(self, frame_num=None):
        x = self.get_frame_time(frame_num)
        self.time_line = plot_or_update(self.time_line, plt.axvline, x, color='k')
    
    def update_vline(self, frame_num=None, rebuild=False):
        if rebuild:
            self.time_line = None
        self._update_vline(frame_num=frame_num,
                           figure=self.mpl_time_plots_fig)
    
    @plotting_decorator(draw=False, cla=True)
    def _update_traces(self):
        if self.filename:
            time_axis = np.arange(self.num_frames) / self._video_frame_rate
            plt.plot(time_axis, time_axis) # stand-in plot for real traces
        self.update_vline(rebuild=True) # rebuild this since we are running cla
                                        # also, this calls draw, so no need to do it twice
    
    def update_traces(self):
        self._update_traces(figure=self.mpl_time_plots_fig)
    
    def plot_frame(self, frame_num, use_mpl=False):
        self.frame_data = cv2_utils.get_opencv_frame_as_array(self.filename, frame_num)
        
        if use_mpl:
            self.mpl_imshow(self.frame_data, figure=self.mpl_image_fig)
        
        if self.use_pygame:
            self.pygame_plot_object.imshowT(self.frame_data)
        
        

    def update(self):
        '''Called when switching frames or hitting pause'''
        frame_num = self.get_frame_number()
        self.plot_frame(frame_num, use_mpl=self.use_mpl)
        self.update_vline()
    
    def play(self, start_frame, playback_speed, reverse=False, skip_frames=False):
        if self.use_pygame:
            self.pygame_thread.putQueue(dict(
                id_string='Start',
                skip_frames=skip_frames,
                speed=playback_speed,
                frame_num=start_frame,
                num_frames=self.get_number_of_frames(),
                reverse=reverse,
                filename=self.filename,
                plot_function=self.plot_frame
            ))
    
    def stop(self):
        if self.use_pygame:
            self.pygame_thread.putQueue({'id_string': 'Stop'})
        self.update()
    
    def load_new_file(self, filename=None):
        filename = wx.FileSelector('Choose a video file') if filename is None else filename
        print(filename)
        if filename == self.filename:    # already loaded
            return
        if not os.path.exists(filename): # file does not exist
            return
        
        self.filename = filename
        self.mpl_image = None
        self._video_frame_rate = cv2_utils.get_frame_rate(self.filename)
        self.get_number_of_frames(rebuild=True) # search for the number of frames
        self.frame = cv2_utils.get_opencv_frame_as_array(self.filename, 0) # load the first frame
        self.gui_app.set_filename(self.filename)
        self.update()
    
    def get_number_of_frames(self, rebuild=False):
        if rebuild or self.num_frames is None:
            self.num_frames = int(cv2_utils.binary_search_end(self.filename) + 1)
        return self.num_frames
    
    def get_frame_number(self):
        frame_num = int(self.gui_app.video_frame.get_frame_number())
        return frame_num
    
    def get_frame_time(self, frame_num=None):
        frame_num = (frame_num if frame_num is not None else
                     self.get_frame_number())
        return frame_num / self._video_frame_rate
    
    def pygame_callback(self, frame_number):
        '''Everything to run during the pygame thread updating'''
        self.gui_app.video_frame.set_frame_number_no_update(frame_number)
        
        # Skip if the draw is in progress or it is less than 10 ms after the last draw finished
        # This allows the wxPython GUI time in the thread to respond
        # (tests to run matplotlib in a separate thread totally flopped)
        WAIT_TIME = 0.01
        
        # If the timer is up, release the lock
        if (self._lock_finished_time is not None and
            self._lock_finished_time + WAIT_TIME < time.time()):
            self._lock_finished_time = None
        
        if self._lock_finished_time is None:
            self._lock_finished_time = -1
            self.update_vline(frame_number)
            self._lock_finished_time = time.time()

class VideoApp(wx.App):
    def __init__(self, *args, **kwds):
        self.traces_checkbox_names = kwds.pop('traces_checkbox_names', [])
        wx.App.__init__(self, *args, **kwds)

    def OnInit(self):
        wx.InitAllImageHandlers()
        self.video_frame = VideoPlayerFrame(None, -1, "", traces_checkbox_names=self.traces_checkbox_names)
        self.video_frame.Move(wx.Point(wx.DisplaySize()[0] - self.video_frame.GetSize()[0] - 20, 20))
        self.SetTopWindow(self.video_frame)
        self.video_frame.Show()
        return 1

    def set_filename(self, filename):
        self.video_frame.file_name_textbox.SetValue(filename)

    def get_frame_number(self):
        return self.video_frame.get_frame_number()

if __name__ == "__main__":
    #test_video = ''
    
    # Build all the interfaces
    gui_app = VideoApp(0)
    dat = OpenCVDataInterface(gui_app)
    pygame_plot_object = pygame_interface.PygamePlotObject()
    pygame_thread = pygame_interface.PygameThread(dat.pygame_callback)
    
    # Do the other hook-ups
    dat.set_figures()
    dat.link_pygame(pygame_plot_object, pygame_thread)
    gui_app.video_frame.set_data(dat)
    
    # Load a sample file
    #dat.load_new_file(test_video)
    
    # Start the pygame and wxPython threads
    pygame_thread.start()
    gui_app.MainLoop()
