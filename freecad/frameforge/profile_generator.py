import math

import FreeCAD as App
import Part

vec = App.Base.Vector


class ProfileGenerator:
    """Base class for all profile generators"""

    def __init__(self):
        """Initialize the profile generator"""
        pass

    def get_parameters(self, obj):
        """Extract common parameters from the FreeCAD object"""
        params = {
            "width": obj.ProfileWidth,
            "height": obj.ProfileHeight,
            "thickness": obj.Thickness,
            "flange_thickness": obj.ThicknessFlange,
            "radius_large": obj.RadiusLarge,
            "radius_small": obj.RadiusSmall,
            "make_fillet": obj.MakeFillet,
            "centered_width": obj.CenteredOnWidth,
            "centered_height": obj.CenteredOnHeight,
            "length": obj.ProfileLength,
        }

        # Origin position
        params["w"] = -params["width"] / 2 if params["centered_width"] else 0
        params["h"] = -params["height"] / 2 if params["centered_height"] else 0

        return params

    def get_bevel_parameters(self, obj, bevels_combined=False):
        """Get bevel parameters from object"""
        if bevels_combined:
            return {
                "B1Y": obj.BevelStartCut,
                "B1Z": -obj.BevelStartRotate,
                "B2Y": -obj.BevelEndCut,
                "B2Z": -obj.BevelEndRotate,
                "B1X": 0,
                "B2X": 0,
            }
        else:
            return {
                "B1Y": obj.BevelStartCut1,
                "B2Y": -obj.BevelEndCut1,
                "B1X": -obj.BevelStartCut2,
                "B2X": obj.BevelEndCut2,
                "B1Z": 0,
                "B2Z": 0,
            }

    def generate_shape(self, obj):
        """Generate and return a Part.Shape object"""
        raise NotImplementedError("Subclasses must implement generate_shape()")

    def apply_bevels(self, shape, obj, bevels_combined=False):
        """Apply bevels to the given shape"""
        bevel_params = self.get_bevel_parameters(obj, bevels_combined)
        B1Y, B2Y = bevel_params["B1Y"], bevel_params["B2Y"]
        B1X, B2X = bevel_params["B1X"], bevel_params["B2X"]
        B1Z, B2Z = bevel_params["B1Z"], bevel_params["B2Z"]

        # If no bevels to apply, just return the original shape
        if not (B1Y or B2Y or B1X or B2X or B1Z or B2Z):
            return shape

        params = self.get_parameters(obj)
        W, H = params["width"], params["height"]
        L = params["length"]
        w, h = params["w"], params["h"]

        hc = 10 * max(H, W)

        face = None
        if hasattr(shape, "Faces") and shape.Faces:
            # First try to find a face perpendicular to z-axis at z=0
            for f in shape.Faces:
                try:
                    # Check if the face is at z=0 (within tolerance)
                    if abs(f.BoundBox.ZMin) < 0.001 and abs(f.BoundBox.ZMax) < 0.001:
                        # Check if it's the right size (approximately the profile footprint)
                        bbox = f.BoundBox
                        if abs(bbox.XLength - W) < 0.1 and abs(bbox.YLength - H) < 0.1:
                            face = f
                            break
                except Exception:
                    continue

            # If first method fails, try a more general approach
            if not face:
                for f in shape.Faces:
                    try:
                        center = f.CenterOfMass
                        if abs(center.z) < 0.001:  # Face is near z=0 plane
                            face = f
                            break
                    except Exception:
                        continue

        if not face and hasattr(shape, "Face1"):
            # Last resort - try to use the first face
            face = shape.Face1

        if not face:
            App.Console.PrintWarning("Profile: Cannot find face for beveling\n")
            return shape

        # Continue with original bevel code
        ProfileExt = shape.fuse(face.extrude(vec(0, 0, L + hc / 4)))

        # End bevel
        box = Part.makeBox(hc, hc, hc)
        box.translate(vec(-hc / 2 + w, -hc / 2 + h, L))
        pr = vec(0, 0, L)
        box.rotate(pr, vec(0, 1, 0), B2Y)
        if bevels_combined:
            box.rotate(pr, vec(0, 0, 1), B2Z)
        else:
            box.rotate(pr, vec(1, 0, 0), B2X)
        ProfileCut = ProfileExt.cut(box)

        # Start bevel
        ProfileExt = ProfileCut.fuse(face.extrude(vec(0, 0, -hc / 4)))
        box = Part.makeBox(hc, hc, hc)
        box.translate(vec(-hc / 2 + w, -hc / 2 + h, -hc))
        pr = vec(0, 0, 0)
        box.rotate(pr, vec(0, 1, 0), B1Y)
        if bevels_combined:
            box.rotate(pr, vec(0, 0, 1), B1Z)
        else:
            box.rotate(pr, vec(1, 0, 0), B1X)
        ProfileCut = ProfileExt.cut(box)

        return ProfileCut.removeSplitter()
