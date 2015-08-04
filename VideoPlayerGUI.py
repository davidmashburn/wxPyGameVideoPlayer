#!/usr/bin/python
'''Just a really simple video player that uses OpenCV, wxPython, and PyGame
Options to load the video to memory or load frame-by-frame dynamically
Uses PyGame to acheive fast frame rendering
Display is embedded in a wxPython window so that it can support traditional GUI elements
'''

import os
import wx
import inspect
from functools import partial

import numpy as np
import pygame
import matplotlib
import cv2
# http://stackoverflow.com/questions/17754774/combine-pyside-and-pygame ??


def docAppend(newFun,oldFun):
    '''Append oldFun's docstring to the end of newFun's docstring
       Useful for quick documentation of functional modifications'''
    newFun.__doc__ = '\n'.join([ (oldFun.__doc__ if oldFun.__doc__ else ''),
                                 (newFun.__doc__ if newFun.__doc__ else ''), ])

def add_common_kwd_args(func):
    '''So far this includes:
           value=None
           min_size=None
           tooltip=None
           '''
    def func_wrapper(frame, *args, **kwds):
        '''Also has option value=None
           Also has option min_size=None
           Also has option tooltip=None'''
        value = kwds.pop('value', None)
        min_size = kwds.pop('min_size', None)
        tooltip = kwds.pop('tooltip', None)
        ctrl = func(frame, *args, **kwds)
        if value is not None:
            ctrl.SetValue(value)
        if min_size is not None:
            ctrl.SetMinSize(min_size)
        if tooltip is not None:
            ctrl.SetToolTipString(tooltip)
        return ctrl
    
    docAppend(func_wrapper, func)
    return func_wrapper

def make_callback(func):
    '''Adds an 'event' option to the function to make it a callback
       This allows functions that don't need event information to serve as callbacks'''
    def func_wrapper(event):
        return func()
    return func_wrapper

def add_callback_kwd_arg(event_type):
    def wrap(func):
        def func_wrapper(frame, *args, **kwds):
            ''''Also has option callback=None'''
            callback = kwds.pop('callback', None)
            ctrl = func(frame, *args, **kwds)
            if callback is not None:
                needs_arg = True
                print func.__name__
                if hasattr(callback, 'args'): # handle partials
                    print 'partial has %d args' % len(callback.args)
                    if len(callback.args)>1:
                        needs_arg = False
                else:
                    print callback.__name__+' has %d args' % len(inspect.getargspec(callback).args)
                    if len(inspect.getargspec(callback).args)>1: # handle normal functions
                        needs_arg = False
                
                if needs_arg:
                    print 'NEEDS ARG'
                    callback = make_callback(callback)
                frame.Bind(event_type, callback, ctrl)
            return ctrl
        docAppend(func_wrapper, func)
        return func_wrapper
    return wrap

@add_common_kwd_args
def static_text(frame, text, **kwds):
    return wx.StaticText(frame, -1, text, **kwds)

@add_common_kwd_args
@add_callback_kwd_arg(wx.EVT_TEXT_ENTER)
def text_ctrl(frame, text, **kwds):
    return wx.TextCtrl(frame, -1, text, **kwds)

@add_common_kwd_args
@add_callback_kwd_arg(wx.EVT_COMBOBOX)
def check_box(frame, text, **kwds):
    return wx.CheckBox(frame, -1, text, **kwds)

@add_common_kwd_args
@add_callback_kwd_arg(wx.EVT_BUTTON)
def button(frame, text, **kwds):
    return wx.Button(frame, -1, text, **kwds)

@add_common_kwd_args
def static_box(frame, text, **kwds):
    return wx.StaticBox(frame, -1, text, **kwds)

def VSizer():
    return wx.BoxSizer(wx.VERTICAL)

def HSizer():
    return wx.BoxSizer(wx.HORIZONTAL)

#def frame(title, size, *args, **kwds):
#    kwds['style'] = wx.DEFAULT_FRAME_STYLE
#    frame = wx.Frame(*args, **kwds)
#    self.SetTitle('Experiment Viewing GUI')
#    self.SetSize(size)

