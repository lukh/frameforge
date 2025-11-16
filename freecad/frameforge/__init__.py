import os

RESSOURCESPATH = os.path.join(os.path.dirname(__file__), "resources")

PROFILESPATH = os.path.join(RESSOURCESPATH, "profiles")

ICONPATH = os.path.join(RESSOURCESPATH, "icons")
PROFILEIMAGES_PATH = os.path.join(RESSOURCESPATH, "images", "profiles")
UIPATH = os.path.join(RESSOURCESPATH, "ui")
TRANSLATIONSPATH = os.path.join(RESSOURCESPATH, "translations")


class FrameForgeException(BaseException):
    pass


from .create_end_miter_tool import *
from .create_extruded_cutout_tool import *
from .create_profiles_tool import *
from .create_trimmed_profiles_tool import *
from .create_custom_profiles_tool import * 
from .edit_profile_tool import *
from .extruded_cutout import *
from .parametric_line import *
from .profile import *
from .trimmed_profile import *
