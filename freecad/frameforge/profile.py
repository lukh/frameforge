import math

import FreeCAD as App
import Part

from .profile_generators import *

# Global variable for a 3D float vector (used in Profile class)
vec = App.Base.Vector

class Profile:
    # Add a flag to prevent recursive execution
    _busy = False

    def __init__(self, obj, init_w, init_h, init_mt, init_ft, init_r1, init_r2, init_len, init_wg, init_mf,
                 init_hc, init_wc, fam, bevels_combined, link_sub=None):
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

        self.WM = init_wg
        self.fam = fam
        self.bevels_combined = bevels_combined
        obj.Proxy = self

    def on_changed(self, obj, prop):
        """This method is kept for backward compatibility"""

        update_props = [
            "ProfileWidth",
            "ProfileHeight",
            "Thickness",
            "ThicknessFlange",
            "RadiusLarge",
            "RadiusSmall",
            "MakeFillet",
            "ProfileLength",
            "BevelStartCut1",
            "BevelEndCut1",
            "BevelStartCut2",
            "BevelEndCut2",
            "BevelStartCut",
            "BevelEndCut",
            "BevelStartRotate",
            "BevelEndRotate",
            "OffsetA",
            "OffsetB",
        ]

        # Only execute if not already busy and the property is in update_props
        if prop in update_props and not Profile._busy:
            try:
                Profile._busy = True
                self.execute(obj)
            finally:
                Profile._busy = False

    def execute(self, obj):

        try:
            L = obj.Target[0].getSubObject(obj.Target[1][0]).Length
            L += obj.OffsetA + obj.OffsetB
            obj.ProfileLength = L
        except:
            L = obj.ProfileLength + obj.OffsetA + obj.OffsetB

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

        if obj.CenteredOnWidth == True:  w = -W / 2
        if obj.CenteredOnHeight == True: h = -H / 2

        # First try to get family from object property if it exists
        if hasattr(obj, 'ProfileFamily') and obj.ProfileFamily:
            self.fam = obj.ProfileFamily

        # Directly select an appropriate generator based on profile family
        generator = None
        if self.fam in ['Square Hollow', 'Rectangular Hollow']:
            generator = RectangularHollowGenerator()
        elif self.fam in ['Equal Leg Angles', 'Unequal Leg Angles']:
            generator = AngleGenerator()
        elif self.fam == 'Pipe':
            generator = PipeGenerator()
        elif self.fam in ['IPE', 'IPN', 'HEA', 'HEB', 'HEM']:
            generator = BeamGenerator()
        elif self.fam in ['UPE', 'UPN']:
            generator = ChannelGenerator()
        elif self.fam == 'Square':
            generator = SquareBarGenerator()
        elif self.fam == 'Flat Sections':
            generator = RectangularBarGenerator()
        elif self.fam == 'Round Bar':
            generator = RoundBarGenerator()
        # Use the generator if one was selected
        if generator:
            shape = generator.generate_shape(obj)

            # Apply bevels if needed
            any_bevel = False
            if self.bevels_combined:
                any_bevel = obj.BevelStartCut or obj.BevelEndCut or obj.BevelStartRotate or obj.BevelEndRotate
            else:
                any_bevel = obj.BevelStartCut1 or obj.BevelEndCut1 or obj.BevelStartCut2 or obj.BevelEndCut2

            if any_bevel:
                shape = generator.apply_bevels(shape, obj, self.bevels_combined)

            obj.Shape = shape
            obj.Placement = pl
            obj.positionBySupport()
            return

        # Fallback to traditional approach (existing code)
        else:
            error_msg = 'Profile family \'{}\' is not implemented in the generator system'.format(self.fam)
            App.Console.PrintError(error_msg + '\n')