#def memberize(func, obj):
#    '''Decorator to add this function as a member to an object'''
#    obj.__dict__[func.__name__] = func
#    return func

def clip(x, lower=0, upper=None):
    if None not in [lower, upper]:
        assert lower<=upper, 'Upper must be greater than lower!'
    return (upper if x>upper else
            lower if x<lower else
            x)

def AddMultiple(x, func_args, *args):
    '''Call x.Add(i, *func_args) for each args given
       Return x'''
    for i in args:
        x.Add(i, *func_args)
    return x

def AddMultipleSplat(x, *args):
    '''Call x.Add(*i) for each args given
       Return x
       NOTE: each "arg" after x must be a tuple
       '''
    for i in args:
        x.Add(*i)
    return x

SKIP_VALUE = 20

class PlaybackControlsFrameMixin(wx.Frame):
    '''A frame with a box for playback controls in a ready-made sizer :)
       But seriously, this expects subclasses to implement the following:
       Variables:
           
       Functions:
           update_data(self)
           get_last_frame(self)
           play(self, reverse_direction=False)
           stop(self)
    '''
    def __init__(self):
        # Misc Controls:
        self.playback_controls_box = static_box(self, "Playback Controls")
        self.playback_speed_label = static_text(self, 'Playback Speed (Hz): ')
        self.playback_speed_textbox = text_ctrl(self, '50', min_size=(60, -1),
                                                callback=self.update_data)
        self.skip_frames_checkbox = check_box(self, 'SkipFrames?', value=1,
                                              tooltip='When checked, this skips frames to honor the playback speed',
                                              callback=self.update_data)

        self.frame_number_label = static_text(self, 'Frame Number:')
        self.frame_number_textbox = text_ctrl(self, '0', min_size=(60, -1),
                                              callback=self.update_data)

        # Playback buttons:
        self.skip_to_start_button = button(self, '|<', min_size=(35, -1),
                                           tooltip='Skip to the first frame',
                                           callback=partial(self.set_frame_number, 0))
        self.rewind_button = button(self, '<|', min_size=(35, -1),
                                    tooltip='Rewind',
                                    callback=partial(self.play, reverse_direction=True))
        self.jump_back_button = button(self, '-'+str(SKIP_VALUE), min_size=(15*(len(str(SKIP_VALUE))+1), -1),
                                       tooltip='Jump back {0} frames'.format(SKIP_VALUE),
                                       callback=partial(self.offset_frame_num, -SKIP_VALUE), )
        self.step_back_button = button(self, '<', min_size=(40, -1),
                                       tooltip='Go back one frame',
                                       callback=partial(self.offset_frame_num, -1))
        self.stop_button = button(self, '||', min_size=(25, -1),
                                  tooltip='Stop',
                                  callback=self.stop)
        self.step_forward_button = button(self, '>', min_size=(40, -1),
                                          tooltip='Go forward one frame',
                                          callback=partial(self.offset_frame_num, 1))
        self.jump_forward_button = button(self, '+'+str(SKIP_VALUE), min_size=(15*(len(str(SKIP_VALUE))+1), -1),
                                          tooltip='Jump forward {0} frames'.format(SKIP_VALUE),
                                          callback=partial(self.offset_frame_num, 10))
        self.play_button = button(self, '|>', min_size=(35, -1),
                                  tooltip='Go back one frame',
                                  callback=self.play)
        self.skip_to_end_button = button(self, '>|', min_size=(35, -1),
                                         tooltip='Go back one frame',
                                         callback=partial(self.set_frame_number, self.get_last_frame()))

        # Sizers
        self.playback_speed_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                           (75, 20),
                                           self.playback_speed_label,
                                           self.playback_speed_textbox,
                                           self.skip_frames_checkbox
                                          )
        self.play_controls_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                               (45, 20),
                                               self.skip_to_start_button,
                                               self.rewind_button,
                                               self.jump_back_button,
                                               self.step_back_button,
                                               self.stop_button,
                                               self.step_forward_button,
                                               self.jump_forward_button,
                                               self.play_button,
                                               self.skip_to_end_button
                                              )
        self.frame_num_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                           (43, 20),
                                           self.frame_number_label,
                                           (44, 20),
                                           self.frame_number_textbox
                                          )
        _pcs = wx.StaticBoxSizer(self.playback_controls_box, wx.VERTICAL)
        self.playback_controls_sizer = AddMultiple(_pcs, (1, wx.EXPAND, 0),
                                                   self.playback_speed_sizer,
                                                   self.play_controls_sizer,
                                                   self.frame_num_sizer
                                                  )
    def set_frame_number(self, frame_number):
        new_frame_number = clip(int(frame_number), 0, self.get_last_frame())
        self.frame_number_textbox.SetValue(str(new_frame_number))
        self.update_data()

    def offset_frame_num(self, offset):
        frame_number = int(self.frame_number_textbox.GetValue()) + offset
        self.set_frame_number(frame_number)


