import os, glob
import json

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App

import Part, ArchCommands
import BOPTools.SplitAPI

from freecad.frameforge.translate_utils import translate
from freecad.frameforge import PROFILESPATH, PROFILEIMAGES_PATH, ICONPATH, UIPATH

from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile



class CreateEndMiterCommand():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "corner-end-miter.svg"),
            "MenuText": translate("MetalWB", "Create Miter Ends"),
            "Accel": "M, C",
            "ToolTip": translate("MetalWB", "<html><head/><body><p><b>Create Miter Ends</b> \
                    <br><br> \
                    Select two profiles. \
                    </p></body></html>"),
        }

    def IsActive(self):
        if App.ActiveDocument:
            if len(Gui.Selection.getSelection()) == 2:
                active = False
                for sel in Gui.Selection.getSelection():
                    if hasattr(sel, 'Target'):
                        active = True
                    elif hasattr(sel, 'TrimmedBody'):
                        active = True
                    else:
                        return False
                return active
        return False

    def Activated(self):
        # create a TrimmedProfile object
        sel = Gui.Selection.getSelectionEx()
        App.ActiveDocument.openTransaction("Make End Miter Profile")
        
        if len(sel) == 2:
            self.make_end_miter_profile(sel[0].Object, [(sel[1].Object, sel[1].SubElementNames)])
            self.make_end_miter_profile(sel[1].Object, [(sel[0].Object, sel[0].SubElementNames)])

        App.ActiveDocument.commitTransaction()
        App.ActiveDocument.recompute()

    def make_end_miter_profile(self, trimmedBody=None, trimmingBoundary=None):
        doc = App.ActiveDocument

        trimmed_profile = doc.addObject("Part::FeaturePython","TrimmedProfile")

        if trimmedBody is not None and len(trimmedBody.Parents) > 0:
            trimmedBody.Parents[-1][0].addObject(trimmed_profile)

        TrimmedProfile(trimmed_profile)
        
        ViewProviderTrimmedProfile(trimmed_profile.ViewObject)
        trimmed_profile.TrimmedBody = trimmedBody
        trimmed_profile.TrimmingBoundary = trimmingBoundary

        trimmed_profile.TrimmedProfileType = "End Miter"
        
        # doc.recompute()
        return trimmed_profile

Gui.addCommand("FrameForge_EndMiter", CreateEndMiterCommand())
