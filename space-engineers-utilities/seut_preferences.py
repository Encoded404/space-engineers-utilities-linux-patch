import bpy
import os
import sys
import json
import addon_utils

from bpy.types  import Operator, AddonPreferences
from bpy.props  import BoolProperty, StringProperty, EnumProperty, IntProperty

from .utils.seut_repositories       import *
from .seut_errors                   import seut_report, get_abs_path
from .seut_utils                    import get_preferences, get_addon, get_seut_blend_data, wrap_text
from .seut_bau                      import draw_bau_ui, get_config, set_config


preview_collections = {}
empties = {}
loaded_json = {}


class SEUT_OT_SetDevPaths(Operator):
    """Sets the SEUT dev paths"""
    bl_idname = "wm.set_dev_paths"
    bl_label = "Set Dev Paths"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        preferences = get_preferences()

        # enenra
        if os.path.isdir("D:\\Modding\\Space Engineers\\SEUT\\seut-assets\\Materials\\"):
            preferences.game_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\SpaceEngineers\\"
            preferences.asset_path = "D:\\Modding\\Space Engineers\\SEUT\\seut-assets\\"
            preferences.havok_path = "D:\\Modding\\Space Engineers\\SEUT\\Tools\\Havok\\HavokContentTools\\hctStandAloneFilterManager.exe"

        # Stollie
        elif os.path.isdir("C:\\3D_Projects\\SpaceEngineers\\MaterialLibraries\\Materials\\"):
            preferences.asset_path = "C:\\3D_Projects\\SpaceEngineers\\MaterialLibraries\\"
            preferences.havok_path = "C:\\3D_Projects\\BlenderPlugins\\Havok\\HavokContentTools\\hctStandAloneFilterManager.exe"

        else:
            load_addon_prefs()

        update_register_repos()
        load_configs()

        return {'FINISHED'}


def update_game_path(self, context):
    if self.game_path == "":
        return

    path = get_abs_path(self.game_path)

    if os.path.isdir(path):
        if not path.endswith('SpaceEngineers') or not os.path.exists(os.path.join(path, 'Bin64', 'SpaceEngineers.exe')):
            seut_report(self, context, 'ERROR', False, 'E012', "Game Directory", path)
            self.game_path = ""
    else:
        if os.path.basename(os.path.dirname(path)) == 'SpaceEngineers':
          self.game_path = os.path.dirname(path) + '\\'
        else:
          seut_report(self, context, 'ERROR', False, 'E003', 'SpaceEngineers', path)
          self.game_path = ""

    save_addon_prefs()


def update_asset_path(self, context):
    data = get_seut_blend_data()

    if self.asset_path == "":
        return

    path = get_abs_path(self.asset_path)

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    if path.endswith('SpaceEngineers') or path.endswith('SpaceEngineersModSDK'):
        seut_report(self, context, 'ERROR', False, 'E012', "Asset Directory", path)
        self.asset_path = ""

    materials_path = os.path.join(path, 'Materials')
    if not os.path.exists(materials_path):
        os.makedirs(materials_path, exist_ok=True)
    relocate_matlibs(materials_path)

    preferences = get_preferences()
    mwmb_path = os.path.join(os.path.dirname(materials_path), 'Tools', 'MWMBuilder', 'MwmBuilder.exe')
    if os.path.exists(mwmb_path):
        preferences.mwmb_path = mwmb_path
    else:
        preferences.mwmb_path = ""

    # This is suboptimal but works.
    found = False
    libraries = bpy.context.preferences.filepaths.asset_libraries
    if 'SEUT' in libraries:
        libraries['SEUT'].path = path
        found = True

    if not found:
        for al in libraries:
            if al.path == path:
                al.name = "SEUT"
                found = True
                break

        if not found:
            bpy.ops.preferences.asset_library_add(directory=path)
            for al in bpy.context.preferences.filepaths.asset_libraries:
                if al.path == path:
                    al.name = "SEUT"
                    break

    if not 'seut-assets' in data.seut.repos:
        update_register_repos()

    repo_assets = data.seut.repos['seut-assets']
    repo_assets.cfg_path = path
    check_repo_update(repo_assets)
    repo_mwmb = data.seut.repos['MWMBuilder']
    repo_mwmb.cfg_path = os.path.join(path, 'Tools', 'MWMBuilder')
    check_repo_update(repo_mwmb)

    save_addon_prefs()


