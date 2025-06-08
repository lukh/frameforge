import math

import FreeCAD as App
import Part

# Global variable for a 3D float vector (used in Profile class)
vec = App.Base.Vector

class Profile:
    def __init__(self, obj, init_w, init_h, init_mt, init_ft, init_r1, init_r2, init_len, init_wg, init_mf,
             init_hc, init_wc, fam, bevels_combined, link_sub=None, unit="mm"):
        """
        Constructor. Add properties to FreeCAD Profile object. Profile object have 11 nominal properties associated
        with initialization value 'init_w' to 'init_wc' : ProfileHeight, ProfileWidth, [...] CenteredOnWidth. Depending
        on 'bevels_combined' parameters, there is 4 others properties for bevels : BevelStartCut1, etc. Depending on
        'fam' parameter, there is properties specific to profile family.
        """

        obj.addProperty("App::PropertyFloat", "ProfileHeight", "Profile", "", ).ProfileHeight = init_h
        obj.addProperty("App::PropertyFloat", "ProfileWidth", "Profile", "").ProfileWidth = init_w
        obj.addProperty("App::PropertyFloat", "ProfileLength", "Profile", "").ProfileLength = init_len # should it be ?

        obj.addProperty("App::PropertyFloat", "Thickness", "Profile",
                        "Thickness of all the profile or the web").Thickness = init_mt
        obj.addProperty("App::PropertyFloat", "ThicknessFlange", "Profile",
                        "Thickness of the flanges").ThicknessFlange = init_ft

        obj.addProperty("App::PropertyFloat", "RadiusLarge", "Profile", "Large radius").RadiusLarge = init_r1
        obj.addProperty("App::PropertyFloat", "RadiusSmall", "Profile", "Small radius").RadiusSmall = init_r2
        obj.addProperty("App::PropertyBool", "MakeFillet", "Profile",
                        "Whether to draw the fillets or not").MakeFillet = init_mf

        if not bevels_combined:
            obj.addProperty("App::PropertyFloat", "BevelStartCut1", "Profile",
                            "Bevel on First axle at the start of the profile").BevelStartCut1 = 0
            obj.addProperty("App::PropertyFloat", "BevelStartCut2", "Profile",
                            "Rotate the cut on Second axle at the start of the profile").BevelStartCut2 = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut1", "Profile",
                            "Bevel on First axle at the end of the profile").BevelEndCut1 = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut2", "Profile",
                            "Rotate the cut on Second axle at the end of the profile").BevelEndCut2 = 0
        if bevels_combined:
            obj.addProperty("App::PropertyFloat", "BevelStartCut", "Profile",
                            "Bevel at the start of the profile").BevelStartCut = 0
            obj.addProperty("App::PropertyFloat", "BevelStartRotate", "Profile",
                            "Rotate the second cut on Profile axle").BevelStartRotate = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut", "Profile",
                            "Bevel on First axle at the end of the profile").BevelEndCut = 0
            obj.addProperty("App::PropertyFloat", "BevelEndRotate", "Profile",
                            "Rotate the second cut on Profile axle").BevelEndRotate = 0

        obj.addProperty("App::PropertyFloat", "ApproxWeight", "Base",
                        "Approximate weight in Kilogram").ApproxWeight = init_wg * init_len / 1000

        obj.addProperty("App::PropertyBool", "CenteredOnHeight", "Profile",
                        "Choose corner or profile centre as origin").CenteredOnHeight = init_hc
        obj.addProperty("App::PropertyBool", "CenteredOnWidth", "Profile",
                        "Choose corner or profile centre as origin").CenteredOnWidth = init_wc

        if fam == "UPE":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57
        if fam == "UPN":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57

        if fam == "IPE" or fam == "HEA" or fam == "HEB" or fam == "HEM":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8
        if fam == "IPN":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8

        obj.addProperty("App::PropertyLength", "Width", "Structure",
                        "Parameter for structure").Width = obj.ProfileWidth  # Property for structure
        obj.addProperty("App::PropertyLength", "Height", "Structure",
                        "Parameter for structure").Height = obj.ProfileLength  # Property for structure
        obj.addProperty("App::PropertyLength", "Length", "Structure",
                        "Parameter for structure", ).Length = obj.ProfileHeight  # Property for structure
        obj.setEditorMode("Width", 1)  # user doesn't change !
        obj.setEditorMode("Height", 1)
        obj.setEditorMode("Length", 1)

        obj.addProperty("App::PropertyFloat", "OffsetA", "Structure",
                        "Parameter for structure").OffsetA = .0  # Property for structure

        obj.addProperty("App::PropertyFloat", "OffsetB", "Structure",
                        "Parameter for structure").OffsetB = .0  # Property for structure

        if link_sub:
            obj.addProperty("App::PropertyLinkSub", "Target", "Base", "Target face").Target = link_sub
            obj.setExpression('.AttachmentOffset.Base.z', u'-OffsetA')

        # Add a property to store family type
        obj.addProperty("App::PropertyString", "ProfileFamily", "Profile", 
                   "Profile family type (IPE, UPN, etc.)").ProfileFamily = fam

        # Keep the proxy attribute for backward compatibility
        self.fam = fam
        self.bevels_combined = bevels_combined
        self.unit = unit  # Store the unit from JSON
        obj.Proxy = self

    def on_changed(self, obj, p):

        if p == "ProfileWidth" or p == "ProfileHeight" or p == "Thickness" \
                or p == "FilletRadius" or p == "Centered" or p == "Length" \
                or p == "BevelStartCut1" or p == "BevelEndCut1" \
                or p == "BevelStartCut2" or p == "BevelEndCut2" \
                or p == "BevelStartCut" or p == "BevelEndCut" \
                or p == "BevelStartRotate" or p == "BevelEndRotate" \
                or p == "OffsetA" or p == "OffsetB" :
            self.execute(obj)

    def execute(self, obj):
        try:
            L = obj.Target[0].getSubObject(obj.Target[1][0]).Length
            L += obj.OffsetA + obj.OffsetB
            obj.ProfileLength = L
        except:
            L = obj.ProfileLength + obj.OffsetA + obj.OffsetB

        # Add safety check for WM attribute
        if not hasattr(self, 'WM'):
            self.WM = getattr(obj, 'ApproxWeight', 0) * 1000 / max(L, 1)  # Recover from obj if possible
            
        # Add safety check for bevels_combined attribute
        if not hasattr(self, 'bevels_combined'):
            # Check if object has combined bevel properties
            if hasattr(obj, 'BevelStartCut') and hasattr(obj, 'BevelStartRotate'):
                self.bevels_combined = True
            # Check if object has separate bevel properties
            elif hasattr(obj, 'BevelStartCut1') and hasattr(obj, 'BevelStartCut2'):
                self.bevels_combined = False
            else:
                # Default if we can't determine
                self.bevels_combined = True
    
        # Add safety check for unit attribute
        if not hasattr(self, 'unit'):
            self.unit = 'mm'  # Default to mm
            
        # Add safety check for fam attribute
        if not hasattr(self, 'fam'):
            # First try to get family from object property if available
            if hasattr(obj, 'ProfileFamily') and obj.ProfileFamily:
                self.fam = obj.ProfileFamily
            # Otherwise keep the fallback logic for backward compatibility
            elif not hasattr(self, 'fam'):
                # Try to determine family from object properties
                if hasattr(obj, 'IPN') and obj.IPN:
                    self.fam = "IPN"
                    # Also set the property for future use
                    if hasattr(obj, 'ProfileFamily'):
                        obj.ProfileFamily = self.fam
                elif hasattr(obj, 'UPN') and obj.UPN:
                    self.fam = "UPN"
                # Use aspect ratio to guess if we can't determine from properties
                elif obj.ProfileHeight > 0 and obj.ProfileWidth > 0:
                    ratio = obj.ProfileWidth / obj.ProfileHeight
                    if 0.95 < ratio < 1.05:  # Nearly equal
                        self.fam = "Square"
                    else:
                        self.fam = "Rectangular Hollow"
                else:
                    self.fam = "Square"  # Safe default

        obj.ApproxWeight = self.WM * L / 1000
        W = obj.ProfileWidth
        H = obj.ProfileHeight
        obj.Height = L
        pl = obj.Placement
        TW = obj.Thickness
        TF = obj.ThicknessFlange

        R = obj.RadiusLarge
        r = obj.RadiusSmall
        d = vec(0, 0, 1)

        if W == 0: W = H
        w = h = 0
        
        try:
        # Use the unit from JSON instead of deriving from Width
            if hasattr(self, 'unit'):
                # Convert unit name to FreeCAD unit suffix
                unit_map = {
                    'mm': 'mm', 
                    'cm': 'cm',
                    'in': 'in',
                    'inch': 'in',
                    'Metric Unit': 'mm',
                    'Metric Units': 'mm',
                    'Imperial': 'in'
                }
                
                unit_suffix = unit_map.get(self.unit, 'mm')
            else:
                # Fallback to deriving from Width if unit is not available
                unit_suffix = str(App.Units.parseQuantity(str(W)).getUserPreferred()[2])
        
            # Convert all dimension variables to explicit quantities
            W_q = App.Units.Quantity(str(W) + ' ' + unit_suffix)
            H_q = App.Units.Quantity(str(H) + ' ' + unit_suffix) 
            TW_q = App.Units.Quantity(str(TW) + ' ' + unit_suffix)
            TF_q = App.Units.Quantity(str(TF) + ' ' + unit_suffix)
            R_q = App.Units.Quantity(str(R) + ' ' + unit_suffix)
            r_q = App.Units.Quantity(str(r) + ' ' + unit_suffix)
            
            # Create zero quantities with matching units
            self.zero_w = App.Units.Quantity('0' + unit_suffix)
            self.zero_h = App.Units.Quantity('0' + unit_suffix)
            
            # Handle w and h offset calculations with proper units
            if obj.CenteredOnWidth == True:
                w = -W_q/2
            else:
                w = self.zero_w
            
            if obj.CenteredOnHeight == True:
                h = -H_q/2
            else:
                h = self.zero_h
            
        except Exception as e:
            App.Console.PrintError(f"Unit conversion error: {str(e)}\n")
            App.Console.PrintError(f"W is: {W}, H is: {H}, TW is: {TW}, TF is: {TF}, R is: {R}, r is: {r}\n")
            # Fallback to mm if unit parsing fails
            unit_suffix = 'mm'
            
            # ADD SPACES BETWEEN NUMBERS AND UNITS
            W_q = App.Units.Quantity(str(W) + ' mm')  # Add space here
            H_q = App.Units.Quantity(str(H) + ' mm')  # Add space here
            TW_q = App.Units.Quantity(str(TW) + ' mm')  # Add space here
            TF_q = App.Units.Quantity(str(TF) + ' mm')  # Add space here
            R_q = App.Units.Quantity(str(R) + ' mm')  # Add space here
            r_q = App.Units.Quantity(str(r) + ' mm')  # Add space here
            
            self.zero_w = App.Units.Quantity('0 mm')  # Add space here
            self.zero_h = App.Units.Quantity('0 mm')  # Add space here

