# >>> # Gui.Selection.addSelection('Unnamed','Body','BaseFeature.Face2',631.032,745.084,10)
# >>> ### Begin command PartDesign_CompSketches
# >>> App.getDocument('Unnamed').getObject('Body').newObject('Sketcher::SketchObject','Sketch001')
# >>> App.getDocument('Unnamed').getObject('Sketch001').AttachmentSupport = (App.getDocument('Unnamed').getObject('BaseFeature'),['Face2',])
# >>> App.getDocument('Unnamed').getObject('Sketch001').MapMode = 'FlatFace'
# >>> App.ActiveDocument.recompute()
# >>> # Gui.getDocument('Unnamed').setEdit(App.getDocument('Unnamed').getObject('Body'), 0, 'Sketch001.')
# >>> # ActiveSketch = App.getDocument('Unnamed').getObject('Sketch001')
# >>> # tv = Show.TempoVis(App.ActiveDocument, tag= ActiveSketch.ViewObject.TypeId)
# >>> # ActiveSketch.ViewObject.TempoVis = tv
# >>> # if ActiveSketch.ViewObject.EditingWorkbench:
# >>> #   tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
# >>> # if ActiveSketch.ViewObject.HideDependent:
# >>> #   tv.hide(tv.get_all_dependent(App.getDocument('Unnamed').getObject('Body'), 'Sketch001.'))
# >>> # if ActiveSketch.ViewObject.ShowSupport:
# >>> #   tv.show([ref[0] for ref in ActiveSketch.AttachmentSupport if not ref[0].isDerivedFrom("PartDesign::Plane")])
# >>> # if ActiveSketch.ViewObject.ShowLinks:
# >>> #   tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
# >>> # tv.sketchClipPlane(ActiveSketch, ActiveSketch.ViewObject.SectionView)
# >>> # tv.hide(ActiveSketch)
# >>> # del(tv)
# >>> # del(ActiveSketch)
# >>> #
# >>> import PartDesignGui
# >>> # ActiveSketch = App.getDocument('Unnamed').getObject('Sketch001')
# >>> # if ActiveSketch.ViewObject.RestoreCamera:
# >>> #   ActiveSketch.ViewObject.TempoVis.saveCamera()
# >>> #   if ActiveSketch.ViewObject.ForceOrtho:
# >>> #     ActiveSketch.ViewObject.Document.ActiveView.setCameraType('Orthographic')
# >>> #
# >>> ### End command PartDesign_CompSketches
# >>> # Gui.Selection.clearSelection()
