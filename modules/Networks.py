from __future__ import annotations
from dataclasses import dataclass

import modules.Devices as Devices

@dataclass
class NetworkInterface:
    Name: Optional[str]
    Address: Optional[str]
    NodeId: Optional[str] # read only
    NodeType: Optional[str] # unsupported
    UseIsoProtocol: Optional[bool]
    MacAddress: Optional[str]
    UseIpProtocol: Optional[bool]
    IpProtocolSelection: Optional[str] # unsupported
    Address: Optional[str]
    SubnetMask: Optional[str]
    UseRouter: Optional[bool] # no need, just set RouterAddress to make this true
    RouterAddress: Optional[str]
    DhcpClientId: Optional[str]
    PnDeviceNameSetDirectly: Optional[bool]
    PnDeviceNameAutoGeneration: Optional[bool]
    PnDeviceName: Optional[str]
    PnDeviceNameConverted: Optional[str] # read only


def create_network_service(imports: Imports, device_data: Devices.Device, device: Siemens.Engineering.HW.Device) -> list[Siemens.Engineering.HW.Features.NetworkInterface]:
    SE: Siemens.Engineering = imports.DLL

    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    services: list[tuple[Siemens.Engineering.HW.Features.NetworkInterface, Siemens.Engineering.HW.DeviceItem]] = find_network_interface_of_device(imports, device)
    for service in services:
        device_item: Siemens.Engineering.HW.DeviceItem = service[0]
        network_service: Siemens.Engineering.HW.Features.NetworkInterface = service[1]

        if type(network_service) is SE.HW.Features.NetworkInterface:
            node: Siemens.Engineeering.HW.Node = network_service.Nodes[0]
            data: dict = device_data.NetworkInterface
            for key, value in data.items():
                if key == "RouterAddress" and value:
                    node.SetAttribute("UseRouter", True)
                    
                node.SetAttribute(key, value)

                # logging.info(f"Device {device.Name}'s {key} Attribute set to '{value}'")

            # logging.info(f"Network address of {device.Name} has been set to '{node.GetAttribute("Address")}' through {device_item.Name}")

            interfaces.append(network_service)

    return interfaces

def find_network_interface_of_device(imports: Imports, device: Siemens.Engineering.HW.Device) -> list[tuple[Siemens.Engineering.HW.Features.NetworkInterface, Siemens.Engineering.HW.DeviceItem]]:
    SE: Siemens.Engineering = imports.DLL

    # logging.debug(f"Looking for NetworkInterfaces for Device {device.Name}")

    device_items: Siemens.Engineering.HW.DeviceItem = device.DeviceItems[1].DeviceItems # DeviceItems[1] is used because index 0 is a rack / rail
    network_services: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    for i, item in enumerate(device_items):
        # logging.debug(f"Checking if [{i}] DeviceItem {item.Name} is a NetworkInterface")

        network_service: Siemens.Engineering.HW.Features.NetworkInterface = SE.IEngineeringServiceProvider(item).GetService[SE.HW.Features.NetworkInterface]()
        if not network_service:
            # logging.debug(f"[{i}] DeviceItem {item.Name} is not a NetworkInterface")
            continue

        # logging.debug(f"Found NetworkInterface for DeviceItem {item.Name} at index {i}")

        network_services.append((item, network_service))

    # logging.debug(f"Found {len(network_services)} NetworkInterfaces for Device {device.Name}")

    return network_services