# Always use mm for the z-coordinate
        self.zero_unit = App.Units.Quantity('0 mm')  # Add space here
    
    # NOW USE W_q, H_q, TW_q, TF_q, R_q, r_q INSTEAD OF W, H, TW, TF, R, r
    # IN ALL VECTOR CALCULATIONS

        if self.bevels_combined == False:
            if obj.BevelStartCut1 > 60: obj.BevelStartCut1 = 60
            if obj.BevelStartCut1 < -60: obj.BevelStartCut1 = -60
            if obj.BevelStartCut2 > 60: obj.BevelStartCut2 = 60
            if obj.BevelStartCut2 < -60: obj.BevelStartCut2 = -60

            if obj.BevelEndCut1 > 60: obj.BevelEndCut1 = 60
            if obj.BevelEndCut1 < -60: obj.BevelEndCut1 = -60
            if obj.BevelEndCut2 > 60: obj.BevelEndCut2 = 60
            if obj.BevelEndCut2 < -60: obj.BevelEndCut2 = -60

            B1Y = obj.BevelStartCut1
            B2Y = -obj.BevelEndCut1
            B1X = -obj.BevelStartCut2
            B2X = obj.BevelEndCut2
            B1Z = 0
            B2Z = 0

        if self.bevels_combined == True:
            if obj.BevelStartCut > 60: obj.BevelStartCut = 60
            if obj.BevelStartCut < -60: obj.BevelStartCut = -60
            if obj.BevelStartRotate > 60: obj.BevelStartRotate = 60
            if obj.BevelStartRotate < -60: obj.BevelStartRotate = -60

            if obj.BevelEndCut > 60: obj.BevelEndCut = 60
            if obj.BevelEndCut < -60: obj.BevelEndCut = -60
            if obj.BevelEndRotate > 60: obj.BevelEndRotate = 60
            if obj.BevelEndRotate < -60: obj.BevelEndRotate = -60

            B1Y = obj.BevelStartCut
            B1Z = -obj.BevelStartRotate
            B2Y = -obj.BevelEndCut
            B2Z = -obj.BevelEndRotate
            B1X = 0
            B2X = 0
        """
        if obj.CenteredOnWidth == True:
            w = -W / 2
        if obj.CenteredOnHeight == True:
            h = -H / 2
        """

        if self.fam == "Equal Leg Angles" or self.fam == "Unequal Leg Angles":
            if obj.MakeFillet == False:
                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(TW_q + w, H_q + h, self.zero_unit)  # Should use TW_q
                p4 = vec(TW_q + w, TW_q + h, self.zero_unit)   # Should use TW_q twice
                p5 = vec(W_q + w, TW_q + h, self.zero_unit)  # Should use TW_q
                p6 = vec(W_q + w, self.zero_h + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6])

            if obj.MakeFillet == True:
                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(TW_q - r_q + w, H_q + h, self.zero_unit)
                p4 = vec(TW_q + w, H_q - r_q + h, self.zero_unit)
                p5 = vec(TW_q + w, TW_q + R_q + h, self.zero_unit)
                p6 = vec(TW_q + R_q + w, TW_q + h, self.zero_unit)
                p7 = vec(W_q - r_q + w, TW_q + h, self.zero_unit)
                p8 = vec(W_q + w, TW_q - r_q + h, self.zero_unit)
                p9 = vec(W_q + w, self.zero_h + h, self.zero_unit)
                c1 = vec(TW_q - r_q + w, H_q - r_q + h, self.zero_unit)
                c2 = vec(TW_q + R_q + w, TW_q + R_q + h, self.zero_unit)
                c3 = vec(W_q - r_q + w, TW_q - r_q + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p8, p9)
                L6 = Part.makeLine(p9, p1)
                A1 = Part.makeCircle(r_q, c1, d, 0, 90)
                A2 = Part.makeCircle(R_q, c2, d, 180, 270)
                A3 = Part.makeCircle(r_q, c3, d, 0, 90)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, A3, L5, L6])

            p = Part.Face(wire1)

        if self.fam == "Flat Sections" or self.fam == "Square" or self.fam == "Square Hollow" or self.fam == "Rectangular Hollow":
            wire1 = wire2 = 0

            if self.fam == "Square" or self.fam == "Flat Sections":
                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(W_q + w, H_q + h, self.zero_unit)
                p4 = vec(W_q + w, self.zero_h + h, self.zero_unit)
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                wire1 = Part.Wire([L1, L2, L3, L4])

            if obj.MakeFillet == False and (self.fam == "Square Hollow" or self.fam == "Rectangular Hollow"):
                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(W_q + w, H_q + h, self.zero_unit)
                p4 = vec(W_q + w, self.zero_h + h, self.zero_unit)
                p5 = vec(TW_q + w, TW_q + h, self.zero_unit)
                p6 = vec(TW_q + w, H_q + h - TW_q, self.zero_unit)  # Should use H_q
                p7 = vec(W_q + w - TW_q, H_q + h - TW_q, self.zero_unit)
                p8 = vec(W_q + w - TW_q, TW_q + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p5)

                wire1 = Part.Wire([L1, L2, L3, L4])
                wire2 = Part.Wire([L5, L6, L7, L8])

            if obj.MakeFillet == True and (self.fam == "Square Hollow" or self.fam == "Rectangular Hollow"):
                p1 = vec(self.zero_w + w, self.zero_h + h + R_q, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q - R_q + h, self.zero_unit)
                p3 = vec(R_q + w, H_q + h, self.zero_unit)
                p4 = vec(W_q - R_q + w, H_q + h, self.zero_unit)
                p5 = vec(W_q + w, H_q - R_q + h, self.zero_unit)
                p6 = vec(W_q + w, R_q + h, self.zero_unit)
                p7 = vec(W_q - R_q + w, self.zero_h + h, self.zero_unit)
                p8 = vec(R_q + w, self.zero_h + h, self.zero_unit)

                c1 = vec(R_q + w, R_q + h, self.zero_unit)
                c2 = vec(R_q + w, H_q - R_q + h, self.zero_unit)
                c3 = vec(W_q - r_q + w, TW_q - r_q + h, self.zero_unit)
                c4 = vec(W_q - r_q + w, R_q + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(R_q, c1, d, 180, 270)
                A2 = Part.makeCircle(R_q, c2, d, 90, 180)
                A3 = Part.makeCircle(r, c3, d, 0, 90)
                A4 = Part.makeCircle(r, c4, d, 270, 0)

                wire1 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

                p1 = vec(TW_q + w, TW_q + r_q + h, self.zero_unit)
                p2 = vec(TW_q + w, H_q - TW_q - r_q + h, self.zero_unit)
                p3 = vec(TW_q + r_q + w, H_q - TW_q + h, self.zero_unit)
                p4 = vec(W_q - TW_q - r_q + w, H_q - TW_q + h, self.zero_unit)
                p5 = vec(W_q - TW_q + w, H_q - TW_q - r_q + h, self.zero_unit)
                p6 = vec(W_q - TW_q + w, TW_q + r_q + h, self.zero_unit)
                p7 = vec(W_q - TW_q - r_q + w, TW_q + h, self.zero_unit)
                p8 = vec(TW_q + r_q + w, TW_q + h, self.zero_unit)

                c1 = vec(TW_q + r_q + w, TW_q + r_q + h, self.zero_unit)
                c2 = vec(TW_q + r_q + w, H_q - TW_q - r_q + h, self.zero_unit)
                c3 = vec(W_q - TW_q - r_q + w, H_q - TW_q - r_q + h, self.zero_unit)
                c4 = vec(W_q - TW_q - r_q + w, TW_q + r_q + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(r_q, c1, d, 180, 270)
                A2 = Part.makeCircle(r_q, c2, d, 90, 180)
                A3 = Part.makeCircle(r_q, c3, d, 0, 90)
                A4 = Part.makeCircle(r_q, c4, d, 270, 0)

                wire2 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

            if wire2:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)

        if self.fam == "UPE" or self.fam == "UPN":
            if obj.MakeFillet == False:  # UPE ou UPN sans arrondis

                Yd = 0
                if obj.UPN == True: Yd = (W / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(self.zero_w + w + W_q, H_q + h, self.zero_unit)
                p4 = vec(self.zero_w + W_q + w, h, self.zero_unit)
                p5 = vec(self.zero_w + W_q + w + Yd - TW_q, h, self.zero_unit)
                p6 = vec(self.zero_w + W_q + w - Yd - TW_q, H_q + h - TF_q, self.zero_unit)
                p7 = vec(self.zero_w + w + TW_q + Yd, H_q + h - TF_q, self.zero_unit)
                p8 = vec(self.zero_w + w + TW_q - Yd, h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8])

            if obj.MakeFillet == True and obj.UPN == False:  # UPE avec arrondis

                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p3 = vec(self.zero_w + w + W_q, H_q + h, self.zero_unit)
                p4 = vec(self.zero_w + W_q + w, h, self.zero_unit)
                p5 = vec(self.zero_w + W_q + w - TW_q + r_q, h, self.zero_unit)
                p6 = vec(self.zero_w + W_q + w - TW_q, h + r_q, self.zero_unit)
                p7 = vec(self.zero_w + W_q + w - TW_q, H_q + h - TF_q - R_q, self.zero_unit)
                p8 = vec(self.zero_w + W_q + w - TW_q - R_q, H_q + h - TF_q, self.zero_unit)
                p9 = vec(self.zero_w + w + TW_q + R_q, H_q + h - TF_q, self.zero_unit)
                p10 = vec(self.zero_w + w + TW_q, H_q + h - TF_q - R_q, self.zero_unit)
                p11 = vec(self.zero_w + w + TW_q, h + r_q, self.zero_unit)
                p12 = vec(self.zero_w + w + TW_q - r_q, h, self.zero_unit)

                C1 = vec(self.zero_w + w + TW_q - r_q, h + r_q, self.zero_unit)
                C2 = vec(self.zero_w + w + TW_q + R_q, H_q + h - TF_q - R_q, self.zero_unit)
                C3 = vec(self.zero_w + w + W_q + r_q, H_q + h - TF_q - R_q, self.zero_unit)
                C4 = vec(self.zero_w + w + W_q + r_q, r_q + h, self.zero_unit)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p9, p1)
                A1 = Part.makeCircle(r_q, C1, d, 270, 0)
                A2 = Part.makeCircle(R_q, C2, d, 90, 180)
                A3 = Part.makeCircle(R_q, C3, d, 0, 90)
                A4 = Part.makeCircle(r_q, C4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, A4, L5, A3, L6, A2, L7, A1, L8])

            if obj.MakeFillet == True and obj.UPN == True:  # UPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)

                cot1 = r_q * sina
                y11 = r_q - cot1
                cot2 = (H_q / 2 - r) * tana
                cot3 = cot1 * tana
                x11 = TW_q - cot2 - cot3
                xc1 = TW_q - cot2 - cot3 - r_q * cosa
                yc1 = r_q
                cot8 = (H_q / 2 - R_q - TF_q + R_q * sina) * tana
                x10 = TW_q + cot8
                y10 = H_q - TF_q - R_q + R_q * sina
                xc2 = cot8 + R_q * cosa + TW_q
                yc2 = H_q - TF_q - R_q
                x12 = TW_q - cot2 - cot3 - r_q * cosa
                y12 = 0
                x9 = cot8 + R * cosa + TW
                y9 = H - TF
                xc3 = W - xc2
                yc3 = yc2
                xc4 = W - xc1
                yc4 = yc1
                x1 = 0
                y1 = 0
                x2 = 0
                y2 = H
                x3 = W
                y3 = H
                x4 = W
                y4 = 0
                x5 = W - x12
                y5 = 0
                x6 = W - x11
                y6 = y11
                x7 = W - x10
                y7 = y10
                x8 = W - x9
                y8 = y9

                c1 = vec(xc1 + w, yc1 + h, self.zero_unit)
                c2 = vec(xc2 + w, yc2 + h, self.zero_unit)
                c3 = vec(xc3 + w, yc3 + h, self.zero_unit)
                c4 = vec(xc4 + w, yc4 + h, self.zero_unit)

                p1 = vec(x1 + w, y1 + h, self.zero_unit)
                p2 = vec(x2 + w, y2 + h, self.zero_unit)
                p3 = vec(x3 + w, y3 + h, self.zero_unit)
                p4 = vec(x4 + w, y4 + h, self.zero_unit)
                p5 = vec(x5 + w, y5 + h, self.zero_unit)
                p6 = vec(x6 + w, y6 + h, self.zero_unit)
                p7 = vec(x7 + w, y7 + h, self.zero_unit)
                p8 = vec(x8 + w, y8 + h, self.zero_unit)
                p9 = vec(x9 + w, y9 + h, self.zero_unit)
                p10 = vec(x10 + w, y10 + h, self.zero_unit)
                p11 = vec(x11 + w, y11 + h, self.zero_unit)
                p12 = vec(x12 + w, y12 + h, self.zero_unit)

                A1 = Part.makeCircle(r_q, c1, d, 270, 0 - angarc)
                A2 = Part.makeCircle(R_q, c2, d, 90, 180 - angarc)
                A3 = Part.makeCircle(R_q, c3, d, 0 + angarc, 90)
                A4 = Part.makeCircle(r_q, c4, d, 180 + angarc, 270)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])

            p = Part.Face(wire1)

        if self.fam == "IPE" or self.fam == "IPN" or self.fam == "HEA" or self.fam == "HEB" or self.fam == "HEM":
            XA1 = W_q / 2 - TW_q / 2  # face gauche du web
            XA2 = W_q / 2 + TW_q / 2  # face droite du web
            if obj.MakeFillet == False:  # IPE ou IPN sans arrondis
                Yd = 0
                if obj.IPN == True: Yd = (W_q / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, TF_q + h - Yd, self.zero_unit)
                p3 = vec(XA1 + w, TF_q + h + Yd, self.zero_unit)
                p4 = vec(XA1 + w, H_q - TF_q + h - Yd, self.zero_unit)
                p5 = vec(self.zero_w + w, H_q - TF_q + h + Yd, self.zero_unit)
                p6 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p7 = vec(W_q + w, H_q + h, self.zero_unit)
                p8 = vec(W_q + w, H_q - TF_q + h + Yd, self.zero_unit)
                p9 = vec(XA2 + w, H_q - TF_q + h - Yd, self.zero_unit)
                p10 = vec(XA2 + w, TF_q + h + Yd, self.zero_unit)
                p11 = vec(W_q + w, TF_q + h - Yd, self.zero_unit)
                p12 = vec(W_q + w, self.zero_h + h, self.zero_unit)

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

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == False:  # IPE avec arrondis
                p1 = vec(self.zero_w + w, self.zero_h + h, self.zero_unit)
                p2 = vec(self.zero_w + w, TF_q + h, self.zero_unit)
                p3 = vec(XA1 - R_q + w, TF_q + h, self.zero_unit)
                p4 = vec(XA1 + w, TF_q + R_q + h, self.zero_unit)
                p5 = vec(XA1 + w, H_q - TF_q - R_q + h, self.zero_unit)
                p6 = vec(XA1 - R_q + w, H_q - TF_q + h, self.zero_unit)
                p7 = vec(self.zero_w + w, H_q - TF_q + h, self.zero_unit)
                p8 = vec(self.zero_w + w, H_q + h, self.zero_unit)
                p9 = vec(W_q + w, H_q + h, self.zero_unit)
                p10 = vec(W_q + w, H_q - TF_q + h, self.zero_unit)
                p11 = vec(XA2 + R_q + w, H_q - TF_q + h, self.zero_unit)
                p12 = vec(XA2 + w, H_q - TF_q - R_q + h, self.zero_unit)
                p13 = vec(XA2 + w, TF_q + R_q + h, self.zero_unit)
                p14 = vec(XA2 + R_q + w, TF_q + h, self.zero_unit)
                p15 = vec(W_q + w, TF_q + h, self.zero_unit)
                p16 = vec(W_q + w, self.zero_h + h, self.zero_unit)

                c1 = vec(XA1 - R_q + w, TF_q + R_q + h, self.zero_unit)
                c2 = vec(XA1 - R_q + w, H_q - TF_q - R_q + h, self.zero_unit)
                c3 = vec(XA2 + R_q + w, H_q - TF_q - R_q + h, self.zero_unit)
                c4 = vec(XA2 + R_q + w, TF_q + R_q + h, self.zero_unit)

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

                A1 = Part.makeCircle(R_q, c1, d, 270, 0)
                A2 = Part.makeCircle(R_q, c2, d, 0, 90)
                A3 = Part.makeCircle(R_q, c3, d, 90, 180)
                A4 = Part.makeCircle(R_q, c4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, L5, L6, L7, A3, L9, A4, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == True:  # IPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)
                cot1 = W_q / 4 * tana  # 1,47
                cot2 = TF_q - cot1  # 4,42
                cot3 = r_q * cosa  # 1,98
                cot4 = r_q - cot3 * tana  # 1,72
                cot5 = cot4 * tana  # 0,24
                cot5 = cot2 + cot5  # 4,66
                cot6 = R_q * sina  # 0,55
                cot7 = W_q / 4 - R_q - TW_q / 2  # 4,6
                cot8 = cot6 + cot7  # 5,15
                cot9 = cot7 * tana  # 0,72
                cot10 = R_q * cosa  # 3,96

                xc1 = r_q
                yc1 = cot5 - cot3
                c1 = vec(xc1 + w, yc1 + h, self.zero_unit)

                xc2 = W_q / 2 - TW_q / 2 - R_q
                yc2 = cot9 + TF_q + cot10
                c2 = vec(xc2 + w, yc2 + h, self.zero_unit)

                xc3 = xc2
                yc3 = H - yc2
                c3 = vec(xc3 + w, yc3 + h, self.zero_unit)

                xc4 = xc1
                yc4 = H - yc1
                c4 = vec(xc4 + w, yc4 + h, self.zero_unit)

                xc5 = W - xc1
                yc5 = yc4
                c5 = vec(xc5 + w, yc5 + h, self.zero_unit)

                xc6 = W - xc2
                yc6 = yc3
                c6 = vec(xc6 + w, yc6 + h, self.zero_unit)

                xc7 = xc6
                yc7 = yc2
                c7 = vec(xc7 + w, yc7 + h, self.zero_unit)

                xc8 = xc5
                yc8 = yc1
                c8 = vec(xc8 + w, yc8 + h, self.zero_unit)

                A1 = Part.makeCircle(r_q, c1, d, 90 + angarc, 180)
                A2 = Part.makeCircle(R_q, c2, d, 270 + angarc, 0)
                A3 = Part.makeCircle(R_q, c3, d, 0, 90 - angarc)
                A4 = Part.makeCircle(r_q, c4, d, 180, 270 - angarc)
                A5 = Part.makeCircle(r_q, c5, d, 270 + angarc, 0)
                A6 = Part.makeCircle(R_q, c6, d, 90 + angarc, 180)
                A7 = Part.makeCircle(R_q, c7, d, 180, 270 - angarc)
                A8 = Part.makeCircle(r_q, c8, d, 0, 90 - angarc)

                xp1 = 0
                yp1 = 0
                p1 = vec(xp1 + w, yp1 + h, self.zero_unit)

                xp2 = 0
                yp2 = cot5 - cot3
                p2 = vec(xp2 + w, yp2 + h, self.zero_unit)

                xp3 = cot4
                yp3 = cot5
                p3 = vec(xp3 + w, yp3 + h, self.zero_unit)

                xp4 = W_q / 4 + cot8
                yp4 = TF_q + cot9
                p4 = vec(xp4 + w, yp4 + h, self.zero_unit)

                xp5 = W_q / 2 - TW_q / 2
                yp5 = yc2
                p5 = vec(xp5 + w, yp5 + h, self.zero_unit)

                xp6 = xp5
                yp6 = H_q - yp5
                p6 = vec(xp6 + w, yp6 + h, self.zero_unit)

                xp7 = xp4
                yp7 = H_q - yp4
                p7 = vec(xp7 + w, yp7 + h, self.zero_unit)

                xp8 = xp3
                yp8 = H_q - yp3
                p8 = vec(xp8 + w, yp8 + h, self.zero_unit)

                xp9 = xp2
                yp9 = H_q - yp2
                p9 = vec(xp9 + w, yp9 + h, self.zero_unit)

                xp10 = xp1
                yp10 = H_q
                p10 = vec(xp10 + w, yp10 + h, self.zero_unit)

                xp11 = W_q
                yp11 = H_q
                p11 = vec(xp11 + w, yp11 + h, self.zero_unit)

                xp12 = xp11
                yp12 = yp9
                p12 = vec(xp12 + w, yp12 + h, self.zero_unit)

                xp13 = W_q - xp8
                yp13 = yp8
                p13 = vec(xp13 + w, yp13 + h, self.zero_unit)

                xp14 = W_q - xp7
                yp14 = yp7
                p14 = vec(xp14 + w, yp14 + h, self.zero_unit)

                xp15 = W_q - xp6
                yp15 = yp6
                p15 = vec(xp15 + w, yp15 + h, self.zero_unit)

                xp16 = W_q - xp5
                yp16 = yp5
                p16 = vec(xp16 + w, yp16 + h, self.zero_unit)

                xp17 = W_q - xp4
                yp17 = yp4
                p17 = vec(xp17 + w, yp17 + h, self.zero_unit)

                xp18 = W_q - xp3
                yp18 = yp3
                p18 = vec(xp18 + w, yp18 + h, self.zero_unit)

                xp19 = W_q - xp2
                yp19 = yp2
                p19 = vec(xp19 + w, yp19 + h, self.zero_unit)

                xp20 = W_q
                yp20 = 0
                p20 = vec(xp20 + w, yp20 + h, self.zero_unit)

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

                wire1 = Part.Wire([L1, A1, L2, A2, L3, A3, L4, A4, L5, L6, L7, A5, L8, A6, L9, A7, L10, A8, L11, L12])

            p = Part.Face(wire1)

        if self.fam == "Round Bar":
            c = vec(H_q / 2 + w, H_q / 2 + h, self.zero_unit)
            A1 = Part.makeCircle(H_q / 2, c, d, 0, 360)
            wire1 = Part.Wire([A1])
            p = Part.Face(wire1)

        if self.fam == "Pipe":
            c = vec(H_q / 2 + w, H_q / 2 + h, self.zero_unit)
            A1 = Part.makeCircle(H_q / 2, c, d, 0, 360)
            A2 = Part.makeCircle((H_q - TW_q) / 2, c, d, 0, 360)
            wire1 = Part.Wire([A1])
            wire2 = Part.Wire([A2])
            p1 = Part.Face(wire1)
            p2 = Part.Face(wire2)
            p = p1.cut(p2)

        if L:
                # Extract scalar value if L is a quantity
                L_value = L.Value if hasattr(L, 'Value') else L
                
                ProfileFull = p.extrude(vec(0, 0, L_value))
                obj.Shape = ProfileFull

                if B1Y or B2Y or B1X or B2X or B1Z or B2Z:  # make the bevels:
                    hc = 10 * max(H_q, W_q)
                    
                    # Extract scalar values from all quantities
                    hc_value = hc.Value if hasattr(hc, 'Value') else hc
                    w_value = w.Value if hasattr(w, 'Value') else w
                    h_value = h.Value if hasattr(h, 'Value') else h
                    
                    # Now we can safely add numeric values
                    extrude_length = L_value + hc_value / 4
                    
                    ProfileExt = ProfileFull.fuse(p.extrude(vec(0, 0, extrude_length)))
                    box = Part.makeBox(hc_value, hc_value, hc_value)
                    box.translate(vec(-hc_value / 2 + w_value, -hc_value / 2 + h_value, L_value))
                    pr = vec(0, 0, L_value)
                    box.rotate(pr, vec(0, 1, 0), B2Y)
                    if self.bevels_combined == True:
                        box.rotate(pr, vec(0, 0, 1), B2Z)
                    else:
                        box.rotate(pr, vec(1, 0, 0), B2X)
                    ProfileCut = ProfileExt.cut(box)

                    ProfileExt = ProfileCut.fuse(p.extrude(vec(0, 0, -hc_value / 4)))
                    box = Part.makeBox(hc_value, hc_value, hc_value)
                    box.translate(vec(-hc_value / 2 + w_value, -hc_value / 2 + h_value, -hc_value))
                    pr = vec(0, 0, 0)
                    box.rotate(pr, vec(0, 1, 0), B1Y)
                    if self.bevels_combined == True:
                        box.rotate(pr, vec(0, 0, 1), B1Z)
                    else:
                        box.rotate(pr, vec(1, 0, 0), B1X)
                    ProfileCut = ProfileExt.cut(box)

                    obj.Shape = ProfileCut.removeSplitter()

                # if wire2: obj.Shape = Part.Compound([wire1,wire2])  # OCC Sweep doesn't be able hollow shape yet :-(
        else:
            obj.Shape = Part.Face(wire1)
        obj.Placement = pl
        obj.positionBySupport()
        obj.recompute()

    def __getstate__(self):
        """Called when saving the document - return a serializable representation"""
        state = {
            "fam": self.fam if hasattr(self, 'fam') else None,
            "bevels_combined": self.bevels_combined if hasattr(self, 'bevels_combined') else False,
            "unit": self.unit if hasattr(self, 'unit') else "mm",
            # Add any other custom attributes here that need saving
        }
        return state

    def __setstate__(self, state):
        """Called when restoring the document - restore from serialized representation"""
        self.fam = state.get("fam")
        self.bevels_combined = state.get("bevels_combined", False)
        self.unit = state.get("unit", "mm")
        # Restore other custom attributes here
        return None