def relocate_matlibs(path):
    for lib in bpy.data.libraries:
        if not os.path.exists(lib.filepath):
            if os.path.exists(os.path.join(path, lib.name.replace("MatLib_", ""))):
                bpy.ops.wm.lib_relocate(library=lib.name, directory=path, filename=lib.name.replace("MatLib_", ""))
            elif os.path.exists(os.path.join(path, lib.name.replace("MatLib_", "")[:-4])):
                bpy.ops.wm.lib_relocate(library=lib.name, directory=path, filename=lib.name.replace("MatLib_", "")[:-4])
            elif os.path.exists(os.path.join(path, lib.name[:-4])):
                bpy.ops.wm.lib_relocate(library=lib.name, directory=path, filename=lib.name[:-4])
            elif os.path.exists(os.path.join(path, lib.name)):
                bpy.ops.wm.lib_relocate(library=lib.name, directory=path, filename=lib.name)


def init_relocate_matlibs():
    preferences = get_preferences()
    if os.path.exists(preferences.asset_path):
        relocate_matlibs(os.path.join(preferences.asset_path, 'Materials'))


def update_havok_path(self, context):
    filename = 'hctStandAloneFilterManager.exe'

    if self.havok_path == "":
        return
    elif self.havok_path == self.havok_path_before:
        return

    path = get_abs_path(self.havok_path)

    self.havok_path_before = verify_tool_path(self, context, path, "Havok Stand Alone Filter Manager", filename)
    self.havok_path = verify_tool_path(self, context, path, "Havok Stand Alone Filter Manager", filename)

    save_addon_prefs()


