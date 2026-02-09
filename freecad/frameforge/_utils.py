# -*- coding: utf-8 -*-

__title__ = "Curves workbench utilities"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Curves workbench utilities common to all tools."

import math

import FreeCAD
import Part


def getRootObject(obj):
    if obj.isDerivedFrom("PartDesign::Feature"):
        body = obj.getParentGeoFeatureGroup()
        if body:
            return body

    return obj


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



def is_fusion(obj):
    if obj.TypeId == "Part::MultiFuse":
        shape = obj.Shape
        if shape is not None and (shape.ShapeType == "Compound" or shape.isValid() and len(shape.Faces) > 0):
            return True
    return False


def is_part(obj):
    return obj.TypeId == "App::Part"


def is_group(obj):
    return obj.TypeId == "App::DocumentObjectGroup"


def is_profile(obj):
    if obj.TypeId == "Part::FeaturePython":
        if hasattr(obj, "ProfileWidth") and hasattr(obj, "ProfileHeight") and hasattr(obj, "ProfileLength"):
            return True
    return False


def is_trimmedbody(obj):
    if obj.TypeId == "Part::FeaturePython":
        if hasattr(obj, "TrimmedBody"):
            return True
    return False


def is_extrudedcutout(obj):
    if obj.TypeId == "Part::FeaturePython":
        if hasattr(obj, "baseObject"):
            return True
    return False


def is_link(obj):
    return obj.TypeId == "App::Link"


def is_part_or_part_design(obj):
    return obj.TypeId.startswith(("Part::", "PartDesign::"))




def get_profiles_and_links_from_object(profiles, links, obj):
    if is_fusion(obj):
        for child in obj.Shapes:
            get_profiles_and_links_from_object(profiles, links, child)

    elif is_group(obj):
        for child in obj.Group:
            get_profiles_and_links_from_object(profiles, links, child)

    elif is_part(obj):
        for child in obj.Group:
            # TODO: Fix this ugly way to find children
            # I didn't find another way when into a Part
            # It makes it mandatory to have visible object when generating BOM
            if child.getParentGroup() in (obj, None) and child.Visibility:
                get_profiles_and_links_from_object(profiles, links, child)


    elif is_profile(obj):
        profiles.append(obj)

    elif is_link(obj):
        links.append(obj)


def get_profiles_and_links_from_document():
    doc = FreeCAD.ActiveDocument
    return [o for o in doc.Objects if is_profile(o)], [o for o in doc.Objects if is_link(o)]




# TODO move this code into TrimmedProfile ?
def get_profile_from_trimmedbody(obj):
    if is_trimmedbody(obj):
        return get_profile_from_trimmedbody(obj.TrimmedBody)
    else:
        return obj


# TODO move this code into ExtrudedCutOut ?
def get_profile_from_extrudedcutout(obj):
    if is_extrudedcutout(obj):
        bo = obj.baseObject[0]
        if is_profile(bo):
            return bo
        elif is_trimmedbody(bo):
            return get_profile_from_trimmedbody(bo)
        elif is_extrudedcutout(bo):
            return get_profile_from_extrudedcutout(bo)
        else:
            return None

    else:
        raise Exception("Not an extruded cutout")


# TODO move this code into ExtrudedCutOut ?
def get_trimmedprofile_from_extrudedcutout(obj):
    if is_extrudedcutout(obj):
        bo = obj.baseObject[0]
        if is_trimmedbody(bo):
            return bo
        elif is_extrudedcutout(bo):
            return get_trimmedprofile_from_extrudedcutout(bo)
        else:
            return None
    else:
        raise Exception("Not an extruded cutout")


