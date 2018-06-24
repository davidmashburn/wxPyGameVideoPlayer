from wxPyGameVideoPlayer.opencv_player import *

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

# Sample file to analyze:
f = os.path.expanduser('~/sciencecasts-_total_eclipse_of_the_moon.mp4')

if not os.path.exists(f):
    print('File not available, downloading to ' + f)
    url = 'http://www.nasa.gov/downloadable/videos/sciencecasts-_total_eclipse_of_the_moon.mp4'
    urlretrieve(url, f)
    print('Finished downloading')

test_video = f

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
dat.load_new_file(test_video)

# Start the pygame and wxPython threads
pygame_thread.start()
gui_app.MainLoop()
