from typing import Any
import xml.etree.ElementTree as ET


# TODO: 
#       - Implement Instance (Network Sources) creation
#       - Under Instances, implement Wire and Parts creation
#       - Implement Single InstanceDB
#       - Implement Multi InstanceDB

from modules.structs import DocumentSWType
from modules.structs import OBEventClass
from modules.structs import XMLNS
from modules.structs import PlcStructData
from modules.structs import SWBlockData
from modules.structs import OBData


class Document:
    def __init__(self, document_type: DocumentSWType, name: str) -> None:
        self.root = ET.fromstring("<Document />") 
        self.SWDoc = ET.SubElement(self.root, document_type.value, attrib={'ID': str(0)})
        self.AttributeList = ET.SubElement(self.SWDoc, "AttributeList")
        self.Interface = ET.SubElement(self.AttributeList, "Interface")
        self.Sections = ET.SubElement(self.Interface, "Sections")
        self.Sections.set('xmlns', XMLNS.SECTIONS.value)
        ET.SubElement(self.AttributeList, "Name").text = name
        ET.SubElement(self.AttributeList, "Namespace")

    def export(self, root: ET.Element) -> str:
        return ET.tostring(root, encoding='utf-8').decode('utf-8')

    def xml(self) -> str:
        return self.export(self.root)

class SWType(Document):
    def __init__(self, document_type: DocumentSWType, name: str) -> None:
        super().__init__(document_type, name)

        self.Section = ET.SubElement(self.Sections, "Section", attrib={'Name': "None"})



class PlcStruct(SWType):
    def __init__(self, plcstructdata: PlcStructData) -> None:
        super().__init__(DocumentSWType.TypesPlcStruct, plcstructdata.Name)

        for udt in plcstructdata.Types:
            self._add_member(udt.get('Name', "Element_1"),
                             udt.get('Datatype', "Bool"),
                             udt.get('attributes', {}))
        return

    def _add_member(self, name: str, datatype: str, attributes: dict):
        Member: ET.Element = ET.SubElement(self.Section, "Member", attrib={
            "Name": name,
            "Datatype": datatype
        })
        if not attributes:
            return
        AttributeList = ET.SubElement(Member, "AttributeList")
        for attrib in attributes:
            ET.SubElement(AttributeList, "BooleanAttribute", attrib={
                'Name': attrib,
                'SystemDefined': "true"
            }).text = str(attributes[attrib]).lower()


class SWBlock(Document):
    def __init__(self, document_type: DocumentSWType, name: str, number: int, programming_language: str) -> None:
        super().__init__(document_type, name)

        ET.SubElement(self.AttributeList, "Number").text = str(number)
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language
        self.ObjectList = ET.SubElement(self.SWDoc, "ObjectList")

    def _create_input_section(self):
        self.InputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Input"})

    def _create_output_section(self):
        self.OutputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Output"})

    def _create_temp_section(self):
        self.TempSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Temp"})

    def _create_constant_section(self):
        self.ConstantSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Constant"})

    def _create_inout_section(self):
        self.InOutSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "InOut"})

    def _create_static_section(self):
        self.StaticSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Static"})

    def _create_return_section(self):
        self.ReturnSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Return"})
        ET.SubElement(self.ReturnSection, "Member", attrib={
            'Name': "Ret_Val", 
            'Datatype': "Void",
        })

class OB(SWBlock):
    def __init__(self, data: OBData) -> None:
        data.Number = 1 if ((data.Number > 1 and data.Number < 123) or data.Number == 0) else data.Number # EventClasses have different number rules
        super().__init__(DocumentSWType.BlocksOB, data.Name, data.Number, data.ProgrammingLanguage)

        ET.SubElement(self.AttributeList, "SecondaryType").text = data.EventClass.value # default is ProgramCycle
        self._create_input_section()
        self._create_temp_section()
        self._create_constant_section()
        ET.SubElement(self.InputSection, "Member", attrib={
            "Name": "Initial_Call",
            "Datatype": "Bool",
            "Informative": "true",
        })
        ET.SubElement(self.InputSection, "Member", attrib={
            "Name": "Remanence",
            "Datatype": "Bool",
            "Informative": "true",
        })

class FB(SWBlock):
    def __init__(self, data: SWBlockData) -> None:
        super().__init__(DocumentSWType.BlocksFB, data.Name, data.Number, data.ProgrammingLanguage)

        self._create_input_section()
        self._create_output_section()
        self._create_inout_section()
        self._create_static_section()
        self._create_temp_section()
        self._create_constant_section()

class FC(SWBlock):
    def __init__(self, data: SWBlockData) -> None:
        super().__init__(DocumentSWType.BlocksFC, data.Name, data.Number, data.ProgrammingLanguage)

        self._create_input_section()
        self._create_output_section()
        self._create_inout_section()
        self._create_temp_section()
        self._create_constant_section()
        self._create_return_section()


