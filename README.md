# SEUT Linux Compatibility Fixes

## Summary of Changes Made

I've modified the Space Engineers Utilities addon to better support Linux by adding Wine integration when running windows tools and general path handling issues because of hardcoded '\\' values.

## Requirements for Linux

To use this addon on Linux, you need:

1. **Wine installed**: `sudo dnf install wine` (fedora) or equivalent for your distribution
2. **Wine configured**: Run `wine wineboot` if you dont already have a default wine prefix
3. **Required Windows tools**: 
- you need to install Havok Content Tools, net framework 3.5 service package 1, and visual cpp redistrutable in your defaut wine prefix

- you can install visual cpp redistrutable with this command ``winetricks -q vcrun2012``
- you can install net framework 3.5 service package 1 with this command ``wintricks -q dotnet35sp1``
- look at the space engineers SEUT wiki for the exe file (here)[https://spaceengineers.wiki.gg/wiki/Modding/Tools/Space_Engineers_Utilities#Downloads] and simply install it with ``wine HavokContentTools_2013-1-0_20130717_64Bit_PcXs.exe`` (name may vary)

## Troubleshooting

### Check Console Output
The addon provides debug output in Blender's console for any execution errors. To see it:
1. find a terminal
2. navigate to the installation location of blender
2. run blender with ./blender

### Common Issues and Solutions

#### Wine Not Found
If you get "wine: command not found":
```bash
sudo dnf install wine
```

#### Wine Tools Not Working
If Windows tools fail to run:
1. Test Wine with a simple command: `wine --version`
2. Check if Wine has the right components installed: `wine uninstaller`
2. 2. Make sure all required .NET Framework/Visual C++ redistributables are installed in Wine

#### Path Issues
If you see path-related errors:
- Make sure export paths don't contain special characters
- Verify that the export directory exists and is writable


### Testing the linux fixes
To test if the fix works:
1. Try importing an FBX file
2. Check the console for "SEUT:" debug messages
3. If you see Wine execution messages, the fix is working

### Reverting Changes

If you need to revert these changes, the main modifications are:
- Added Wine execution to `call_tool()` and `callTool()` functions
- Added path conversion utilities
- Added debug output

The core functionality remains the same, only Linux/Wine compatibility was improved.

## Error Reporting

If you encounter issues after these changes:
1. Check the debug output in the console
2. Look for Wine-specific error messages
3. Test individual tools manually with Wine to isolate issues
4. Ensure all dependencies are properly installed in Wine
5. make a issue on [this repository](https://github.com/Encoded404/space-engineers-utilities-linux-patch) DO NOT report it to the original repository unless you tested in on windows with the orginal version first. this is a small fix i made because i wanted it to work on linux, and is not made, or directly supported by the original creator.

# original decription:

# Space Engineers Utilities
A Blender 4.0+ addon to streamline working on assets for Space Engineers.

## Features
### Blender
* **Full Blender 4.0+ support** using collections to organize models.
* **Simple Navigation** to easily edit models one collection at a time.
* Robust **error handling** and extensive **feedback** to help you avoid issues further down the road and inform you **if and what** is the problem.
* Full support for **multiple scenes** per BLEND file.
* Set the **grid scale** to preset Space Engineers values to easily see the size of your model.
* Get notified of updates to the addon via **update notifications**.

##### Modes
* Use **Bounding Box Mode** to define the bounding box of your model.
* **Mirroring Mode** allows for easy setup of mirroring for blocks.
* By using **Mountpoint Mode** the user can define the mountpoints on a block in a straightforward manner.
* Use **Icon Render Mode** to easily create icons for your blocks in the style of vanilla Space Engineers blocks.

### Import
* Import Space Engineers **FBX files** through the addon to automatically display its materials in Blender.
* **Structure Conversion** functionality allows for easy conversion of BLEND files created with the old 2.7x plugin to the new format.

### Materials
* **Displays** most vanilla Space Engineers materials **directly in Blender**.
* Contains **Material Libraries** with most vanilla materials, ready to apply to new models.
* Create **your own** Space Engineers materials.
* Create **your own Material Libraries**.

### Empties
* **Subparts are instanced** into other scenes to show how the model will look ingame.
* Easily **create and manage** empties for different purposes by selecting from exhaustive lists.

### Export
* Define **LOD Distances** to set from which distance your LOD models are displayed.
* **Export simultaneously** to large and small grids.
* Directly export to **MWM**-format, ready to be loaded into the game.
* Additional definitions are exported to a **CubeBlocks** file.
* Full support for creating **character models** and **character poses & animations**.

## Installation
Please follow the [installation guide](https://spaceengineers.wiki.gg/wiki/Modding/Tutorials/Tools/SEUT/Installation_Guide).

## Credits	
* **Stollie** - So much general help but also writing everything character, export and MWM-related, which I wouldn't have been able to do at all.	
* **Harag** - Writing the [original Blender SE plugin](https://github.com/harag-on-steam/se-blender) as well as adjusting the FBXImporter. A lot of code in this addon is based on his.	
* **Wizard Lizard** - For hours of testing as well as writing the [SE Texture Converter](https://github.com/TheWizardLizard/SETextureConverter) to save us all from having to deal with batch files.
* **Kamikaze (Blender Discord)** - Writing the original `remap_materials()`-function and generally helping out constantly by answering a lot of questions.
