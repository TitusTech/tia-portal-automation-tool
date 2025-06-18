from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import modules.Networks as Networks

class Device:
    p_typeIdentifier: str
    p_name: str
    p_deviceName: str
    ID: int
    SlotsRequired: int
    NetworkInterface: Optional[NetworkInterface]


def create(data: list[Device], project: Siemens.Engineering.Project) -> list[Siemens.Engineering.HW.Device]:
    devices: list[Siemens.Engineering.HW.Device] = []

    for device_data in data:
        device_composition: Siemens.Engineering.HW.DeviceComposition = project.Devices
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(device_data.TypeIdentifier, device_data.Name, device_data.DeviceName)

        # logging.info(f"Created device: ({device_data.DeviceName}, {device_data.TypeIdentifier}) on {device.Name}")

        devices.append(device)

    return devices

def get_plc_software(imports:Imports, device: Siemens.Engineering.HW.Device) -> Siemens.Engineering.HW.Software:
    SE: Siemens.Engineering = imports.DLL

    hw_obj: Siemens.Engineering.HW.HardwareObject = device.DeviceItems

    for device_item in hw_obj:
        # logging.debug(f"Accessing a PlcSoftware from DeviceItem {device_item.Name}")

        software_container: Siemens.Engineering.HW.Features.SoftwareContainer = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.SoftwareContainer]()
        # if not software_container:
            # logging.debug(f"No PlcSoftware found for DeviceItem {device_item.Name}")
        # logging.debug(f"Found PlcSoftware for DeviceItem {device_item.Name}")

        if not software_container:
            continue
        plc_software: Siemens.Engineering.HW.Software = software_container.Software
        if not isinstance(plc_software, SE.SW.PlcSoftware):
            continue

        return plc_software