class SWBlocksCompileUnit:
    def __init__(self, id: int, programming_language: str, network_sources) -> None:
        self.root: ET.Element = ET.Element("SW.Blocks.CompileUnit", attrib={
            'ID': str(id),
            'CompositionName': "CompileUnits",
        })
        self.AttributeList = ET.SubElement(self.root, "AttributeList")
        NetworkSource = ET.SubElement(self.AttributeList, "NetworkSource")
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language

        FlgNet = ET.SubElement(NetworkSource, "FlgNet")
        FlgNet.set('xmlns', XMLNS.SECTIONS.value)

        self.Parts = ET.SubElement(FlgNet, "Parts")
        self.Wires = ET.SubElement(FlgNet, "Wires")

    def et(self) -> ET.Element:
        return self.root





class XML:
    def __init__(self, block_type: str, name: str, number: int) -> None:
        if block_type in ["OB", "FB", "FC"]:
            self.plc_type = PlcType[block_type]
        else:
            self.plc_type = DatabaseType[block_type]

        self.root = ET.fromstring("<Document />") 
        self.SWBlock = ET.SubElement(self.root, f"SW.Blocks.{block_type}", attrib={'ID': str(0)})

        self.AttributeList = ET.SubElement(self.SWBlock, "AttributeList")
        ET.SubElement(self.AttributeList, "Name").text = name
        self.Number = ET.SubElement(self.AttributeList, "Number")
        self.Number.text = str(number)
        ET.SubElement(self.AttributeList, "Namespace")


    def export(self, root: ET.Element) -> str:
        return ET.tostring(root, encoding='utf-8').decode('utf-8')

class PlcBlock(XML):
    def __init__(self, block_type: str, name: str, number: int, db: dict[str, Any]) -> None:
        super().__init__(block_type, name, number)

        self.db = db

        # Interface
        Interface = ET.SubElement(self.AttributeList, "Interface")
        self.Sections = ET.SubElement(Interface, "Sections", attrib={"xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"})
        self.InputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Input"})
        TempSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Temp"})
        ConstantSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Constant"})

    def build(self, programming_language: str,  network_sources: list[list[dict[str, Any]]]) -> str:
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language

        self.ObjectList = ET.SubElement(self.SWBlock, "ObjectList")

        id_counter = 0
        for network in network_sources:
            compile_unit = ET.SubElement(self.ObjectList, "SW.Blocks.CompileUnit", attrib={
                "ID": format(3 + id_counter, 'X'),
                "CompositionName": "CompileUnits",
            })
            AttributeList = ET.SubElement(compile_unit, "AttributeList")
            NetworkSource = ET.SubElement(AttributeList, "NetworkSource")
            FlgNet = self.create_flgnet(network)
            NetworkSource.append(FlgNet)

            ET.SubElement(AttributeList, "ProgrammingLanguage").text = programming_language

            id_counter += 5

        return self.export(self.root)

    def create_parts(self, FlgNet: ET.Element, calls: list[dict[str, Any]]) -> ET.Element:
        Parts = ET.SubElement(FlgNet, "Parts")

        uids = self.calculate_uids(calls)
        call_uids = uids[0]
        wire_uids: list[int] = []

        for i, instance in enumerate(calls):
            db = instance['db']
            uid = call_uids[i]
            Call = ET.SubElement(Parts, "Call", attrib={"UId": str(uid[1])})
            CallInfo = ET.SubElement(Call, "CallInfo", attrib={
                "Name": db.get('instanceOfName', instance['name']),
                "BlockType": instance.get('type', PlcType.FB).value,
            })
            Instance = ET.SubElement(CallInfo, "Instance", attrib={
                "Scope": "GlobalVariable" if db.get('type') == DatabaseType.SINGLE else "LocalVariable",
                "UId": str(uid[1]+1),
            })

            if db['type'] == DatabaseType.SINGLE:
                """
				<Instance Scope="GlobalVariable" UId="22">
					<Component Name="Block_DB" />
				</Instance>
                """
                ET.SubElement(Instance, "Component", attrib={"Name": db.get('name', f"{instance['name']}_DB")})



            if db['type'] == DatabaseType.MULTI:
                """
				<Instance Scope="LocalVariable" UId="24">
					<Component Name="Block_1_Instance_1" />
				</Instance>
				<Parameter Name="Gate 1" Section="Input" Type="Bool" />
				<Parameter Name="Gate 2" Section="Input" Type="Bool" />
				<Parameter Name="Result" Section="Output" Type="Bool" />
                """
                ET.SubElement(Instance, "Component", attrib={"Name": db.get('component_name', f"{instance['name']}_Instance")})
                for section in db['sections']:
                    wire_uids.append(uid[1])
                    for member in section['members']:
                        ET.SubElement(CallInfo, "Parameter", attrib={
                            "Name": member['Name'],
                            "Section": section['name'],
                            "Type": member['Datatype']
                        })
                        wire_uids.append(uid[1])

        return Parts

    def create_wires(self, FlgNet: ET.Element, parts: ET.Element) -> ET.Element:
        Wires = ET.SubElement(FlgNet, "Wires")
        
        for call in parts:
            CallInfo = call.find('.//CallInfo')
            Instance = call.find('.//CallInfo/Instance')
            if CallInfo is None: continue
            if Instance is None: continue

            instance_uid = call.get('UId') # used for NameCon "en" UId 
            parameter_count = len(CallInfo) - 1
            starting_opencon_uid = len(call) * 2 + 21
            
            """
		    <Wire UId="27">
			    <OpenCon UId="23" />
			    <NameCon UId="21" Name="en" />
		    </Wire>
            """
            Wire = ET.SubElement(Wires, "Wire", attrib={'UId': str(starting_opencon_uid+parameter_count+1)})
            ET.SubElement(Wire, "OpenCon", attrib={'UId': str(starting_opencon_uid)})
            ET.SubElement(Wire, "NameCon", attrib={
                'UId': str(instance_uid),
                'Name': 'en'
            })

            i = 1
            for parameter in CallInfo:
                if parameter.tag != "Parameter": continue
                Wire = ET.SubElement(Wires, "Wire", attrib={
                    'UId': str(starting_opencon_uid+parameter_count+1+i)
                })
                ET.SubElement(Wire, "OpenCon", attrib={'UId': str(starting_opencon_uid+i)})
                ET.SubElement(Wire, "NameCon", attrib={
                    'UId': str(instance_uid or 21),
                    'Name': parameter.get('Name') or "en"
                })
                i += 1

        return Wires

    def create_flgnet(self, calls: list[dict[str, Any]]) -> ET.Element:
        root = ET.fromstring("<FlgNet />")
        parts = self.create_parts(root, calls)
        self.create_wires(root, parts)

        root.set('xmlns', "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v4")

        return root



    def calculate_uids(self, calls: list[dict[str, Any]]) -> tuple[list[tuple], int, int]:
        calls_id_end: int = len(calls) + 21 + 2
        call_uids: list[tuple] = [(c.get('db', {}).get('component_name'), 21+(i*2)) for i, c in enumerate(calls)]
        i = 0
        for c in calls:
            for wire in c['db'].get('wires', []):
                if "opencon" in (v.lower() for v in wire.values()):
                    i += 1

        return (call_uids,i, calls_id_end)




