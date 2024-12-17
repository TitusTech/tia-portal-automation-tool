from __future__ import annotations

from pathlib import Path
from typing import Any

from modules import api
from modules.structs import InstanceParameterTemplate, ProjectData
from modules.structs import LibraryConfigData, LibraryData
from modules.structs import DeviceCreationData
from modules.structs import ModuleData, ModulesContainerData
from modules.structs import TagTableData, TagData
from modules.structs import MasterCopiesDeviceData
from modules.structs import InstanceData, LibraryInstanceData, NetworkSourceData, PlcBlockData, DatabaseData, Source
from modules.structs import DocumentSWType, PlcStructData
from modules.structs import DatabaseType, GlobalDBData, VariableStruct
from modules.structs import VariableStruct, VariableSection
from modules.structs import WireParameter
from modules.structs import WatchAndForceTablesData, PlcWatchForceType, PlcWatchTableEntryData, PlcForceTableEntryData


def execute(imports: api.Imports, config: dict[str, Any], settings: dict[str, Any]):
    SE: Siemens.Engineering = imports.DLL

    TIA: Siemens.Engineering.TiaPortal = api.connect_portal(imports, config, settings)

    project_data = ProjectData(config['name'], config['directory'], config['overwrite'])
    library_data = clean_libraries_data(config.get('libraries', []))
    dev_create_data = [DeviceCreationData(dev.get('p_typeIdentifier', 'PLC_1'), dev.get('p_name', 'NewPLCDevice'), dev.get('p_deviceName', '')) for dev in config.get('devices', [])]


    project: Siemens.Engineering.Project = api.create_project(imports, project_data, TIA)
    libraries, template = api.import_libraries(imports, TIA, library_data)
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
        watchandforcetablesdata = clean_watch_and_force_tables(device_data.get('Watch and force tables', []))


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
            plcblockdata.append(clean_program_block_data(block, template))
        api.generate_program_blocks(imports, TIA, plc_software, plcblockdata)
        api.generate_watch_and_force_tables(imports, plc_software, watchandforcetablesdata)




def clean_program_block_data(data: dict, template: list[InstanceParameterTemplate] = []) -> PlcBlockData | DatabaseData:
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
                                                   Database=clean_instance_database(instance),
                                                   Parameters=clean_wire_parameters(instance.get('parameters', {}), instance['name'])
                                                   )
                    case Source.LOCAL:
                        inst = InstanceData(Type=instance['type'],
                                            Source=instance['source'],
                                            Name=instance['name'],
                                            FromFolder=instance.get('from_folder', []),
                                            ToFolder=instance.get('to_folder', []),
                                            Database=clean_instance_database(instance),
                                            Parameters=clean_wire_parameters(instance.get('parameters', {}), instance['name'], template)
                                            )
            else:
                if instance.get('type') in [DocumentSWType.BlocksFB, DocumentSWType.BlocksOB, DocumentSWType.BlocksFC]:
                    inst = clean_program_block_data(instance, template)

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
                            Variables=clean_variable_sections(data.get('variables', [])),
                            Parameters=clean_wire_parameters(data.get('parameters', {}), data['name'])
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


def clean_wire_parameters(data: dict, name: str, template: list[InstanceParameterTemplate] = []) -> list[WireParameter]:
    wires: list[WireParameter] = []
    en: WireParameter = WireParameter(Name="en",
                                      Section="",
                                      Datatype="Bool",
                                      Value=data.get("en", ''),
                                      Negated=False
                                      )
    wires.append(en)

    for instance_T in template:
        if instance_T.Name != name:
            continue
        for parameter in instance_T.Parameters:
            if not parameter.Name in data:
                parameter.Value = ""
                continue
            parameter.Value = data[parameter.Name]
            wires.append(parameter)

    return wires


def clean_watch_and_force_tables(tables: list[dict]) -> list[WatchAndForceTablesData]:
    data: list[WatchAndForceTablesData] = []

    for table in tables:
        entries = []
        for entry in table.get('Entries', []):
            if table['type'] == PlcWatchForceType.PlcWatchTable:
                e = PlcWatchTableEntryData(Name=entry['Name'],
                                           Address=entry.get('Address', ''),
                                           DisplayFormat=entry.get('DisplayFormat', ''),
                                           MonitorTrigger=entry.get('MonitorTrigger', ''),
                                           ModifyIntention=entry.get('ModifyIntention', False),
                                           ModifyTrigger=entry.get('ModifyTrigger', "Permanent"),
                                           ModifyValue=entry.get('ModifyValue', '')
                                           )
                entries.append(e)
            if table['type'] == PlcWatchForceType.PlcForceTable:
                e = PlcForceTableEntryData(Name=entry['Name'],
                                           Address=entry.get('Address', ''),
                                           DisplayFormat=entry.get('DisplayFormat', ''),
                                           MonitorTrigger=entry.get('MonitorTrigger', ''),
                                           ForceIntention=entry.get('ForceIntention', False),
                                           ForceValue=entry.get('ForceValue', '')
                                           )
                entries.append(e)

        t = WatchAndForceTablesData(Type=table['type'],
                                    Name=table['Name'],
                                    Entries=entries
                                    )
        data.append(t)

    return data

def clean_libraries_data(data: list[dict]) -> list[LibraryData]:
    libraries: list[LibraryData] = []

    for library in data:
        config = library.get('config', {})
        cleaned_library = LibraryData(FilePath=Path(library.get('path')),
                                      ReadOnly=library.get('read_only', True),
                                      Config=LibraryConfigData(Template=config.get('template'))
                                      )
        libraries.append(cleaned_library)

    return libraries

# def execute_old(SE: Siemens.Engineering, config: dict[Any, Any], settings: dict[str, Any]):
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
