import bpy
import os


from ..materials.seut_ot_texture_conversion     import convert_texture
from ..seut_errors                              import *
from ..seut_utils                               import check_vanilla_texture, create_relative_path, get_seut_blend_data


def export_material_textures(self, context, material):
    """Checks if source file is newer than converted file, if so, exports to DDS."""

    data = get_seut_blend_data()
    scene = context.scene
    nodes = material.node_tree.nodes
    textures = {}

    if material.node_tree is None or material.node_tree.nodes is None:
        return {'CANCELLED'}

    if 'CM' in nodes and nodes['CM'].image is not None and os.path.exists(get_abs_path(nodes['CM'].image.filepath)):
        textures['cm'] = get_abs_path(nodes['CM'].image.filepath)

    if 'ADD' in nodes and nodes['ADD'].image is not None and os.path.exists(get_abs_path(nodes['ADD'].image.filepath)):
        textures['add'] = get_abs_path(nodes['ADD'].image.filepath)

    if 'NG' in nodes and nodes['NG'].image is not None and os.path.exists(get_abs_path(nodes['NG'].image.filepath)):
        textures['ng'] = get_abs_path(nodes['NG'].image.filepath)
        
    if 'ALPHAMASK' in nodes and nodes['ALPHAMASK'].image is not None and os.path.exists(get_abs_path(nodes['ALPHAMASK'].image.filepath)):
        textures['alphamask'] = get_abs_path(nodes['ALPHAMASK'].image.filepath)

    if len(textures) <= 0:
        return {'CANCELLED'}
    
    if not data.seut.convert_textures:
        return {'FINISHED'}

    for preset, source in textures.items():

        # Skip if texture is a vanilla texture and thus does not need to be converted.
        if check_vanilla_texture(source):
            continue

        if create_relative_path(source, 'Textures'):
            target = os.path.join(get_abs_path(scene.seut.mod_path), create_relative_path(source, 'Textures'))
            target_file = os.path.splitext(target)[0] + '.dds'
            target_dir = os.path.dirname(target)

            if not os.path.exists(target_file):
                os.makedirs(target_dir, exist_ok=True)
                output = convert_texture(source, target_dir, preset)
                try:
                    os.rename(target_file, os.path.splitext(target_file)[0] + '.dds')
                except:
                    pass

            elif os.path.getmtime(source) > os.path.getmtime(target_file):
                output = convert_texture(source, target_dir, preset)
                try:
                    os.rename(target_file, os.path.splitext(target_file)[0] + '.dds')
                except:
                    pass
            
            else:
                continue

            if output[0] == 0:
                seut_report(self, context, 'INFO', False, 'I002', preset, material.name)
            else:
                seut_report(self, context, 'ERROR', False, 'E046', preset, material.name, output[1])

    return {'FINISHED'}