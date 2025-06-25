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

def clone_mastercopy_to_plc(block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup, mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopyFolder):
    if not mastercopyfolder: return

    logging.info(f"Cloning Mastercopies of MasterCopyFolder {mastercopyfolder.Name} to PlcBlockGroup {block_group.Name}")

    for folder in mastercopyfolder.Folders:
        if folder.Name == "__": continue # skip unplanned / unknown blocks, let the config handle it
        new_block_group = block_group.Groups.Create(folder.Name)

        logging.info(f"Copied MasterCopyFolder {folder.Name}")

        clone_mastercopy_to_plc(new_block_group, folder)

    for mastercopy in mastercopyfolder.MasterCopies:
        logging.info(f"Copied MasterCopy {mastercopy.Name}")

        block_group.Blocks.CreateFrom(mastercopy)

    return


def generate_mastercopies_to_device(TIA: Siemens.Engineering.TiaPortal, plc_software: Siemens.Engineering.HW.Software, data: MasterCopiesDeviceData):
    logging.info(f"Copying {len(data.Libraries)} Libraries to {plc_software.Name}...")
    logging.debug(f"Libraries: {data.Libraries}")

    for library_name in data.Libraries:
        library: Siemens.Engineering.GlobalLibraries.GlobalLibrary = get_library(TIA, library_name)
        if not library:
            continue
        mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopySystemFolder = library.MasterCopyFolder
        root_block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup = plc_software.BlockGroup.Groups.Create(library.Name)

        clone_mastercopy_to_plc(root_block_group, mastercopyfolder)

    return
