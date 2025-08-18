import bpy
import os

from bpy.types  import Operator

from ..seut_errors      import seut_report, get_abs_path

class SEUT_OT_MatCreate(Operator):
    """Create a SEUT material for the selected mesh"""
    bl_idname = "object.create_material"
    bl_label = "Create Material"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'


    def execute(self, context):
        
        from ..seut_utils import get_preferences
        preferences = get_preferences()
        materials_path = os.path.join(get_abs_path(preferences.asset_path), 'Materials')
        if not os.path.exists(materials_path):
            seut_report(None, bpy.context, 'ERROR', True, 'E012', "Asset Directory", get_abs_path(preferences.asset_path))
            return {'CANCELLED'}
            
        new_material = create_material()

        if new_material is not None:
            context.active_object.active_material = new_material
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
    

def create_material(material=None):
    """Links SEUT Material"""
    from ..seut_utils import link_material

    if material is None:
        return link_material('SEUT Material', 'SEUT.blend', False)

    temp = link_material('SEUT Material', 'SEUT.blend', False)
    #oldName: str = material.name
    #print(f"old material has {material.users} new one has {temp.users}")
    material.user_remap(temp)
    #print(f"after remap old material has {material.users} users new one has {temp.users} users")
    #print(f"old material is {'not' if bpy.data.materials[material.name].library is None else ''} a link and new one is {'not' if bpy.data.materials[temp.name].library is None else ''} a link")
    temp.rename(material.name, mode="NEVER")
    #print(f"Material '{oldName}' has been replaced with '{temp.name}'")
    return temp