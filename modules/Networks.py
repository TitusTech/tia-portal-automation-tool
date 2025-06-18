from __future__ import annotations
from dataclasses import dataclass

import modules.Devices as Devices

@dataclass
class NetworkInterface:
    Name: Optional[str] = None
    Address: Optional[str] = None
    NodeId: Optional[str] = None # read only
    NodeType: Optional[str] = None # unsupported
    UseIsoProtocol: Optional[bool] = None
    MacAddress: Optional[str] = None
    UseIpProtocol: Optional[bool] = None
    IpProtocolSelection: Optional[str] = None # unsupported
    Address: Optional[str] = None
    SubnetMask: Optional[str] = None
    UseRouter: Optional[bool] = None # no need, just set RouterAddress to make this true
    RouterAddress: Optional[str] = None
    DhcpClientId: Optional[str] = None
    PnDeviceNameSetDirectly: Optional[bool] = None
    PnDeviceNameAutoGeneration: Optional[bool] = None
    PnDeviceName: Optional[str] = None
    PnDeviceNameConverted: Optional[str] = None # read only


def create_network_service(imports: Imports, device_data: Devices.Device, device: Siemens.Engineering.HW.Device) -> list[Siemens.Engineering.HW.Features.NetworkInterface]:
    SE: Siemens.Engineering = imports.DLL

    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    services: list[tuple[Siemens.Engineering.HW.Features.NetworkInterface, Siemens.Engineering.HW.DeviceItem]] = find_network_interface_of_device(imports, device)
    for service in services:
        device_item: Siemens.Engineering.HW.DeviceItem = service[0]
        network_service: Siemens.Engineering.HW.Features.NetworkInterface = service[1]

        if type(network_service) is SE.HW.Features.NetworkInterface:
            node: Siemens.Engineeering.HW.Node = network_service.Nodes[0]

            if device_data.NetworkInterface.Name: node.SetAttribute("Name", device_data.NetworkInterface.Name)
            if device_data.NetworkInterface.Address: node.SetAttribute("Address", device_data.NetworkInterface.Address)
            if device_data.NetworkInterface.NodeId: node.SetAttribute("NodeId", device_data.NetworkInterface.NodeId)
            if device_data.NetworkInterface.NodeType: node.SetAttribute("NodeType", device_data.NetworkInterface.NodeType)
            if device_data.NetworkInterface.UseIsoProtocol: node.SetAttribute("UseIsoProtocol", device_data.NetworkInterface.UseIsoProtocol)
            if device_data.NetworkInterface.MacAddress: node.SetAttribute("MacAddress", device_data.NetworkInterface.MacAddress)
            if device_data.NetworkInterface.UseIpProtocol: node.SetAttribute("UseIpProtocol", device_data.NetworkInterface.UseIpProtocol)
            if device_data.NetworkInterface.IpProtocolSelection: node.SetAttribute("IpProtocolSelection", device_data.NetworkInterface.IpProtocolSelection)
            if device_data.NetworkInterface.Address: node.SetAttribute("Address", device_data.NetworkInterface.Address)
            if device_data.NetworkInterface.SubnetMask: node.SetAttribute("SubnetMask", device_data.NetworkInterface.SubnetMask)
            if device_data.NetworkInterface.UseRouter: node.SetAttribute("UseRouter", device_data.NetworkInterface.UseRouter)
            if device_data.NetworkInterface.RouterAddress: node.SetAttribute("RouterAddress", device_data.NetworkInterface.RouterAddress)
            if device_data.NetworkInterface.DhcpClientId: node.SetAttribute("DhcpClientId", device_data.NetworkInterface.DhcpClientId)
            if device_data.NetworkInterface.PnDeviceNameSetDirectly: node.SetAttribute("PnDeviceNameSetDirectly", device_data.NetworkInterface.PnDeviceNameSetDirectly)
            if device_data.NetworkInterface.PnDeviceNameAutoGeneration: node.SetAttribute("PnDeviceNameAutoGeneration", device_data.NetworkInterface.PnDeviceNameAutoGeneration)
            if device_data.NetworkInterface.PnDeviceName: node.SetAttribute("PnDeviceName", device_data.NetworkInterface.PnDeviceName)
            if device_data.NetworkInterface.PnDeviceNameConverted: node.SetAttribute("PnDeviceNameConverted", device_data.NetworkInterface.PnDeviceNameConverted)

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
