'''Some functional utilities to make working with wxPython less verbose and easier to read'''

from __future__ import print_function

import inspect
import wx

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
            ctrl.SetToolTip(tooltip)
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
                if hasattr(callback, 'args'): # handle partials
                    # print('partial has %d args' % len(callback.args))
                    if len(callback.args)>1:
                        needs_arg = False
                else:
                    # print(callback.__name__+' has %d args' % len(inspect.getargspec(callback).args))
                    if len(inspect.getargspec(callback).args)>1: # handle normal functions
                        needs_arg = False
                
                if needs_arg:
                    #print('NEEDS ARG')
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

@add_common_kwd_args
@add_callback_kwd_arg(wx.EVT_SLIDER)
def slider(frame, *args, **kwds):
    return wx.Slider(frame, -1, *args, **kwds)


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
