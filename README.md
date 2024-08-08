# TIA Portal Automation Tool

## Installation

1. Clone repository:

```
git clone https://github.com/chickenness/tia-portal-automation-tool.git
```

2. Change directory:

```
cd tia-portal-automation-tool
```

3. Install requirements:

```
pip install -r requirements.txt
```

And done.

To run, simply `python main.py`.

## TODO

- [X] Raise Exceptions instead of passing error values
- [ ] Add more keys
  - [X] PLC Tags
  - [X] Network addresses
  - [X] Program Blocks
    - [X] Global library path
    - [X] Master copies
      - [ ] Types
        - [X] PlcBlock
          - [X] PlcBlock Destination
          - [X] Master Copy Source
        - [ ] Device
          - [ ] Master Copy Source
        - [ ] DeviceItem
          - [ ] Device Destination
          - [ ] Master Copy Source
        - [ ] Subnet
          - [ ] Master Copy Source
        - [ ] DeviceGroup
          - [ ] Master Copy Source
- [ ] Fix Contract Reference
- [ ] GUI
  - ~~[X] Proof-of-Concept~~
  - [ ] Showing the json configs
  - ~~[X] wx.StaticBox~~
  - ~~[X] wx.TreeCtrl~~
  - ~~[ ] wx.StyledTextCtrl_2~~
  - ~~[ ] Stopping the portal~~
- ~~[ ] Multithread? (since the gui hangs when tia portal runs)~~
