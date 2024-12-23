# TIA Portal Automation Tool

## Building

### Clone repository:

```
git clone https://github.com/TitusTech/tia-portal-automation-tool.git
```

### Install requirements:

```
cd tia-portal-automation-tool
pip install -r requirements.txt
```

### Compile (Optional)

```
pyinstaller --noconfirm --onefile --windowed --name "tia-portal-automation-tool" "main.py"
```

And done.

To run, simply `python main.py`.

## Usage

### GUI

#### 1. Select Project JSON configuration (Required)

  - Open the application.
  - Navigate to the **Project** tab.
  - Use the **Browse** button to locate the desired project JSON configuration file.
  - Confirm selection by clicking **Open**.
  - The **Config** tab can be used to check the imported project JSON configuration.

#### 2. Select DLL Version (Required)

  - Navigate to the **Project** tab.
  - Use the **Select DLL** button to select preinstalled DLLs from the list or select **Import** to import a specific DLL file.
  - Click **Ok** to confirm.

#### 3. Import Template for Library (Optional)

  - Ensure that a JSON configuration file has been imported.
  - From the file menu **Import**, select **Template** to locate the desired template json file.
  - Confirm selection by clicking **Open**.

#### 4. Execute

  - In the **Project** tab, execute the automation by clicking **Execute** button.
  - A log will be generated in the output box to indicate the current progress.
