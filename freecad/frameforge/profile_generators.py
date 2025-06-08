import math

import Part

from .profile_generator import ProfileGenerator, vec


class HollowTubeGenerator(ProfileGenerator):
    """Base generator for all hollow tube profiles (pipe, square hollow, rectangular hollow)"""

    def generate_shape(self, obj):
        """Generate a hollow tube profile"""
        # Get profile parameters
        params = self.get_parameters(obj)
        L = params["length"]

        # Create the 2D face (to be implemented by subclasses)
        face = self.create_profile_face(obj, params)

        # Create 3D shape if length is provided
        if L:
            return face.extrude(vec(0, 0, L))
        else:
            return face

    def create_profile_face(self, obj, params):
        """Create the 2D face for the hollow profile - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_profile_face()")

    def create_outer_profile(self, obj, params):
        """Create the outer profile wire - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_outer_profile()")

    def create_inner_profile(self, obj, params):
        """Create the inner profile wire - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_inner_profile()")


class SolidBarGenerator(ProfileGenerator):
    """Base generator for solid bar profiles (flat bar, square bar, round bar, etc.)"""

    def get_face(self, obj):
        """Get the 2D face for the solid profile - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_face()")

    def get_profile_type(self):
        """Return the profile type name - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_profile_type()")

    def generate_shape(self, obj):
        """Generate the final 3D solid shape with proper Z-axis centering"""
        face = self.get_face(obj)
        params = self.get_parameters(obj)
        L = params["length"]

        if L:
            # Check if centering is requested
            if params["centered_width"] or params["centered_height"]:
                # Create full-length extrusion first
                extrusion = face.extrude(vec(0, 0, L))
                # Then translate to center it on Z-axis
                return extrusion.translate(vec(0, 0, -L/2))
            else:
                # Standard extrusion from Z=0
                return face.extrude(vec(0, 0, L))
        else:
            return face


class AngleGenerator(ProfileGenerator):
    """Generator for equal and unequal leg angle profiles"""

    def generate_shape(self, obj):
        """Generate an angle profile shape"""
        params = self.get_parameters(obj)
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        w = params["w"]
        h = params["h"]
        L = params["length"]
        make_fillet = params["make_fillet"]
        R = params["radius_large"]
        r = params["radius_small"]
        d = vec(0, 0, 1)

        if not make_fillet:
            # Simple non-filleted angle
            p1 = vec(0 + w, 0 + h, 0)
            p2 = vec(0 + w, H + h, 0)
            p3 = vec(TW + w, H + h, 0)
            p4 = vec(TW + w, TW + h, 0)
            p5 = vec(W + w, TW + h, 0)
            p6 = vec(W + w, 0 + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p2, p3)
            L3 = Part.makeLine(p3, p4)
            L4 = Part.makeLine(p4, p5)
            L5 = Part.makeLine(p5, p6)
            L6 = Part.makeLine(p6, p1)

            wire = Part.Wire([L1, L2, L3, L4, L5, L6])

        else:
            # Filleted angle
            p1 = vec(0 + w, 0 + h, 0)
            p2 = vec(0 + w, H + h, 0)
            p3 = vec(TW - r + w, H + h, 0)
            p4 = vec(TW + w, H - r + h, 0)
            p5 = vec(TW + w, TW + R + h, 0)
            p6 = vec(TW + R + w, TW + h, 0)
            p7 = vec(W - r + w, TW + h, 0)
            p8 = vec(W + w, TW - r + h, 0)
            p9 = vec(W + w, 0 + h, 0)
            c1 = vec(TW - r + w, H - r + h, 0)
            c2 = vec(TW + R + w, TW + R + h, 0)
            c3 = vec(W - r + w, TW - r + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p2, p3)
            L3 = Part.makeLine(p4, p5)
            L4 = Part.makeLine(p6, p7)
            L5 = Part.makeLine(p8, p9)
            L6 = Part.makeLine(p9, p1)
            A1 = Part.makeCircle(r, c1, d, 0, 90)
            A2 = Part.makeCircle(R, c2, d, 180, 270)
            A3 = Part.makeCircle(r, c3, d, 0, 90)

            wire = Part.Wire([L1, L2, A1, L3, A2, L4, A3, L5, L6])

        face = Part.Face(wire)

        # Create 3D shape if length is provided
        if L:
            return face.extrude(vec(0, 0, L))
        else:
            return face


class RectangularBarGenerator(SolidBarGenerator):
    """Generator for rectangular solid bars (including squares and flats)"""

    def get_face(self, obj):
        """Get the 2D rectangular face for the profile"""
        params = self.get_parameters(obj)
        W = params["width"]
        H = params["height"]
        w = params["w"]
        h = params["h"]
        make_fillet = params["make_fillet"]
        R = params["radius_large"]
        d = vec(0, 0, 1)

        if not make_fillet:
            # Simple rectangular profile without fillets
            p1 = vec(0 + w, 0 + h, 0)
            p2 = vec(0 + w, H + h, 0)
            p3 = vec(W + w, H + h, 0)
            p4 = vec(W + w, 0 + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p2, p3)
            L3 = Part.makeLine(p3, p4)
            L4 = Part.makeLine(p4, p1)

            wire = Part.Wire([L1, L2, L3, L4])
        else:
            # Rectangular profile with filleted corners
            p1 = vec(0 + w, 0 + R + h, 0)
            p2 = vec(0 + w, H - R + h, 0)
            p3 = vec(R + w, H + h, 0)
            p4 = vec(W - R + w, H + h, 0)
            p5 = vec(W + w, H - R + h, 0)
            p6 = vec(W + w, R + h, 0)
            p7 = vec(W - R + w, 0 + h, 0)
            p8 = vec(R + w, 0 + h, 0)

            c1 = vec(R + w, R + h, 0)
            c2 = vec(R + w, H - R + h, 0)
            c3 = vec(W - R + w, H - R + h, 0)
            c4 = vec(W - R + w, R + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p3, p4)
            L3 = Part.makeLine(p5, p6)
            L4 = Part.makeLine(p7, p8)
            A1 = Part.makeCircle(R, c1, d, 180, 270)
            A2 = Part.makeCircle(R, c2, d, 90, 180)
            A3 = Part.makeCircle(R, c3, d, 0, 90)
            A4 = Part.makeCircle(R, c4, d, 270, 0)

            wire = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

        return Part.Face(wire)


class SquareBarGenerator(RectangularBarGenerator):
    """Generator specifically for square bar profiles"""

    def get_parameters(self, obj):
        """Override to ensure width equals height"""
        params = super().get_parameters(obj)
        # Enforce square shape if this is explicitly a square bar
        if hasattr(obj, "ProfileFamily") and obj.ProfileFamily == "Square":
            params["height"] = params["width"]
        return params


class RoundBarGenerator(SolidBarGenerator):
    """Generator for round/cylindrical bar profiles"""

    def get_profile_type(self):
        return "Round Bar"
        
    def get_parameters(self, obj):
        """Override to correctly handle centering for circular profiles"""
        params = super().get_parameters(obj)
        
        # For round bars, use height as diameter since that's how it's stored in metal.json
        # Width is used as fallback for backward compatibility
        diameter = params["height"] if "height" in params else params["width"]
        
        # Recalculate centering offsets for circular profile
        if params["centered_width"] or params["centered_height"]:
            # For circular profiles, center equally in both dimensions
            params["w"] = -diameter / 2
            params["h"] = -diameter / 2
        else:
            params["w"] = 0
            params["h"] = 0
            
        return params

    def get_face(self, obj):
        """Get the 2D circular face for the profile"""
        params = self.get_parameters(obj)
        # Use height instead of width for diameter
        diameter = params["height"] if "height" in params else params["width"]
        w = params["w"]
        h = params["h"]

        # Calculate center position
        radius = diameter / 2
        center = vec(radius + w, radius + h, 0)

        # Create a circle
        circle = Part.makeCircle(radius, center, vec(0, 0, 1))
        wire = Part.Wire([circle])

        return Part.Face(wire)


class RectangularHollowGenerator(HollowTubeGenerator):
    """Generator for square and rectangular hollow tube profiles"""

    def create_profile_face(self, obj, params):
        """Create the 2D face for the rectangular hollow profile"""
        # Extract parameters from the params dictionary
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        w = params["w"]
        h = params["h"]
        make_fillet = params["make_fillet"]

        # Create outer and inner wires based on fillet setting
        outer_wire = self.create_outer_profile(obj, params)
        inner_wire = self.create_inner_profile(obj, params)

        # Create face from wires
        face1 = Part.Face(outer_wire)
        face2 = Part.Face(inner_wire)
        return face1.cut(face2)

    def create_outer_profile(self, obj, params):
        """Create the outer profile wire"""
        W = params["width"]
        H = params["height"]
        w = params["w"]
        h = params["h"]
        make_fillet = params["make_fillet"]
        R = params["radius_large"]
        d = vec(0, 0, 1)

        if not make_fillet:
            # Simple rectangular profile without fillets
            p1 = vec(0 + w, 0 + h, 0)
            p2 = vec(0 + w, H + h, 0)
            p3 = vec(W + w, H + h, 0)
            p4 = vec(W + w, 0 + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p2, p3)
            L3 = Part.makeLine(p3, p4)
            L4 = Part.makeLine(p4, p1)

            return Part.Wire([L1, L2, L3, L4])
        else:
            # Outer wire with fillets
            p1 = vec(0 + w, 0 + R + h, 0)
            p2 = vec(0 + w, H - R + h, 0)
            p3 = vec(R + w, H + h, 0)
            p4 = vec(W - R + w, H + h, 0)
            p5 = vec(W + w, H - R + h, 0)
            p6 = vec(W + w, R + h, 0)
            p7 = vec(W - R + w, 0 + h, 0)
            p8 = vec(R + w, 0 + h, 0)

            c1 = vec(R + w, R + h, 0)
            c2 = vec(R + w, H - R + h, 0)
            c3 = vec(W - R + w, H - R + h, 0)
            c4 = vec(W - R + w, R + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p3, p4)
            L3 = Part.makeLine(p5, p6)
            L4 = Part.makeLine(p7, p8)
            A1 = Part.makeCircle(R, c1, d, 180, 270)
            A2 = Part.makeCircle(R, c2, d, 90, 180)
            A3 = Part.makeCircle(R, c3, d, 0, 90)
            A4 = Part.makeCircle(R, c4, d, 270, 0)

            return Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

    def create_inner_profile(self, obj, params):
        """Create the inner profile wire"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        w = params["w"]
        h = params["h"]
        make_fillet = params["make_fillet"]
        r = params["radius_small"]
        d = vec(0, 0, 1)

        if not make_fillet:
            # Inner wire without fillets
            p5 = vec(TW + w, TW + h, 0)
            p6 = vec(TW + w, H - TW + h, 0)
            p7 = vec(W - TW + w, H - TW + h, 0)
            p8 = vec(W - TW + w, TW + h, 0)

            L5 = Part.makeLine(p5, p6)
            L6 = Part.makeLine(p6, p7)
            L7 = Part.makeLine(p7, p8)
            L8 = Part.makeLine(p8, p5)

            return Part.Wire([L5, L6, L7, L8])
        else:
            # Inner wire with fillets
            p1 = vec(TW + w, TW + r + h, 0)
            p2 = vec(TW + w, H - TW - r + h, 0)
            p3 = vec(TW + r + w, H - TW + h, 0)
            p4 = vec(W - TW - r + w, H - TW + h, 0)
            p5 = vec(W - TW + w, H - TW - r + h, 0)
            p6 = vec(W - TW + w, TW + r + h, 0)
            p7 = vec(W - TW - r + w, TW + h, 0)
            p8 = vec(TW + r + w, TW + h, 0)

            c1 = vec(TW + r + w, TW + r + h, 0)
            c2 = vec(TW + r + w, H - TW - r + h, 0)
            c3 = vec(W - TW - r + w, H - TW - r + h, 0)
            c4 = vec(W - TW - r + w, TW + r + h, 0)

            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p3, p4)
            L3 = Part.makeLine(p5, p6)
            L4 = Part.makeLine(p7, p8)
            A1 = Part.makeCircle(r, c1, d, 180, 270)
            A2 = Part.makeCircle(r, c2, d, 90, 180)
            A3 = Part.makeCircle(r, c3, d, 0, 90)
            A4 = Part.makeCircle(r, c4, d, 270, 0)

            return Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])