# TODO move this code into TrimmedProfile ?
def get_trimmed_profile_all_cutting_angles(trimmed_profile):
    """Retourne récursivement la liste des angles de coupe (en degrés)
    d'un TrimmedProfile, y compris ceux de ses parents/enfants imbriqués."""
    doc = FreeCAD.ActiveDocument

    angles = []

    def resolve_edge(link):
        target = trimmed_profile.Proxy.getTarget(link)
        return doc.getObject(target[0].Name).getSubObject(target[1][0])

    edge = resolve_edge(trimmed_profile.TrimmedBody)
    dir_vec = (edge.Vertexes[-1].Point.sub(edge.Vertexes[0].Point)).normalize()

    angle_div = 2.0 if trimmed_profile.TrimmedProfileType == "End Miter" else 1.0

    for bound in trimmed_profile.TrimmingBoundary:
        if trimmed_profile.TrimmedProfileType == "End Miter" or trimmed_profile.CutType == "Simple fit":
            for sub in bound[1]:  # sous-objets (souvent "FaceX")
                face = bound[0].getSubObject(sub)
                if isinstance(face.Surface, Part.Plane):
                    normal = face.normalAt(0.5, 0.5).normalize()
                    angle = math.degrees(dir_vec.getAngle(normal))

                    if angle > 90:
                        angle = 180 - angle

                    angles.append(angle / angle_div)
        else:
            angles.append("P")

    if hasattr(trimmed_profile.TrimmedBody, "TrimmedProfileType"):
        parent_profile = trimmed_profile.TrimmedBody
        angles.extend(get_trimmed_profile_all_cutting_angles(parent_profile))

    return angles




def length_along_normal(obj):
    """
    Calcule la longueur de l'objet le long d'un vecteur normal.

    obj    : objet FreeCAD
    normal : FreeCAD.Vector (doit être normalisé)
    """
    doc = FreeCAD.ActiveDocument

    if is_profile(obj):
        if hasattr(obj, "Target"):
            target = obj.Target
            edge = doc.getObject(target[0].Name).getSubObject(target[1][0])
        else:
            return 0.0 # TODO handle this case !!!

    elif is_trimmedbody(obj):
        def resolve_edge(link):
            target = obj.Proxy.getTarget(link)
            return doc.getObject(target[0].Name).getSubObject(target[1][0])

        edge = resolve_edge(obj.TrimmedBody)

    else:
        return 0.0

    dir_vec = (edge.Vertexes[-1].Point.sub(edge.Vertexes[0].Point)).normalize()
    n = dir_vec.normalize()

    vertices = obj.Shape.Vertexes

    projections = [v.Point.dot(n) for v in vertices]

    length = max(projections) - min(projections)
    return length



def get_readable_cutting_angles(ba_y, ba_x, bb_y, bb_x, *trim_cuts):
    all_bevels = [ba_y, ba_x, bb_y, bb_x]
    start_bevels = [ba_y, ba_x]
    end_bevels = [bb_y, bb_x]

    if len(trim_cuts) == 0:
        # a real profile
        if all([b == 0 for b in all_bevels]):
            return ("0.0", "0.0")

        elif ba_y == bb_y == 0.0:
            angles = (ba_x, bb_x)
            angles = angles if (angles[0] * angles[1] <= 0) else (abs(angles[0]), abs(angles[1]))
            return (f"{angles[0]:.1f}", f"{angles[1]:.1f}")

        elif ba_x == bb_x == 0.0:
            angles = (ba_y, bb_y)
            angles = angles if (angles[0] * angles[1] <= 0) else (abs(angles[0]), abs(angles[1]))
            return (f"{angles[0]:.1f}", f"{angles[1]:.1f}")

        elif (ba_y == 0.0 and bb_x == 0.0) ^ (ba_x == 0.0 and bb_y == 0.0):
            return (f"{(ba_y + ba_x):.1f}", f"* {(bb_y+bb_x):.1f}")

        else:
            return (f"{ba_y:.1f} / {ba_x:.1f}", f"{bb_y:.1f} / {bb_x:.1f}")

    elif len(trim_cuts) == 2:
        trim_cuts = [f"{tc:.1f}" if isinstance(tc, float) else tc for tc in trim_cuts]
        return (f"@ {trim_cuts[0]}", f"@ {trim_cuts[1]}")

    elif len(trim_cuts) == 1:
        bevels_not_zero = [b for b in all_bevels if b != 0]
        if len(bevels_not_zero) == 0:
            return ("0.0", f"@ {trim_cuts[0]}")

        elif len(bevels_not_zero) == 1:
            return (f"{abs(bevels_not_zero[0])}", f"@ {trim_cuts[0]}")

    return ("?", "?")