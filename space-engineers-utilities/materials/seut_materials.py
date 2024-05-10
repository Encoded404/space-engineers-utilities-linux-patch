import bpy
import os

from bpy.types      import UIList
from bpy.types      import Panel
from bpy.types      import PropertyGroup
from bpy.props      import (EnumProperty,
                            FloatProperty,
                            FloatVectorProperty,
                            IntProperty,
                            StringProperty,
                            BoolProperty)

from ..seut_pt_toolbar      import check_display_panels
from ..seut_utils           import get_seut_blend_data, get_preferences, prep_context
from ..seut_errors          import get_abs_path, seut_report

from ..seut_preferences             import loaded_json

def update_technique(self, context):
    if context.active_object is not None and context.active_object.active_material is not None:
        nodes = context.active_object.active_material.node_tree.nodes
        material = context.active_object.active_material

        ng = None
        for node in nodes:
            if node.name == 'SEUT_NODE_GROUP':
                ng = node
        if ng is None:
            return

        switch = None
        for i in ng.inputs:
            if i.name == 'TM Switch':
                switch = i
        if switch is None:
            return
        
        if self.technique in ['GLASS', 'HOLO', 'SHIELD']:
            switch.default_value = 1
            material.blend_method = 'BLEND'
        else:
            switch.default_value = 0
            material.blend_method = 'CLIP'


def update_color(self, context):
    nodes = context.active_object.active_material.node_tree.nodes

    ng = None
    for node in nodes:
        if node.name == 'SEUT_NODE_GROUP':
            ng = node
    if ng is None:
        return
    
    override = None
    override_alpha = None
    overlay = None
    overlay_alpha = None
    mult = None
    for i in ng.inputs:
        if i.name == 'Color Override':
            override = i
        elif i.name == 'Color Override Alpha':
            override_alpha = i
        elif i.name == 'Color Overlay':
            overlay = i
        elif i.name == 'Color Overlay Alpha':
            overlay_alpha = i
        elif i.name == 'Emission Strength':
            mult = i

    override.default_value = self.color
    override_alpha.default_value = self.color[3]
    overlay.default_value = self.color_add
    overlay_alpha.default_value = self.color_add[3]

    max_emission = max(set([self.color[0], self.color[1], self.color[2], self.color_add[0], self.color_add[1], self.color_add[2]]))

    if max_emission > 1:
        mult.default_value = max_emission - 1
    else:
        mult.default_value = 0


