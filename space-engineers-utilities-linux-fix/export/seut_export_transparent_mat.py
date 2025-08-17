import bpy
import os
import re

from ..materials.seut_materials import get_seut_texture_path
from ..utils.seut_xml_utils     import *
from ..seut_errors              import *
from ..seut_utils               import create_relative_path


def export_transparent_mat(self, context, subtype_id):
    """Exports a defined transparent material."""

    scene = context.scene
    material = bpy.data.materials[subtype_id]
    path_data = os.path.join(get_abs_path(scene.seut.mod_path), "Data")
    
    output = get_relevant_sbc(os.path.dirname(path_data), 'TransparentMaterials', 'TransparentMaterial', subtype_id)
    if output is not None:
        file_to_update = output[0]
        lines = output[1]
        start = output[2]
        end = output[3]

    # Neither a TransparentMat file nor an entry for this particular one was found
    if file_to_update is None or scene.seut.export_sbc_type == 'new':
        definitions = ET.Element('Definitions')
        add_attrib(definitions, 'xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        add_attrib(definitions, 'xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
        tms = add_subelement(definitions, 'TransparentMaterials')
        def_definition = add_subelement(tms, 'TransparentMaterial')
        def_Id = add_subelement(def_definition, 'Id')
        add_subelement(def_Id, 'TypeId', 'TransparentMaterialDefinition')
        add_subelement(def_Id, 'SubtypeId', subtype_id)
        lines_entry = None
        update = False
    
    # TransparentMat-tree was found but no entry for this TransparentMat exists
    elif file_to_update is not None and start is None and end is None:
        def_definition = ET.Element('TransparentMaterial')
        def_Id = add_subelement(def_definition, 'Id')
        add_subelement(def_Id, 'TypeId', 'TransparentMaterialDefinition')
        add_subelement(def_Id, 'SubtypeId', subtype_id)
        lines_entry = None
        update = False
    
    # TransparentMat-tree & entry for this particular TransparentMat was found
    else:
        def_definition = None
        lines_entry = lines[start:end]
        update = True
    
    lines_entry = update_add_subelement(def_definition, 'AlphaMistingEnable', str(material.seut.alpha_misting_enable).lower(), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'AlphaMistingStart', round(material.seut.alpha_misting_start, 2), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'AlphaMistingEnd', round(material.seut.alpha_misting_end, 2), update, lines_entry)
    
    lines_entry = update_add_subelement(def_definition, 'CanBeAffectedByOtherLights', str(material.seut.affected_by_other_lights).lower(), update, lines_entry)
    
    lines_entry = update_add_subelement(def_definition, 'SoftParticleDistanceScale', round(material.seut.soft_particle_distance_scale, 2), update, lines_entry)
    
    cm_path = get_seut_texture_path('CM', material)
    if cm_path is not None:
        cm_path = os.path.splitext(cm_path)[0] + ".dds"
        cm_path = create_relative_path(cm_path, 'Textures')
        seut_report(self, context, 'WARNING', True, 'W014', material.name, 'CM')
    lines_entry = update_add_subelement(def_definition, 'Texture', str(cm_path), update, lines_entry)
    
    if not update:
        def_color = add_subelement(def_definition, 'Color')
    else:
        def_color = ET.Element('Color')
    add_subelement(def_color, 'X', round(material.seut.color[0], 2))
    add_subelement(def_color, 'Y', round(material.seut.color[1], 2))
    add_subelement(def_color, 'Z', round(material.seut.color[2], 2))
    add_subelement(def_color, 'W', round(material.seut.color[3], 2))
    if update:
        lines_entry = convert_back_xml(def_color, 'Color', lines_entry)
        
    if not update:
        def_color_add = add_subelement(def_definition, 'ColorAdd')
    else:
        def_color_add = ET.Element('ColorAdd')
    add_subelement(def_color_add, 'X', round(material.seut.color_add[0], 2))
    add_subelement(def_color_add, 'Y', round(material.seut.color_add[1], 2))
    add_subelement(def_color_add, 'Z', round(material.seut.color_add[2], 2))
    add_subelement(def_color_add, 'W', round(material.seut.color_add[3], 2))
    if update:
        lines_entry = convert_back_xml(def_color_add, 'ColorAdd', lines_entry)

    if not update:
        def_shadow_multiplier = add_subelement(def_definition, 'ShadowMultiplier')
    else:
        def_shadow_multiplier = ET.Element('ShadowMultiplier')
    if material.seut.technique == 'SHIELD':
        add_subelement(def_shadow_multiplier, 'X', round(material.seut.shadow_multiplier_x, 2))
        add_subelement(def_shadow_multiplier, 'Y', round(material.seut.shadow_multiplier_y, 2))
        add_subelement(def_shadow_multiplier, 'Z', 0) # unused
        add_subelement(def_shadow_multiplier, 'W', 0) # unused
    else:
        add_subelement(def_shadow_multiplier, 'X', round(material.seut.shadow_multiplier[0], 2))
        add_subelement(def_shadow_multiplier, 'Y', round(material.seut.shadow_multiplier[1], 2))
        add_subelement(def_shadow_multiplier, 'Z', round(material.seut.shadow_multiplier[2], 2))
        add_subelement(def_shadow_multiplier, 'W', round(material.seut.shadow_multiplier[3], 2))
    if update:
        lines_entry = convert_back_xml(def_shadow_multiplier, 'ShadowMultiplier', lines_entry)
    
    if not update:
        def_light_multiplier = add_subelement(def_definition, 'LightMultiplier')
    else:
        def_light_multiplier = ET.Element('LightMultiplier')
    if material.seut.technique == 'SHIELD':
        add_subelement(def_light_multiplier, 'X', round(material.seut.light_multiplier_x, 2))
        add_subelement(def_light_multiplier, 'Y', round(material.seut.light_multiplier_y, 2))
        add_subelement(def_light_multiplier, 'Z', round(material.seut.light_multiplier_z, 2))
        add_subelement(def_light_multiplier, 'W', 0) # unused
    else:
        add_subelement(def_light_multiplier, 'X', round(material.seut.light_multiplier[0], 2))
        add_subelement(def_light_multiplier, 'Y', round(material.seut.light_multiplier[1], 2))
        add_subelement(def_light_multiplier, 'Z', round(material.seut.light_multiplier[2], 2))
        add_subelement(def_light_multiplier, 'W', round(material.seut.light_multiplier[3], 2))
    if update:
        lines_entry = convert_back_xml(def_light_multiplier, 'LightMultiplier', lines_entry)

    lines_entry = update_add_subelement(def_definition, 'Reflectivity', round(material.seut.reflectivity, 2), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'Fresnel', round(material.seut.fresnel, 2), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'ReflectionShadow', round(material.seut.reflection_shadow, 2), update, lines_entry)

    lines_entry = update_add_subelement(def_definition, 'Gloss', round(material.seut.gloss, 2), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'GlossTextureAdd', round(material.seut.gloss_texture_add, 2), update, lines_entry)

    ng_path = get_seut_texture_path('NG', material)
    if ng_path is not None:
        ng_path = os.path.splitext(ng_path)[0] + ".dds"
        ng_path = create_relative_path(ng_path, 'Textures')
        seut_report(self, context, 'WARNING', True, 'W014', material.name, 'NG')
    lines_entry = update_add_subelement(def_definition, 'GlossTexture', str(ng_path), update, lines_entry)

    lines_entry = update_add_subelement(def_definition, 'SpecularColorFactor', round(material.seut.specular_color_factor, 2), update, lines_entry)
    lines_entry = update_add_subelement(def_definition, 'IsFlareOccluder', str(material.seut.is_flare_occluder).lower(), update, lines_entry)

    if file_to_update is None or scene.seut.export_sbc_type == 'new':
        temp_string = ET.tostring(definitions, 'utf-8')
        try:
            temp_string.decode('ascii')
        except UnicodeDecodeError:
            seut_report(self, context, 'ERROR', True, 'E033')
            return {'CANCELLED'}
        xml_string = xml.dom.minidom.parseString(temp_string)
        xml_formatted = xml_string.toprettyxml()
    
    elif file_to_update is not None and start is None and end is None:
        temp_string = ET.tostring(def_definition, 'utf-8')
        xml_string = xml.dom.minidom.parseString(temp_string)
        xml_formatted = xml_string.toprettyxml()

        insert_index = lines.rfind('</TransparentMaterial>') + len('</TransparentMaterial>')
        xml_formatted = lines[:insert_index] + '\n' + xml_formatted.replace('<?xml version="1.0" ?>\n', "") + '\n' + lines[insert_index:]

        xml_formatted = format_entry(xml_formatted)
        target_file = file_to_update

    else:
        xml_formatted = lines.replace(lines[start:end], lines_entry)
        xml_formatted = format_entry(xml_formatted)
        target_file = file_to_update

    # This removes empty lines
    # xml_formatted = re.sub(r'\n\s*\n', '\n', xml_formatted)

    if file_to_update is None or scene.seut.export_sbc_type == 'new':
        target_file = os.path.join(path_data, "TransparentMaterials.sbc")
        if not os.path.exists(path_data):
            os.makedirs(path_data)
        
        # This covers the case where a file exists but the SBC export setting forces new file creation.
        if os.path.exists(target_file):
            target_file = os.path.splitext(target_file)[0] + f"_{subtype_id}.sbc"
        counter = 1
        while os.path.exists(target_file):
            target_file = os.path.splitext(target_file)[0]
            split = target_file.split("_")
            try:
                number = int(split[len(split)-1]) + 1
                target_file = target_file[:target_file.rfind("_")]
                target_file = f"{target_file}_{number}.sbc"
            except:
                target_file = target_file + "_1.sbc"

    elif file_to_update is not None and start is None and end is None:
        target_file = os.path.join(path_data, file_to_update)

    else:
        target_file = file_to_update

    exported_xml = open(target_file, "w")
    exported_xml.write(xml_formatted)

    if file_to_update is None or scene.seut.export_sbc_type == 'new':
        seut_report(self, context, 'INFO', False, 'I004', target_file)
    else:
        seut_report(self, context, 'INFO', False, 'I015', subtype_id, target_file)

    return {'FINISHED'}