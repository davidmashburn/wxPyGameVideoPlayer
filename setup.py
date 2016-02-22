from distutils.core import setup

# Read the version number
with open("wxPyGameVideoPlayer/_version.py") as f:
    exec(f.read())

setup(
    name='wxPyGameVideoPlayer',
    version=__version__, # use the same version that's in _version.py
    author='David N. Mashburn',
    author_email='david.n.mashburn@gmail.com',
    packages=['wxPyGameVideoPlayer'],
    scripts=[],
    url='http://pypi.python.org/pypi/wxpygamevideoplayer/',
    license='LICENSE.txt',
    description='Just a simple video player using wxPython, PyGame, and OpenCV',
    long_description=open('README.md').read(),
    install_requires=[
                      'attrdict>=2.0',
                      'numpy>=1.0',
                      'wxPython>=2.8',
                      'matplotlib>=1.0'
                      'pygame>=1.9',
                      'mpl_utils>=0.1.1.0',
                      # 'cv2', # there is no way to depend on this here, but you need to have it :)
                     ],
)