class VideoPlayerFrame(PlaybackControlsFrameMixin):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        
        self.SetTitle("Experiment Viewing GUI")
        self.SetSize((522, 572))
        
        self._build_file_controls()
        PlaybackControlsFrameMixin.__init__(self)
        self._build_update_traces()
        
        self.main_sizer = AddMultipleSplat(wx.FlexGridSizer(6, 1, 0, 0),
                                           (self.file_controls_sizer, 1, wx.EXPAND, 0),
                                           ((20, 20), 0, 0, 0),
                                           (self.playback_controls_sizer, 1, wx.EXPAND, 0),
                                           ((20, 20), 0, 0, 0),
                                           (self.update_traces_sizer, 1, wx.EXPAND, 0),
                                          )
        self.SetSizer(self.main_sizer)
        self.Layout()
        
        self.data = None # This is where the meat of everything actually
                         # happens with PyGame and matplotlib

    def _build_file_controls(self):
        self.file_controls_box = static_box(self, "File Controls")
        self.load_new_file_button = button(self, "Load New File",
                                           tooltip="Load a new experiment data file to memory",
                                           callback=self.load_new_file)
        self.load_whole_movie_checkbox = check_box(self, "LoadWholeMovie?")
        self.file_name_textbox = text_ctrl(self, "", min_size=(400, 21))
        self.comments_label = static_text(self, "Comments:")
        self.comments_textbox = text_ctrl(self, "", min_size=(400, 100),
                                          style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        
        self.load_new_file_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                               self.load_new_file_button,
                                               (20, 20),
                                               self.load_whole_movie_checkbox,
                                              )
        self.file_controls_grid_sizer = AddMultipleSplat(wx.FlexGridSizer(4, 1, 0, 0),
                                                        (self.load_new_file_sizer, 1, wx.EXPAND, 0),
                                                        (self.file_name_textbox, 0, wx.EXPAND, 0),
                                                        (self.comments_label, 0, 0, 0),
                                                        (self.comments_textbox, 0, 0, 0),
                                                       )
        
        self.file_controls_sizer = AddMultipleSplat(wx.StaticBoxSizer(self.file_controls_box, wx.HORIZONTAL),
                                                    (self.file_controls_grid_sizer, 1, wx.EXPAND, 0),
                                                   )
    def _build_update_traces(self):
        self.update_traces_button = button(self, "Update Traces",
                                           callback=self.update_traces)
        self.update_traces_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                               self.update_traces_button
                                              )
    def set_data(self, data_object):
        pass#self.data = data_object
    def update_data(self):
        pass#self.data.
    def get_last_frame(self):
        # FOR TESTING
        return 10 #pass#self.data.
    def play(self, reverse_direction=False):
        pass#self.data.
    def stop(self):
        pass#self.data.
    def load_new_file(self):
        pass#self.data.
    def update_traces(self):
        pass#self.data.

class VideoApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.video_frame = VideoPlayerFrame(None, -1, "")
        self.video_frame.Move(wx.Point(wx.DisplaySize()[0] - self.video_frame.GetSize()[0] - 20, 20))
        self.SetTopWindow(self.video_frame)
        self.video_frame.Show()
        return 1

if __name__ == "__main__":
    app = VideoApp(0)
    app.MainLoop()