class SEUT_Materials(PropertyGroup):
    """Holder for the varios material properties"""

    version: IntProperty(
        name="SEUT Material Version",
        description="Used as a reference to patch the SEUT material properties to newer versions",
        default=0
    )
    
    technique: EnumProperty(
        name='Technique',
        description="The technique with which the material is rendered ingame",
        items=(
            ('MESH', 'MESH', 'The standard technique'),
            ('DECAL', 'DECAL', "Makes the material look like it's part of the model behind it. Does not support transparency"),
            ('DECAL_NOPREMULT', 'DECAL_NOPREMULT', "Higher accuracy of transparency than 'DECAL', but same visual style"),
            ('DECAL_CUTOUT', 'DECAL_CUTOUT', "Makes the material look like it cuts into the model behind it"),
            ('GLASS', 'GLASS', 'Transparent material - requires additional values to be set in TransparentMaterials.sbc'),
            ('ALPHA_MASKED', 'ALPHA_MASKED', 'Has an alphamask texture'),
            ('ALPHA_MASKED_SINGLE_SIDED', 'ALPHA_MASKED_SINGLE_SIDED', 'Alpha mask texture, but only for a single side. Used in LOD materials'),
            ('SHIELD', 'SHIELD', 'Animated material used on SafeZone shield.\nWarning: Causes Space Engineers to crash with some block types'),
            ('HOLO', 'HOLO', 'Transparent LCD screen texture'),
            ('FOLIAGE', 'FOLIAGE', 'Used for half-transparent textures like leaves - shadows observe transparency in texture'),
            ('CLOUD_LAYER', 'CLOUD_LAYER', 'Used for cloud layers of planets')
            ),
        default='MESH',
        update=update_technique
    )
    facing: EnumProperty(
        name='Facing',
        description="The facing mode of the material",
        items=(
            ('None', 'None', 'No facing mode (standard)'),
            ('Vertical', 'Vertical', 'Vertical facing mode'),
            ('Full', 'Full', 'Full facing mode'),
            ('Impostor', 'Imposter', 'Imposter facing mode')
            ),
        default='None'
    )
    windScale: FloatProperty(
        name="Wind Scale:",
        description="Determines the amount of displacement of the material",
        default=0,
        min=0,
        max=1
    )
    windFrequency: FloatProperty(
        name="Wind Frequency:",
        description="Determines the speed of the displacement animation of the material",
        default=0,
        min=0,
        max=100
    )

    nodeLinkedToOutputName: StringProperty(
        name="Node Linked to Output",
        default=""
    )

    # TransparentMaterial properties
    alpha_misting_enable: BoolProperty(
        name="Alpha Misting",
        description="Start and end values determine the distance in meters at which a material's transparency is rendered.\nNote: Only works on billboards spawned by code, not on models",
        default=False
    )
    alpha_misting_start: FloatProperty(
        name="Alpha Misting Start",
        description="The distance at which the material starts to fade in",
        unit='LENGTH',
        default=0.0
    )
    alpha_misting_end: FloatProperty(
        name="Alpha Misting End",
        description="The distance at which the material finishes fading in",
        unit='LENGTH',
        default=0.0
    )
    affected_by_other_lights: BoolProperty(
        name="Affected by Other Lights",
        description="Whether or not other lights will cast light onto this texture.\nNote: Only works on billboards spawned by code, not on models",
        default=False
    )
    soft_particle_distance_scale: FloatProperty(
        name="Soft Particle Distance Scale",
        description="Changes the way normals are applied to a transparent surface, making it appear to have smoother transitions between hard surfaces.\nNote: Only works on billboards spawned by code, not on models",
        default=1.0,
        min=0.0
    )
    # Texture from CM
    # GlossTexture from NG
    color: FloatVectorProperty(
        name="Color Override",
        description="Overrides the color of the CM texture.\nValues over 1.0 will result in the material becoming emissive in that color",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=100.0,
        default=(0.0, 0.0, 0.0, 0.0),
        update=update_color
    )
    color_add: FloatVectorProperty(
        name="Color Overlay",
        description="This color is added on top of the color of the CM texture\nValues over 1.0 will result in the material becoming emissive in that color",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=100.0,
        default=(0.0, 0.0, 0.0, 0.0),
        update=update_color
    )
    shadow_multiplier_x: FloatProperty(
        name="UV Scale",
        description="Multiplies the scale of the UV Map",
        default=0.0,
        min=0.0
    )
    shadow_multiplier_y: FloatProperty(
        name="Speed",
        description="Controls the speed at which the UV Map moves",
        default=0.0,
        min=0.0
    )
    shadow_multiplier: FloatVectorProperty(
        name="Shadow Multiplier",
        description="Controls the contribution of the color in shadowed areas",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=100.0,
        default=(0.0, 0.0, 0.0, 0.0)
    )
    light_multiplier_x: FloatProperty(
        name="Emissivity Strength",
        description="Controls the strength of the emissivity",
        default=0.0,
        min=0.0
    )
    light_multiplier_y: FloatProperty(
        name="Backlight Falloff",
        description="Controls how quickly the backlight disappears at distance",
        default=0.0,
        min=0.0
    )
    light_multiplier_z: FloatProperty(
        name="Backlight Strength",
        description="Controls the strength of the backlight",
        default=0.0,
        min=0.0
    )
    light_multiplier: FloatVectorProperty(
        name="Light Multiplier",
        description="Controls the contribution of the sun to the lighting",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0,
        max=100.0,
        default=(0.0, 0.0, 0.0, 0.0)
    )
    reflectivity: FloatProperty(
        name="Reflectivity",
        description="If Fresnel and Reflectivity are greater than 0, there can be a reflection. Increase Reflectivity if you want reflections at all angles",
        default=0.6,
        min=0.0,
        max=1.0
    )
    fresnel: FloatProperty(
        name="Fresnel",
        description="If Fresnel and Reflectivity are greater than 0, there can be a reflection. Increase Fresnel if you want reflections at glancing angles",
        default=1.0
    )
    reflection_shadow: FloatProperty(
        name="Reflection Shadow",
        description="Controls how intense the reflection is in the shadowed part of the block. Intensity is always 1 in the unshadowed part",
        default=0.1,
        min=0.0,
        max=1.0
    )
    gloss_texture_add: FloatProperty(
        name="Gloss Texture Add",
        description="Increases the gloss defined by the NG texture of the material. If both are zero, the reflection devolves into ambient color",
        default=0.55,
        min=0.0,
        max=1.0
    )
    gloss: FloatProperty(
        name="Gloss",
        description="How clearly the reflected sun can be seen on the material",
        default=0.4,
        min=0.0,
        max=1.0
    )
    specular_color_factor: FloatProperty(
        name="Specular Color Factor",
        description="Increases the specularity of the color (the size of the sun glare)",
        default=0.0
    )
    is_flare_occluder: BoolProperty(
        name="Flare Occluder",
        description="Whether sprite flares of the sun, lights, thrusters, etc. can be seen through the Transparent Material",
        default=False
    )


