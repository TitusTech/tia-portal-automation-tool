# TIA Portal Automation Tool

## Features

- import a Global Library
- choose an API version
- insert PLC device
- insert PLC local modules
- insert PLC tags
- insert PLC data types
- import program blocks to a device
- supports function blocks, organization blocks, functions, and different types of databases
- create networking system
- can define all these in a simple JSON file

### Next update will include these features

- auto compiling of program blocks
- auto saving
- attaching the automation tool to an existing project

## Building

### Clone repository:

```
git clone https://github.com/TitusTech/tia-portal-automation-tool.git
```

### Install requirements:

Install the package manager [uv](https://docs.astral.sh/uv/#installation).

```
cd tia-portal-automation-tool

```

### Compile (Optional)

```
uv run pyinstaller --noconfirm --onefile --windowed --name "tia-portal-automation-tool" "main.py"
```

And done.

To run, simply `uv run main.py`.
