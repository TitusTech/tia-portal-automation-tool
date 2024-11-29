from __future__ import annotations

from pathlib import Path
from typing import Any

from modules import api
from modules.structs import ProjectData
from modules.structs import LibraryData
from modules.structs import DeviceCreationData
from modules.structs import ModuleData, ModulesContainerData
from modules.structs import TagTableData, TagData
from modules.structs import MasterCopiesDeviceData
from modules.structs import InstanceData, LibraryInstanceData, NetworkSourceData, PlcBlockData, DatabaseData, Source
from modules.structs import DocumentSWType, PlcStructData
from modules.structs import DatabaseType, GlobalDBData, VariableStruct
from modules.structs import VariableStruct, VariableSection


def execute(imports: api.Imports, config: dict[str, Any], settings: dict[str, Any]):
    SE: Siemens.Engineering = imports.DLL

    TIA: Siemens.Engineering.TiaPortal = api.connect_portal(imports, config, settings)

    project_data = ProjectData(config['name'], config['directory'], config['overwrite'])
    library_data = [LibraryData(Path(lib.get('path')), lib.get('read_only')) for lib in config.get('libraries', [])]
    dev_create_data = [DeviceCreationData(dev.get('p_typeIdentifier', 'PLC_1'), dev.get('p_name', 'NewPLCDevice'), dev.get('p_deviceName', '')) for dev in config.get('devices', [])]


    project: Siemens.Engineering.Project = api.create_project(imports, project_data, TIA)
    api.import_libraries(imports, library_data, TIA)
    devices: list[Siemens.Engineering.HW.Device] = api.create_devices(dev_create_data, project)
    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    for i, device_data in enumerate(config['devices']):
        device = devices[i]
        plc_software: Siemens.Engineering.HW.Software = api.get_plc_software(imports, device)

        localmodule_data = [ModuleData(module['TypeIdentifier'], module['Name'], module['PositionNumber']) for module in device_data.get('Local modules', [])]
        hmimodule_data = [ModuleData(module['TypeIdentifier'], module['Name'], module['PositionNumber']) for module in device_data.get('Modules', [])]
        modules_container = ModulesContainerData(localmodule_data, hmimodule_data, device_data.get('slots_required', 2))
        tagtabledata = [TagTableData(table.get('Name', 'Tag table_1')) for table in device_data.get('PLC tags', [])]
        plcstructdata = [PlcStructData(p.get('Name'), p.get('types')) for p in device_data.get('PLC data types', [])]
        requiredlibsdata = MasterCopiesDeviceData(device_data.get('required_libraries', []))

        api.generate_mastercopies_to_device(TIA, plc_software, requiredlibsdata)
        api.generate_modules(modules_container, device)
        itf: Siemens.Engineering.HW.Features.NetworkInterface = api.create_device_network_service(imports, device_data, device)
        interfaces.append(itf)

        api.generate_tag_tables(tagtabledata, plc_software)
        for tag_table in device_data.get('PLC tags', []):
            table: Siemens.Engineering.SW.Tags.PlcTagTable = api.find_tag_table(imports, tag_table['Name'], plc_software)
            if not isinstance(table, SE.SW.Tags.PlcTagTable):
                continue
            for tag_data in tag_table['Tags']:
                tag = TagData(tag_data['Name'], tag_data['DataTypeName'], tag_data['LogicalAddress'])
                api.create_tag(table, tag)

        api.generate_user_data_types(imports, plc_software, plcstructdata)

        plcblockdata = []
        for block in device_data.get('Program blocks', []):
            plcblockdata.append(clean_program_block_data(block))
        api.generate_program_blocks(imports, TIA, plc_software, plcblockdata)



