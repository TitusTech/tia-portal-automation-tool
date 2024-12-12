import xml.etree.ElementTree as ET


from modules.structs import DocumentSWType
from modules.structs import DatabaseType
from modules.structs import VariableStruct, VariableSection
from modules.structs import OBEventClass
from modules.structs import XMLNS
from modules.structs import PlcStructData
from modules.structs import SWBlockData
from modules.structs import OBData, FBData
from modules.structs import GlobalDBData
from modules.structs import NetworkSourceContainer
from modules.structs import PlcForceTableEntryData, PlcWatchTableEntryData, WatchForceTable
from modules.structs import InstanceContainer, WireParameter


class BaseDocument:
    def __init__(self, document_type: DocumentSWType | DatabaseType, name: str) -> None:
        self.root = ET.fromstring("<Document />") 
        self.SWDoc = ET.SubElement(self.root, document_type.value, attrib={'ID': str(0)})
        self.AttributeList = ET.SubElement(self.SWDoc, "AttributeList")
        ET.SubElement(self.AttributeList, "Name").text = name

        return

    def export(self, root: ET.Element) -> str:
        return ET.tostring(root, encoding='utf-8').decode('utf-8')

    def xml(self) -> str:
        return self.export(self.root)

class Document(BaseDocument):
    def __init__(self, document_type: DocumentSWType | DatabaseType, name: str) -> None:
        super().__init__(document_type, name)

        self.Interface = ET.SubElement(self.AttributeList, "Interface")
        self.Sections = ET.SubElement(self.Interface, "Sections")
        self.Sections.set('xmlns', XMLNS.SECTIONS.value)
        ET.SubElement(self.AttributeList, "Namespace")


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
    def __init__(self,
                 document_type: DocumentSWType | DatabaseType,
                 name: str,
                 number: int,
                 programming_language: str,
                 variables: list[VariableSection]
                 ) -> None:
        super().__init__(document_type, name)
        self.variables: list[VariableSection] = variables

        ET.SubElement(self.AttributeList, "Number").text = str(number)
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language
        self.ObjectList = ET.SubElement(self.SWDoc, "ObjectList")

        self.sections_enabled: list[str] = []

    def _create_input_section(self):
        self.InputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Input"})
        self.sections_enabled.append("Input")

    def _create_output_section(self):
        self.OutputSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Output"})
        self.sections_enabled.append("Output")

    def _create_temp_section(self):
        self.TempSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Temp"})
        self.sections_enabled.append("Temp")

    def _create_constant_section(self):
        self.ConstantSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Constant"})
        self.sections_enabled.append("Constant")

    def _create_inout_section(self):
        self.InOutSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "InOut"})
        self.sections_enabled.append("InOut")

    def _create_static_section(self):
        self.StaticSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Static"})
        self.sections_enabled.append("Static")

    def _create_return_section(self):
        self.ReturnSection = ET.SubElement(self.Sections, "Section", attrib={"Name": "Return"})
        self.sections_enabled.append("Return")
        ET.SubElement(self.ReturnSection, "Member", attrib={
            'Name': "Ret_Val", 
            'Datatype': "Void",
        })

    def _add_variables(self):
        for section in self.variables:
            if not section.Name in self.sections_enabled:
                continue

            if section.Name == "Input":
                self._create_member(section.Variables, self.InputSection)
            if section.Name == "Output":
                self._create_member(section.Variables, self.OutputSection)
            if section.Name == "Temp":
                self._create_member(section.Variables, self.TempSection)
            if section.Name == "Constant":
                self._create_member(section.Variables, self.ConstantSection)
            if section.Name == "InOut":
                self._create_member(section.Variables, self.InOutSection)
            if section.Name == "Return":
                self._create_member(section.Variables, self.ReturnSection)
            if section.Name == "Static":
                self._create_member(section.Variables, self.StaticSection)

        return

    def _create_member(self, structs: list[VariableStruct], section: ET.Element):
        for struct in structs:
            Member = ET.SubElement(section,
                                   "Member",
                                   attrib={'Name': struct.Name,
                                           'Datatype': struct.Datatype,
                                           'Remanence': "Retain" if struct.Retain else "NonRetain",
                                           'Accessibility': "Public"
                                           }
                                   )
            if struct.StartValue != '':
                ET.SubElement(Member, "StartValue").text = struct.StartValue

            bool_attribs = generate_boolean_attributes(struct)
            if len(bool_attribs):
                Member.append(bool_attribs)

        return