# class OB(PlcBlock):
#     def __init__(self, name: str, number: int, db: dict[str, Any]) -> None:
#         super().__init__("OB", name, number, db)
#
#         ET.SubElement(self.AttributeList, "SecondaryType").text = "ProgramCycle"
#         self.Number.text = "1" if ((number > 1 and number < 123) or number == 0) else str(number)
#         ET.SubElement(self.InputSection, "Member", attrib={
#             "Name": "Initial_Call",
#             "Datatype": "Bool",
#             "Informative": "true",
#         })
#         ET.SubElement(self.InputSection, "Member", attrib={
#             "Name": "Remanence",
#             "Datatype": "Bool",
#             "Informative": "true",
#         })


# class FB(PlcBlock):
#     def __init__(self, name: str, number: int, db: dict[str, Any]) -> None:
#         super().__init__("FB", name, number, db)
#
#         self.OutputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Output"})
#         self.InOutSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "InOut"})
#         self.StaticSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Static"})
#
#     def build(self, programming_language: str, network_sources: list[list[dict[str, Any]]]) -> str:
#         super().build(programming_language, network_sources)
#
#         if self.db.get('type') == DatabaseType.MULTI:
#             db = self.db
#             for section in db['sections']:
#                 for member in section['members']:
#                     match section['name']:
#                         case "Input":
#                             ET.SubElement(self.InputSection, "Member", attrib={
#                                 "Name": member['Name'],
#                                 "Datatype": member['Datatype']
#                             })
#                         case "Output":
#                             ET.SubElement(self.OutputSection, "Member", attrib={
#                                 "Name": member['Name'],
#                                 "Datatype": member['Datatype']
#                             })
#
#         for networks in network_sources:
#             for instance in networks:
#                 if not instance.get('db'):
#                     continue
#                 if not instance['db']['type'] == DatabaseType.MULTI:
#                     continue
#                 el = ET.SubElement(self.StaticSection, "Member", attrib={
#                     "Name": instance.get('db', {}).get('component_name', f"{instance['name']}_Instance"),
#                     "Datatype": f'"{instance["name"]}"',
#                 })
#                 ET.SubElement(ET.SubElement(el, "AttributeList"), "BooleanAttribute", attrib={
#                     "Name": "SetPoint",
#                     "SystemDefined": "true",
#                 }).text = "true"
#
#         return self.export(self.root)




class GlobalDB(XML):
    def __init__(self, block_type: str, name: str, number: int) -> None:
        super().__init__(block_type, name, number)

    def build(self, programming_language: str) -> str:
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language
        ET.SubElement(self.SWBlock, "ObjectList")

        return self.export(self.root)
