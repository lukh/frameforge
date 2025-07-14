# -*- coding: utf-8 -*-

__title__ = "Curves workbench utilities"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Curves workbench utilities common to all tools."

import FreeCAD
import Part


def getSubShape(shape, shape_type, n):
    if shape_type == "Vertex" and len(shape.Vertexes) >= n:
        return shape.Vertexes[n - 1]
    elif shape_type == "Edge" and len(shape.Edges) >= n:
        return shape.Edges[n - 1]
    elif shape_type == "Face" and len(shape.Faces) >= n:
        return shape.Faces[n - 1]
    else:
        return None


def getShape(obj, prop, shape_type):
    if hasattr(obj, prop) and obj.getPropertyByName(prop):
        prop_link = obj.getPropertyByName(prop)
        if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSub":
            if shape_type in prop_link[1][0]:
                # try:  # FC 0.19+
                # return prop_link[0].getSubObject(prop_link[1][0])
                # except AttributeError:  # FC 0.18 (stable)
                n = eval(obj.getPropertyByName(prop)[1][0].lstrip(shape_type))
                osh = obj.getPropertyByName(prop)[0].Shape
                sh = osh.copy()
                if (
                    sh
                    and (not shape_type == "Vertex")
                    and hasattr(obj.getPropertyByName(prop)[0], "getGlobalPlacement")
                ):
                    pl = obj.getPropertyByName(prop)[0].getGlobalPlacement()
                    sh.Placement = pl
                return getSubShape(sh, shape_type, n)

        elif obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
            res = []
            for tup in prop_link:
                for ss in tup[1]:
                    if shape_type in ss:
                        # try:  # FC 0.19+
                        # res.append(tup[0].getSubObject(ss))
                        # except AttributeError:  # FC 0.18 (stable)
                        n = eval(ss.lstrip(shape_type))
                        sh = tup[0].Shape.copy()
                        if sh and (not shape_type == "Vertex") and hasattr(tup[0], "getGlobalPlacement"):
                            pl = tup[0].getGlobalPlacement()
                            sh.Placement = pl
                        res.append(getSubShape(sh, shape_type, n))
            return res
        else:
            FreeCAD.Console.PrintError("CurvesWB._utils.getShape: wrong property type.\n")
            return None
    else:
        # FreeCAD.Console.PrintError("CurvesWB._utils.getShape: %r has no property %r\n"%(obj, prop))
        return None
