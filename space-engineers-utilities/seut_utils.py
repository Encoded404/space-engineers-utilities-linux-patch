import bpy
import sys
import os

from bpy.types      import Operator
from math           import pi
from mathutils      import Matrix, Vector

from .seut_collections              import get_collections, get_cols_by_type
from .seut_errors                   import check_collection, get_abs_path, seut_report


class SEUT_OT_UpdateSubpartInstances(Operator):
    """Updates the subpart instances in the scene"""
    bl_idname = "scene.update_subpart_instances"
    bl_label = "Update Subparts"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):

        scene = context.scene

        scene.seut.linkSubpartInstances = False
        scene.seut.linkSubpartInstances = True

        return {'FINISHED'}


def link_subpart_scene(self, origin_scene, empty, target_collection):
    """Link instances of subpart scene objects as children to empty"""

    context = bpy.context
    current_scene = context.window.scene
    subpart_scene = empty.seut.linkedScene
    parent_collections = get_collections(origin_scene)
    subpart_collections = get_collections(subpart_scene)

    col_type = target_collection.seut.col_type
    type_index = target_collection.seut.type_index

    if col_type == 'bs':
        subpart_col = get_cols_by_type(subpart_scene, col_type)[type_index]
    elif col_type == 'lod':
        ref_col = get_parent_collection(context, empty).seut.ref_col
        subpart_col = get_cols_by_type(subpart_scene, col_type, ref_col)[type_index]
    elif col_type == 'mirroring':
        subpart_col = subpart_collections['main'][0]
    else:
        subpart_col = subpart_collections[col_type][0]

    # Checks whether collection exists, is excluded or is empty
    result = check_collection(self, context, subpart_scene, subpart_col, False)

    if not result == {'CONTINUE'}:
        empty.seut.linkedScene = None
        empty['file'] = None
        return

    # This prevents instancing loops.
    for obj in subpart_col.objects:
        if obj is not None and obj.type == 'EMPTY' and obj.seut.linkedScene == origin_scene:
            seut_report(self, context, 'ERROR', False, 'E005', subpart_scene.name, current_scene.name)
            empty.seut.linkedScene = None
            empty['file'] = None
            return

    # Switch to subpart_scene to get collections
    context.window.scene = subpart_scene
    current_area = prep_context(context)

    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    subpart_objects = set(subpart_col.objects)

    for obj in subpart_objects:

        # The following is done only on a first-level subpart as further-nested subparts already have empties as parents.
        # Needs to account for empties being parents that aren't subpart empties.
        if obj is not None and (obj.parent is None or obj.parent.type != 'EMPTY' or not 'file' in obj.parent) and not obj.seut.linked:
            obj.hide_viewport = False
            existing_objects = set(subpart_col.objects)

            # Create instance of object
            if context.window.view_layer.objects.active is not None:
                context.window.view_layer.objects.active.select_set(state=False, view_layer=context.window.view_layer)
            context.window.view_layer.objects.active = obj
            obj.select_set(state=True, view_layer=context.window.view_layer)
            bpy.ops.object.duplicate(linked=False)

            new_objects = set(subpart_col.objects)
            created_objects = new_objects.copy()
            delete_objects = set()

            for new_obj in new_objects:
                for existing_obj in existing_objects:
                    if new_obj == existing_obj:
                        created_objects.remove(new_obj)

                if new_obj in created_objects and new_obj.seut.linked:
                    created_objects.remove(new_obj)
                    delete_objects.add(new_obj)

            for obj in delete_objects:
                bpy.data.objects.remove(obj, do_unlink=True)

            # Rename instance
            linked_object = None
            for obj in created_objects:
                obj.name = obj.name + " (L)"
                obj.seut.linked = True
                linked_object = obj

            if linked_object is not None:
                # Link instance to empty
                try:
                    if target_collection is None:
                        if col_type == 'bs':
                            get_cols_by_type(current_scene, col_type)[type_index].objects.link(linked_object)
                        if col_type == 'lod':
                            get_cols_by_type(current_scene, col_type, ref_col)[type_index].objects.link(linked_object)
                        else:
                            parent_collections[col_type][0].objects.link(linked_object)
                    else:
                        target_collection.objects.link(linked_object)
                except RuntimeError as e:
                    print(f"Exception: RuntimeError '{e}'")
                    pass
                # apply modifiers and position/rotation/scale on objects that aren't empties
                if linked_object.type != 'EMPTY':
                    old_active = context.window.view_layer.objects.active
                    if len(linked_object.modifiers) > 0:
                        context.window.view_layer.objects.active = linked_object
                        for mod in linked_object.modifiers:
                            name = mod.name
                            try:
                                bpy.ops.object.modifier_apply(modifier = name)
                            except Exception as e:
                                print(f"Exception: '{e}'")
                                pass

                    bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
                    context.window.view_layer.objects.active = old_active

                lock_object(linked_object)
                subpart_col.objects.unlink(linked_object)
                linked_object.parent = empty

                if linked_object.type == 'EMPTY' and linked_object.seut.linkedScene is not None and linked_object.seut.linkedScene.name in bpy.data.scenes and origin_scene.seut.linkSubpartInstances:
                    # This ensures that the action of the original empty is associated with the linked one.
                    if linked_object.animation_data is not None:
                        if linked_object.animation_data.action is not None and linked_object.animation_data.action.name[:-4] in bpy.data.actions:
                            duplicate_action = linked_object.animation_data.action
                            linked_object.animation_data.action = bpy.data.actions[linked_object.animation_data.action.name[:-4]]
                            bpy.data.actions.remove(duplicate_action)

                    link_subpart_scene(self, origin_scene, linked_object, target_collection)


    # Switch back to previous scene
    context.area.type = current_area
    context.window.scene = current_scene