class PipeGenerator(HollowTubeGenerator):
    """Generator for pipe/circular hollow profiles"""

    def get_parameters(self, obj):
        """Override to correctly handle centering for circular profiles"""
        params = super().get_parameters(obj)

        # For pipes, both width and height refer to the same dimension (diameter)
        # So we need to ensure centering is consistent
        diameter = params["height"]  # We use height as diameter

        # Recalculate centering offsets for circular profile
        if params["centered_width"] or params["centered_height"]:
            # For circular profiles, center equally in both dimensions
            params["w"] = -diameter / 2
            params["h"] = -diameter / 2
        else:
            params["w"] = 0
            params["h"] = 0

        return params

    def create_profile_face(self, obj, params):
        """Create the 2D face for the pipe profile"""
        outer_wire = self.create_outer_profile(obj, params)
        inner_wire = self.create_inner_profile(obj, params)

        face1 = Part.Face(outer_wire)
        face2 = Part.Face(inner_wire)
        return face1.cut(face2)

    def create_outer_profile(self, obj, params):
        """Create the outer circular profile"""
        H = params["height"]  # Use height as diameter
        w = params["w"]
        h = params["h"]
        d = vec(0, 0, 1)

        # Calculate center position and radius
        radius = H / 2
        center = vec(radius + w, radius + h, 0)

        # Create a circle
        circle = Part.makeCircle(radius, center, d, 0, 360)
        return Part.Wire([circle])

    def create_inner_profile(self, obj, params):
        """Create the inner circular profile"""
        H = params["height"]  # Use height as diameter
        TW = params["thickness"]  # Wall thickness
        w = params["w"]
        h = params["h"]
        d = vec(0, 0, 1)

        # Calculate center position and inner radius
        radius = H / 2
        inner_radius = radius - TW
        center = vec(radius + w, radius + h, 0)

        # Create inner circle
        circle = Part.makeCircle(inner_radius, center, d, 0, 360)
        return Part.Wire([circle])


