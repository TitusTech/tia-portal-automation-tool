from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError




schema_network = Schema({
        "address": str, # 192.168.0.112
        "subnet_name": str, # Profinet
        "io_controller": str, # PNIO
    })

schema_network_interface = Schema({
    # Optional("Name"): str, # read only
    Optional("Address"): str,
    # Optional("NodeId"): str, # read only
    # Optional("NodeType"): str, # unsupported
    Optional("UseIsoProtocol"): bool,
    Optional("MacAddress"): str,
    Optional("UseIpProtocol"): bool,
    # Optional("IpProtocolSelection"): str, # unsupported
    Optional("Address"): str,
    Optional("SubnetMask"): str,
    # Optional("UseRouter"): bool, # no need, just set RouterAddress to make this true
    Optional("RouterAddress"): str,
    Optional("DhcpClientId"): str,
    Optional("PnDeviceNameSetDirectly"): bool,
    Optional("PnDeviceNameAutoGeneration"): bool,
    Optional("PnDeviceName"): str,
    # Optional("PnDeviceNameConverted"): str, # read only
})

schema_device = {
    "id": int,
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): schema_network_interface,
    Optional("required_libraries", default=[]): list[str],
}

schema_device_plc = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
    }


schema = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(schema_device_plc)]),
        Optional("networks", default=[]): [schema_network],
    },
    ignore_extra_keys=True  
)

def validate_config(data):
    return schema.validate(data)

