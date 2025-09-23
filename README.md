# FrameForge

Frameforge is a FreeCAD workbench that aids in designing beams and frames, with cut, mitter joins and so on.

## Prerequisite

- FreeCAD ≥ v0.21.x

## Installation

Frameforge workbench can be installed via the [Addon Manager](https://wiki.freecad.org/Std_AddonMgr)

## Quick Start

### Create the skeleton

Beams are mapped onto Edges or ParametricLine (from a Sketch for instance)

For a start, we are going to create a simple frame.

1. In a new file, switch to the Frameforge workbench.
2. Create a [sketch](https://wiki.freecad.org/Sketcher_NewSketch)  
3. A dialog will open asking you to 'Select orientation'. Choose the XY for instance.
3. Draw a simple square in the sketch... this will be our skeleton

![Create Skeleton](docs/images/02-create-frame-skeleton.png)

5. Close the Sketch edit mode.

### Create the frame

1. Launch the FrameForge Profile tool

![profile](docs/images/10-profiles.png)

2. It opens a FrameForge dialog (with options)

![profile](docs/images/10-profiles-task.png)
![profile](docs/images/10-profiles-task-2.png)

3. Select a profile from the lists (Material / Family / Size).  
*Note*: Size can be adjusted just below the family, the tool has a lot of predefined profiles. Same for parameters.

![profiles choice](docs/images/11-profiles-family.png)

4. In the 3D View, select edges to apply the profile creation:

![Edge Selection](docs/images/13-edge-selection.png)

5. Press OK in the Create Profile Task.  
**Result**: now there are four profiles!

![Profiles](docs/images/14-profiles-done.png)

![Zoom in profile](docs/images/14-zoom-on-profiles.png)

**Voila!** You have your first frame! For more information, follow the [tutorial](docs/tutorial.md)

## Maintainer

Vivien HENRY
vivien.henry@inductivebrain.fr


## Credits

This workbench is based on [MetalWB](https://framagit.org/Veloma/freecad_metal_workbench)

Special thanks to:

- Vincent B
- Quentin Plisson
- rockn
- Jonathan Wiedemann

And others people that I don't know but they should be in this [thread](https://forum.freecad.org/viewtopic.php?style=5&t=72389)


## Changelog

* v0.1.5
  - Add ExtrudedCutout
  - Add BOM
  - Add linting
  - Fix typo

* v0.1.4
  - Split UI for create_profiles
  - Rename Profile CutType 
  - Edit Profile
  - Add size, family, material in obj
  - fix #28, center offset on circular profile
  - Add wood profiles

* v0.1.3
  - Fix #10, Non attached profile (move profile inside the sketch 's parent)
  - Fix #27, Link to object go out of the allowed scope
  - Implement #23 Allow profile creation with selection of a whole sketch
  - Allows to create a Part to group all the Profile
  - Profile Naming Option

* v0.1.2
  - Fix recursive import
* v0.1.1
  - remove f-string with quote and double quote
* v0.1.0
  - Porting code from MetalWB
  - Improving UI
  - Split Corners into EndTrim and EndMiter


## LICENSE

FrameForge is licensed under the [GPLv3](LICENSE)
