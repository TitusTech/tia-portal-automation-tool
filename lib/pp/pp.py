from __future__ import annotations

from .modules import objects
from pathlib import Path
import json
import os

class PPError(Exception):
    def __init__(self, err: str) -> None:
        self.err: str = err

class ProjectExistsError(PPError):
    def __init__(err: str) -> None:
        super().__init__(self, err)

    def __repr__(self) -> str:
        return f"ProjectExistsError: {self.err}"

class Portal:
    def __init__(self, config: objects.Config) -> None:
        self.config = config

        import clr
        clr.AddReference(self.config.dll.as_posix())

        from System.IO import DirectoryInfo, FileInfo
        import Siemens.Engineering as tia
        import Siemens.Engineering.Compiler as comp
        import Siemens.Engineering.HW.Features as hwf

        self.DirectoryInfo = DirectoryInfo
        self.FileInfo = FileInfo
        self.tia = tia
        self.comp = comp
        self.hwf = hwf

        self.TIA: Siemens.Engineering.TiaPortal = self.tia.TiaPortal()

    def run(self) -> None:
        # probs make this part run multithreaded since it hangs the gui process
        conf = self.config
        if conf.enable_ui:
            print("Starting TIA with UI")
            self.TIA = self.tia.TiaPortal(self.tia.TiaPortalMode.WithUserInterface)
        else:
            print("Starting TIA without UI")
            self.TIA = self.tia.TiaPortal(self.tia.TiaPortalMode.WithoutUserInterface)

        project = self.create_project(conf.project.name, conf.project.directory)

        PLC1 = project.Devices.CreateWithItem(conf.project.devices[0].device, conf.project.devices[0].device_name, 'PLC1')

    def create_project(self, name: str, directory: Path) -> Siemens.Engineering.Project:
        path = self.DirectoryInfo(directory.joinpath(name).as_posix())
        if path.Exists:
            raise PPError(f"Failed creating project. Project already exists ({path})")

        directory = self.DirectoryInfo(directory.as_posix())

        project = self.TIA.Projects.Create(directory, name)

        return project



def parse(path: str) -> Portal:
    """
    Initialize TIA Portal config parser with the path to the configuration file
    Loads and process the JSON configuration file into python classes.

    :param path: String path to the JSON configuration file
    """

    config_file_path: Path = Path(path)
    
    if not config_file_path.exists():
        raise ValueError(f"JSON config file does not exist: {config_file_path}")

    if not config_file_path.is_file():
        raise ValueError(f"JSON config is not a file: {config_file_path}")

    with open(config_file_path, 'r') as file:
        conf: dict = json.load(file)

    config: objects.Config = objects.start(**conf)

    return Portal(config)


