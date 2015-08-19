import os
import time
import threading
import Queue

import attrdict
import numpy as np
import wx
import cv2
import pygame

import matplotlib
matplotlib.use('WxAgg')
matplotlib.interactive(False)
import matplotlib.pyplot as plt

from VideoPlayerGUI import VideoPlayerFrame

USE_MPL = False
USE_PYGAME = True

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

class PygamePlotObject(object):
    def __init__(self):
        pygame.init()
        self._set_screen_res((10, 10))
    
    def _set_screen_res(self, shape, scale=(1, 1)):
        self.shape = shape
        self.screen = pygame.display.set_mode((self.shape[0] * scale[0], self.shape[1] * scale[1]))
        self.scale_screen = pygame.surface.Surface(self.shape)
    
    def imshow(self, dat, scale=(1, 1), transpose=False):
        dat = np.asarray(dat, dtype=np.int32)
        dat = (np.transpose(dat, (1,0,2)) if transpose else dat)
        dat_shape = dat.shape[:2]
        if dat_shape != self.shape:
            self._set_screen_res(dat_shape, scale=(1, 1))
            pygame.display.set_caption('ImShow...with Pygame')
            black = 20, 20, 40
            self.screen.fill(black)
            self.scale_screen.fill(black)
        pygame.surfarray.blit_array(self.scale_screen, dat)
        temp = pygame.transform.scale(self.scale_screen, self.screen.get_size())
        self.screen.blit(temp, (0,0))
        pygame.display.update()
    
    def imshowT(self, dat, scale=(1, 1)):
        return self.imshow(dat, scale=scale, transpose=True)

PYGAME_INTERFACE = PygamePlotObject()

class PygameThread(threading.Thread):
    def __init__(self, gui_callback):
        threading.Thread.__init__(self)
        self.gui_callback = gui_callback
        self.queue = Queue.Queue()
        self.setDaemon(True)

    def run(self):
        while True:
            qval = attrdict.AttrDict(self.queue.get(True))
            if qval.id_string == 'Stop':
                pass
            if qval.id_string == 'Start':
                print 'reverse is', qval.reverse
                step, test = ((-1, lambda x: x > 0)
                              if qval.reverse else
                              (1, lambda x: x < qval.num_frames))
                
                start_wall_time = time.time()
                start_frame = qval.frame_num
                cur_frame = qval.frame_num
                while test(cur_frame):
                    t = time.time()
                    
                    if self.queue.qsize() > 0:
                        qval = attrdict.AttrDict(self.queue.get(True))
                    if qval.id_string == 'Stop':
                        break
                    
                    wx.CallAfter(self.gui_callback, cur_frame) # send the frame number back to the GUI to update
                    
                    qval.plot_function(cur_frame)
                    print 'show frame', cur_frame
                    
                    while time.time()<t+(1.0/qval.speed):
                        pass
                    
                    cur_frame = cur_frame + step
                    
                    if qval.skip_frames:
                        time_so_far = t - start_wall_time
                        frame_jump = start_frame + int(step * qval.speed * time_so_far)
                        if step * (frame_jump-cur_frame) > 0: # multiplying by step ensures you get positive numbers
                            cur_frame = frame_jump
    
    def putQueue(self,arg):
        self.queue.put_nowait(arg)

class OpenCVDataInterface(object):
    def __init__(self, gui_app, pygame_thread):
        self.gui_app = gui_app
        self.filename = None
        self._video_frame_rate = None
        self.num_frames = None
        self.pygame_thread = pygame_thread
    
    def plot(self, frame_num):
        self.frame_data = get_opencv_frame_as_array(self.filename, frame_num)
        if USE_MPL:
            plt.imshow(self.frame_data)
            plt.draw()
        if USE_PYGAME:
            PYGAME_INTERFACE.imshowT(self.frame_data)
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
        self._video_frame_rate = get_frame_rate(self.filename)
        self.get_number_of_frames(rebuild=True) # search for the number of frames
        self.frame = get_opencv_frame_as_array(self.filename, 0) # load the first frame
        self.gui_app.set_filename(self.filename)
        self.update()
    
    def update_traces(self):
        pass
    
    def get_number_of_frames(self, rebuild=False):
        if rebuild or self.num_frames is None:
            self.num_frames = binary_search_end(self.filename) + 1
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
    pygame_thread = PygameThread(gui_app.set_frame_number)
    pygame_thread.start()
    
    dat = OpenCVDataInterface(gui_app, pygame_thread)
    gui_app.video_frame.set_data(dat)
    #dat.load_new_file(test_video)
    gui_app.MainLoop()
    plt.show()
