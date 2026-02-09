import math
from collections import defaultdict
from itertools import groupby

import Assembly
import FreeCAD
import FreeCADGui as Gui
import Part


from freecad.frameforge._utils import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_part,
    is_profile,
    is_trimmedbody,
    is_link,
    is_part_or_part_design
)

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
        for child in obj.Group:
            # TODO: Fix this ugly way to find children
            # I didn't find another way when into a Part
            # It makes it mandatory to have visible object when generating BOM
            if child.getParentGroup() in (obj, None) and child.Visibility:
                traverse_assembly(
                    profiles_data,
                    links_data,
                    child,
                    parent=(f"{parent} / " if full_parent_path else "") + obj.Label,
                    full_parent_path=full_parent_path,
                )

    elif is_profile(obj) or is_trimmedbody(obj) or is_extrudedcutout(obj):
        p["parent"] = parent
        p["label"] = obj.Label
        p["family"] = (
            getattr(getattr(obj, "CustomProfile"), "Label", "Custom Profile")
            if hasattr(obj, "CustomProfile")
            else getattr(obj, "Family", "N/A")
        )
        p["size_name"] = obj.SizeName
        p["material"] = obj.Material
        p["length"] = f"{obj.Length.Value:.1f}"
        p["cut_angle_1"] = obj.CuttingAngleA
        p["cut_angle_2"] = obj.CuttingAngleB
        p["cutout"] = "Yes" if obj.Cutout else ""
        p["approx_weight"] = str(obj.ApproxWeight)
        p["price"] = str(obj.Price)
        p["quantity"] = "1"

        profiles_data.append(p)


    elif is_link(obj):
        links_data.append({"parent": parent, "label": obj.Label, "part": obj.LinkedObject.Label, "quantity": "1", "price":getattr(obj.LinkedObject, "Price", "N/A")})

    elif is_part_or_part_design(obj):
        links_data.append({"parent": parent, "label": obj.Label, "part": obj.Label, "quantity": "1", "price":getattr(obj, "Price", "N/A")})


def group_profiles(profiles_data):
    key_func = lambda x: (
        x["parent"],
        x["family"],
        round(float(x["length"]), 1),
        x["material"],
        x["size_name"],
        # round(float(x["price"]), 1), # TODO: Workaround for Lenght problem
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
        d["price"] = g["price"]
        d["quantity"] = len(group)

        profiles_data_grouped.append(d)

    return profiles_data_grouped


def group_links(links_data):
    out_list = []
    links_data_grouped = defaultdict(list)

    for lnk in links_data:
        key = (lnk["parent"], lnk["part"], lnk["price"])
        links_data_grouped[key].append(lnk)

    for k, group in links_data_grouped.items():
        ol = {}
        ol["parent"] = k[0]
        ol["label"] = ", ".join([g["label"] for g in group])
        ol["part"] = k[1]
        ol["price"] = k[2]
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
    spreadsheet.set("K2", "Price/U")
    spreadsheet.set("L2", "Quantity")

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
        spreadsheet.set("K" + str(row), prof["price"])
        spreadsheet.set("L" + str(row), str(prof["quantity"]))

        row += 1

    if len(links_data) > 0:
        row += 1
        spreadsheet.set("A" + str(row), "Parts")
        row += 1
        spreadsheet.set("A" + str(row), "Parent")
        spreadsheet.set("B" + str(row), "Name")
        spreadsheet.set("C" + str(row), "Part/Type")
        spreadsheet.set("D" + str(row), "Price/U")
        spreadsheet.set("E" + str(row), "Quantity")
        row += 1

        for lnk in links_data:
            spreadsheet.set("A" + str(row), lnk["parent"])
            spreadsheet.set("B" + str(row), lnk["label"])
            spreadsheet.set("C" + str(row), lnk["part"])
            spreadsheet.set("D" + str(row), str(lnk["price"]))
            spreadsheet.set("E" + str(row), str(lnk["quantity"]))

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
    spreadsheet.set("A" + str(row + 4), "P")
    spreadsheet.set("B" + str(row + 4), "Perfect Cut, you have to notch it !")
