import os, glob
import json

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App

from freecad.frameforge.profile import Profile, ViewProviderProfile

from freecad.frameforge.create_profiles_tool import CreateProfileTaskPanel


class EditProfileTaskPanel(CreateProfileTaskPanel):
    def __init__(self, profile):
        super().__init__()

        # connect all the control to    slots that will update the profile...

        self.profile = profile
        self.dump = profile.dumpContent()

    def open(self):
        App.ActiveDocument.openTransaction("Edit Profile")


    def reject(self):
        self.profile.restoreContent(self.dump)
        Gui.ActiveDocument.resetEdit()

        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True


    def accept(self):
        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True

