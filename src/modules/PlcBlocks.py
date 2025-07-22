from __future__ import annotations
import logging
from pathlib import Path, PurePosixPath

from src.core import logs

logs.setup(logging.DEBUG)
logger = logging.getLogger(__name__)


def import_xml_to_block_group(imports: Imports,
                              plc_software: Siemens.Engineering.HW.Software,
                              xml_location: Path,
                              blockgroup_folder: PurePosixPath,
                              mkdir: bool = False
                              ) -> Siemens.Engineering.SW.Blocks.PlcBlock:
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    logging.info(f"Import of XML {xml_location.absolute()} started")

    xml_dotnet_path: FileInfo = FileInfo(xml_location.absolute().as_posix())

    blockgroup = locate_blockgroup(
        plc_software, blockgroup_folder, mkdir)

    plcblock: Siemens.Engineering.SW.Blocks.PlcBlock = blockgroup.Blocks.Import(
        xml_dotnet_path, SE.ImportOptions.Override)

    logging.info(f"Finished: Import of XML {xml_dotnet_path}")

    return plcblock


def locate_blockgroup(plc_software: Siemens.Engineering.HW.Software,
                      blockgroup_folder: PurePosixPath,
                      mkdir: bool = False) -> Siemens.Engineering.SW.Blocks.BlockGroup | None:
    if not blockgroup_folder.is_absolute():
        blockgroup_folder = PurePosixPath('/') / blockgroup_folder

    current_blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup | None = plc_software.BlockGroup
    previous_blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup | None = plc_software.BlockGroup
    for part in blockgroup_folder.parts:
        if part == '/':
            continue
        current_blockgroup = current_blockgroup.Groups.Find(part)
        if not current_blockgroup:
            if mkdir:
                current_blockgroup = previous_blockgroup.Groups.Create(part)
            else:
                return
        previous_blockgroup = current_blockgroup

    return current_blockgroup


def find_plcblock(plc_software: Siemens.Engineering.HW.Software,
                  blockgroup_folder: PurePosixPath,
                  name: str) -> Siemens.Engineering.SW.Blocks.PlcBlock:
    if not name:
        return

    blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup = locate_blockgroup(
        plc_software, blockgroup_folder)

    if not blockgroup:
        return

    plcblock: Siemens.Engineering.SW.Blocks.PlcBlock = blockgroup.Blocks.Find(
        name)

    return plcblock


def copy_plcblock_from_library(TIA: Siemens.Engineering.TiaPortal,
                               plc_software: Siemens.Engineering.HW.Software,
                               name: str,
                               blockgroup_folder: PurePosixPath
                               ) -> Siemens.Engineering.SW.Blocks.PlcBlock:
    library: Siemens.Engineering.GlobalLibraries.GlobalLibrary = get_library(
        TIA, data.Library)
    if not library:
        logging.info(f"Instance {data.Name} not added to PlcSoftware {
                     plc_software.Name}. GlobalLibrary {data.Library} not found.")
        return

    mastercopy: Siemens.Engineering.Library.MasterCopies.MasterCopy = get_mastercopy_from_folder(
        library.MasterCopyFolder, data.FromFolder, data.Name)
    if not mastercopy:
        logging.info(f"Instance {data.Name} not added to PlcSoftware {
                     plc_software.Name}. MasterCopy {data.Name} not found.")
        return

    plcblock: Siemens.Engineering.SW.Blocks.PlcBlock | None = import_mastercopy_to_software(
        plc_software.BlockGroup, data.ToFolder, mastercopy)

    return plcblock


def generate_plcblock(imports: Imports,
                      TIA: Siemens.Engineering.TiaPortal,
                      plc_software: Siemens.Engineering.HW.Software,
                      data: DataBlock,
                      xml: Base):

    if data.IsInstance:
        # if we want to copy from GLOBAL LIBRARY
        if not isinstance(data.LibraryData, dict):
            pass  # nothing to do here

    else:
        filename: Path = xml.write()

        logger.info(f"Written Program Block {
                    data.Name} XML data to: {filename}")
        import_xml_to_block_group(imports, plc_software, xml_location=filename,
                                  blockgroup_folder=data.BlockGroupPath,
                                  mkdir=True)
        if filename.exists():
            filename.unlink()
