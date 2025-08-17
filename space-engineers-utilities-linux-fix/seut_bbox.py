import bpy
import gpu
import math

from gpu_extras.batch   import batch_for_shader
from bpy.types          import Operator

from .seut_utils        import get_seut_blend_data

# Most of the code used in this class is **heavily** based on Jayanam's "Blender 2.8 Python GPU : Draw Lines"-video:
# https://www.youtube.com/watch?v=EgrgEoNFNsA
class SEUT_OT_BBox(Operator):
    """Sets the bounding box"""
    bl_idname = "object.bbox"
    bl_label = "Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draw_handle = None
        self.draw_event = None


    def invoke(self, context, event):
        scene = context.scene
        data = get_seut_blend_data()

        # If the toggle is off, don't do anything.
        if data.seut.bBox == 'off':
            return {'FINISHED'}

        factor = 1

        if scene.seut.gridScale == 'large': factor = 2.5
        if scene.seut.gridScale == 'small': factor = 0.5

        x = scene.seut.bBox_X * factor
        y = scene.seut.bBox_Y * factor
        z = scene.seut.bBox_Z * factor

        self.coords = (
            (-x/2, -y/2, -z/2), (+x/2, -y/2, -z/2),
            (-x/2, +y/2, -z/2), (+x/2, +y/2, -z/2),
            (-x/2, -y/2, +z/2), (+x/2, -y/2, +z/2),
            (-x/2, +y/2, +z/2), (+x/2, +y/2, +z/2)
        )

        self.indices = (
            (0, 1), (0, 2), (1, 3), (2, 3),
            (4, 5), (4, 6), (5, 7), (6, 7),
            (0, 4), (1, 5), (2, 6), (3, 7)
        )

        self.create_batch()

        args = (self, context)
        self.register_handlers(args, context)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def register_handlers(self, args, context):
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_3d, args, "WINDOW", "POST_VIEW"
        )
        self.draw_event = context.window_manager.event_timer_add(1, window=context.window)


    def unregister_handlers(self, context):
        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")

        self.draw_handle = None
        self.draw_event = None


    def modal(self, context, event):
        scene = context.scene
        data = get_seut_blend_data()

        if context.area:
            context.area.tag_redraw()

        # Escape condition for when the user turns off the bounding box.
        if data.seut.bBox == 'off':
            self.unregister_handlers(context)
            return {'FINISHED'}

        factor = 1

        if scene.seut.gridScale == 'large': factor = 2.5
        if scene.seut.gridScale == 'small': factor = 0.5

        x = scene.seut.bBox_X * factor
        y = scene.seut.bBox_Y * factor
        z = scene.seut.bBox_Z * factor

        if not scene.seut.sceneType == 'mainScene':
            x = 0
            y = 0
            z = 0

        self.coords = (
            (-x/2, -y/2, -z/2), (+x/2, -y/2, -z/2),
            (-x/2, +y/2, -z/2), (+x/2, +y/2, -z/2),
            (-x/2, -y/2, +z/2), (+x/2, -y/2, +z/2),
            (-x/2, +y/2, +z/2), (+x/2, +y/2, +z/2)
        )

        self.create_batch()

        return {'PASS_THROUGH'}


    def finish(self):
        self.unregister_handlers(bpy.context)
        return {'FINISHED'}


    def create_batch(self):
        self.shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": self.coords}, indices=self.indices)


    def draw_callback_3d(self, op, context):
        data = get_seut_blend_data()

        try:
            blend_state = gpu.state.blend_get()
            gpu.state.blend_set('ALPHA')
            self.shader.bind()
            self.shader.uniform_float("color", (data.seut.bBox_color[0], data.seut.bBox_color[1], data.seut.bBox_color[2], data.seut.bBox_color[3]))
            self.batch.draw(self.shader)
            gpu.state.blend_set(blend_state)
        except:
            pass