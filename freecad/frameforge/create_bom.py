import math
from collections import defaultdict
from itertools import groupby

import Assembly
import FreeCAD
import FreeCADGui as Gui
import Part


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
        if hasattr(obj, "Family") or hasattr(obj, "ProfileLength"):
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


def get_profile_from_trimmedbody(obj):
    if is_trimmedbody(obj):
        return get_profile_from_trimmedbody(obj.TrimmedBody)
    else:
        return obj


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


def get_all_cutting_angles(trimmed_profile):
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

    if trimmed_profile.TrimmedProfileType == "End Miter" or trimmed_profile.CutType == "Simple fit":
        for bound in trimmed_profile.TrimmingBoundary:
            for sub in bound[1]:  # sous-objets (souvent "FaceX")
                face = bound[0].getSubObject(sub)
                if isinstance(face.Surface, Part.Plane):
                    normal = face.normalAt(0.5, 0.5).normalize()
                    angle = math.degrees(dir_vec.getAngle(normal))

                    if angle > 90:
                        angle = 180 - angle

                    angles.append(angle / angle_div)
    else:
        angles = ["?", "?"]

    if hasattr(trimmed_profile.TrimmedBody, "TrimmedProfileType"):
        parent_profile = trimmed_profile.TrimmedBody
        angles.extend(get_all_cutting_angles(parent_profile))

    return angles


def length_along_normal(obj):
    """
    Calcule la longueur de l'objet le long d'un vecteur normal.

    obj    : objet FreeCAD
    normal : FreeCAD.Vector (doit être normalisé)
    """
    doc = FreeCAD.ActiveDocument

    if is_profile(obj):
        target = obj.Target
        edge = doc.getObject(target[0].Name).getSubObject(target[1][0])

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


def get_readable_cutting_angles(bsc1, bsc2, bec1, bec2, *trim_cuts):
    all_bevels = [bsc1, bsc2, bec1, bec2]
    start_bevels = [bsc1, bsc2]
    end_bevels = [bec1, bec2]

    if len(trim_cuts) == 0:
        # a real profile
        if all([b == 0 for b in all_bevels]):
            return ("0.0", "0.0")

        elif bsc1 == bec1 == 0.0:
            angles = (bsc2, bec2)
            angles = angles if (angles[0] * angles[1] <= 0) else (abs(angles[0]), abs(angles[1]))
            return (f"{angles[0]:.1f}", f"{angles[1]:.1f}")

        elif bsc2 == bec2 == 0.0:
            angles = (bsc1, bec1)
            angles = angles if (angles[0] * angles[1] <= 0) else (abs(angles[0]), abs(angles[1]))
            return (f"{angles[0]:.1f}", f"{angles[1]:.1f}")

        elif (bsc1 == 0.0 and bec2 == 0.0) ^ (bsc2 == 0.0 and bec1 == 0.0):
            return (f"{(bsc1 + bsc2):.1f}", f"* {(bec1+bec2):.1f}")

        else:
            return (f"{bsc1:.1f} / {bsc2:.1f}", f"{bec1:.1f} / {bec2:.1f}")

    elif len(trim_cuts) == 2:
        return (f"@ {trim_cuts[0]:.1f}", f"@ {trim_cuts[1]:.1f}")

    elif len(trim_cuts) == 1:
        bevels_not_zero = [b for b in all_bevels if b != 0]
        if len(bevels_not_zero) == 0:
            return ("0.0", f"@ {trim_cuts[0]:.1f}")

        elif len(bevels_not_zero) == 1:
            return (f"{abs(bevels_not_zero[0]):.1f}", f"@ {trim_cuts[0]:.1f}")

    return ("?", "?")