def clean_program_block_data(data: dict) -> PlcBlockData | DatabaseData:
    if data['type'] == DatabaseType.GlobalDB:
        return GlobalDBData(Type=data['type'],
                            Name=data['name'],
                            Number=data.get('number', 1),
                            Folder=data.get('folder', []),
                            Structs=clean_variable_structs(data['data']),
                            Attributes=data.get('attributes', {}),
                            )
    if data['type'] == DatabaseType.InstanceDB:
        return DatabaseData(Type=data['type'],
                            Name=data['name'],
                            Number=data.get('number', 1),
                            Folder=data.get('folder', [])
                            )


    network_sources = []
    for ns in data.get('network_sources', []):
        instances = []
        for instance in ns.get('instances', []):
            inst = None
            if instance.get('source'):
                match instance['source']:
                    case Source.LIBRARY:
                        inst = LibraryInstanceData(Type=instance['type'],
                                                   Source=instance['source'],
                                                   Library=instance['library'],
                                                   Name=instance['name'],
                                                   FromFolder=instance.get('from_folder', []),
                                                   ToFolder=instance.get('to_folder', []),
                                                   Database=clean_instance_database(instance)
                                                  )
                    case Source.LOCAL:
                        inst = InstanceData(Type=instance['type'],
                                            Source=instance['source'],
                                            Name=instance['name'],
                                            FromFolder=instance.get('from_folder', []),
                                            ToFolder=instance.get('to_folder', []),
                                            Database=clean_instance_database(instance)
                                            )
            else:
                if instance.get('type') in [DocumentSWType.BlocksFB, DocumentSWType.BlocksOB, DocumentSWType.BlocksFC]:
                    inst = clean_program_block_data(instance)

            if not inst: continue

            instances.append(inst)

        network_sources.append(NetworkSourceData(Title=ns.get('title', ""),
                                Comment=ns.get('comment', ""),
                                Instances=instances,
                                )
                            )
    plcblock = PlcBlockData(Type=data['type'],
                            Name=data['name'],
                            ProgrammingLanguage=data.get('programming_language', "FBD"),
                            Number=data.get('number', 1),
                            Folder=data.get('folder', []),
                            NetworkSources=network_sources,
                            Database=clean_instance_database(data),
                            Variables=clean_variable_sections(data.get('variables', []))
                           )
    return plcblock


def clean_instance_database(instance: dict) -> DatabaseData:
    db = instance.get('db', {})

    return DatabaseData(Type=db.get('type', DatabaseType.InstanceDB),
                        Name=db.get('name', ""),
                        Folder=db.get('folder', []),
                        Number=db.get('number', 1)
                        )
    

def clean_variable_structs(structs: list[dict]) -> list[VariableStruct]:
    variables: list[VariableStruct] = []
    for struct in structs:
        var = VariableStruct(Name=struct['name'],
                             Datatype=struct['datatype'],
                             Retain=struct.get('retain', True),
                             StartValue=struct.get('start_value', ""),
                             Attributes=struct.get('attributes', {})
                             )
        variables.append(var)
    return variables

def clean_variable_sections(sections: list[dict]) -> list[VariableSection]:
    var_sections: list[VariableSection] = []

    for section in sections:
        sec = VariableSection(Name=section['name'], Variables=clean_variable_structs(section['data']))
        var_sections.append(sec)
    return var_sections



