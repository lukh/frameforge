set(Namespace_SRCS
        freecad/frameforge/resources/icons/corner.svg
        freecad/frameforge/resources/icons/splitcurve.svg
        freecad/frameforge/resources/icons/warehouse_profiles.svg
        freecad/frameforge/resources/icons/warehouse_custom_profiles.svg
        freecad/frameforge/resources/icons/trim_extend.svg
        freecad/frameforge/resources/icons/metalwb.svg
        freecad/frameforge/resources/icons/line.svg
        freecad/frameforge/resources/icons/corner-end-miter.svg
        freecad/frameforge/resources/icons/discretize.svg
        freecad/frameforge/resources/icons/joincurve.svg
        freecad/frameforge/resources/icons/overlap.svg
        freecad/frameforge/resources/icons/box.svg
        freecad/frameforge/resources/icons/bom.svg
        freecad/frameforge/resources/icons/parts_list.svg
        freecad/frameforge/resources/icons/corner-coped-type.svg
        freecad/frameforge/resources/icons/corner-simple-type.svg
        freecad/frameforge/resources/icons/corner-end-trim.svg
        freecad/frameforge/resources/icons/list-remove.svg
        freecad/frameforge/resources/icons/extendcurve.svg
        freecad/frameforge/resources/icons/list-add.svg
        freecad/frameforge/resources/icons/extrude-cutout.svg

        freecad/frameforge/resources/images/profiles/Metal/HEB_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Square_Hollow.png
        freecad/frameforge/resources/images/profiles/Metal/HEM_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/UPN_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Round_Bar.png
        freecad/frameforge/resources/images/profiles/Metal/UPE.png
        freecad/frameforge/resources/images/profiles/Metal/HEA.png
        freecad/frameforge/resources/images/profiles/Metal/HEA_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/HEB.png
        freecad/frameforge/resources/images/profiles/Metal/IPN_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/IPN.png
        freecad/frameforge/resources/images/profiles/Metal/UPN.png
        freecad/frameforge/resources/images/profiles/Metal/Square_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Unequal_Leg_Angles.png
        freecad/frameforge/resources/images/profiles/Metal/Flat_Sections.png
        freecad/frameforge/resources/images/profiles/Metal/IPE.png
        freecad/frameforge/resources/images/profiles/Metal/UPE_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Unequal_Leg_Angles_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Rectangular_Hollow_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/HEM.png
        freecad/frameforge/resources/images/profiles/Metal/Square_Hollow_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Equal_Leg_Angles_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Equal_Leg_Angles.png
        freecad/frameforge/resources/images/profiles/Metal/Rectangular_Hollow.png
        freecad/frameforge/resources/images/profiles/Metal/IPE_Fillet.png
        freecad/frameforge/resources/images/profiles/Metal/Pipe.png
        freecad/frameforge/resources/images/profiles/Metal/Square.png
        freecad/frameforge/resources/images/profiles/Warehouse.png

        freecad/frameforge/resources/ui/create_trimmed_profiles.ui
        freecad/frameforge/resources/ui/create_profiles.ui
        freecad/frameforge/resources/ui/create_custom_profiles.ui

        freecad/frameforge/resources/profiles/metal.json

        freecad/frameforge/version.py
        freecad/frameforge/translate_utils.py
        freecad/frameforge/create_trimmed_profiles_tool.py
        freecad/frameforge/edit_profile_tool.py
        freecad/frameforge/profile.py
        freecad/frameforge/_utils.py
        freecad/frameforge/parametric_line.py
        freecad/frameforge/__init__.py
        freecad/frameforge/create_end_miter_tool.py
        freecad/frameforge/trimmed_profile.py
        freecad/frameforge/init_gui.py
        freecad/frameforge/create_profiles_tool.py
        freecad/frameforge/create_custom_profiles_tool.py
)

SOURCE_GROUP("" FILES ${Namespace_SRCS})

ADD_CUSTOM_TARGET(SEARCHBAR ALL
        SOURCES ${Namespace_SRCS}
)

fc_copy_sources(SEARCHBAR "${CMAKE_BINARY_DIR}/Mod/FrameForge" ${Namespace_SRCS})

INSTALL(
    FILES
        ${Namespace_SRCS}
    DESTINATION
        Mod/SearchBar
)