class OB(SWBlock):
    def __init__(self, data: OBData) -> None:
        data.Number = max(123, min(data.Number, 32767)) if data.Number != 1 else 1 # EventClasses have different number rules
        super().__init__(DocumentSWType.BlocksOB, data.Name, data.Number, data.ProgrammingLanguage, data.Variables)

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

        id = 3
        for network_source in data.NetworkSources:
            CompileUnit = SWBlocksCompileUnit(data.ProgrammingLanguage, network_source, id).root
            self.ObjectList.append(CompileUnit)
            id += 5
        

class FB(SWBlock):
    def __init__(self, data: FBData) -> None:
        super().__init__(DocumentSWType.BlocksFB, data.Name, data.Number, data.ProgrammingLanguage, data.Variables)

        self._create_input_section()
        self._create_output_section()
        self._create_inout_section()
        self._create_static_section()
        self._create_temp_section()
        self._create_constant_section()

        self._add_variables()

        id = 3
        for network_source in data.NetworkSources:
            CompileUnit = SWBlocksCompileUnit(data.ProgrammingLanguage, network_source, id).root
            self.ObjectList.append(CompileUnit)
            id += 5

        return

    def _create_member(self, structs: list[VariableStruct], section: ET.Element):
        # code duplication lol
        for struct in structs:
            Member = ET.SubElement(section,
                                   "Member",
                                   attrib={'Name': struct.Name,
                                           'Datatype': struct.Datatype,
                                           'Accessibility': "Public"
                                           }
                                   )
            if struct.StartValue != '':
                ET.SubElement(Member, "StartValue").text = struct.StartValue

            bool_attribs = generate_boolean_attributes(struct)
            if len(bool_attribs):
                Member.append(bool_attribs)

        return


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
    def __init__(self, programming_language: str, network_source: NetworkSourceContainer, id) -> None:
        self.root: ET.Element = ET.Element("SW.Blocks.CompileUnit", attrib={
            'ID': format(id, 'X'),
            'CompositionName': "CompileUnits",
        })
        self.AttributeList = ET.SubElement(self.root, "AttributeList")
        self.ObjectList = ET.SubElement(self.root, "ObjectList")
        self.NetworkSource = ET.SubElement(self.AttributeList, "NetworkSource")
        ET.SubElement(self.AttributeList, "ProgrammingLanguage").text = programming_language

        self._generate_texts(id+1, network_source.Title, network_source.Comment)

        self._create_instances(network_source.Instances)

        return

    def _generate_texts(self, id: int, title: str, comment: str):
        Comment = generate_MultilingualText(id, "Comment", comment)
        Title = generate_MultilingualText(id + 2, "Title", title)
        self.ObjectList.append(Comment)
        self.ObjectList.append(Title)

        return

    def _create_instances(self, instances: list):
        if not instances:
            return

        self.FlgNet = ET.SubElement(self.NetworkSource, "FlgNet")
        self.FlgNet.set('xmlns', XMLNS.FLGNET.value)
        self.Parts = ET.SubElement(self.FlgNet, "Parts")
        self.Wires = ET.SubElement(self.FlgNet, "Wires")

        for instance in instances:
            # for now, we only do 1 instance per network source
            if len(instances) == 1:
                self._insert_parts(instance, 21)
                self._insert_wires(instance, 21 + len(instance.Parameters))

        return
    
    def _insert_parts(self, instance: InstanceContainer, uid: int):
        for parameter in instance.Parameters:
            parameter.__dict__['UId'] = uid
            parameter.__dict__['call'] = 21 + len(instance.Parameters)
            access = generate_access(parameter, uid)
            self.Parts.append(access)
            uid += 1

        Call = ET.SubElement(self.Parts, "Call", attrib={'UId': str(uid)})
        CallInfo = ET.SubElement(Call, "CallInfo", attrib={'Name': instance.Name, 'BlockType': instance.Type.value.split('.')[-1]})
        if instance.Type != DocumentSWType.BlocksFC:
            scope = "GlobalVariable"
            if instance.Database.Type == DatabaseType.MultiInstance:
                scope = "LocalVariable"
            InstanceTag = ET.SubElement(CallInfo, "Instance", attrib={'Scope': scope, 'UId': str(uid+1)})
            db_name = instance.Database.Name if instance.Database.Name != "" else f"{instance.Name}_DB"
            ET.SubElement(InstanceTag, "Component", attrib={'Name': db_name})

        for parameter in instance.Parameters:
            if parameter.Name == "en":
                continue
            ET.SubElement(CallInfo, "Parameter", attrib={
                'Name': parameter.Name,
                'Section': parameter.Section,
                'Type': parameter.Datatype
            })

        return

    def _insert_wires(self, instance: InstanceContainer, call_uid: int):
        # find en first
        en_found = False
        for param in instance.Parameters:
            if param.Name == "en":
                en_found = True
                break

        # add "en"
        en_uid = call_uid + 3 - en_found
        Wire = ET.SubElement(self.Wires, "Wire", attrib={'UId': str(en_uid)})
        if not en_found:
            ET.SubElement(Wire, "OpenCon", attrib={'UId': str(call_uid + 2)})
        else:
            ET.SubElement(Wire, "OpenCon", attrib={'UId': str(call_uid - len(instance.Parameters))})
        ET.SubElement(Wire, "NameCon", attrib={'UId': str(call_uid), 'Name': "en"})

        uid = en_uid + 1
        for param in instance.Parameters:
            if param.Name == "en":
                continue

            ident_uid = param.__dict__.get('UId', 23)
            p_call_uid = param.__dict__.get('call', 23)

            Wire = ET.SubElement(self.Wires, "Wire", attrib={'UId': str(uid)})
            ET.SubElement(Wire, "IdentCon", attrib={'UId': str(ident_uid)})
            ET.SubElement(Wire, "NameCon", attrib={'UId': str(p_call_uid), 'Name': param.Name})

            uid += 1

        return
    

