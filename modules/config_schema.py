from enum import Enum
from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

class SourceType(Enum):
    LIBRARY = "LIBRARY"
    PLC     = "PLC"

class PlcType(Enum):
    OB = "OB"
    FB = "FB"
    FC = "FC"

class DatabaseType(Enum):
    GLOBAL      = "GLOBAL"
    SINGLE      = "SINGLE"
    MULTI       = "MULTI"
    LOCAL       = "LOCAL"

schema_wire = Schema({
    "name": str,
    "from": str,
    "to": str,
})

schema_source = {
    "name": str,
}

schema_source_plc = Schema({
    **schema_source,
    "plc": str, 
})

schema_source_library = Schema({
    **schema_source,
    "library": str, 
})


schema_database = {
    "type": And(str, Use(DatabaseType)),
    "name": str,
    "programming_language": And(str, Use(str.upper)),
    Optional("number", default=1): int,
}

schema_globaldb = Schema(schema_database)
schema_instancedb = Schema({
    **schema_database,
    "instanceOfName": str,
    Optional("data", {}): Schema({
        Optional("Address", default="DB"): str,
        Optional("BlockNumber", default=1): int,
        Optional("BitOffset", default=0): int,
        Optional("Informative", default=True): bool,
    }),
})

schema_sections_members_attributelist = Schema({
    "BooleanAttribute": list[dict],
})

schema_sections_members = Schema({
    "Name": str,
    "Datatype": str,
    Optional("attributes", default={}): dict, # rename back to "AttributeList" if something crashes in xml_builder.py lol
})

schema_sections = Schema({
    "name": str,
    "members": [schema_sections_members],
})

schema_multi_instance_db = Schema({
    "type": And(str, Use(DatabaseType)),
    "component_name": str,
    Optional("sections", default=[]): And(list, [schema_sections]),
    Optional("wires", default={}): And(list, list[schema_wire]),
})

schema_program_block = {
    "name": str,
    "programming_language": And(str, Use(str.upper)),
    Optional("number", default=0): int,
}

schema_program_block.update({
    "type": And(str, Or(Use(PlcType), Use(DatabaseType))),
    Optional("source", default={}): Or(schema_source_library, schema_source_plc),
    Optional('network_sources', default=[]): And(list, [[Schema(schema_program_block)]]),
})

schema_program_block_ob = {**schema_program_block}
schema_program_block_fb = {**schema_program_block}
schema_program_block_fc = {**schema_program_block}
schema_program_block_ob.update({
    Optional('db', default={}): schema_instancedb,
    Optional('network_sources', default=[]): And(list, [[Schema(schema_program_block_ob)]]),
})
schema_program_block_fb.update({
    Optional('db', default={}): Or(schema_instancedb, schema_multi_instance_db),
    Optional('network_sources', default=[]): And(list, [[Schema(schema_program_block_fb)]]),
})
schema_program_block_fc.update({
    Optional('db', default={}): Or(schema_instancedb,),
    Optional('network_sources', default=[]): And(list, [[Schema(schema_program_block_fc)]]),
})
schema_program_block_ob = Schema(schema_program_block_ob)
schema_program_block_fb = Schema(schema_program_block_fb)
schema_program_block_fc = Schema(schema_program_block_fc)


schema_plc_tag = Schema({
        "Name": str,
        "DataTypeName": str,
        "LogicalAddress": str,
    })

schema_plc_tag_table = Schema({
        "Name": str,
        Optional("Tags", default=[]): [schema_plc_tag],
    })

schema_plc_data_types = Schema({
    "Name": str,
    Optional("types", default=[]): [schema_sections_members],
})

schema_module = Schema({
        "TypeIdentifier": str,
        "Name": str,
        "PositionNumber": int,
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
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): schema_network_interface,
}

schema_device_plc = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
        Optional("Program blocks", default=[]): And(list, [Or(schema_program_block_ob,schema_program_block_fb,schema_program_block_fc, schema_globaldb)]),
        Optional("PLC tags", default=[]): [schema_plc_tag_table],
        Optional("PLC data types", default=[]): [schema_plc_data_types],
        Optional("Local modules", default=[]): [schema_module],
    }


schema_device_ionode = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
        Optional("Modules", default=[]): [schema_module],
    }


schema_device_hmi = {
        **schema_device,
        Optional("HMI tags", default=[]): [schema_plc_tag_table],
    }

schema_network = Schema({
        "address": str, # 192.168.0.112
        "subnet_name": str, # Profinet
        "io_controller": str, # PNIO
    })


schema_library = Schema({
    "path": And(str, Use(Path), lambda p: Path(p)),
    Optional("read_only", default=True): bool,
    })

schema = Schema(
    {
        Optional("overwrite", default=False): bool,
        Optional("devices", default=[]): And(list, [Or(schema_device_plc, schema_device_hmi, schema_device_ionode)]),
        Optional("networks", default=[]): [schema_network],
        Optional("libraries", default=[]): [schema_library],
    },
    ignore_extra_keys=True  
)

def validate_config(data):
    return schema.validate(data)

