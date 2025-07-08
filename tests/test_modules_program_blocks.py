from pathlib import Path
import json
import pytest
import xml.etree.ElementTree as ET

from src.modules.ProgramBlocks import NetworkSource
from src.modules.OrganizationBlocks import OB, OrganizationBlock, OrganizationBlockEventClass
from src.modules.ProgramBlocks import FB, FunctionBlock

def test_organization_block():
    ob_data = OrganizationBlock(Name="Main",
                                Number=1,
                                ProgrammingLanguage="FBD",
                                EventClass=OrganizationBlockEventClass.ProgramCycle,
                                NetworkSources=[NetworkSource(Title="First Scan",
                                                              Comment="",
                                                              Instances=[],
                                                              )
                                                ],
                                Variables=[],
                                )
    ob = OB(ob_data)