class SEUT_AddonPreferences(AddonPreferences):
    """Saves the preferences set by the user"""
    bl_idname = __package__

    dev_mode: BoolProperty(
        default = get_addon().bl_info['dev_version'] > 0
    )
    asset_path: StringProperty(
        name="Asset Directory",
        description="This directory contains all SEUT assets. It contains both a Materials- and a Textures-folder",
        subtype='DIR_PATH',
        update=update_asset_path
    )
    game_path: StringProperty(
        name="Game Directory",
        description="This is the path to the directory where Space Engineers is installed",
        subtype='DIR_PATH',
        update=update_game_path
    )
    havok_path: StringProperty(
        name="Havok Standalone Filter Manager",
        description="This tool is required to create Space Engineers collision models",
        subtype='FILE_PATH',
        update=update_havok_path
    )
    havok_path_before: StringProperty(
        subtype='FILE_PATH'
    )
    mwmb_path: StringProperty(
        name="MWM Builder",
        description="This tool converts the individual 'loose files' that the export yields into MWM files the game can read",
        subtype='FILE_PATH'
    )
    quick_tools: BoolProperty(
        name="Quick Tools",
        description="Enable or disable the SEUT Quick Tools menu panel being displayed",
        default= True,
    )
    animation: BoolProperty(
        name="Animations Panel",
        description="Enable or disable the SEUT Animations menu panel being displayed.\nNote that animations are not working yet",
        default= False,
    )

    def draw(self, context):
        layout = self.layout
        data = get_seut_blend_data()
        preferences = get_preferences()

        self.dev_mode = get_addon().bl_info['dev_version'] > 0

        preview_collections = get_icons()
        pcoll = preview_collections['main']

        row = layout.row()
        row.alignment = 'RIGHT'
        row.operator('wm.discord_link', text="", icon_value=pcoll['discord'].icon_id)
        link = row.operator('wm.docu_link', text="", icon='INFO')
        link.section = 'Reference/Tools/SEUT/'
        link.page = 'Addon_Preferences'

        if bpy.app.version < (4, 0, 0):
            box = layout.box()
            row = box.row()
            row.alert = True
            row.label(text="Version Incompatibility", icon='ERROR')
            for l in wrap_text("SEUT requires Blender 4.0 or later. Using an earlier version may lead to unexpected and non-obvious errors. Please update your Blender installation!", int(context.region.width / 7)):
                row = box.row()
                row.scale_y = 0.75
                row.alert = True
                row.label(text=l)

        try:
            draw_bau_ui(self, context)
        except:
            row = layout.row()
            row.alert = True
            row.label(text="An error occurred during draw of Blender Addon Updater UI. Make sure BAU is up to date.")

        if 'space-engineers-utilities' not in data.seut.repos:
            try:
                update_register_repos()
            except Exception:
                pass
                
        if 'space-engineers-utilities' in data.seut.repos:
            if addon_utils.check('blender_addon_updater') != (True, True):
                row = layout.row()
                row.label(text="Update Status:")

                repo = data.seut.repos['space-engineers-utilities']

                if repo.needs_update:
                    row.alert = True
                    row.label(text=repo.update_message, icon='ERROR')
                    op = row.operator('wm.get_update', icon='IMPORT')
                    op.repo_name = 'space-engineers-utilities'
                else:
                    row.label(text=repo.update_message, icon='CHECKMARK')
                    op = row.operator('wm.get_update', text="Releases", icon='IMPORT')
                    op.repo_name = 'space-engineers-utilities'

                box = layout.box()
                box.label(text="Install the Blender Addon Updater to easily update SEUT:", icon='FILE_REFRESH')
                row = box.row()
                row.scale_y = 2.0
                op = row.operator('wm.url_open', text="Blender Addon Updater", icon='URL')
                op.url = "https://github.com/enenra/blender_addon_updater/releases/"

        if self.dev_mode:
            row = layout.row()
            row.scale_x = 1.25
            row.scale_y = 1.5
            row.operator('wm.set_dev_paths', icon='FILEBROWSER')

        layout.prop(self, "game_path", expand=True)

        box = layout.box()
        split = box.split(factor=0.55)
        split.label(text="Assets", icon='ASSET_MANAGER')
        if self.dev_mode:
            split = split.split(factor=0.15, align=True)
            row = split.row(align=True)
            row.prop(data.seut, 'setup_conversion_filetype', text="")
        split = split.split(factor=0.90, align=True)
        row = split.row(align=True)
        row.operator('wm.mass_convert_textures', icon='FILE_REFRESH')
        if sys.platform == "win32":
            split.operator('wm.console_toggle', text="", icon='CONSOLE')
        box.prop(self, "asset_path", expand=True)

        if os.path.exists(preferences.asset_path):
            repo = data.seut.repos['seut-assets']
            box2 = box.box()
            row = box2.row(align=True)

            if not os.path.exists(os.path.join(repo.cfg_path, f"{repo.name}.cfg")):
                row.alert = True
                row.label(text=f"Assets ({repo.current_version}):", icon='TOOL_SETTINGS')
                if repo.update_message == "Rate limit exceeded!":
                    icon = 'CANCEL'
                else:
                    icon = 'ERROR'
                row.label(text=repo.update_message, icon=icon)
                op = row.operator('wm.download_update', text="Download & Install", icon='IMPORT')
                op.repo_name = repo.name
                op.wipe = False
                op = row.operator('wm.get_update', text="", icon='URL')
                op.repo_name = repo.name
            else:
                if repo.needs_update:
                    row.alert = True
                    split = row.split(factor=0.30)
                    split.label(text=f"Assets ({repo.current_version}):", icon='ASSET_MANAGER')
                    if repo.update_message == "Rate limit exceeded!":
                        icon = 'CANCEL'
                    else:
                        icon = 'ERROR'
                    split.label(text=repo.update_message, icon=icon)
                    op = row.operator('wm.download_update', text="", icon='IMPORT')
                    op.repo_name = repo.name
                    op.wipe = False
                    op = row.operator('wm.check_update', text="", icon='FILE_REFRESH')
                    op.repo_name = repo.name
                    op = row.operator('wm.get_update', text="", icon='URL')
                    op.repo_name = repo.name
                else:
                    split = row.split(factor=0.30)
                    split.label(text=f"Assets ({repo.current_version}):", icon='ASSET_MANAGER')
                    if repo.update_message == "Rate limit exceeded!":
                        icon = 'CANCEL'
                    else:
                        icon = 'CHECKMARK'
                    split.label(text=repo.update_message, icon=icon)
                    op = row.operator('wm.check_update', text="", icon='FILE_REFRESH')
                    op.repo_name = repo.name
                    op = row.operator('wm.get_update', text="", icon='URL')
                    op.repo_name = repo.name

            repo = data.seut.repos['MWMBuilder']
            box2 = box.box()
            row = box2.row(align=True)

            if preferences.mwmb_path == "":
                row.alert = True
                row.label(text=f"MWMBuilder ({repo.current_version}):", icon='TOOL_SETTINGS')
                if repo.update_message == "Rate limit exceeded!":
                    icon = 'CANCEL'
                else:
                    icon = 'ERROR'
                row.label(text=repo.update_message, icon=icon)
                op = row.operator('wm.download_update', text="Download & Install", icon='IMPORT')
                op.repo_name = repo.name
                op.wipe = True
                op = row.operator('wm.get_update', text="", icon='URL')
                op.repo_name = repo.name
            else:
                if repo.needs_update:
                    row.alert = True
                    split = row.split(factor=0.30)
                    split.label(text=f"MWMBuilder ({repo.current_version}):", icon='TOOL_SETTINGS')
                    if repo.update_message == "Rate limit exceeded!":
                        icon = 'CANCEL'
                    else:
                        icon = 'ERROR'
                    split.label(text=repo.update_message, icon=icon)
                    op = row.operator('wm.download_update', text="", icon='IMPORT')
                    op.repo_name = repo.name
                    op.wipe = True
                    op = row.operator('wm.check_update', text="", icon='FILE_REFRESH')
                    op.repo_name = repo.name
                    op = row.operator('wm.get_update', text="", icon='URL')
                    op.repo_name = repo.name
                else:
                    split = row.split(factor=0.30)
                    split.label(text=f"MWMBuilder ({repo.current_version}):", icon='TOOL_SETTINGS')
                    if repo.update_message == "Rate limit exceeded!":
                        icon = 'CANCEL'
                    else:
                        icon = 'CHECKMARK'
                    split.label(text=repo.update_message, icon=icon)
                    op = row.operator('wm.check_update', text="", icon='FILE_REFRESH')
                    op.repo_name = repo.name
                    op = row.operator('wm.get_update', text="", icon='URL')
                    op.repo_name = repo.name

        box = layout.box()
        box.label(text="External Tools", icon='TOOL_SETTINGS')
        box.prop(self, "havok_path", text="Havok Filter Manager", expand=True)

        box = layout.box()
        box.label(text="SEUT Panels", icon="META_PLANE")
        row = box.row()

        box1 = row.box()
        box1.prop(self, "quick_tools", text="  Quick Tools")
        row1 = box1.row()
        row1.label(text="An assortment of shortcuts for modelling SE objects.")

        if self.dev_mode:
            box2 = row.box()
            box2.prop(self, "animation", text="  Animations Panel")
            row2 = box2.row()
            row2.label(text="Animation setup and export for the AnimationEngine framework.")


