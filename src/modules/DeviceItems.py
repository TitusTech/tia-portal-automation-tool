from __future__ import annotations
from dataclasses import dataclass

@dataclass
class DeviceItem:
    DeviceID: int
    typeIdentifier: str
    name: str
    positionNumber: int



def plug_new(data: DeviceItem, device: Siemens.Engineering.HW.Device, slots_required: int):
    hw_object: Siemens.Engineering.HW.HardwareObject = device.DeviceItems[0]

    # logging.info(f"Plugging {module.TypeIdentifier} on [{module.PositionNumber + slots_required}]...")

    if hw_object.CanPlugNew(data.typeIdentifier, data.name, data.positionNumber + slots_required):
        hw_object.PlugNew(data.typeIdentifier, data.name, data.positionNumber + slots_required)

        # logging.info(f"{module.TypeIdentifier} PLUGGED on [{module.PositionNumber + slots_required}]")

        return

    # logging.info(f"{module.TypeIdentifier} Not PLUGGED on {module.PositionNumber + slots_required}")

    return

