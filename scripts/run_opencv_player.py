from wxPyGameVideoPlayer.opencv_player import *

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
