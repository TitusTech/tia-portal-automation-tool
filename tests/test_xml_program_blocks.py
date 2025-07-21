from pathlib import Path
import json
import xml.etree.ElementTree as ET

from src.core.core import helper_clean_variable_sections, helper_clean_network_sources
from src.modules.BlocksFB import FB, FunctionBlock
from src.modules.BlocksOB import OB, OrganizationBlock, EventClassEnum
from src.modules.BlocksData import DataBlock, XML
from src.modules.XML.ProgramBlocks import PlcEnum
from src.schemas import configuration

BASE_DIR = Path(__file__).parent
smc = BASE_DIR / "configs" / "smc.json"


CONFIG = None
with open(smc) as file:
    CONFIG = configuration.validate(json.load(file))


def test_organization_block():
    for ob in CONFIG.get('Program blocks'):
        if ob.get('type') != PlcEnum.OrganizationBlock:
            continue

        variable_sections = helper_clean_variable_sections(
            CONFIG.get('Variable sections'), ob.get('id'))
        network_sources = helper_clean_network_sources(
            CONFIG.get('Network sources'),
            CONFIG.get('Program blocks'),
            CONFIG.get('Variable sections'),
            ob.get('id')
        )
        data = OrganizationBlock(Name=ob.get('name'),
                                 PlcType=ob.get('type'),
                                 Number=ob.get('number'),
                                 ProgrammingLanguage=ob.get(
                                     'programming_language'),
                                 EventClass=EventClassEnum.ProgramCycle,
                                 NetworkSources=network_sources,
                                 Variables=variable_sections,
                                 )
        xml = OB(data).xml()
        root = ET.fromstring(xml)

        assert root.tag == "Document"
        obxml = root.find('SW.Blocks.OB')
        assert obxml is not None
        assert obxml.attrib.get('ID') == "0"

        attr_list = obxml.find('AttributeList')
        assert attr_list is not None

        name = attr_list.find('Name')
        assert name is not None
        assert name.text == ob.get('name')

        number = attr_list.find('Number')
        assert number is not None
        assert number.text == str(
            max(123, min(ob.get('number'), 32767))
            if ob.get('number') != 1 else 1
        )

        interface = attr_list.find('Interface')
        assert interface is not None

        sections = interface.find(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Sections')
        assert sections is not None

        # Variable Sections
        section = sections.find(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Section')
        if section is None:
            continue
        assert section is not None
        # assert section.attrib.get('Name') == "Static"

        members = section.findall(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Member')


def test_globaldb():
    for db in CONFIG.get('Program blocks'):
        if db.get('type') != PlcEnum.GlobalDB.value:
            continue

        variable_sections = helper_clean_variable_sections(
            CONFIG.get('Variable sections'), db.get('id'))
        data = DataBlock(
            DeviceID=db.get('DeviceID'),
            Name=db.get('name'),
            Number=db.get('number'),
            BlockGroupPath=db.get('blockgroup_folder', '/'),
            VariableSections=variable_sections,
            Attributes=db.get('attributes', {})
        )

        root = ET.fromstring(XML(data).xml())

        assert root.tag == "Document"
        gdb = root.find('SW.Blocks.GlobalDB')
        assert gdb is not None
        assert gdb.attrib.get('ID') == "0"

        attr_list = gdb.find('AttributeList')
        assert attr_list is not None

        name = attr_list.find('Name')
        assert name is not None
        assert name.text == db.get('name')

        number = attr_list.find('Number')
        assert number is not None
        assert number.text == str(db.get('number'))

        interface = attr_list.find('Interface')
        assert interface is not None

        sections = interface.find(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Sections')
        assert sections is not None

        # Variable Sections
        section = sections.find(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Section')
        if section is None:
            continue
        assert section is not None
        assert section.attrib.get('Name') == "Static"

        members = section.findall(
            '{http://www.siemens.com/automation/Openness/SW/Interface/v5}Member')
        # for member in members:
        #     print(member)
        #     assert member is not None
        # assert member.attrib.get('Name') == "Event_Pool"
        # assert member.attrib.get(
        #     'Datatype') == 'Array[0..999] of "Event_Pool"'
        # assert member.attrib.get('Remanence') == "Retain"
        # assert member.attrib.get('Accessibility') == "Public"
