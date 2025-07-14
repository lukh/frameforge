from setuptools import setup
import os

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "freecad", "frameforge", "version.py")
with open(version_path) as fp:
    exec(fp.read())

setup(
    name="frameforge",
    version=str(__version__),
    packages=["freecad", "freecad.frameforge"],
    maintainer="Vivien HENRY",
    maintainer_email="vivien.henry@inductivebrain.fr",
    url="https://github.com/lukh/frameforge",
    description="FrameForge is dedicated for creating Frames and Beams, and apply operations (miter cuts, trim cuts) on these profiles.",
    include_package_data=True,
)
