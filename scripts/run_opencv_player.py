from wxPyGameVideoPlayer.opencv_player import *

# Build all the interfaces
gui_app = VideoApp(0)
dat = OpenCVDataInterface(gui_app)
pygame_plot_object = pygame_interface.PygamePlotObject()
pygame_thread = pygame_interface.PygameThread(dat.pygame_callback)

# Do the other hook-ups
dat.set_figures()
dat.link_pygame(pygame_plot_object, pygame_thread)
gui_app.video_frame.set_data(dat)

# Start the pygame and wxPython threads
pygame_thread.start()
gui_app.MainLoop()