def unlink_subpart_scene(empty):
    """Unlinks all subpart instances from an empty"""

    for obj in empty.children:
        unlink_objects_in_hierarchy(obj)


def unlink_objects_in_hierarchy(obj):
    """Unlinks all objects in hierarchy of an object"""

    for child in obj.children:
        unlink_objects_in_hierarchy(child)

    bpy.data.objects.remove(obj, do_unlink=True)


def get_parent_collection(context, obj):
    scene = context.scene
    collections = get_collections(scene)

    for col_type in collections.values():
        if col_type is None:
            continue
        for col in col_type:
            if obj.name in col.objects:
                return col

    return None


def to_radians(number):
    """Converts degrees to radians"""
    return pi * number / 180


def get_addon():
    return sys.modules.get(__package__)


def get_preferences():
    """Returns the preferences of the addon"""

    if __package__.find(".") == -1:
        addon = __package__
    else:
        addon = __package__[:__package__.find(".")]

    return bpy.context.preferences.addons.get(addon).preferences


def prep_context(context):
    """Prep context for doing larger alterations, returns previous area"""

    try:
        current_area = context.area.type
        context.area.type = 'VIEW_3D'
        bpy.ops.object.mode_set(mode='OBJECT')
    except:
        context.area.type = 'VIEW_3D'
        current_area = context.area.type

    clear_selection(context)

    return current_area


def clear_selection(context):
    """Deselects object and sets active object to None."""

    if context.object is not None:
        context.object.select_set(False)
        context.view_layer.objects.active = None


def toggle_scene_modes(context, mirroring, mountpoints, icon_render):
    """Sets modes in all scenes."""

    original_scene = context.scene

    for scn in bpy.data.scenes:
        context.window.scene = scn

        if scn == original_scene:
            if scn.seut.mirroringToggle != mirroring:
                scn.seut.mirroringToggle = mirroring
            if scn.seut.mountpointToggle != mountpoints:
                scn.seut.mountpointToggle = mountpoints
            if scn.seut.renderToggle != icon_render:
                scn.seut.renderToggle = icon_render

        else:
            if scn.seut.mirroringToggle == 'on':
                scn.seut.mirroringToggle = 'off'
            if scn.seut.mountpointToggle == 'on':
                scn.seut.mountpointToggle = 'off'
            if scn.seut.renderToggle == 'on':
                scn.seut.renderToggle = 'off'

    context.window.scene = original_scene


