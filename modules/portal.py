from __future__ import annotations

from pathlib import Path
from typing import Any

from modules import api
from modules.structs import InstanceParameterTemplate, ProjectData
from modules.structs import DeviceCreationData
from modules.structs import SubnetData

def execute(imports: api.Imports, config: dict[str, Any], settings: dict[str, Any]):
    SE: Siemens.Engineering = imports.DLL

    TIA: Siemens.Engineering.TiaPortal = api.connect_portal(imports, config, settings)

    project_data = ProjectData(config['name'], config['directory'], config['overwrite'])
    dev_create_data = [DeviceCreationData(dev.get('p_typeIdentifier', 'PLC_1'), dev.get('p_name', 'NewPLCDevice'), dev.get('p_deviceName', '')) for dev in config.get('devices', [])]
    subnetsdata = [SubnetData(net.get('subnet_name'), net.get('address'), net.get('io_controller')) for net in config.get('networks', [])]

    project: Siemens.Engineering.Project = api.create_project(imports, project_data, TIA)
    devices: list[Siemens.Engineering.HW.Device] = api.create_devices(dev_create_data, project)
    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    for i, device_data in enumerate(config['devices']):
        device = devices[i]
        plc_software: Siemens.Engineering.HW.Software = api.get_plc_software(imports, device)

        itf: Siemens.Engineering.HW.Features.NetworkInterface = api.create_device_network_service(imports, device_data, device)

        for network_interface in itf:
            interfaces.append(network_interface)


    subnet: Siemens.Engineering.HW.Subnet = None
    io_system: Siemens.Engineering.HW.IoSystem = None
    for network_interface in interfaces:
        for network in subnetsdata:
            if network_interface.Nodes[0].GetAttribute('Address') != network.Address:
                continue
            if interfaces.index(network_interface) == 0:
                subnet: Siemens.Engineering.HW.Subnet = network_interface.Nodes[0].CreateAndConnectToSubnet(network.Name)
                io_system: Siemens.Engineering.HW.IoSystem = network_interface.IoControllers[0].CreateIoSystem(network.IoController)
            else:
                network_interface.Nodes[0].ConnectToSubnet(subnet)
                if network_interface.IoConnectors.Count > 0:
                    network_interface.IoConnectors[0].ConnectToIoSystem(io_system)