class ChannelGenerator(ProfileGenerator):
    """Generator for UPE and UPN channel profiles"""

    def generate_shape(self, obj):
        """Generate a channel profile shape"""
        params = self.get_parameters(obj)
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]
        L = params["length"]
        make_fillet = params["make_fillet"]
        R = params["radius_large"]  # For outer corners
        r = params["radius_small"]  # For inner corners
        d = vec(0, 0, 1)  # Direction for circle creation

        # Check if we're making UPN (angled flanges) or UPE (straight flanges)
        is_upn = hasattr(obj, "UPN") and obj.UPN
        flange_angle = obj.FlangeAngle if hasattr(obj, "FlangeAngle") else 4.57

        face = None

        if not make_fillet:
            # Non-filleted channel
            face = self.create_nonfilletted_channel(obj, params, is_upn, flange_angle)
        else:
            # Filleted channel
            if is_upn:
                face = self.create_filleted_upn(obj, params, flange_angle)
            else:
                face = self.create_filleted_upe(obj, params)

        # Create 3D shape if length is provided
        if L:
            return face.extrude(vec(0, 0, L))
        else:
            return face

    def create_nonfilletted_channel(self, obj, params, is_upn, flange_angle):
        """Create a non-filleted channel profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]

        # Calculate flange angle offset for UPN
        Yd = 0
        if is_upn:
            Yd = (W / 4) * math.tan(math.pi * flange_angle / 180)

        # Create points for profile
        p1 = vec(w, h, 0)
        p2 = vec(w, H + h, 0)
        p3 = vec(w + W, H + h, 0)
        p4 = vec(W + w, h, 0)
        p5 = vec(W + w + Yd - TW, h, 0)
        p6 = vec(W + w - Yd - TW, H + h - TF, 0)
        p7 = vec(w + TW + Yd, H + h - TF, 0)
        p8 = vec(w + TW - Yd, h, 0)

        # Create lines
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p2, p3)
        L3 = Part.makeLine(p3, p4)
        L4 = Part.makeLine(p4, p5)
        L5 = Part.makeLine(p5, p6)
        L6 = Part.makeLine(p6, p7)
        L7 = Part.makeLine(p7, p8)
        L8 = Part.makeLine(p8, p1)

        # Create wire and face
        wire = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8])
        return Part.Face(wire)

    def create_filleted_upe(self, obj, params):
        """Create a filleted UPE channel profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]
        r = params["radius_small"]
        R = params["radius_large"]
        d = vec(0, 0, 1)

        # Create points for the profile
        p1 = vec(w, h, 0)
        p2 = vec(w, H + h, 0)
        p3 = vec(w + W, H + h, 0)
        p4 = vec(W + w, h, 0)
        p5 = vec(W + w - TW + r, h, 0)
        p6 = vec(W + w - TW, h + r, 0)
        p7 = vec(W + w - TW, H + h - TF - R, 0)
        p8 = vec(W + w - TW - R, H + h - TF, 0)
        p9 = vec(w + TW + R, H + h - TF, 0)
        p10 = vec(w + TW, H + h - TF - R, 0)
        p11 = vec(w + TW, h + r, 0)
        p12 = vec(w + TW - r, h, 0)

        # Create centers for arcs
        C1 = vec(w + TW - r, h + r, 0)
        C2 = vec(w + TW + R, H + h - TF - R, 0)
        C3 = vec(W + w - TW - R, H + h - TF - R, 0)
        C4 = vec(W + w - TW + r, r + h, 0)

        # Create straight lines
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p2, p3)
        L3 = Part.makeLine(p3, p4)
        L4 = Part.makeLine(p4, p5)
        L5 = Part.makeLine(p6, p7)
        L6 = Part.makeLine(p8, p9)
        L7 = Part.makeLine(p10, p11)
        L8 = Part.makeLine(p12, p1)

        # Create arcs
        A1 = Part.makeCircle(r, C1, d, 270, 0)
        A2 = Part.makeCircle(R, C2, d, 90, 180)
        A3 = Part.makeCircle(R, C3, d, 0, 90)
        A4 = Part.makeCircle(r, C4, d, 180, 270)

        # Create wire and face
        wire = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])
        return Part.Face(wire)

    def create_filleted_upn(self, obj, params, flange_angle):
        """Create a filleted UPN channel profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]
        r = params["radius_small"]
        R = params["radius_large"]
        w = params["w"]
        h = params["h"]
        d = vec(0, 0, 1)

        # Calculate angles and offsets
        angarc = flange_angle
        angrad = math.pi * angarc / 180
        sina = math.sin(angrad)
        cosa = math.cos(angrad)
        tana = math.tan(angrad)

        # Calculate geometry points
        cot1 = r * sina
        y11 = r - cot1
        cot2 = (H / 2 - r) * tana
        cot3 = cot1 * tana
        x11 = TW - cot2 - cot3
        xc1 = TW - cot2 - cot3 - r * cosa
        yc1 = r
        cot8 = (H / 2 - R - TF + R * sina) * tana
        x10 = TW + cot8
        y10 = H - TF - R + R * sina
        xc2 = cot8 + R * cosa + TW
        yc2 = H - TF - R
        x12 = TW - cot2 - cot3 - r * cosa
        y12 = 0
        x9 = cot8 + R * cosa + TW
        y9 = H - TF

        # Mirror points for the right side
        xc3 = W - xc2
        yc3 = yc2
        xc4 = W - xc1
        yc4 = yc1

        # Define all the points for the profile
        x1, y1 = 0, 0
        x2, y2 = 0, H
        x3, y3 = W, H
        x4, y4 = W, 0
        x5, y5 = W - x12, 0
        x6, y6 = W - x11, y11
        x7, y7 = W - x10, y10
        x8, y8 = W - x9, y9

        # Create points
        c1 = vec(xc1 + w, yc1 + h, 0)
        c2 = vec(xc2 + w, yc2 + h, 0)
        c3 = vec(xc3 + w, yc3 + h, 0)
        c4 = vec(xc4 + w, yc4 + h, 0)

        p1 = vec(x1 + w, y1 + h, 0)
        p2 = vec(x2 + w, y2 + h, 0)
        p3 = vec(x3 + w, y3 + h, 0)
        p4 = vec(x4 + w, y4 + h, 0)
        p5 = vec(x5 + w, y5 + h, 0)
        p6 = vec(x6 + w, y6 + h, 0)
        p7 = vec(x7 + w, y7 + h, 0)
        p8 = vec(x8 + w, y8 + h, 0)
        p9 = vec(x9 + w, y9 + h, 0)
        p10 = vec(x10 + w, y10 + h, 0)
        p11 = vec(x11 + w, y11 + h, 0)
        p12 = vec(x12 + w, y12 + h, 0)

        # Create arcs
        A1 = Part.makeCircle(r, c1, d, 270, 0 - angarc)
        A2 = Part.makeCircle(R, c2, d, 90, 180 - angarc)
        A3 = Part.makeCircle(R, c3, d, 0 + angarc, 90)
        A4 = Part.makeCircle(r, c4, d, 180 + angarc, 270)

        # Create lines
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p2, p3)
        L3 = Part.makeLine(p3, p4)
        L4 = Part.makeLine(p4, p5)
        L5 = Part.makeLine(p6, p7)
        L6 = Part.makeLine(p8, p9)
        L7 = Part.makeLine(p10, p11)
        L8 = Part.makeLine(p12, p1)

        # Create wire and face
        wire = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])
        return Part.Face(wire)


class BeamGenerator(ProfileGenerator):
    """Generator for I-beam profiles (IPE, IPN, HEA, HEB, HEM)"""

    def generate_shape(self, obj):
        """Generate an I-beam profile shape"""
        params = self.get_parameters(obj)
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]  # Web thickness
        TF = params["flange_thickness"]  # Flange thickness
        w = params["w"]
        h = params["h"]
        L = params["length"]
        make_fillet = params["make_fillet"]
        R = params["radius_large"]
        d = vec(0, 0, 1)

        # Determine if we're making IPN-style (angled flanges) or IPE/HE-style (straight flanges)
        is_ipn = hasattr(obj, "IPN") and obj.IPN
        flange_angle = obj.FlangeAngle if hasattr(obj, "FlangeAngle") else 8.0

        # Create the 2D face for the beam profile
        face = None

        if not make_fillet:
            face = self.create_non_filleted_beam(obj, params, is_ipn, flange_angle)
        else:
            if is_ipn:
                face = self.create_filleted_ipn(obj, params, flange_angle)
            else:
                face = self.create_filleted_ipe_he(obj, params)

        # Create 3D shape if length is provided
        if L:
            return face.extrude(vec(0, 0, L))
        else:
            return face

    def create_non_filleted_beam(self, obj, params, is_ipn, flange_angle):
        """Create a non-filleted I-beam profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]

        # Web position
        XA1 = W / 2 - TW / 2  # left face of web
        XA2 = W / 2 + TW / 2  # right face of web

        # Calculate flange angle offset for IPN
        Yd = 0
        if is_ipn:
            Yd = (W / 4) * math.tan(math.pi * flange_angle / 180)

        # Create points for profile
        p1 = vec(0 + w, 0 + h, 0)
        p2 = vec(0 + w, TF + h - Yd, 0)
        p3 = vec(XA1 + w, TF + h + Yd, 0)
        p4 = vec(XA1 + w, H - TF + h - Yd, 0)
        p5 = vec(0 + w, H - TF + h + Yd, 0)
        p6 = vec(0 + w, H + h, 0)
        p7 = vec(W + w, H + h, 0)
        p8 = vec(W + w, H - TF + h + Yd, 0)
        p9 = vec(XA2 + w, H - TF + h - Yd, 0)
        p10 = vec(XA2 + w, TF + h + Yd, 0)
        p11 = vec(W + w, TF + h - Yd, 0)
        p12 = vec(W + w, 0 + h, 0)

        # Create lines
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p2, p3)
        L3 = Part.makeLine(p3, p4)
        L4 = Part.makeLine(p4, p5)
        L5 = Part.makeLine(p5, p6)
        L6 = Part.makeLine(p6, p7)
        L7 = Part.makeLine(p7, p8)
        L8 = Part.makeLine(p8, p9)
        L9 = Part.makeLine(p9, p10)
        L10 = Part.makeLine(p10, p11)
        L11 = Part.makeLine(p11, p12)
        L12 = Part.makeLine(p12, p1)

        # Create wire and face
        wire = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12])
        return Part.Face(wire)

    def create_filleted_ipe_he(self, obj, params):
        """Create a filleted IPE/HEA/HEB/HEM beam profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        w = params["w"]
        h = params["h"]
        R = params["radius_large"]
        d = vec(0, 0, 1)

        # Web position
        XA1 = W / 2 - TW / 2  # left face of web
        XA2 = W / 2 + TW / 2  # right face of web

        # Create points
        p1 = vec(0 + w, 0 + h, 0)
        p2 = vec(0 + w, TF + h, 0)
        p3 = vec(XA1 - R + w, TF + h, 0)
        p4 = vec(XA1 + w, TF + R + h, 0)
        p5 = vec(XA1 + w, H - TF - R + h, 0)
        p6 = vec(XA1 - R + w, H - TF + h, 0)
        p7 = vec(0 + w, H - TF + h, 0)
        p8 = vec(0 + w, H + h, 0)
        p9 = vec(W + w, H + h, 0)
        p10 = vec(W + w, H - TF + h, 0)
        p11 = vec(XA2 + R + w, H - TF + h, 0)
        p12 = vec(XA2 + w, H - TF - R + h, 0)
        p13 = vec(XA2 + w, TF + R + h, 0)
        p14 = vec(XA2 + R + w, TF + h, 0)
        p15 = vec(W + w, TF + h, 0)
        p16 = vec(W + w, 0 + h, 0)

        # Create centers for arcs
        c1 = vec(XA1 - R + w, TF + R + h, 0)
        c2 = vec(XA1 - R + w, H - TF - R + h, 0)
        c3 = vec(XA2 + R + w, H - TF - R + 0)
        c4 = vec(XA2 + R + w, TF + R + h, 0)

        # Create lines and arcs
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p2, p3)
        L3 = Part.makeLine(p4, p5)
        L4 = Part.makeLine(p6, p7)
        L5 = Part.makeLine(p7, p8)
        L6 = Part.makeLine(p8, p9)
        L7 = Part.makeLine(p9, p10)
        L8 = Part.makeLine(p10, p11)
        L9 = Part.makeLine(p12, p13)
        L10 = Part.makeLine(p14, p15)
        L11 = Part.makeLine(p15, p16)
        L12 = Part.makeLine(p16, p1)

        A1 = Part.makeCircle(R, c1, d, 270, 0)
        A2 = Part.makeCircle(R, c2, d, 0, 90)
        A3 = Part.makeCircle(R, c3, d, 90, 180)
        A4 = Part.makeCircle(R, c4, d, 180, 270)

        # Create wire and face
        wire = Part.Wire(
            [L1, L2, A1, L3, A2, L4, L5, L6, L7, L8, A3, L9, A4, L10, L11, L12]
        )
        return Part.Face(wire)

    def create_filleted_ipn(self, obj, params, flange_angle):
        """Create a filleted IPN beam profile face"""
        W = params["width"]
        H = params["height"]
        TW = params["thickness"]
        TF = params["flange_thickness"]
        r = params["radius_small"]
        R = params["radius_large"]
        w = params["w"]
        h = params["h"]
        d = vec(0, 0, 1)

        # Calculate angles and offsets
        angarc = flange_angle
        angrad = math.pi * angarc / 180
        sina = math.sin(angrad)
        cosa = math.cos(angrad)
        tana = math.tan(angrad)

        # Calculate geometry points (IPN has a more complex geometry)
        cot1 = W / 4 * tana
        cot2 = TF - cot1
        cot3 = r * cosa
        cot4 = r - cot3 * tana
        cot5 = cot2 + cot4 * tana
        cot6 = R * sina
        cot7 = W / 4 - R - TW / 2
        cot8 = cot6 + cot7
        cot9 = cot7 * tana
        cot10 = R * cosa

        # Define centers for arcs
        xc1 = r
        yc1 = cot5 - cot3
        c1 = vec(xc1 + w, yc1 + h, 0)

        xc2 = W / 2 - TW / 2 - R
        yc2 = cot9 + TF + cot10
        c2 = vec(xc2 + w, yc2 + h, 0)

        xc3 = xc2
        yc3 = H - yc2
        c3 = vec(xc3 + w, yc3 + h, 0)

        xc4 = xc1
        yc4 = H - yc1
        c4 = vec(xc4 + w, yc4 + h, 0)

        xc5 = W - xc1
        yc5 = yc4
        c5 = vec(xc5 + w, yc5 + h, 0)

        xc6 = W - xc2
        yc6 = yc3
        c6 = vec(xc6 + w, yc6 + h, 0)

        xc7 = xc6
        yc7 = yc2
        c7 = vec(xc7 + w, yc7 + h, 0)

        xc8 = xc5
        yc8 = yc1
        c8 = vec(xc8 + w, yc8 + h, 0)

        # Create arcs
        A1 = Part.makeCircle(r, c1, d, 90 + angarc, 180)
        A2 = Part.makeCircle(R, c2, d, 270 + angarc, 0)
        A3 = Part.makeCircle(R, c3, d, 0, 90 - angarc)
        A4 = Part.makeCircle(r, c4, d, 180, 270 - angarc)
        A5 = Part.makeCircle(r, c5, d, 270 + angarc, 0)
        A6 = Part.makeCircle(R, c6, d, 90 + angarc, 180)
        A7 = Part.makeCircle(R, c7, d, 180, 270 - angarc)
        A8 = Part.makeCircle(r, c8, d, 0, 90 - angarc)

        # Define all points
        xp1, yp1 = 0, 0
        p1 = vec(xp1 + w, yp1 + h, 0)

        xp2, yp2 = 0, cot5 - cot3
        p2 = vec(xp2 + w, yp2 + h, 0)

        xp3, yp3 = cot4, cot5
        p3 = vec(xp3 + w, yp3 + h, 0)

        xp4, yp4 = W / 4 + cot8, TF + cot9
        p4 = vec(xp4 + w, yp4 + h, 0)

        xp5, yp5 = W / 2 - TW / 2, yc2
        p5 = vec(xp5 + w, yp5 + h, 0)

        xp6, yp6 = xp5, H - yp5
        p6 = vec(xp6 + w, yp6 + h, 0)

        xp7, yp7 = xp4, H - yp4
        p7 = vec(xp7 + w, yp7 + h, 0)

        xp8, yp8 = xp3, H - yp3
        p8 = vec(xp8 + w, yp8 + h, 0)

        xp9, yp9 = xp2, H - yp2
        p9 = vec(xp9 + w, yp9 + h, 0)

        xp10, yp10 = xp1, H
        p10 = vec(xp10 + w, yp10 + h, 0)

        xp11, yp11 = W, H
        p11 = vec(xp11 + w, yp11 + h, 0)

        xp12, yp12 = xp11, yp9
        p12 = vec(xp12 + w, yp12 + h, 0)

        xp13, yp13 = W - xp8, yp8
        p13 = vec(xp13 + w, yp13 + h, 0)

        xp14, yp14 = W - xp7, yp7
        p14 = vec(xp14 + w, yp14 + h, 0)

        xp15, yp15 = W - xp6, yp6
        p15 = vec(xp15 + w, yp15 + h, 0)

        xp16, yp16 = W - xp5, yp5
        p16 = vec(xp16 + w, yp16 + h, 0)

        xp17, yp17 = W - xp4, yp4
        p17 = vec(xp17 + w, yp17 + h, 0)

        xp18, yp18 = W - xp3, yp3
        p18 = vec(xp18 + w, yp18 + h, 0)

        xp19, yp19 = W - xp2, yp2
        p19 = vec(xp19 + w, yp19 + h, 0)

        xp20, yp20 = W, 0
        p20 = vec(xp20 + w, yp20 + h, 0)

        # Create lines
        L1 = Part.makeLine(p1, p2)
        L2 = Part.makeLine(p3, p4)
        L3 = Part.makeLine(p5, p6)
        L4 = Part.makeLine(p7, p8)
        L5 = Part.makeLine(p9, p10)
        L6 = Part.makeLine(p10, p11)
        L7 = Part.makeLine(p11, p12)
        L8 = Part.makeLine(p13, p14)
        L9 = Part.makeLine(p15, p16)
        L10 = Part.makeLine(p17, p18)
        L11 = Part.makeLine(p19, p20)
        L12 = Part.makeLine(p20, p1)

        # Create wire and face
        wire = Part.Wire(
            [
                L1,
                A1,
                L2,
                A2,
                L3,
                A3,
                L4,
                A4,
                L5,
                L6,
                L7,
                A5,
                L8,
                A6,
                L9,
                A7,
                L10,
                A8,
                L11,
                L12,
            ]
        )
        return Part.Face(wire)

    def get_profile_type(self, obj):
        """Return the profile type based on the object family"""
        if hasattr(obj, "ProfileFamily"):
            return obj.ProfileFamily
        return "I-Beam"  # Default type
