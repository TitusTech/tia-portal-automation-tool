from schema import Schema, And, Or, Use, Optional, SchemaError

NetworkInterface = Schema({
    Optional("subnet_name"): str,
    Optional("io_controller"): str,
    Optional("Name"): str, # read only
    Optional("Address"): str,
    Optional("NodeId"): str, # read only
    Optional("NodeType"): str, # unsupported
    Optional("UseIsoProtocol"): bool,
    Optional("MacAddress"): str,
    Optional("UseIpProtocol"): bool,
    Optional("IpProtocolSelection"): str, # unsupported
    Optional("Address"): str,
    Optional("SubnetMask"): str,
    Optional("UseRouter"): bool, # no need, just set RouterAddress to make this true
    Optional("RouterAddress"): str,
    Optional("DhcpClientId"): str,
    Optional("PnDeviceNameSetDirectly"): bool,
    Optional("PnDeviceNameAutoGeneration"): bool,
    Optional("PnDeviceName"): str,
    Optional("PnDeviceNameConverted"): str, # read only
})
