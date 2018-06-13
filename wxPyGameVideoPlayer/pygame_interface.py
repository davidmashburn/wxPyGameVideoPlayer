'''Objects to handle threaded image drawing with Pygame'''

from __future__ import absolute_import

import sys
import time
import threading

if sys.version[0] == '2':
    import Queue as queue
else:
    import queue as queue

import numpy as np
import wx
import pygame

import attrdict

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

class PygameThread(threading.Thread):
    def __init__(self, gui_callback):
        threading.Thread.__init__(self)
        self.gui_callback = gui_callback
        self.queue = queue.Queue()
        self.setDaemon(True)

    def run(self):
        while True:
            qval = attrdict.AttrDict(self.queue.get(True))
            if qval.id_string == 'Stop':
                pass
            if qval.id_string == 'Start':
                print('reverse is', qval.reverse)
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
                    print('show frame', cur_frame)
                    
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
