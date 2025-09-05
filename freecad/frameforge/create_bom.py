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



def traverse_assembly(spreadsheet, obj, row=1, parent=""):
    if is_fusion(obj):
        for child in obj.Shapes:
            row = traverse_assembly(spreadsheet, child, row, parent=obj.Label)
            
    elif is_profile(obj):
        spreadsheet.set("A" + str(row), parent)
        spreadsheet.set("B" + str(row), obj.Label)
        spreadsheet.set("C" + str(row), getattr(obj, "Family", "N/A"))
        spreadsheet.set("D" + str(row), getattr(obj, "SizeName", "N/A"))
        spreadsheet.set("E" + str(row), getattr(obj, "Material", "N/A"))
        spreadsheet.set("F" + str(row), str(length_along_normal(obj)))
        spreadsheet.set("G" + str(row), str(getattr(obj, "BevelStartCut1", "N/A")))
        spreadsheet.set("H" + str(row), str(getattr(obj, "BevelStartCut2", "N/A")))
        spreadsheet.set("I" + str(row), str(getattr(obj, "BevelEndCut1", "N/A")))
        spreadsheet.set("J" + str(row), str(getattr(obj, "BevelEndCut2", "N/A")))
        spreadsheet.set("K" + str(row), str(getattr(obj, "ApproxWeight", "N/A")))
        spreadsheet.set("L" + str(row), getattr(obj, "Quantity", "1"))
        row += 1

    elif is_trimmedbody(obj):
        prof = get_profile_from_trimmedbody(obj)
        angles = get_all_cutting_angles(obj)
        spreadsheet.set("A" + str(row), parent)
        spreadsheet.set("B" + str(row), obj.Label)
        spreadsheet.set("C" + str(row), getattr(prof, "Family", "N/A"))
        spreadsheet.set("D" + str(row), getattr(prof, "SizeName", "N/A"))
        spreadsheet.set("E" + str(row), getattr(prof, "Material", "N/A"))
        spreadsheet.set("F" + str(row), str(length_along_normal(obj)))
        spreadsheet.set("G" + str(row), str(angles[0]))
        spreadsheet.set("H" + str(row), "N/A")
        spreadsheet.set("I" + str(row), str(angles[1]))
        spreadsheet.set("J" + str(row), "N/A")
        spreadsheet.set("K" + str(row), str(getattr(obj, "ApproxWeight", "N/A")))
        spreadsheet.set("L" + str(row), getattr(obj, "Quantity", "1"))
        row += 1
    return row


def make_bom(objects):
    doc = FreeCAD.ActiveDocument
    spreadsheet = doc.addObject("Spreadsheet::Sheet", "BOM")

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
    for obj in objects:
        row = traverse_assembly(spreadsheet, obj, row)
