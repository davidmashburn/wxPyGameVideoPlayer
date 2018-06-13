'''Basic funcitonal wxPython UI without any actually plotting'''

from __future__ import absolute_import
from __future__ import print_function

import wx
from functools import partial

from .wx_func_utils import (static_text, text_ctrl, check_box, button, static_box,
                            VSizer, HSizer, clip, AddMultiple, AddMultipleSplat)

class DummyDataInterface(object):
    def update(self):
        pass
    def play(self, start_frame, playback_speed, reverse=False, skip_frames=False):
        pass
    def stop(self):
        pass
    def load_new_file(self):
        pass
    def update_traces(self):
        pass
    def get_number_of_frames(self):
        return 50

SKIP_VALUE = 20

class PlaybackControlsFrameMixin(wx.Frame):
    '''A frame with a box for playback controls in a ready-made sizer :)
       But seriously, this expects subclasses to implement the following:
       Variables:
           
       Functions:
           update_data(self)
           get_last_frame(self)
           play(self, reverse=False)
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
                                    callback=partial(self.play, reverse=True))
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
                                  callback=partial(self.play, reverse=False))
        self.skip_to_end_button = button(self, '>|', min_size=(35, -1),
                                         tooltip='Go back one frame',
                                         callback=self.skip_to_end)

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
    def get_frame_number(self):
        return int(self.frame_number_textbox.GetValue())
    
    def set_frame_number_no_update(self, frame_number):
        new_frame_number = clip(int(frame_number), 0, self.get_last_frame())
        self.frame_number_textbox.SetValue(str(new_frame_number))
    
    def set_frame_number(self, frame_number):
        self.set_frame_number_no_update(frame_number)
        self.update_data()
    
    def get_playback_speed(self):
        return int(self.playback_speed_textbox.GetValue())
    
    def set_playback_speed(self, speed):
        self.playback_speed_textbox.SetValue(str(speed))

    def offset_frame_num(self, offset):
        frame_number = int(self.frame_number_textbox.GetValue()) + offset
        self.set_frame_number(frame_number)

    def skip_to_end(self): # Because you can only cheat so much :)
        return self.set_frame_number(self.get_last_frame())

class VideoPlayerFrame(PlaybackControlsFrameMixin):
    def __init__(self, *args, **kwds):
        self.traces_checkbox_names = kwds.pop('traces_checkbox_names', [])
        
        wx.Frame.__init__(self, *args, **kwds)
        
        self.SetTitle("Experiment Viewing GUI")
        self.SetSize((522, 572))
        
        self._build_file_controls()
        PlaybackControlsFrameMixin.__init__(self)
        self._build_update_traces()
        self._build_traces_checkboxes()
        
        self.main_sizer = AddMultipleSplat(wx.FlexGridSizer(6, 1, 0, 0),
                                           (self.file_controls_sizer, 1, wx.EXPAND, 0),
                                           ((20, 20), 0, 0, 0),
                                           (self.playback_controls_sizer, 1, 0, 0),
                                           ((20, 20), 0, 0, 0),
                                           (self.update_traces_sizer, 1, wx.EXPAND, 0),
                                           (self.trace_checkbox_sizer, 1, wx.EXPAND, 0),
                                          )
        self.main_sizer.AddGrowableCol(0)
        self.SetSizer(self.main_sizer)
        self.Layout()
        
        self.data = None # This is where the meat of everything actually
                         # happens with PyGame and matplotlib

    def _build_file_controls(self):
        self.file_controls_box = static_box(self, "File Controls")
        self.file_name_textbox = text_ctrl(self, "", min_size=(400, 21))
        self.load_new_file_button = button(self, "Load New File",
                                           tooltip="Load a new experiment data file to memory",
                                           callback=self.load_new_file)
        self.comments_label = static_text(self, "Comments:")
        self.comments_textbox = text_ctrl(self, "", min_size=(400, 100),
                                          style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        
        self.file_controls_grid_sizer = AddMultipleSplat(wx.FlexGridSizer(4, 1, 0, 0),
                                                         (self.file_name_textbox, 0, wx.EXPAND, 0),
                                                         (self.load_new_file_button, 1, 0, 0),
                                                         (self.comments_label, 0, 0, 0),
                                                         (self.comments_textbox, 0, 0, 0),
                                                        )
        self.file_controls_grid_sizer.AddGrowableCol(0)
        
        self.file_controls_sizer = AddMultipleSplat(wx.StaticBoxSizer(self.file_controls_box, wx.HORIZONTAL),
                                                    (self.file_controls_grid_sizer, 1, wx.EXPAND, 0),
                                                   )
    def _build_update_traces(self):
        self.update_traces_button = button(self, "Update Traces",
                                           callback=self.update_traces)
        self.update_traces_sizer = AddMultiple(HSizer(), (0, 0, 0),
                                               self.update_traces_button
                                              )
    def _build_traces_checkboxes(self):
        self.trace_checkboxes = [check_box(self, trace_name)
                                 for trace_name in self.traces_checkbox_names]
        self.trace_checkbox_sizer = AddMultiple(VSizer(), (0, 0, 0),
                                                *self.trace_checkboxes)

    def set_data(self, data_object):
        self.data = data_object
    
    def update_data(self):
        self.data.update()
    
    def get_last_frame(self):
        return self.data.get_number_of_frames() - 1
    
    def play(self, reverse=False):
        start_frame = self.get_frame_number()
        playback_speed = self.get_playback_speed()
        skip_frames = bool(self.skip_frames_checkbox.GetValue())
        self.data.play(start_frame, playback_speed=playback_speed, reverse=reverse, skip_frames=skip_frames)
    
    def stop(self):
        self.data.stop()
    
    def load_new_file(self):
        self.data.load_new_file()
    
    def update_traces(self):
        self.data.update_traces()

class DummyVideoApp(wx.App):
    def __init__(self, *args, **kwds):
        self.traces_checkbox_names = kwds.pop('traces_checkbox_names', [])
        wx.App.__init__(self, *args, **kwds)

    def OnInit(self):
        wx.InitAllImageHandlers()
        self.video_frame = VideoPlayerFrame(None, -1, "", traces_checkbox_names=self.traces_checkbox_names)
        self.video_frame.set_data(DummyDataInterface())
        self.video_frame.Move(wx.Point(wx.DisplaySize()[0] - self.video_frame.GetSize()[0] - 20, 20))
        self.SetTopWindow(self.video_frame)
        self.video_frame.Show()
        return 1

if __name__ == "__main__":
    app = DummyVideoApp(0, traces_checkbox_names=['that', 'this', 'those'])
    app.MainLoop()
