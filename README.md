# TIA Portal Automation Tool

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
