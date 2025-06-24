from pathlib import Path
import json
import pytest

from src.schemas import configuration
import src.modules.Devices as Devices
import src.modules.Networks as Networks

BASE_DIR = Path(__file__).parent

one_device = BASE_DIR / "configs" / "one_device.json"
plc_tags = BASE_DIR / "configs" / "plc_tags.json"

def test_device():
    config = None
    with open(one_device) as file:
       config = configuration.validate(json.load(file))
    devices_data = [Devices.Device(
                            dev.get('p_typeIdentifier', 'PLC_1'),
                            dev.get('p_name', 'NewPLCDevice'),
                            dev.get('p_deviceName', ''),
                            dev.get('id', 1),
                            dev.get('slots_required', 2),
                            Networks.NetworkInterface(
                                Address=dev.get('network_interface', {}).get('Address'),
                                RouterAddress=dev.get('network_interface', {}).get('RouterAddress'),
                                UseRouter=dev.get('network_interface', {}).get('UseRouter'),
                                subnet_name=dev.get('network_interface', {}).get('subnet_name'),
                                io_controller=dev.get('network_interface', {}).get('io_controller'),
                            )
                        )
                        for dev in config.get('devices', [])
                    ]
    d = Devices.Device("OrderNumber:6ES7 512-1DK01-0AB0/V2.6", "PLC_12", "PLC_12", 1, 1, Networks.NetworkInterface(subnet_name="PN/IE_1", io_controller="PNIO", Address="192.168.88.211", RouterAddress="192.168.88.1", UseRouter=True))
    assert d == devices_data[0]
    
    del config['devices'][0]['network_interface']
    devices_data = [Devices.Device(
                            dev.get('p_typeIdentifier', 'PLC_1'),
                            dev.get('p_name', 'NewPLCDevice'),
                            dev.get('p_deviceName', ''),
                            dev.get('id', 1),
                            dev.get('slots_required', 2),
                            Networks.NetworkInterface(
                                Address=dev.get('network_interface', {}).get('Address'),
                                RouterAddress=dev.get('network_interface', {}).get('RouterAddress'),
                                UseRouter=dev.get('network_interface', {}).get('UseRouter'),
                                subnet_name=dev.get('network_interface', {}).get('subnet_name'),
                                io_controller=dev.get('network_interface', {}).get('io_controller'),
                            )
                        )
                        for dev in config.get('devices', [])
                    ]
    d = Devices.Device("OrderNumber:6ES7 512-1DK01-0AB0/V2.6", "PLC_12", "PLC_12", 1, 1, Networks.NetworkInterface())
    assert d == devices_data[0]
