import os
from collections import Counter

import FreeCAD
import FreeCADGui
import TechDrawGui
from PySide import QtCore, QtGui

import freecad.frameforge._utils as ffu
from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate

# TechDraw PDF Gen


class ExportTechDrawCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "gen_techdraw.svg"),
            "MenuText": translate("MetalWB", "Export all TechDraw Pages as PDF"),
            "Accel": "M, T",
            "ToolTip": translate(
                "MetalWB",
                "<html><head/><body><p>Export all TechDraw Pages as PDF</p></body></html>",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument

        if doc is None:
            raise RuntimeError("No active document")

        # Output directory
        if doc.FileName:
            out_dir = QtGui.QFileDialog.getExistingDirectory(None, "Export folder", os.path.dirname(doc.FileName))
        else:
            out_dir = FreeCAD.getUserAppDataDir()

        for obj in doc.Objects:
            if obj.TypeId == "TechDraw::DrawPage":
                pdf_path = os.path.join(
                    out_dir, f"{''.join(c for c in obj.Label if c.isalnum() or c in (' ', '.', '_')).rstrip()}.pdf"
                )

                TechDrawGui.exportPageAsPdf(obj, pdf_path)

                FreeCAD.Console.PrintMessage(f"Exported: {pdf_path}\n")

        FreeCAD.Console.PrintMessage("All TechDraw pages exported.\n")


FreeCADGui.addCommand("FrameForge_ExportTechDraw", ExportTechDrawCommand())


class RecomputeFrameForgeObjectsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "recompute.svg"),
            "MenuText": translate("MetalWB", "recursivly recompute all profiles and related FF Objects"),
            "Accel": "M, R",
            "ToolTip": translate(
                "MetalWB",
                "<html><head/><body><p>recursivly recompute all profiles and related FF Objects</p></body></html>",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        stats = []

        def recursive_recompute(objs):
            for obj in objs:
                if ffu.is_profile(obj) or ffu.is_trimmedbody(obj) or ffu.is_extrudedcutout(obj):
                    recursive_recompute(obj.OutList)

                    FreeCAD.Console.PrintMessage(f"{obj.Label} ...")

                    obj.recompute()

                    stats.append(obj.Label)
                    FreeCAD.Console.PrintMessage("ok\n")

        recursive_recompute(FreeCAD.ActiveDocument.Objects)

        cs = Counter(stats)
        for k in cs:
            FreeCAD.Console.PrintMessage(f"{k} = {cs[k]}\n")
        # FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("FrameForge_RecomputeFrameForgeObjects", RecomputeFrameForgeObjectsCommand())