class GlobalDB(SWBlock):
    def __init__(self, data: GlobalDBData) -> None:
        data.Number = max(1, min(data.Number, 599999))
        section_struct = VariableSection("Static", data.Structs)
        super().__init__(DatabaseType.GlobalDB, data.Name, data.Number, "DB", [section_struct])

        self._create_static_section()

        self._add_variables()

        for attrib in data.Attributes:
            ET.SubElement(self.AttributeList, attrib).text = data.Attributes[attrib]

        return


class WatchAndForceTables(BaseDocument):
    def __init__(self, document_type: DocumentSWType | DatabaseType, name: str) -> None:
        super().__init__(document_type, name)

        self.ObjectList = ET.SubElement(self.SWDoc, "ObjectList")

        return

    def _create_entry_element(self, kind: DocumentSWType, id: int) -> ET.Element:
        Entry = ET.SubElement(self.ObjectList,
                              DocumentSWType.PlcWatchTableEntry.value,
                              attrib={"ID": format(id, 'X'),
                                      "CompositionName": "Entries"
                                      }
                              )
        if kind == DocumentSWType.PlcForceTableEntry:
            Entry.tag = DocumentSWType.PlcForceTableEntry.value

        return Entry

    def _create_base_entry(self, Entry: ET.Element, entry: WatchForceTable):
        AttributeList = ET.SubElement(Entry, "AttributeList")

        ET.SubElement(AttributeList, "Name").text = entry.Name
        if entry.Address:
            ET.SubElement(AttributeList, "Address").text = entry.Address
        if entry.DisplayFormat:
            ET.SubElement(AttributeList, "DisplayFormat").text = entry.DisplayFormat
        if entry.MonitorTrigger:
            ET.SubElement(AttributeList, "MonitorTrigger").text = entry.MonitorTrigger
        
        if type(entry) == PlcWatchTableEntryData:
            if entry.ModifyIntention:
                ET.SubElement(AttributeList, "ModifyIntention").text = str(entry.ModifyIntention)
            if entry.ModifyTrigger:
                ET.SubElement(AttributeList, "ModifyTrigger").text = entry.ModifyTrigger
            if entry.ModifyValue:
                ET.SubElement(AttributeList, "ModifyValue").text = entry.ModifyValue

        if type(entry) == PlcForceTableEntryData:
            if entry.ForceIntention:
                ET.SubElement(AttributeList, "ForceIntention").text = str(entry.ForceIntention)
            if entry.ForceValue:
                ET.SubElement(AttributeList, "ForceValue").text = entry.ForceValue

        return