def load_icons():
    import bpy.utils.previews
    icon_discord = bpy.utils.previews.new()
    icon_dir = os.path.join(os.path.dirname(__file__), "assets")
    icon_discord.load("discord", os.path.join(icon_dir, "discord.png"), 'IMAGE')

    preview_collections['main'] = icon_discord


def unload_icons():

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


def get_icons() -> dict:
    return preview_collections


def verify_tool_path(self, context, path: str, name: str, filename: str) -> str:
    """Verifies the path of an external tool"""

    # If it's a directory but appending the name gives a valid path, do that. Else, error.
    if os.path.isdir(path):
        if os.path.exists(os.path.join(path, filename)):
            return os.path.join(path, filename)
        else:
            seut_report(self, context, 'ERROR', False, 'E030', 'directory', 'EXE')
            return ""

    # If it's not a directory and the path doesn't exist, error. If the basename is equal to the name, use the path. If the basename is not equal, error.
    elif not os.path.isdir(path):
        if not os.path.exists(path):
            seut_report(self, context, 'ERROR', False, 'E003', name, path)
            return ""
        else:
            if os.path.basename(path) == filename:
                return path
            else:
                seut_report(self, context, 'ERROR', False, 'E013', name, filename, os.path.basename(path))
                return ""


def get_addon_version():
    return addon_version


