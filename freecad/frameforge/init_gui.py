import os

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge import ICONPATH, TRANSLATIONSPATH
from freecad.frameforge.translate_utils import translate


class FrameForge(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = translate("frameforge", "FrameForge")
    ToolTip = translate("frameforge", "a simple FrameForge")
    Icon = os.path.join(ICONPATH, "metalwb.svg")

    toolbox_drawing = ["Sketcher_NewSketch", "FrameForge_ParametricLine"]

    toolbox_frameforge = [
        "FrameForge_CreateProfiles",
        "FrameForge_TrimProfiles",
        "FrameForge_EndMiter",
        "FrameForge_AddExtrudeCutout",
    ]

    toolbox_part = ["Part_Fuse", "Part_Cut", "PartDesign_Body"]

    toolbox_output = ["FrameForge_CreateBOM"]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        from freecad.frameforge import (
            create_end_miter_tool,
            create_extruded_cutout_tool,
            create_profiles_tool,
            create_trimmed_profiles_tool,
            edit_profile_tool,
            parametric_line,
            create_bom_tool
        )

        # Add translations path
        Gui.addLanguagePath(TRANSLATIONSPATH)
        Gui.updateLocale()

        App.Console.PrintMessage(translate("frameforge", "Switching to frameforge") + "\n")

        self.appendToolbar(translate("frameforge", "Drawing Primitives"), self.toolbox_drawing)
        self.appendMenu(translate("frameforge", "Drawing Primitives"), self.toolbox_drawing)

        self.appendToolbar(translate("frameforge", "Frameforge"), self.toolbox_frameforge)
        self.appendMenu(translate("frameforge", "Frameforge"), self.toolbox_frameforge)

        self.appendToolbar(translate("frameforge", "Part Primitives"), self.toolbox_part)
        self.appendMenu(translate("frameforge", "Part Primitives"), self.toolbox_part)

        self.appendToolbar(translate("frameforge", "Frameforge output"), self.toolbox_output)
        self.appendMenu(translate("frameforge", "Frameforge output"), self.toolbox_output)

    def Activated(self):
        """
        code which should be computed when a user switch to this workbench
        """
        App.Console.PrintMessage(translate("frameforge", "Workbench frameforge activated.") + "\n")

    def Deactivated(self):
        """
        code which should be computed when this workbench is deactivated
        """
        App.Console.PrintMessage(translate("frameforge", "Workbench frameforge de-activated.") + "\n")


Gui.addWorkbench(FrameForge())
