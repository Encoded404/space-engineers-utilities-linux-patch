import bpy
import os
import tempfile

from ..seut_export_utils        import ExportSettings
from ...utils.called_tool_type  import ToolType
from ...utils.seut_xml_utils    import update_subelement, format_entry
from ...seut_errors             import seut_report
from ...seut_utils              import linux_path_to_wine_path

def convert_fbx_to_fbxi_hkt(context, settings: ExportSettings, source: str, target: str):
    """Converts the FBX created by export to FBXImporter FBX for HKT creation."""

    settings.callTool(
        context,
        [settings.fbximporter, source, target],
        ToolType(1),
        logfile=f"{target}.convert.log"
    )

def convert_fbxi_hkt_to_hkt(self, context, settings: ExportSettings, source: str, target: str, adjustments: dict = None):
    """Converts the HKT created by FBXImporter to the final HKT."""

    havok_options = get_hko_content(adjustments)

    hko = tempfile.NamedTemporaryFile(mode='wt', prefix='space_engineers_', suffix=".hko", delete=False) # wt mode is write plus text mode.
    try:
        with hko.file as tempfile_to_process:
            tempfile_to_process.write(havok_options)
        
        # Convert paths for Wine compatibility on Linux
        hko_wine_path: str = linux_path_to_wine_path(hko.name)
        target_wine_path: str = linux_path_to_wine_path(target)
        source_wine_path: str = linux_path_to_wine_path(source)
        logfile_wine_path: str = linux_path_to_wine_path(target + ".filter.log")

        # -t is for standard ouput, -s designates a filter set (hko created above), -p designates path.
        # Above referenced from running "hctStandAloneFilterManager.exe -h"
        result = settings.callTool(
            context,
            [settings.havokfilter, '-t', '-s', hko_wine_path, '-p', target_wine_path, source_wine_path],
            ToolType(2),
            logfile=logfile_wine_path,
            successfulExitCodes=[0,1]
        )

    except Exception as e:
        print(e)

    finally:
        if context.scene.seut.export_deleteLooseFiles:
            os.remove(hko.name)


def get_hko_content(adjustments: dict = None) -> str:
    """Returns the content of the default HKO file."""

    # This file is taken entirely from Balmung's fork of Harag's plugin. No reason to reinvent the wheel.
    # https://github.com/Hotohori/se-blender/blob/master/src/python/space_engineers/havok_options.py
    path = os.path.join(os.path.dirname(__file__), 'default.hko')

    with open(path, 'r') as file:
        hko = file.read()

    if adjustments is not None:
        for elem, value in adjustments.items():
            hko = update_subelement(hko, 'hkparam', value, elem)
        hko = format_entry(hko)

    return hko