def traverse_assembly(profiles_data, links_data, obj, parent="", full_parent_path=False):
    p = {}
    if is_fusion(obj):
        for child in obj.Shapes:
            traverse_assembly(
                profiles_data,
                links_data,
                child,
                parent=(f"{parent} / " if full_parent_path else "") + obj.Label,
                full_parent_path=full_parent_path,
            )

    elif is_group(obj):
        for child in obj.Group:
            traverse_assembly(
                profiles_data,
                links_data,
                child,
                parent=(f"{parent} / " if full_parent_path else "") + obj.Label,
                full_parent_path=full_parent_path,
            )

    elif is_part(obj):
        for child in obj.OutList:
            if child.InList == [obj]:
                traverse_assembly(
                    profiles_data,
                    links_data,
                    child,
                    parent=(f"{parent} / " if full_parent_path else "") + obj.Label,
                    full_parent_path=full_parent_path,
                )

    elif is_profile(obj):
        cut_angles = get_readable_cutting_angles(
            getattr(obj, "BevelStartCut1", "N/A"),
            getattr(obj, "BevelStartCut2", "N/A"),
            getattr(obj, "BevelEndCut1", "N/A"),
            getattr(obj, "BevelEndCut2", "N/A"),
        )

        p["parent"] = parent
        p["label"] = obj.Label
        p["family"] = (
            getattr(getattr(obj, "CustomProfile"), "Label", "Custom Profile")
            if hasattr(obj, "CustomProfile")
            else getattr(obj, "Family", "N/A")
        )
        p["size_name"] = getattr(obj, "SizeName", "N/A")
        p["material"] = getattr(obj, "Material", "N/A")
        p["length"] = f"{length_along_normal(obj):.1f}"
        p["cut_angle_1"] = cut_angles[0]
        p["cut_angle_2"] = cut_angles[1]
        p["cutout"] = ""
        p["approx_weight"] = str(getattr(obj, "ApproxWeight", "N/A"))
        p["quantity"] = getattr(obj, "Quantity", "1")

        profiles_data.append(p)

    elif is_trimmedbody(obj) or is_extrudedcutout(obj):
        if is_trimmedbody(obj):
            prof = get_profile_from_trimmedbody(obj)
            trim_prof = obj

            angles = get_all_cutting_angles(obj)
            has_cutout = False

        elif is_extrudedcutout(obj):
            prof = get_profile_from_extrudedcutout(obj)
            trim_prof = get_trimmedprofile_from_extrudedcutout(obj)

            angles = get_all_cutting_angles(trim_prof)
            has_cutout = True

        cut_angles = get_readable_cutting_angles(
            getattr(prof, "BevelStartCut1", "N/A"),
            getattr(prof, "BevelStartCut2", "N/A"),
            getattr(prof, "BevelEndCut1", "N/A"),
            getattr(prof, "BevelEndCut2", "N/A"),
            *angles,
        )

        p["parent"] = parent
        p["label"] = trim_prof.Label
        p["family"] = (
            getattr(getattr(prof, "CustomProfile"), "Label", "Custom Profile")
            if hasattr(prof, "CustomProfile")
            else getattr(prof, "Family", "N/A")
        )
        p["size_name"] = getattr(prof, "SizeName", "N/A")
        p["material"] = getattr(prof, "Material", "N/A")
        p["length"] = str(length_along_normal(trim_prof if trim_prof else prof))
        p["cut_angle_1"] = cut_angles[0]
        p["cut_angle_2"] = cut_angles[1]
        p["cutout"] = "Yes" if has_cutout else ""
        p["approx_weight"] = str(getattr(prof, "ApproxWeight", "N/A"))
        p["quantity"] = "1"

        profiles_data.append(p)

    elif is_link(obj):
        links_data.append({"parent": parent, "label": obj.Label, "part": obj.LinkedObject.Label, "quantity": "1"})

    elif is_part_or_part_design(obj):
        links_data.append({"parent": parent, "label": obj.Label, "part": obj.Label, "quantity": "1"})


def group_profiles(profiles_data):
    key_func = lambda x: (
        x["parent"],
        x["family"],
        round(float(x["length"]), 1),
        x["material"],
        x["size_name"],
        x["cut_angle_1"],
        x["cut_angle_2"],
        x["cutout"],
    )

    profiles_data_sorted = sorted(profiles_data, key=key_func)

    profiles_data_grouped = []

    for k, group in groupby(profiles_data_sorted, key=key_func):
        group = list(group)
        g = group[0]
        d = {}

        d["parent"] = g["parent"]
        d["label"] = ", ".join([g["label"] for g in group])
        d["family"] = g["family"]
        d["size_name"] = g["size_name"]
        d["material"] = g["material"]
        d["length"] = g["length"]
        d["cut_angle_1"] = g["cut_angle_1"]
        d["cut_angle_2"] = g["cut_angle_2"]
        d["cutout"] = g["cutout"]
        d["approx_weight"] = g["approx_weight"]
        d["quantity"] = len(group)

        profiles_data_grouped.append(d)

    return profiles_data_grouped


