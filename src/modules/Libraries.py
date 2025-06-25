from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class GlobalLibrary:
    FilePath: Path
    ReadOnly: Optional[bool] = None


def import_library(imports: Imports, data: GlobalLibrary, TIA: Siemens.Engineering.TiaPortal) -> Siemens.Engineering.Library.GlobalLibrary:
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    library_path: FileInfo = FileInfo(data.FilePath.as_posix())

    # logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.ReadOnly})")

    library: Siemens.Engineering.Library.GlobalLibrary = SE.Library.GlobalLibrary
    if data.ReadOnly:
        library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadOnly)
    else:
        library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadWrite)

    # logging.info(f"Successfully opened GlobalLibrary: {library.Name}")

    return library

def copy_mastercopies_to_plc_group(mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopyFolder, block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup):
    if not mastercopyfolder: return

    # logging.info(f"Cloning Mastercopies of MasterCopyFolder {mastercopyfolder.Name} to PlcBlockGroup {block_group.Name}")

    for folder in mastercopyfolder.Folders:
        if folder.Name == "__": continue # skip unplanned / unknown blocks, let the config handle it
        new_block_group = block_group.Groups.Create(folder.Name)

        # logging.info(f"Copied MasterCopyFolder {folder.Name}")

        copy_mastercopies_to_plc_group(folder, new_block_group)

    for mastercopy in mastercopyfolder.MasterCopies:
        # logging.info(f"Copied MasterCopy {mastercopy.Name}")

        block_group.Blocks.CreateFrom(mastercopy)

    return


def generate_mastercopies(name: str, plc_software: Siemens.Engineering.HW.Software, TIA: Siemens.Engineering.TiaPortal):
    # logging.info(f"Copying {len(data.Libraries)} Libraries to {plc_software.Name}...")
    # logging.debug(f"Libraries: {data.Libraries}")

    library: Siemens.Engineering.GlobalLibraries.GlobalLibrary = find(TIA, name)
    if not library:
        return
    mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopySystemFolder = library.MasterCopyFolder
    root_block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup = plc_software.BlockGroup.Groups.Create(library.Name)

    copy_mastercopies_to_plc_group(mastercopyfolder, root_block_group)

    return


def find(TIA: Siemens.Engineering.TiaPortal, name: str) -> Siemens.Engineering.GlobalLibraries.GlobalLibrary:
    # logging.info(f"Searching for Library {name}")
    # logging.info(f"List of GlobalLibraries: {TIA.GlobalLibraries}")

    for global_library in TIA.GlobalLibraries:
        if global_library.Name == name:
            # logging.info(f"Found Library {glob_lib.Name}")
            return global_library