class SEUT_PT_Panel_Materials(Panel):
    """Creates the materials panel for SEUT"""
    bl_idname = "SEUT_PT_Panel_Materials"
    bl_label = "Space Engineers Utilities"
    bl_category = "SEUT"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"


    @classmethod
    def poll(cls, context):
        scene = context.scene
        return check_display_panels(context)


    def draw(self, context):
        layout = self.layout

        if bpy.context.active_object is not None and context.active_object.active_material is not None:

            material = context.active_object.active_material

            box = layout.box()
            split = box.split(factor=0.85)
            split.label(text=material.name, icon_value=layout.icon(material))
            link = split.operator('wm.docu_link', text="", icon='INFO')
            link.section = 'Reference/Tools/SEUT/'
            link.page = 'Shader_Editor'

            row = box.row(align=True)
            box.prop(material.seut, 'technique', icon='IMGDISPLAY')
            box.prop(material.seut, 'facing')
            
            if material.seut.technique in ['FOLIAGE', 'ALPHA_MASKED']:
                box.prop(material.seut, 'windScale', icon='SORTSIZE')
                box.prop(material.seut, 'windFrequency', icon='GROUP')

            if material.seut.technique in ['GLASS', 'HOLO', 'SHIELD']:
                box = layout.box()
                box.label(text="Transparent Material Options", icon='SETTINGS')

                box2 = box.box()
                box2.label(text="Color Adjustments", icon='COLOR')
                col = box2.column(align=True)
                col.prop(material.seut, 'color', text="")
                col.prop(material.seut, 'color_add', text="")

                if not material.seut.technique == 'SHIELD':
                    col = box2.column(align=True)
                    col.prop(material.seut, 'shadow_multiplier', text="")
                    col.prop(material.seut, 'light_multiplier', text="")

                else:
                    box3 = box.box()
                    box3.label(text="UV Options", icon='UV')
                    col = box3.column(align=True)
                    col.prop(material.seut, 'shadow_multiplier_x')
                    col.prop(material.seut, 'shadow_multiplier_y')
                    
                    box4 = box.box()
                    box4.label(text="Light Influence", icon='LIGHT_POINT')
                    col = box4.column(align=True)
                    col.prop(material.seut, 'light_multiplier_x')
                    col.prop(material.seut, 'light_multiplier_y')
                    col.prop(material.seut, 'light_multiplier_z')
                
                box2 = box.box()
                box2.label(text="Reflection Adjustments", icon='MOD_MIRROR')
                
                col = box2.column(align=True)
                col.prop(material.seut, 'reflectivity')
                col.prop(material.seut, 'fresnel')
                col.prop(material.seut, 'reflection_shadow')

                box2.prop(material.seut, 'gloss_texture_add', slider=True)

                col = box2.column(align=True)
                col.prop(material.seut, 'gloss')
                col.prop(material.seut, 'specular_color_factor')
                col.prop(material.seut, 'is_flare_occluder', icon='LIGHT_SUN')

                box2 = box.box()
                box2.label(text="Billboards", icon='IMAGE_PLANE')
                col = box2.column(align=True)
                col.prop(material.seut, 'alpha_misting_enable', icon='ZOOM_ALL')
                if material.seut.alpha_misting_enable:
                    row = col.row(align=True)
                    row.prop(material.seut, 'alpha_misting_start', text="Start")
                    row.prop(material.seut, 'alpha_misting_end', text="End")
                box2.prop(material.seut, 'soft_particle_distance_scale')
                box2.prop(material.seut, 'affected_by_other_lights', icon='LIGHT')


        box = layout.box()

        split = box.split(factor=0.85)
        split.label(text="Create SEUT Material", icon='MATERIAL')
        link = split.operator('wm.docu_link', text="", icon='INFO')
        link.section = 'Tutorials/Tools/SEUT/'
        link.page = 'Material'

        box.operator('object.create_material', icon='ADD')
        box.operator('wm.import_materials', icon='IMPORT')


