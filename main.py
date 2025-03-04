from pathlib import Path
from threading import Thread
import argparse
import base64
import json
import wx

from modules import config_schema, portal, logger, api
from res import dlls


EVT_RESULT_ID = wx.NewIdRef()
def EVT_RESULT(win, func):
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class WorkerThread(Thread):
    def __init__(self, window, config: dict, dll: Path):
        Thread.__init__(self)
        self._window = window
        self.config = config
        self.dll: Path = dll

        self.start()

    def run(self):
        import_and_execute(self.config, self.dll)
        wx.PostEvent(self._window, ResultEvent({"finished": True}))


class DLLPickerWindow(wx.Frame):
    def __init__(self, parent, dll_paths: dict[str, Path], callback, title="Choose DLL version"):
        super().__init__(parent, title=title, size=(450,100))
        self.SetMinSize((450,100))
        self.dll_paths: dict[str, Path] = dll_paths
        self.callback = callback

        dll_choices = [dll for dll in self.dll_paths]

        panel = wx.Panel(self)
        self.versions_drpdwn = wx.Choice(panel, choices=dll_choices)
        self.versions_drpdwn.SetSelection(0)
        import_btn = wx.Button(panel, label="Import")
        ok_btn = wx.Button(panel, label="Ok")

        self.versions_drpdwn.SetMinSize((200,-1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.versions_drpdwn, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox.Add(import_btn, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox.Add(ok_btn, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=10)

        panel.SetSizer(hbox)

        ok_btn.Bind(wx.EVT_BUTTON, self.OnOk)
        import_btn.Bind(wx.EVT_BUTTON, self.OnImport)

        self.Show()

    def OnOk(self, e):
        if self.callback:
            index = self.versions_drpdwn.GetCurrentSelection()
            version = self.versions_drpdwn.GetString(self.versions_drpdwn.GetCurrentSelection() if index > 0 else 0)
            self.callback(version)
        self.Close()


    def OnImport(self, e):
        with wx.FileDialog(self, "Open path of Siemens.Engineering.dll", wildcard= "DLL (*.dll)|*.dll", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.callback(fileDialog.GetPath())


class MainWindow(wx.Frame):
    def __init__(self, parent, title) -> None:
        wx.Frame.__init__(self, parent, title=title, size=(800,600))
        self.worker: WorkerThread | None = None
        EVT_RESULT(self,self.OnResult)

        self.config: dict = {}
        self.dll: str = ""

        self.CreateStatusBar()

        # Menubars and menu items
        menubar: wx.MenuBar = wx.MenuBar()
        _filemenu = wx.Menu()
        _open = _filemenu.Append(wx.ID_OPEN, "&Open", " Open project configuration.")
        _close = _filemenu.Append(wx.ID_CLOSE, "&Close", " Close current configuration.")
        _filemenu.AppendSeparator()
        _exit = _filemenu.Append(wx.ID_EXIT, "&Exit", "Terminate this tool. (Does not close TIA Portal)")
        _runmenu = wx.Menu()
        _run = _runmenu.Append(wx.NewIdRef(), "&Run", " Run project.")
        _importmenu = wx.Menu()
        _import_dll = _importmenu.Append(wx.NewIdRef(), "&DLL", " Import Siemens.Engineering.dll")
        _import_library = _importmenu.Append(wx.NewIdRef(), "&Library", " Import Library")
        _import_library_template = _importmenu.Append(wx.NewIdRef(), "&Library Template", " Import Library Template")
        _import_plcdatatype_template = _importmenu.Append(wx.NewIdRef(), "&PLC Data Type Template", " Import PLC Data Type Template")
        self.Bind(wx.EVT_MENU, self.OnOpen, _open)
        self.Bind(wx.EVT_MENU, self.OnExit, _exit)
        self.Bind(wx.EVT_MENU, self.OnClose, _close)
        self.Bind(wx.EVT_MENU, self.OnRun, _run)
        self.Bind(wx.EVT_MENU, self.OnSelectDLL, _import_dll)
        self.Bind(wx.EVT_MENU, self.OnImportLibrary, _import_library)
        self.Bind(wx.EVT_MENU, self.OnImportLibraryTemplate, _import_library_template)
        self.Bind(wx.EVT_MENU, self.OnImportPlcDataTypeTemplate, _import_plcdatatype_template)
        menubar.Append(_filemenu, "&File")
        menubar.Append(_runmenu, "&Action")
        menubar.Append(_importmenu, "&Import")
        self.SetMenuBar(menubar)


        # notebook
        notebook: wx.Notebook = wx.Notebook(self)
        _tab_project = wx.Panel(notebook)
        _vsizer = wx.BoxSizer(wx.VERTICAL)
        _hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.textctrl_config = wx.TextCtrl(_tab_project, size=(300, -1))
        self.browse_btn: wx.Button = wx.Button(_tab_project, label="Browse")
        self.select_dll_btn: wx.Button = wx.Button(_tab_project, label="Select DLL")
        self.execute_btn: wx.Button = wx.Button(_tab_project, label="Execute")
        _hsizer.Add(self.textctrl_config, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        _hsizer.Add(self.browse_btn, flag=wx.ALL, border=5)
        _hsizer.Add(self.select_dll_btn, flag=wx.ALL, border=5)
        _hsizer.Add(self.execute_btn, flag=wx.ALL, border=5)
        _vsizer.Add(_hsizer, flag= wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)
        self.logs: wx.TextCtrl = wx.TextCtrl(_tab_project, style=wx.TE_MULTILINE)
        # _override_path: wx.CheckBox = wx.CheckBox(_tab_project, label="Override Config Project Path")
        # _override_path.SetValue(True)
        # _vsizer.Add(_override_path, flag=wx.ALL|wx.EXPAND, border=5)
        _vsizer.Add(self.logs, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        _tab_project.SetSizer(_vsizer)
        self.Bind(wx.EVT_BUTTON, self.OnOpen, self.browse_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRun, self.execute_btn)
        self.Bind(wx.EVT_BUTTON, self.OnSelectDLL, self.select_dll_btn)

        _tab_config = wx.Panel(notebook)

        _library_box_1 = wx.StaticBox(_tab_config, -1, "Library")
        _lib_box_sizer1 = wx.BoxSizer(wx.VERTICAL)
        _import_lib_btn = wx.Button(_tab_config, label="Import Library")
        _import_lib_template_btn = wx.Button(_tab_config, label="Import Template")
        _lib_box_sizer1.Add(_import_lib_btn, 0, 5)
        _lib_box_sizer1.Add(_import_lib_template_btn, 0, 5)
        self.Bind(wx.EVT_BUTTON, self.OnImportLibrary, _import_lib_btn)
        self.Bind(wx.EVT_BUTTON, self.OnImportLibraryTemplate, _import_lib_template_btn)
        static_box_sizer1 = wx.StaticBoxSizer(_library_box_1)
        static_box_sizer1.Add(_lib_box_sizer1, 1, 5)

        _plc_data_type_box_1 = wx.StaticBox(_tab_config, -1, "PLC Data Type")
        _pdt_box_sizer1 = wx.BoxSizer(wx.VERTICAL)
        _pdt_import_btn = wx.Button(_tab_config, label="Import Template")
        self.Bind(wx.EVT_BUTTON, self.OnImportPlcDataTypeTemplate, _pdt_import_btn)
        _pdt_box_sizer1.Add(_pdt_import_btn, 0, 5)
        _pdt_static_box_sizer1 = wx.StaticBoxSizer(_plc_data_type_box_1)
        _pdt_static_box_sizer1.Add(_pdt_box_sizer1, 1, 5)

        _tab_config_sizer = wx.BoxSizer()
        _tab_config_sizer.Add(static_box_sizer1, 0, wx.TOP, 5)
        _tab_config_sizer.Add(_pdt_static_box_sizer1, 0, wx.TOP, 5)
        _tab_config.SetSizer(_tab_config_sizer)

        _tab_debug = wx.SplitterWindow(notebook, style=wx.SP_LIVE_UPDATE)
        _sty = wx.BORDER_SUNKEN
        _p1 = wx.Window(_tab_debug, style=_sty)
        _p2 = wx.Window(_tab_debug, style=_sty)
        self.tree = wx.TreeCtrl(_p1, wx.NewIdRef(), wx.DefaultPosition, wx.DefaultSize, style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT)
        self.root_item = self.tree.AddRoot("TIA Portal")
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectConfigTree, self.tree)
        self.tab_config_value: wx.TextCtrl = wx.TextCtrl(_p2, style=wx.TE_WORDWRAP|wx.TE_NO_VSCROLL|wx.TE_READONLY)
        _p1sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        _p1sizer.Add(self.tree, proportion=1, flag=wx.EXPAND|wx.ALL, border=1)
        _p1.SetSizer(_p1sizer)
        _p2sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        _p2sizer.Add(self.tab_config_value, proportion=1, flag=wx.EXPAND|wx.ALL, border=1)
        _p2.SetSizer(_p2sizer)
        _tab_debug.SetMinimumPaneSize(100)
        _tab_debug.SplitVertically(_p1, _p2, 250)
        _tab_debug.SetSashPosition(0)
        notebook.AddPage(_tab_project, "Project")
        notebook.AddPage(_tab_config, "Config")
        notebook.AddPage(_tab_debug, "Debug")

        logger.setup(self.logs, 10)

        self.SetMinSize((600,480))
        self.Show(True)

    def set_b64_dlls(self, dll: dict[str, Path]):
        self.b64_dlls: dict[str, Path] = dll

    def receive_callback(self, version):
        if version in self.b64_dlls:
            self.dll = self.b64_dlls[version].as_posix()
        else:
            self.dll = version

    def OnOpen(self, e):
        with wx.FileDialog(self, "Open TIA Portal project config", wildcard= "json (*.json)|*.json", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.json_config = fileDialog.GetPath()
            self.textctrl_config.Clear()
            self.textctrl_config.write(self.json_config)

        with open(self.json_config) as file:
            config = json.load(file)
            self.config = config_schema.validate_config(config)
            self.config['directory'] = Path(self.textctrl_config.Value).parent
            self.config['name'] = Path(self.textctrl_config.Value).stem
            self.populate_config(self.config)

    def OnSelectDLL(self, e):
        dll_picker = DLLPickerWindow(self, dll_paths=self.b64_dlls, callback=self.receive_callback)

    def OnImportLibrary(self, e):
        if not self.config:
            error_dialog = wx.MessageDialog(parent=self,
                                            message="Config has not yet been imported",
                                            caption="Error",
                                            style=wx.OK|wx.ICON_ERROR
                                            )
            error_dialog.ShowModal()
            return

        with wx.FileDialog(self, "Open Global Library", wildcard="Global library (*.al*)|*.al*", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as filedialog:
            if filedialog.ShowModal() == wx.ID_CANCEL:
                return
            library_path = filedialog.GetPath()
            library_name = Path(library_path).stem
            library = {
                "path": library_path,
                "read_only": True
            }
            for i in range(len(self.config.get('devices', []))):
                self.config['devices'][i]['required_libraries'] = [library_name]

            self.config['libraries'] = [library]
            self.tree.DeleteChildren(self.root_item)
            self.populate_config(self.config)


        return
        

    def OnImportLibraryTemplate(self, e):
        if not self.config:
            error_dialog = wx.MessageDialog(parent=self,
                                            message="Config has not yet been imported",
                                            caption="Error",
                                            style=wx.OK|wx.ICON_ERROR
                                            )
            error_dialog.ShowModal()
            return

        with wx.FileDialog(self, "Open Library Template", wildcard="json (*.json)|*.json", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as filedialog:
            if filedialog.ShowModal() == wx.ID_CANCEL:
                return
            template_path = filedialog.GetPath()
            if not self.config['libraries'][0]:
                return
            if not 'config' in self.config['libraries'][0]:
                self.config['libraries'][0]['config'] = {}
            self.config['libraries'][0]['config']['template'] = template_path
            self.tree.DeleteChildren(self.root_item)
            self.populate_config(self.config)


        return

    def OnImportPlcDataTypeTemplate(self, e):
        if not self.config:
            error_dialog = wx.MessageDialog(parent=self,
                                            message="Config has not yet been imported",
                                            caption="Error",
                                            style=wx.OK|wx.ICON_ERROR
                                            )
            error_dialog.ShowModal()
            return

        with wx.FileDialog(self, "Open PLC Data Type Template", wildcard="json (*.json)|*.json", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as filedialog:
            if filedialog.ShowModal() == wx.ID_CANCEL:
                return
            with open(filedialog.GetPath(), 'r') as jsonfile:
                data = json.load(jsonfile)

            self.config['devices'][0]['PLC data types'] = data
            # self.config['devices'][0] = 
            self.tree.DeleteChildren(self.root_item)
            self.populate_config(self.config)


        return

    def OnClose(self, e):
        self.config = {}
        self.textctrl_config.Clear()
        while self.tree.ItemHasChildren(self.root_item):
            item = self.tree.GetFirstChild(self.root_item)[0]
            self.tree.Delete(item)


    def OnExit(self, e):
        self.Close(True)
        self.Destroy()

    
    def OnSelectConfigTree(self, e):
        item = e.GetItem()
        
        value = self.tree.GetItemData(item)

        if value is not None:
            self.tab_config_value.SetValue(str(value))
        else:
            self.tab_config_value.SetValue("")


    def OnRun(self, e):
        dll = Path(self.dll) 
        if not dll.exists() or not dll.is_file():
            error_message = "Siemens.Engineering.dll path does not exist!"
            dialog = wx.MessageDialog(self, error_message, "Error", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()

            return
        self.set_button_active_status(False)


        if not self.worker:
            self.worker = WorkerThread(self, self.config, dll)


    def OnResult(self, e):
        if e.data.get('finished', False) == True:
            self.worker = None
        self.set_button_active_status()


    def set_button_active_status(self, enable: bool = True):
        self.execute_btn.Enable(enable)
        self.browse_btn.Enable(enable)
        self.select_dll_btn.Enable(enable)

    def populate_config(self, config: dict) -> None:
        def add_children(root, children):
            for key, value in children.items():
                child = self.tree.AppendItem(root, str(key))
                if isinstance(value, dict):
                    add_children(child, value)
                elif isinstance(value, list):
                    add_children_as_list(child, value)
                else:
                    self.tree.SetItemData(child, value)

        def add_children_as_list(root, children):
            for i,value in enumerate(children):
                name = str(i)
                if isinstance(value, dict):
                    names = ['p_name', 'Name', 'name', 'address', 'path']
                    for n in names:
                        if value.get(n):
                            name = str(value.get(n))
                            break
                child = self.tree.AppendItem(root, name)
                if isinstance(value, dict):
                    add_children(child, value)
                elif isinstance(value, list):
                    add_children_as_list(child, value)
                else:
                    self.tree.SetItemData(child, value)

        add_children(self.root_item, config)

        self.tree.Expand(self.root_item)


def import_and_execute(config, dll: Path):
    import clr
    from System.IO import DirectoryInfo, FileInfo

    clr.AddReference(dll.as_posix())
    import Siemens.Engineering as SE

    print("TIA Portal Automation Tool")
    print()

    imports = api.Imports(SE, DirectoryInfo, FileInfo)
    portal.execute(imports, config, { "enable_ui": True, })

if __name__ == '__main__':
    dll_paths: dict[str, Path] = {}
    for key in dlls.b64_dlls:
        if key == "Siemens.Engineering.Contract":
            continue
        if "Hmi" in key:
            continue
        data = base64.b64decode(dlls.b64_dlls[key])
        hmi_data = base64.b64decode(dlls.b64_dlls[f"{key}.Hmi"])
        dlls_dir = Path("./DLLs")
        dlls_dir.mkdir(exist_ok=True)

        save_path = Path(dlls_dir) / key
        save_path.mkdir(exist_ok=True)
        version_dll_path = save_path / f"Siemens.Engineering.dll"
        with version_dll_path.open('wb') as version_dll_file:
            version_dll_file.write(data)
            logger.logging.debug(f"Written data of {key}")

        version_hmi_dll_path = save_path / f"Siemens.Engineering.Hmi.dll"
        with version_hmi_dll_path.open('wb') as version_hmi_dll_file:
            version_hmi_dll_file.write(hmi_data)
            logger.logging.debug(f"Written data of {key}")
        dll_paths[key] = version_dll_path.absolute()
    logger.logging.debug(f"DLL Paths: {dll_paths}")

    parser = argparse.ArgumentParser(description="A simple tool for automating TIA Portal projects.")
    parser.add_argument("-c", "--config",
                        type=Path,
                        help="JSON config file path"
                        )
    parser.add_argument("--dll",
                        type=Path,
                        help="Siemens.Engineering.dll path",
                        default=r"C:/Program Files/Siemens/Automation/Portal V18/PublicAPI/V18/Siemens.Engineering.dll"
                        )
    parser.add_argument("--debug",
                        action="store_true",
                        help="Set log level to DEBUG"
                        )
    args = parser.parse_args()

    json_config = args.config
    dll = args.dll
    debug = args.debug

    if json_config:
        with open(json_config) as file:
            config = json.load(file)
            validated_config = config_schema.validate_config(config)

            validated_config['directory'] = json_config.absolute().parent
            validated_config['name'] = json_config.stem
            import_and_execute(validated_config, dll)

    else:
        app = wx.App(False)
        frame = MainWindow(None, title="TIA Portal Automation Tool")
        frame.set_b64_dlls(dll_paths)
        app.MainLoop()
