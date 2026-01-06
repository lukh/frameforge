import os

import FreeCAD

RESSOURCESPATH = os.path.join(os.path.dirname(__file__), "resources")

PROFILESPATH = os.path.join(RESSOURCESPATH, "profiles")

ICONPATH = os.path.join(RESSOURCESPATH, "icons")
PROFILEIMAGES_PATH = os.path.join(RESSOURCESPATH, "images", "profiles")
UIPATH = os.path.join(RESSOURCESPATH, "ui")
TRANSLATIONSPATH = os.path.join(RESSOURCESPATH, "translations")


translate = FreeCAD.Qt.translate


class FormProxy(object):
    def __init__(self, form):
        self.members = {o: f for f in form for o in vars(f)}

    def __getattr__(self, name):
        if name not in self.members:
            raise ValueError(f"{name} not a member of one of the forms")

        return getattr(self.members[name], name)