def group_links(links_data):
    out_list = []
    links_data_grouped = defaultdict(list)

    for lnk in links_data:
        key = (lnk["parent"], lnk["part"])
        links_data_grouped[key].append(lnk)

    for k, group in links_data_grouped.items():
        ol = {}
        ol["parent"] = k[0]
        ol["label"] = ", ".join([g["label"] for g in group])
        ol["part"] = k[1]
        ol["quantity"] = len(group)

        out_list.append(ol)

    return out_list


def make_bom(profiles_data, links_data, bom_name="BOM"):
    doc = FreeCAD.ActiveDocument
    spreadsheet = doc.addObject("Spreadsheet::Sheet", bom_name)

    spreadsheet.set("A1", "Profiles")

    spreadsheet.set("A2", "Parent")
    spreadsheet.set("B2", "Name")
    spreadsheet.set("C2", "Family")
    spreadsheet.set("D2", "SizeName")
    spreadsheet.set("E2", "Material")
    spreadsheet.set("F2", "Length")
    spreadsheet.set("G2", "CutAngle1")
    spreadsheet.set("H2", "CutAngle2")
    spreadsheet.set("I2", "Drill/Cutout")
    spreadsheet.set("J2", "ApproxWeight")
    spreadsheet.set("K2", "Quantity")

    row = 3

    for prof in profiles_data:
        spreadsheet.set("A" + str(row), prof["parent"])
        spreadsheet.set("B" + str(row), prof["label"])
        spreadsheet.set("C" + str(row), prof["family"])
        spreadsheet.set("D" + str(row), prof["size_name"])
        spreadsheet.set("E" + str(row), prof["material"])
        spreadsheet.set("F" + str(row), prof["length"])
        spreadsheet.set("G" + str(row), "'" + str(prof["cut_angle_1"]))
        spreadsheet.set("H" + str(row), "'" + str(prof["cut_angle_2"]))
        spreadsheet.set("I" + str(row), "'" + str(prof["cutout"]))
        spreadsheet.set("J" + str(row), prof["approx_weight"])
        spreadsheet.set("K" + str(row), str(prof["quantity"]))

        row += 1

    if len(links_data) > 0:
        row += 1
        spreadsheet.set("A" + str(row), "Parts")
        row += 1
        spreadsheet.set("A" + str(row), "Parent")
        spreadsheet.set("B" + str(row), "Name")
        spreadsheet.set("C" + str(row), "Part/Type")
        spreadsheet.set("D" + str(row), "Quantity")
        row += 1

        for lnk in links_data:
            spreadsheet.set("A" + str(row), lnk["parent"])
            spreadsheet.set("B" + str(row), lnk["label"])
            spreadsheet.set("C" + str(row), lnk["part"])
            spreadsheet.set("D" + str(row), str(lnk["quantity"]))

            row += 1

    row += 2
    spreadsheet.set("A" + str(row), "Legend")
    spreadsheet.set("A" + str(row + 1), "*")
    spreadsheet.set("B" + str(row + 1), "Angles 1 and 2 are rotated 90° along the edge")
    spreadsheet.set("A" + str(row + 2), "-")
    spreadsheet.set(
        "B" + str(row + 2),
        "Angles 1 and 2 are cut in the same direction (no need to rotate the stock 180° when cutting)",
    )
    spreadsheet.set("A" + str(row + 3), "@")
    spreadsheet.set(
        "B" + str(row + 3),
        "Angle is calculated from a TrimmedProfile -> be careful to check length, angles and cut direction",
    )
    spreadsheet.set("A" + str(row + 4), "?")
    spreadsheet.set("B" + str(row + 4), "Can't compute the angle, do it yourself !")