class PlcWatchTable(WatchAndForceTables):
    def __init__(self, name: str, entries: list[PlcForceTableEntryData | PlcWatchTableEntryData]) -> None:
        super().__init__(DocumentSWType.PlcWatchTable, name)

        id = 1
        for entry in entries:
            Entry = self._create_entry_element(DocumentSWType.PlcWatchTableEntry, id)
            self._create_base_entry(Entry, entry)
            id += 3

        return


class PlcForceTable(WatchAndForceTables):
    def __init__(self, name: str, entries: list[PlcForceTableEntryData | PlcWatchTableEntryData]) -> None:
        super().__init__(DocumentSWType.PlcForceTable, name)

        id = 1
        for entry in entries:
            Entry = self._create_entry_element(DocumentSWType.PlcForceTableEntry, id)
            self._create_base_entry(Entry, entry)
            id += 3

        return


def generate_boolean_attributes(struct: VariableStruct) -> ET.Element:
    AttributeList = ET.Element("AttributeList")
    for attrib in struct.Attributes:
        ET.SubElement(AttributeList, "BooleanAttribute", attrib={
            'Name': attrib,
            'SystemDefined': "true"
        }).text = str(struct.Attributes[attrib]).lower()

    return AttributeList


def generate_MultilingualTextItem(id: int, text: str) -> ET.Element:
    root = ET.Element("MultilingualTextItem", attrib={
        'ID': format(id, 'X'),
        'CompositionName': "Items"
    })

    AttributeList = ET.SubElement(root, "AttributeList")
    ET.SubElement(AttributeList, "Culture").text = "en-US"
    ET.SubElement(AttributeList, "Text").text = text

    return root
    

def generate_MultilingualText(id: int, composition_name: str, text: str) -> ET.Element:
    root = ET.Element("MultilingualText", attrib={
        'ID': format(id, 'X'),
        'CompositionName': composition_name
    })
    MultilingualTextItem = generate_MultilingualTextItem(id+1, text)
    ObjectList = ET.SubElement(root, "ObjectList")
    ObjectList.append(MultilingualTextItem)

    return root

class Access:
    def __init__(self, uid: int, scope: str) -> None:
        self.Access = ET.Element("Access", attrib={
            "Scope": scope,
            "UId": str(uid),
        })

        return

    def _create_symbol_constant(self, name: str):
        self.Value = ET.SubElement(self.Access, name)

        return

class AccessGlobalVariable(Access):
    def __init__(self, value: list, uid: int) -> None:
        super().__init__(uid, "GlobalVariable")

        self._create_symbol_constant("Symbol")
        for v in value:
            ET.SubElement(self.Value, "Component", attrib={'Name': v})

        return

class AccessLiteralConstant(Access):
    def __init__(self, value: str, const_type: str, uid: int) -> None:
        super().__init__(uid, "LiteralConstant")

        self._create_symbol_constant("Constant")
        ET.SubElement(self.Value, "ConstantType").text = const_type
        ET.SubElement(self.Value, "ConstantValue").text = value

        return

class AccessTypedConstant(Access):
    def __init__(self, value: str, uid: int) -> None:
        super().__init__(uid, "TypedConstant")

        self._create_symbol_constant("Constant")
        ET.SubElement(self.Value, "ConstantValue").text = value

        return

def generate_access(parameter: WireParameter, uid: int) -> ET.Element:
    if isinstance(parameter.Value, list):
        Access = AccessGlobalVariable(parameter.Value, uid)
        return Access.Access
    
    if parameter.Datatype in ["Int", "Bool"]:
        Access = AccessLiteralConstant(parameter.Value, parameter.Datatype, uid)
        return Access.Access

    Access = AccessTypedConstant(parameter.Value, uid)
    return Access.Access
