from pathlib import Path
import json
import pytest
import xml.etree.ElementTree as ET

from src.modules.FunctionBlocks import FB, FunctionBlock
from src.modules.OrganizationBlocks import OB, OrganizationBlock, EventClassEnum
from src.modules.XML.ProgramBlocks import NetworkSource

def test_organization_block():
    ob_data = OrganizationBlock(Name="Main",
                                Number=1,
                                ProgrammingLanguage="FBD",
                                EventClass=EventClassEnum.ProgramCycle,
                                NetworkSources=[NetworkSource(Title="First Scan",
                                                              Comment="",
                                                              Instances=[],
                                                              )
                                                ],
                                Variables=[],
                                )
    ob = OB(ob_data)