def save_addon_prefs():
    """Saves params from the addon's preferences to a json cfg."""

    wm = bpy.context.window_manager
    path = os.path.join(bpy.utils.user_resource('CONFIG'), 'space-engineers-utilities.cfg')

    data = get_config()

    with open(path, 'w') as cfg_file:
        json.dump(data, cfg_file, indent = 4)

    if addon_utils.check('blender_addon_updater') == (True, True) and __package__ in wm.bau.addons:
        bpy.ops.wm.bau_save_config(name=__package__, config=str(data))


def load_addon_prefs():
    """Loads params from the json cfg and saves them to preferences."""

    wm = bpy.context.window_manager
    if addon_utils.check('blender_addon_updater') == (True, True) and __package__ in wm.bau.addons:
        config = wm.bau.addons[__package__].config
        if config != "":
            set_config(config)

    else:
        path = os.path.join(bpy.utils.user_resource('CONFIG'), 'space-engineers-utilities.cfg')

        if os.path.exists(path):
            with open(path) as cfg_file:
                data = json.load(cfg_file)
                set_config(data)


def load_configs():
    """Loads all the json config files."""

    load_empty_json('dummies')
    load_empty_json('highlight_empties')
    load_empty_json('preset_subparts')

    load_json('material_variations')


def load_json(json_type):
    """Loads an individual config file for an empty type."""

    preferences = get_preferences()
    path = os.path.join(preferences.asset_path, "Config", json_type + ".cfg")
    global loaded_json
    loaded_json[json_type]= {}

    if not os.path.exists(path):
        return

    with open(path) as cfg_file:
        data = json.load(cfg_file)

    if not json_type in data:
        return

    entries = data[json_type]

    for key, entry in entries.items():
        loaded_json[json_type][key] = entry
        

def load_empty_json(empty_type):
    """Loads an individual config file for an empty type."""

    # TODO: Swap this to a generalized method that doesn't care about filenames and just looks for the dicts with empty types inside of the configs.
    # This way, more empties can be added by users without issues with overwriting.

    preferences = get_preferences()
    path = os.path.join(preferences.asset_path, "Config", empty_type + ".cfg")
    global empties
    empties[empty_type] = {}

    if not os.path.exists(path):
        return

    with open(path) as cfg_file:
        data = json.load(cfg_file)

    if not empty_type in data:
        return

    entries = data[empty_type]

    for key, entry in entries.items():
        empties[empty_type][key] = {
            'name': entry['name'],
            'description': entry['description'],
            'index': entry['index']
        }