# def execute_old(SE: Siemens.Engineering, config: dict[Any, Any], settings: dict[str, Any]):
#     # do tags next, but before that finish network setup of device
#         for device_item in device.DeviceItems:
#             logging.info(f"Adding Program blocks for {software_base.Name}")
#             logging.debug(f"Program blocks data: {device_data.get('Program blocks', {})}")
#
#             def create_instance(plc_block):
#                 wires = []
#                 for networks in plc_block.get('network_sources', []):
#                     for instance in networks:
#                         data = create_instance(instance)
#                         if not data: continue
#                         wires.append(data)
#
#                 if not plc_block.get('source'):
#                     xml = None
#                     match plc_block.get('type'):
#                         case PlcType.OB:
#                             xml_obj = OB(
#                                 plc_block.get('name'),
#                                 plc_block.get('number'),
#                                 plc_block.get('db', {})
#                             )
#                             xml = xml_obj.build(
#                                 programming_language=plc_block.get('programming_language'),
#                                 network_sources=plc_block.get('network_sources', []),
#                             )
#                         case PlcType.FB:
#                             xml_obj = FB(
#                                 plc_block.get('name'),
#                                 plc_block.get('number'),
#                                 plc_block.get('db', {})
#                             )
#                             for i, nws in enumerate(plc_block.get('network_sources', [])):
#                                 for j, network in enumerate(nws):
#                                     if not network.get('db', {}).get('sections'):
#                                         plc_block['network_sources'][i][j]['db']['sections'] = wires[i]
#
#                             xml = xml_obj.build(
#                                 programming_language=plc_block.get('programming_language'),
#                                 network_sources=plc_block.get('network_sources', [])
#                             )
#                         case DatabaseType.GLOBAL:
#                             xml_obj = GlobalDB(
#                                 plc_block.get('type', DatabaseType.GLOBAL).value,
#                                 plc_block.get('name'),
#                                 plc_block.get('number')
#                             )
#                             xml = xml_obj.build(plc_block.get('programming_language'))
#
#                     if not xml:
#                         return
#
#                     logging.debug(f"XML data: {xml}")
#
#                     filename = uuid.uuid4().hex
#                     path = Path(tempfile.gettempdir()).joinpath(filename)
#
#                     with open(path, 'w') as file:
#                         file.write(xml)
#
#                         logging.info(f"Written XML data to: {path}")
#
#                     software_base.BlockGroup.Blocks.Import(FileInfo(path.as_posix()), SE.ImportOptions.Override)
#                     
#                     logging.info(f"New PLC Block: {plc_block.get('name')} added to {software_base.Name}")
#
#
#                     db = plc_block.get('db')
#                     if db.get('type') == DatabaseType.SINGLE:
#                         logging.info(f"Creating InstanceDB '{db.get('name')}' for PlcSoftware {software_base.Name}...")
#
#                         software_base.BlockGroup.Blocks.CreateInstanceDB(db['name'], True, db.get('number', 1), db['instanceOfName'])
#
#                     logging.info(f"New Single InstanceDB: {plc_block.get('name')} added to {software_base.Name}")
#
#                     return
#
#                 block_source = plc_block.get('source')
#
#                 logging.debug(f"Source: {block_source}")
#
#                 is_valid_library_source = config_schema.schema_source_library.is_valid(block_source)
#
#                 logging.info(f"Checking if PLC Block source is a library: {is_valid_library_source}")
#
#                 if is_valid_library_source:
#                     for library in TIA.GlobalLibraries:
#                         db_sections: list[dict[str, Any]] = []
#
#                         logging.debug(f"Checking Library: {block_source.get('library')}")
#
#                         if library.Name != block_source.get('library'): continue
#                         mastercopy = library.MasterCopyFolder.MasterCopies.Find(block_source.get('name'))
#                         if not mastercopy: continue
#                         new_block = software_base.BlockGroup.Blocks.CreateFrom(mastercopy)
#                         new_block.SetAttribute("Name", plc_block.get('name'))
#
#                         logging.info(f"New PLC Block {new_block.Name} from Library {library.Name} added to {software_base.Name}")
#
#                         singleCompile = new_block.GetService[SE.Compiler.ICompilable]();
#                         singleCompile.Compile()
#                         filename = uuid.uuid4().hex
#                         path = f"{Path(tempfile.gettempdir()).absolute().as_posix()}/{filename}.xml"
#                         new_block.Export(FileInfo(path), getattr(SE.ExportOptions, "None")   )
#
#                         with open(path, 'r', encoding='utf-8') as file:
#                             xml = ET.fromstring(file.read().replace('\ufeff<?xml version="1.0" encoding="utf-8"?>\n', ''))
#                             namespace = {'ns': 'http://www.siemens.com/automation/Openness/SW/Interface/v5'}
#
#                             sections = xml.find('.//ns:Sections', namespace)
#                             if not sections:
#                                 break
#                             for section in sections:
#                                 if section.get('Name') in ['Constant']:
#                                     continue
#                                 section_name = section.get('Name')
#                                 for member in section:
#                                     name = member.get('Name')
#                                     datatype = member.get('Datatype')
#                                     if not name: continue
#                                     if not section: continue
#                                     if not datatype: continue
#                                     data = {
#                                         "name": section_name,
#                                         "members": [
#                                             {
#                                                 "Name": name,
#                                                 "Datatype": datatype
#                                             }
#                                         ]
#                                     }
#                                     db_sections.append(data)
#         
#                         return db_sections
#                     return
#                     
#                 is_valid_plc_source = config_schema.schema_source_plc.is_valid(block_source)
#
#                 logging.info(f"Checking if PLC Block source is a plc: {is_valid_plc_source}")
#
#                 if is_valid_plc_source:
#                     # TODO:implement this when needed
#                     return
#
#             
#             for plc_block in device_data.get('Program blocks', []):
#                 plc_block['network_sources'] = [blck for blck in plc_block.get('network_sources', []) if blck]
#                 create_instance(plc_block)
#                 db = plc_block.get('db')
#                 if db.get('type') == DatabaseType.GLOBAL:
#                     logging.info(f"Creating GlobalDB '{db.get('name')}' for PlcSoftware {software_base.Name}...")
#
#                     xml_obj = GlobalDB(
#                         db['type'].value,
#                         db['name'],
#                         db['number']
#                     )
#                     xml = xml_obj.build(db['programming_language'])
#
#                     logging.debug(f"XML data: {xml}")
#
#                     filename = uuid.uuid4().hex
#                     path = Path(tempfile.gettempdir()).joinpath(filename)
#
#                     with open(path, 'w') as file:
#                         file.write(xml)
#
#                         logging.info(f"Written XML data to: {path}")
#
#                     software_base.BlockGroup.Blocks.Import(FileInfo(path.as_posix()), SE.ImportOptions.Override)
#
#                     logging.info(f"New GlobalDB: {plc_block.get('name')} added to {software_base.Name}")
#
#
#     # interfaces is used here
#     subnet: Siemens.Engineering.HW.Subnet = None
#     io_system: Siemens.Engineering.HW.IoSystem = None
#     for i, network in enumerate(config.get('networks', [])):
#         for itf in interfaces:
#             if itf.Nodes[0].GetAttribute('Address') != network.get('address'): continue
#             if i == 0:
#
#                 logging.info(f"Creating ({network.get('subnet_name')} subnet, {network.get('io_controller')} IO Controller)")
#
#                 subnet: Siemens.Engineering.HW.Subnet = itf.Nodes[0].CreateAndConnectToSubnet(network.get('subnet_name'))
#                 io_system: Siemens.Engineering.HW.IoSystem = itf.IoControllers[0].CreateIoSystem(network.get('io_controller'))
#
#                 logging.info(f"Successfully created ({network.get('subnet_name')} subnet, {network.get('io_controller')} IO Controller)")
#                 logging.debug(f"""Subnet: {subnet.Name}
#                 NetType: {subnet.NetType}
#                 TypeIdentifier: {subnet.TypeIdentifier}
#             IO System: {io_system.Name}
#                 Number: {io_system.Number}
#                 Subnet: {io_system.Subnet.Name}""")
#
#                 continue
#
#             logging.info(f"Connecting Subnet {subnet.Name} to IoSystem {io_system.Name}")
#
#             itf.Nodes[0].ConnectToSubnet(subnet)
#
#             logging.debug(f"Subnet {subnet.Name} connected to NetworkInterface Subnets")
#
#             if itf.IoConnectors.Count > 0:
#                 itf.IoConnectors[0].ConnectToIoSystem(io_system)
#
#                 logging.info(f"IoSystem {io_system.Name} connected to NetworkInterface IoConnectors")
