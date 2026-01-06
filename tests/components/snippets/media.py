from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("media")

# Audio tests
tests.audio_simple = Audio("path/to/audio.mp3", id="audio1")
tests.audio_simple = """
<audio controls id="audio1" src="path/to/audio.mp3">
</audio>
"""

tests.audio_controls_only = Audio(
    "music.ogg", controls=True, autoplay=False, loop=False, muted=False, id="audio2"
)
tests.audio_controls_only = """
<audio controls id="audio2" src="music.ogg">
</audio>
"""

tests.audio_autoplay = Audio(
    "background.mp3", controls=False, autoplay=True, muted=True, id="bg-audio"
)
tests.audio_autoplay = """
<audio autoplay id="bg-audio" muted src="background.mp3">
</audio>
"""

tests.audio_loop = Audio("loop_sound.mp3", loop=True, id="audio1")
tests.audio_loop = """
<audio controls id="audio1" loop src="loop_sound.mp3">
</audio>
"""

# Video tests
tests.video_simple = Video("path/to/video.mp4", id="vid1")
tests.video_simple = """
<video controls id="vid1" src="path/to/video.mp4">
</video>
"""

tests.video_with_dimensions = Video("tutorial.mp4", width=640, height=480, id="vid1")
tests.video_with_dimensions = """
<video controls height="480" id="vid1" src="tutorial.mp4" width="640">
</video>
"""

tests.video_autoplay_muted = Video(
    "intro.mp4", autoplay=True, muted=True, controls=False, id="vid2"
)
tests.video_autoplay_muted = """
<video autoplay id="vid2" muted src="intro.mp4">
</video>
"""

tests.video_loop = Video("demo.mp4", loop=True, id="vid1")
tests.video_loop = """
<video controls id="vid1" loop src="demo.mp4">
</video>
"""

# Canvas tests
tests.canvas_simple = Canvas("myCanvas")
tests.canvas_simple = """
<canvas height="150" id="myCanvas" width="300">
</canvas>
"""

tests.canvas_with_dimensions = Canvas("drawArea", width=800, height=600)
tests.canvas_with_dimensions = """
<canvas height="600" id="drawArea" width="800">
</canvas>
"""

# SVG tests
tests.svg_simple = SVG('<circle cx="50" cy="50" r="40" fill="red"/>', id="circle1")
tests.svg_simple = """
<svg id="circle1">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>
"""

tests.svg_with_dimensions = SVG(
    '<rect width="100" height="100" fill="blue"/>', width=100, height=100, id="rect1"
)
tests.svg_with_dimensions = """
<svg height="100" id="rect1" width="100">
  <rect width="100" height="100" fill="blue"/>
</svg>
"""

tests.svg_with_viewbox = SVG(
    '<polygon points="0,0 100,0 50,100" fill="green"/>',
    viewBox="0 0 100 100",
    id="shape",
)
tests.svg_with_viewbox = """
<svg id="shape" viewBox="0 0 100 100">
  <polygon points="0,0 100,0 50,100" fill="green"/>
</svg>
"""