def lock_object(target):
    """Locks the specified object's location, rotation and scale"""

    target.lock_location = (True, True, True)
    target.lock_rotation = (True, True, True)
    target.lock_scale = (True, True, True)


def create_relative_path(path: str, folder_name: str):
    """Returns the path capped off before the last occurrence of the foldername, returns False if foldername is not found in path"""

    path = get_abs_path(path)
    offset = path.rfind("\\" + folder_name + "\\")

    if offset == -1:
        if path.endswith("\\" + folder_name):
            return path[path.rfind("\\" + folder_name) + 1:]
        else:
            return False
    else:
        return path[offset + 1:]


def wrap_text(text: str, width: int):
    """Returns a list of strings, formatted to a specified width"""

    lines = text.splitlines()
    lines_new = []

    for l in lines:
        if len(l) > width:
            temp = l[:width]
            space_idx = temp.rfind(" ")
            if temp.rfind("\\") > space_idx:
                space_idx = temp.rfind("\\") + 1
            lines_new.append(l[:space_idx])

            overflow = l[space_idx:]
            if overflow.startswith(" ") and not overflow.startswith("  "):
                overflow = overflow[1:]
            lines_new.insert(len(lines_new), overflow)
        else:
            lines_new.append(l)

    return lines_new


def get_enum_items(rna_type, property: str, id: str = None) -> dict:
    """Returns a dict of the enum's items with the IDs as its key. If ID is provided, only that item's info is returned."""

    output = {}
    prop = rna_type.bl_rna.properties[property]
    for p in prop.enum_items:
        output[p.identifier] = [p.name, p.description]

    if id is not None:
        return output[id]

    return output


def check_vanilla_texture(path: str) -> bool:
    """Returns whether a texture is a vanilla texture."""

    preferences = get_preferences()
    assets_textures = os.path.join(preferences.asset_path, "Textures")

    if assets_textures in path and os.path.join(assets_textures, "Custom") not in path:
        return True
    else:
        return False


def get_seut_blend_data():
    """"""

    if '.seut-data' not in bpy.data.texts:
        data = bpy.data.texts.new('.seut-data')
    else:
        data = bpy.data.texts['.seut-data']

    return data


def link_material(name: str, source: str = None, link: bool = True) -> bpy.types.Material:
    """Links a material from a specified source blend file in the Materials folder to the current file"""

    if name in bpy.data.materials:
        if link and bpy.data.materials[name].library is not None:
            return bpy.data.materials[name]
        elif not link and bpy.data.materials[name].library is None:
            return bpy.data.materials[name]

    preferences = get_preferences()
    materials_path = os.path.join(get_abs_path(preferences.asset_path), 'Materials')

    if source is None:
        blends = []
        for file in os.listdir(materials_path):
            if file is not None and file.endswith(".blend"):
                blends.append(file)

        if blends == []:
            seut_report(self, context, 'ERROR', True, 'E021', materials_path)
            return

        for file in blends:
            with bpy.data.libraries.load(os.path.join(materials_path, file), link=link) as (data_from, data_to):
                if name in data_from.materials:
                    data_to.materials = [data_from.materials[data_from.materials.index(name)]]
                    break

    else:
        with bpy.data.libraries.load(os.path.join(materials_path, source), link=link) as (data_from, data_to):
            if name in data_from.materials:
                data_to.materials = [data_from.materials[data_from.materials.index(name)]]

    for mat in bpy.data.materials:
        if link and mat.name == name and mat.library is not None:
            material = mat
            break
        elif not link and mat.name == name and mat.library is None:
            material = mat
            material.asset_clear()
            break
        else:
            material = None

    return material


def set_origin_to_geometry(objs: list):
    """Sets the origins of all objects in the list to their individual geometry"""

    mesh_obs = [obj for obj in objs if obj.type == 'MESH']

    for obj in mesh_obs:
        me = obj.data
        mw = obj.matrix_world
        origin = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)

        T = Matrix.Translation(-origin)
        me.transform(T)
        mw.translation = mw @ origin