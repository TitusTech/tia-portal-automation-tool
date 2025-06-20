from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from src.modules.Portals import Imports

@dataclass
class Project:
    Name: str
    Directory: Path
    Overwrite: bool


def create(imports: Imports, data: Project, TIA: Siemens.Engineering.TiaPortal) -> Siemens.Engineering.Project:
    DirectoryInfo: DirectoryInfo = imports.DirectoryInfo

    # logging.info(f"Creating project {data.Name} at \"{data.Directory}\"...")

    existing_project_path: DirectoryInfo = DirectoryInfo(data.Directory.joinpath(data.Name).as_posix())

    # logging.info(f"Checking for existing project: {existing_project_path}")

    if existing_project_path.Exists:

        # logging.info(f"{data.Name} already exists...")

        if data.Overwrite:

            # logging.info(f"Deleting project {data.Name}...")

            existing_project_path.Delete(True)

            # logging.info(f"Deleted project {data.Name}")

        else:
            err = f"Failed creating project. Project already exists ({existing_project_path})"
            logging.error(err)
            raise ValueError

    # logging.info("Creating project...")

    project_path: DirectoryInfo = DirectoryInfo(data.Directory.as_posix())

    # logging.debug(f"Project Path: {project_path}")

    project_composition: Siemens.Engineering.ProjectComposition = TIA.Projects
    project: Siemens.Engineering.Project = project_composition.Create(project_path, data.Name)

    # logging.info(f"Created project {data.Name} at {data.Directory}")

    return project


