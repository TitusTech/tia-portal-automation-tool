from __future__ import annotations

from pathlib import Path
from typing import Any
import base64

import modules.Portals as Portals
import modules.Projects as Projects
import modules.Devices as Devices
import modules.Networks as Networks
import resources.dlls

def generate_dlls() -> list[Path]:
    dll_paths: dict[str, Path] = {}
    for key in resources.dlls.b64_dlls:
        if key == "Siemens.Engineering.Contract":
            continue
        if "Hmi" in key:
            continue
        data = base64.b64decode(resources.dlls.b64_dlls[key])
        hmi_data = base64.b64decode(resources.dlls.b64_dlls[f"{key}.Hmi"])
        dlls_dir = Path("./DLLs")
        dlls_dir.mkdir(exist_ok=True)

        save_path = Path(dlls_dir) / key
        save_path.mkdir(exist_ok=True)
        version_dll_path = save_path / f"Siemens.Engineering.dll"
        with version_dll_path.open('wb') as version_dll_file:
            version_dll_file.write(data)
            # logger.logging.debug(f"Written data of {key}")

        version_hmi_dll_path = save_path / f"Siemens.Engineering.Hmi.dll"
        with version_hmi_dll_path.open('wb') as version_hmi_dll_file:
            version_hmi_dll_file.write(hmi_data)
            # logger.logging.debug(f"Written data of {key}")
        dll_paths[key] = version_dll_path.absolute()

    return dll_paths

def execute(imports: api.Imports, config: dict[str, Any], settings: dict[str, Any]):
    SE: Siemens.Engineering = imports.DLL

    TIA: Siemens.Engineering.TiaPortal = Portals.connect(imports, config, settings)

    project_data = Projects.Project(config['name'], config['directory'], config['overwrite'])
    devices_data = [Devices.Device(
                            dev.get('p_typeIdentifier', 'PLC_1'),
                            dev.get('p_name', 'NewPLCDevice'),
                            dev.get('p_deviceName', ''),
                            dev.get('id', 1),
                            dev.get('slots_required', 2),
                            Networks.NetworkInterface(
                                Address=dev.get('network_interface', {}).get('Address'),
                                RouterAddress=dev.get('network_interface', {}).get('RouterAddress'),
                                UseRouter=dev.get('network_interface', {}).get('UseRouter', False),
                            )
                        )
                        for dev in config.get('devices', [])
                    ]
    # subnetsdata = [SubnetData(net.get('subnet_name'), net.get('address'), net.get('io_controller')) for net in config.get('networks', [])]

    se_project: Siemens.Engineering.Project = Projects.create(imports, project_data, TIA)
    se_devices: list[Siemens.Engineering.HW.Device] = Devices.create(devices_data, se_project)
    se_interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    
    for i in range(len(devices_data)):
        se_device: Siemens.Engineering.HW.Device = se_devices[i]
        device_data: Devices.Device = devices_data[i]

        se_plc_software: Siemens.Engineering.HW.Software = Devices.get_plc_software(imports, se_device)
        se_net_itf: Siemens.Engineering.HW.Features.NetworkInterface = Networks.create_network_service(imports, device_data, se_device)

    #     for network_interface in itf:
    #         interfaces.append(network_interface)
