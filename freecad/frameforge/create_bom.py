from itertools import groupby

import FreeCAD
import FreeCADGui as Gui
import Assembly
import math
import Part



def is_fusion(obj):
    if obj.TypeId == "Part::MultiFuse":
        shape = obj.Shape
        if shape is not None and (shape.ShapeType == "Compound" or shape.isValid() and len(shape.Faces) > 0):
            return True
    return False

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



def get_profile_from_trimmedbody(obj):
    if hasattr(obj, "TrimmedBody"):
        return get_profile_from_trimmedbody(obj.TrimmedBody)
    else:
        return obj


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

                    angles.append(90 - (angle / angle_div))
    else:
        angles = ['?', '?']

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



def traverse_assembly(data, obj, parent=""):
    d = {}
    if is_fusion(obj):
        for child in obj.Shapes:
            traverse_assembly(data, child, parent=obj.Label)
            
    elif is_profile(obj):
        d["parent"] =  parent
        d["label"] =  obj.Label
        d["family"] =  getattr(obj, "Family", "N/A")
        d["size_name"] =  getattr(obj, "SizeName", "N/A")
        d["material"] =  getattr(obj, "Material", "N/A")
        d["length"] =  str(length_along_normal(obj))
        d["bevel_start_cut_1"] =  str(getattr(obj, "BevelStartCut1", "N/A"))
        d["bevel_start_cut_2"] =  str(getattr(obj, "BevelStartCut2", "N/A"))
        d["bevel_end_cut_1"] =  str(getattr(obj, "BevelEndCut1", "N/A"))
        d["bevel_end_cut_2"] =  str(getattr(obj, "BevelEndCut2", "N/A"))
        d["approx_weight"] =  str(getattr(obj, "ApproxWeight", "N/A"))
        d["quantity"] =  getattr(obj, "Quantity", "1")

        data.append(d)

    elif is_trimmedbody(obj):
        prof = get_profile_from_trimmedbody(obj)
        angles = get_all_cutting_angles(obj)

        d["parent"] =  parent
        d["label"] =  obj.Label
        d["family"] =  getattr(prof, "Family", "N/A")
        d["size_name"] =  getattr(prof, "SizeName", "N/A")
        d["material"] =  getattr(prof, "Material", "N/A")
        d["length"] =  str(length_along_normal(obj))
        d["bevel_start_cut_1"] =  str(angles[0])
        d["bevel_start_cut_2"] =  "N/A"
        d["bevel_end_cut_1"] =  str(angles[1])
        d["bevel_end_cut_2"] =  "N/A"
        d["approx_weight"] =  str(getattr(obj, "ApproxWeight", "N/A"))
        d["quantity"] =  getattr(obj, "Quantity", "1")

        data.append(d)


def sort_profiles(profiles_data):
    key_func = lambda x: (
        x['parent'],
        x['bevel_end_cut_1'], x['bevel_end_cut_2'], x['bevel_start_cut_1'], x['bevel_start_cut_2'], 
        x['family'],
        round(float(x['length']), 1),
        x['material'], x['size_name']
    )

    profiles_data_sorted = sorted(profiles_data, key=key_func)

    profiles_data_grouped = []

    for k, group in groupby(profiles_data_sorted, key=key_func):
        group = list(group)
        g = group[0]
        d = {}

        d["parent"] = g["parent"]
        d["label"] = ", ".join([g['label'] for g in group])
        d["family"] = g["family"]
        d["size_name"] = g["size_name"]
        d["material"] = g["material"]
        d["length"] = g["length"]
        d["bevel_start_cut_1"] = g["bevel_start_cut_1"]
        d["bevel_start_cut_2"] = g["bevel_start_cut_2"]
        d["bevel_end_cut_1"] = g["bevel_end_cut_1"]
        d["bevel_end_cut_2"] = g["bevel_end_cut_2"]
        d["approx_weight"] = g["approx_weight"]
        d["quantity"] = len(group)

        profiles_data_grouped.append(d)


    return profiles_data_grouped

def make_bom(objects, bom_name="BOM", group_profiles=False):
    doc = FreeCAD.ActiveDocument
    spreadsheet = doc.addObject("Spreadsheet::Sheet", bom_name)

    spreadsheet.set("A1", "Parent")
    spreadsheet.set("B1", "Name")
    spreadsheet.set("C1", "Family")
    spreadsheet.set("D1", "SizeName")
    spreadsheet.set("E1", "Material")
    spreadsheet.set("F1", "Length")
    spreadsheet.set("G1", "BevelStartCut1")
    spreadsheet.set("H1", "BevelStartCut2")
    spreadsheet.set("I1", "BevelEndCut1")
    spreadsheet.set("J1", "BevelEndCut2")
    spreadsheet.set("K1", "Weight")
    spreadsheet.set("L1", "Quantity")

    row = 2

    profiles_data = []
    for obj in objects:
        traverse_assembly(profiles_data, obj)


    if group_profiles:
        profiles_data = sort_profiles(profiles_data)



    for prof in profiles_data:
        spreadsheet.set("A" + str(row), prof['parent'])
        spreadsheet.set("B" + str(row), prof['label'])
        spreadsheet.set("C" + str(row), prof['family'])
        spreadsheet.set("D" + str(row), prof['size_name'])
        spreadsheet.set("E" + str(row), prof['material'])
        spreadsheet.set("F" + str(row), prof['length'])
        spreadsheet.set("G" + str(row), prof['bevel_start_cut_1'])
        spreadsheet.set("H" + str(row), prof['bevel_start_cut_2'])
        spreadsheet.set("I" + str(row), prof['bevel_end_cut_1'])
        spreadsheet.set("J" + str(row), prof['bevel_end_cut_2'])
        spreadsheet.set("K" + str(row), prof['approx_weight'])
        spreadsheet.set("L" + str(row), str(prof['quantity']))

        row += 1