class SEUT_PT_Panel_TextureConversion(Panel):
    """Creates the Texture Conversion panel for SEUT"""
    bl_idname = "SEUT_PT_Panel_TextureConversion"
    bl_label = "Texture Conversion"
    bl_category = "SEUT"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        scene = context.scene
        return check_display_panels(context)


    def draw(self, context):
        layout = self.layout
        data = get_seut_blend_data()

        layout.prop(data.seut, 'texconv_preset')

        box = layout.box()
        box.label(text="Input", icon='IMPORT')

        row = box.row()
        if data.seut.texconv_input_type == 'file':
            row.prop(data.seut, 'texconv_input_type', expand=True)
            box.prop(data.seut, 'texconv_input_file', text="File", icon='FILE_IMAGE')
        else:
            row.prop(data.seut, 'texconv_input_type', expand=True)
            box.prop(data.seut, 'texconv_input_dir', text="Directory", icon='FILE_FOLDER')

        box = layout.box()
        box.label(text="Output", icon='EXPORT')
        box.prop(data.seut, 'texconv_output_dir', text="Directory", icon='FILE_FOLDER')
        if data.seut.texconv_preset == 'custom':
            box.prop(data.seut, 'texconv_output_filetype', text="Type")

            box = layout.box()
            box.label(text="Options", icon='SETTINGS')
            box.prop(data.seut, 'texconv_format')
            row = box.row()
            row.prop(data.seut, 'texconv_pmalpha')
            row.prop(data.seut, 'texconv_sepalpha')
            box.prop(data.seut, 'texconv_pdd')
        
        layout.operator('wm.convert_textures', icon='EXPORT')


def get_seut_texture_path(texture_type: str, material) -> str:
    """Returns the path to a material's texture of a specified type. Valid is CM, NG, ADD, AM."""

    path = None
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.label == texture_type and node.name == texture_type:
            if node.image is None:
                continue
            image = node.image.name
            path = bpy.data.images[image].filepath

    return path


class SEUT_PT_Panel_Shading(Panel):
    """Creates the shading panel for SEUT"""
    bl_idname = "SEUT_PT_Panel_Shading"
    bl_label = "Space Engineers Utilities"
    bl_category = "SEUT"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"


    @classmethod
    def poll(cls, context):

        match_material = False
        if context.object is None or context.object.active_material is None:
            return False
        if context.object.active_material.name in loaded_json:
            match_material = True
        else:
            for mat in loaded_json['material_variations']:
                for var in loaded_json['material_variations'][mat]:
                    if mat + var == context.object.active_material.name or mat + var == context.object.active_material.name[:-4]:
                        match_material = True
                        break

        return check_display_panels(context) and match_material


    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.prop(obj.seut, 'material_variant')