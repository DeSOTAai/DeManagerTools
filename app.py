import os
import webbrowser
import json
import PySimpleGUI as psg
from Tools.services_manager import WinBatManager
import subprocess
import time
import requests

DEBUG = True
DESOTA_TOOLS_SERVICES = {    # Desc -> Service: Checkbox Disabled = REQUIRED
    "desotaai/derunner": True,
    "franciscomvargas/deurlcruncher": False
}
EVENT_TO_METHOD = {
    "TABMOVE": "move_2_tab",
    "WEBREQUEST": "open_url",
    "selectTheme": "theme_select",
    "startInstall": "install_models",
    "tool_table": "tool_table_row_selected",
    "model_table": "model_table_row_selected",
    "upgradeServConf": "update_service_config",
    "openSource": "open_models_sourcecode",
    "openModelUI": "open_models_ui",
    "startUninstall": "uninstall_services",
    "stopManualServices": "stop_manual_services",
    "windowConfigure": "window_configure"
}

user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services

# Services Configurations - Latest version URL
LATEST_SERV_CONF_RAW = "https://raw.githubusercontent.com/DeSOTAai/DeRunner/main/Assets/latest_services.config.yaml"


# Construct APP with PySimpleGui
class SGui():
    def __init__(self, ignore_update=False) -> None:
        #Class Vars
        self.debug = DEBUG
        self.tools_services = DESOTA_TOOLS_SERVICES
        self.event_to_method = EVENT_TO_METHOD
        self.tab_keys= [ '-TAB1-', '-TAB2-', '-TAB3-']
        self.themes = psg.ListOfLookAndFeelValues()
        self.current_theme = self.get_user_theme()
        self.icon = os.path.join(app_path, "Assets", "icon.ico")
        self.started_manual_services_file = os.path.join(config_folder, "Services", "manual_services_started.txt")
        
        self.services_config, self.latest_services_config = self.get_services_config(ignore_update=ignore_update)
        if not self.services_config:
            raise EnvironmentError()

        self.user_config = self.get_user_config()
        if not self.user_config:
            raise EnvironmentError()
        
        self.system = self.user_config['system']
        
        #define pysimplegui theme
        psg.theme(self.current_theme)
        
        #define open tab
        if self.user_config["models"]:
            self.set_current_tab(self.tab_keys[0])
        else:
            self.set_current_tab(self.tab_keys[1])

        #define pysimplegui fonts
        self.header_f = ("Helvetica", 14, "bold")
        self.title_f = ("Helvetica", 12, "bold")
        self.bold_f = ("Helvetica", 10, "bold")
        self.default_f = psg.DEFAULT_FONT

        #define tab layouts
        self.tab1 = self.construct_monitor_models_tab()
        self.tab2 = self.construct_install_tab()
        self.tab3 = self.construct_api_tab()
        
        #define Tab Group Layout
        self.tabgrp = [
            # pad=((626,0),(0,0)), 
            [psg.Push(), psg.Text('Theme: ', font=self.default_f, key="pad_theme"), psg.Combo(values=self.themes, size=(20), default_value=self.current_theme, enable_events=True, key='selectTheme')],
            [psg.TabGroup(
                [[
                    psg.Tab('Models Dashboard', self.tab1, title_color='Red',border_width =10, background_color=None,tooltip='', element_justification= 'left', key=self.tab_keys[0]),
                    psg.Tab('Models Instalation', self.tab2,title_color='Blue',background_color=None, key=self.tab_keys[1]),
                    psg.Tab('DeSOTA API Key', self.tab3,title_color='Black',background_color=None,tooltip='', key=self.tab_keys[2])
                ]],
                enable_events=True,
                tab_location='topleft',
                title_color='Gray', 
                tab_background_color='White',
                selected_title_color='White',
                selected_background_color='Gray', 
                border_width=5
            )]
        ]

        #define dashboard selected rows
        self.tools_selected = []
        self.tools_click = True
        self.models_selected = []
        self.models_click = True

        #define user services
        self.user_tools = []
        self.user_models = []

        #Define Window
        self.root = psg.Window(
            "Desota - Manager Tools",
            self.tabgrp, 
            icon=self.icon,
            default_element_size=(12, 1),
            resizable=True,
            finalize=True
        )
        self.root_size, self.root.size = self.root.size, self.root.size
        self.root.bind('<Configure>',"windowConfigure")

        #Define APP Just Started (check APP Update)
        self.just_started = True

    # TAB Constructors
    # TAB 1 - Models Dashboard
    def construct_monitor_models_tab(self):
        # No Models Available
        if not self.user_config['models']:
            return [
                [psg.Text('No Model Installed', font=self.header_f)],
                [psg.Button('Install Models', key=f"TABMOVE {self.tab_keys[1]}")]
            ]
        # Models Available
        else: # Inspited in https://stackoverflow.com/a/65778327 
            _dashboard_layout = []
            
            # Tools Table
            _tools_data = []
            _tool_table_header = ["Tool", "Service Status", "Description"]
            for _k, _v in self.user_config['models'].items():
                if _k not in self.tools_services:
                    continue
                if not _tools_data:
                    _dashboard_layout.append([psg.Text('Installed Tools', font=self.header_f)])
                _tool_params = self.services_config["services_params"][_k]
                _tool_desc = _tool_params["short_description"]
                _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"]) if _tool_params[self.system]["status"] else None
                _tool_status = self.get_service_status(_tool_status_path).lower() if _tool_status_path else "Not Service"
                _tools_data.append([_k, _tool_status, _tool_desc])
            if _tools_data:
                _dashboard_layout.append([psg.Table(
                    values=_tools_data, 
                    headings=_tool_table_header, 
                    max_col_width=40,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=len(_tools_data),
                    alternating_row_color='#000020',
                    select_mode=psg.TABLE_SELECT_MODE_EXTENDED,
                    enable_events=True,
                    row_height=25,
                    hide_vertical_scroll=True,
                    key='tool_table'
                )])
                # _dashboard_layout.append([psg.Graph()]) #TODO
            
            # Models Table
            _models_data = []
            _model_table_header = ["AI Model", "Service Status", "Description"]
            for _k, _v in self.user_config['models'].items():
                if _k in self.tools_services:
                    continue
                if not _models_data:
                    _dashboard_layout.append([psg.Text('Installed AI Models', font=self.header_f, pad=(0, (20,0)) if _tools_data else (0, (0,0)))])
                _tool_params = self.services_config["services_params"][_k]
                _tool_desc = _tool_params["short_description"]
                _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"]) if _tool_params[self.system]["status"] else None
                _tool_status = self.get_service_status(_tool_status_path).lower() if _tool_status_path else "Not a Service"
                _models_data.append([_k, _tool_status, _tool_desc])
            if _models_data:
                _dashboard_layout.append([psg.Table(
                    values=_models_data, 
                    headings=_model_table_header, 
                    max_col_width=40,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=len(_models_data),
                    alternating_row_color='#000020',
                    select_mode=psg.TABLE_SELECT_MODE_EXTENDED,
                    enable_events=True,
                    row_height=25,
                    hide_vertical_scroll=True,
                    key='model_table'
                )])
                # _dashboard_layout.append([psg.Graph()]) #TODO

            # Handle Stop Manual Services
            _started_malual_services = self.get_started_manual_services()
            if _started_malual_services:
                _disabled = False
            else:
                _disabled = True

            return [
                [psg.Column(_dashboard_layout, size=(800, 400), scrollable=True, key="_SCROLL_COL1_")],
                [
                    psg.Button('Take a Peek', button_color=("Green","White"), key="openModelUI", pad=(5, 0)), 
                    psg.Button('Source Code', button_color=("Blue","White"), key="openSource", pad=(5, 0)),
                    psg.Button('Stop Manual Services', button_color=("Orange","White"), key="stopManualServices", disabled=_disabled,pad=(5, 0)),
                    psg.Button('Uninstall', button_color=("Red","White"), key="startUninstall", pad=(5, 0))
                ]
            ]
    
    # TAB 2 - Models Instalation
    def construct_install_tab(self):
        _install_layout = []
        # Desota Tools Services
        _req_services_header = False
        for _desota_serv, _cb_disabled in self.tools_services.items():
            if not self.user_config['models'] or _desota_serv not in self.user_config['models']:
                if not _req_services_header:
                    _req_services_header = True
                    _install_layout.append([psg.Text('Available Tools', font=self.header_f)])
                _install_layout.append([
                    psg.Checkbox(_desota_serv, font=self.title_f, default=_cb_disabled, disabled=_cb_disabled, key=f"SERVICE {_desota_serv}"),
                    psg.Button('Source Code', button_color=("Blue","White"), key=f'WEBREQUEST {self.services_config["services_params"][_desota_serv]["source_code"]}', pad=(5, 0))
                ])
                _install_layout.append(
                    [
                        psg.Text(f'Description:', font=self.bold_f, pad=(30, 0)), 
                        psg.Text(f'{self.services_config["services_params"][_desota_serv]["short_description"]}', font=self.default_f)
                    ]
                )

        if _req_services_header:
            _install_layout.append([psg.HorizontalSeparator(pad=(0, 20))])

        # TODO: Upgrade Models
        _upgrade_models_header = False
        for _serv, _params in self.latest_services_config['services_params'].items():
            if _params["submodel"] == True:
                continue
            _latest_model_version = _params[self.system]['version']
            if self.user_config['models'] and _serv in self.user_config['models'] and self.user_config['models'][_serv] != _latest_model_version:
                if not _upgrade_models_header:
                    _upgrade_models_header = True
                    _install_layout.append([psg.Text('Availabe Upgrades', font=self.header_f)])
                _install_layout.append([
                    psg.Checkbox(_serv, font=self.title_f, key=f"UPGRADE {_serv}"),
                    psg.Button('Source Code', button_color=("Blue","White"), key=f'WEBREQUEST {self.services_config["services_params"][_serv]["source_code"]}', pad=(5, 0))
                ])
                _install_layout.append(
                    [
                        psg.Text(f'Description:', font=self.bold_f, pad=(30, 0)), 
                        psg.Text(f'{self.services_config["services_params"][_serv]["short_description"]}', font=self.default_f)
                    ]
                )

        if _upgrade_models_header:
            _install_layout.append([psg.HorizontalSeparator(pad=(0, 20))])
        
        # Available Uninstalled Models
        _available_models_header = False
        for _k, _v in self.latest_services_config['services_params'].items():
            if (self.user_config['models'] and _k in self.user_config['models'] ) or (_v["submodel"] == True) or (_k in self.tools_services):
                continue
            if not _available_models_header:
                _available_models_header = True
                _install_layout.append([psg.Text('Available AI Models', font=self.header_f)])
            _install_layout.append([
                psg.Checkbox(_k, font=self.title_f, key=f"SERVICE {_k}"),
                psg.Button('Source Code', button_color=("Blue","White"), key=f'WEBREQUEST {self.latest_services_config["services_params"][_k]["source_code"]}', pad=(5, 0))
            ])
            _install_layout.append(
                [
                    psg.Text(f'Description:', font=self.bold_f, pad=(30, 0)), 
                    psg.Text(f'{self.latest_services_config["services_params"][_k]["short_description"]}', font=self.default_f)
                ]
            )

        if not _install_layout:
            self.exist_installer = False
            return [
                [psg.Text('You are an absolute LEGEND!', font=self.header_f)],
                [psg.Text('You have currently installed all DeSOTA Models!', font=self.default_f)],
                [psg.Button('Check 4 Upgrades', button_color=("White","Black"), key="upgradeServConf")]
            ]
        self.exist_installer = True
        return [
            [psg.Column(_install_layout, size=(800,400), scrollable=True, key="_SCROLL_COL2_")],
            [
                psg.Button('Check 4 Upgrades', button_color=("White","Black"), key="upgradeServConf0"),
                psg.Button('Start Instalation', key="startInstall"), 
                psg.ProgressBar(100, orientation='h', expand_x=True, size=(20, 20),  key='installPBAR')
            ]
        ]

    # TAB 3 - DeSOTA API Key
    def construct_api_tab(self):
        # No Models Installed
        if not self.user_config['models']:
            return [
                [psg.Text('No Model Installed', font=self.header_f)],
                [psg.Button('Install Models', key=f"TABMOVE0 {self.tab_keys[1]}")]
            ]
        # TODO . Discuss w/ Kris what about if people have models installed but need key authenticato for new models...
        # Models Installed
        else:
            _strip_models = [ m.strip() for m, v in self.user_config['models'].items() if m not in self.tools_services]
            _str_models = ",".join(_strip_models)
            return [
                [psg.Text('Create your API Key', font=self.header_f)],  # Title
                [psg.Text('1. Log In DeSOTA ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/index.php')],    # Log In DeSOTA
                [psg.Text('2. Confirm you are logged in DeOTA API ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/assistant/api.php')],    # Confirm Log In DeSOTA
                [psg.Text('3. Get your DeSOTA API Key ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/assistant/api.php?models_list={_str_models}')],    # SET API Key
                [psg.Text('4. Insert DeSOTA API Key', font=self.default_f),psg.Input('',key='inpKey')],
                [psg.Button('Set API Key', key="setAPIkey")]
            ]



    ## Util Funks
    def get_user_theme(self):
        if not os.path.isfile(os.path.join(app_path, "user_theme.txt")):
            with open(os.path.join(app_path, "user_theme.txt"), "w") as fw:
                fw.write("DarkBlue")
                return "DarkBlue"
        with open(os.path.join(app_path, "user_theme.txt"), "r") as fr:
            return fr.read().strip()
    def set_user_theme(self, theme):
        with open(os.path.join(app_path, "user_theme.txt"), "w") as fw:
            fw.write(theme)

    def get_app_status(self):
        if not os.path.isfile(os.path.join(app_path, "status.txt")):
            with open(os.path.join(app_path, "status.txt"), "w") as fw:
                fw.write("0")
                return "0"
        with open(os.path.join(app_path, "status.txt"), "r") as fr:
            return fr.read().strip()
    def set_app_status(self, status):
        with open(os.path.join(app_path, "status.txt"), "w") as fw:
            fw.write(str(status))

    def set_current_tab(self, current_tab):
        self.current_tab = current_tab

    def get_service_status(self, get_status_path):
        _curr_epoch = time.time()
        _target_status_res = os.path.join(app_path, f"tmp_status_serv{_curr_epoch}.txt")
        # retrieved from https://stackoverflow.com/a/62226026
        _sproc = subprocess.Popen(
            [get_status_path, _target_status_res],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        returnCode = _sproc.wait()

        if not os.path.isfile(_target_status_res):
            return "unable to get status"
        
        with open(_target_status_res, "r") as fr:
            _status = fr.read().replace("\n", "").strip()
        os.remove(_target_status_res)
        return _status

    def set_installed_services(self):
        self.user_tools = []
        self.user_models = []
        if self.user_config['models']:
            for _user_service, _v in self.user_config['models'].items():
                if _user_service in self.tools_services:
                    self.user_tools.append(_user_service)
                else:
                    self.user_models.append(_user_service)

    def get_started_manual_services(self):
        if os.path.isfile(self.started_manual_services_file):
            with open(self.started_manual_services_file, "r") as fr:
                return fr.readlines()
        return []
    
    def close_manual_services(self):
        _started_manual_services = self.get_started_manual_services()
        if not _started_manual_services:
            return "-done-"
        psg.popup(
            f"You have started the manual started Services: {json.dumps(_started_manual_services, indent=4)}\n\nAfter closing this pop-up you'll be requested premission to stop them",  
            title="", 
            icon=self.icon
        )
        _started_manual_services = [m.replace("\n", "").strip() for m in _started_manual_services]
        wbm = WinBatManager(self.user_config, self.services_config, _started_manual_services)
        _target_tmp_stopper = os.path.join(app_path, f"tmp_manual_services_stopper{time.time()}.bat")
        wbm.update_models_stopper(only_selected=True, tmp_bat_target=_target_tmp_stopper, autodelete=True)
        subprocess.call([_target_tmp_stopper])
        
        os.remove(self.started_manual_services_file)

        return "-done-"

    def get_services_config(self, ignore_update=False):
        _serv_conf_path = os.path.join(config_folder, "services.config.yaml")
        _latest_serv_conf_path = os.path.join(config_folder, "latest_services_config.yaml") 
        if ignore_update:
            with open( _serv_conf_path ) as f_curr:
                with open(_latest_serv_conf_path) as f_last:
                    return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
        _req_res = requests.get(LATEST_SERV_CONF_RAW)
        if _req_res.status_code != 200:
            return None
        else:
            # Create Latest Services Config File
            with open(_latest_serv_conf_path, "w") as fw:
                fw.write(_req_res.text)

            # Create Services Config File if don't exist
            if not os.path.isfile(_serv_conf_path):
                with open(_latest_serv_conf_path, "w") as fw:
                    fw.write(_req_res.text)

            with open( _serv_conf_path ) as f_curr:
                with open(_latest_serv_conf_path) as f_last:
                    return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
    def set_services_config(self):
        _serv_conf_path = os.path.join(config_folder, "services.config.yaml")
        with open(_serv_conf_path, 'w',) as fw:
            yaml.dump(self.services_config, fw, sort_keys=False)

    def get_user_config(self):
        _user_config_path = os.path.join(config_folder, "user.config.yaml")
        if os.path.isfile(_user_config_path):
            with open(_user_config_path) as f:
                return yaml.load(f, Loader=SafeLoader)
        return None
    
    def get_app_update(self):
        _app_curr_v = self.services_config["manager_params"][self.system]["version"]
        _app_last_v = self.latest_services_config["manager_params"][self.system]["version"]
        return (_app_curr_v != _app_last_v), _app_curr_v, _app_last_v
    


    # Methods
    # - Move Within Tkinter Tabs
    def move_2_tab(self, tab_name):
        self.root[tab_name].select()
        return "-done-"

    # - Open URL in Browser
    def open_url(self, url):
        webbrowser.open(url, autoraise=False)
        return "-done-"

    # - Change APP Theme
    def theme_select(self, values):
        self.set_user_theme(values["selectTheme"])
        _ok_res = psg.popup_ok("The APP will restart in order to change the theme\nPress Ok to proceed", title="", icon=self.icon)
        if _ok_res:
            return "-restart-"
        return "-ignore-"
    
    # - Install Services
    def install_models(self, values):
        _models_2_install = []
        _models_2_upgrade = []
        for _k, _v in values.items():
            if isinstance(_k, str) and "SERVICE " in _k and _v:
                _models_2_install.append(_k.split(' ')[1].strip())
            if isinstance(_k, str) and "UPGRADE " in _k and _v:
                _models_2_upgrade.append(_k.split(' ')[1].strip())
        _models_2_upgrade += _models_2_install
        print(f" [ DEBUG ] -> Models to install = {_models_2_upgrade} ")
        if not _models_2_upgrade:
            return "-ignore-"
        
        
        _ammount_models = len(_models_2_upgrade)
        
        _ok_res = psg.popup_ok(f"You will install the following models: {json.dumps(_models_2_upgrade, indent=4)}\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            return "-ignore-"
        
        if self.system == "win":
            wbm = WinBatManager(self.user_config, self.latest_services_config, _models_2_upgrade)
            _installer_tmp_path = os.path.join(out_bat_folder, "desota_tmp_installer.bat")
            _install_prog_file = os.path.join(app_path, "install_progress.txt")
            wbm.create_models_instalation(_installer_tmp_path, _install_prog_file, start_install=True)
            del wbm
            
            self.root['startInstall'].update(disabled=True)
            self.root['installPBAR'].update(current_count=0)
            
            _mem_prog = 0
            while True:
                if not os.path.isfile(_install_prog_file):
                    _curr_prog_file = 0
                else:
                    with open(_install_prog_file, "r") as fr:
                        _curr_prog_file = fr.read().replace("\n", "").strip()
                        
                if _curr_prog_file == "":
                    _curr_prog_file = _mem_prog
                else:
                    _curr_prog_file = int(_curr_prog_file)
                    
                if _mem_prog != _curr_prog_file:
                    _mem_prog = _curr_prog_file
                    
                _curr_prog = (_curr_prog_file/_ammount_models) * 100
                self.root['installPBAR'].update(current_count=_curr_prog)
                
                if _curr_prog == 100:
                    os.remove(_install_prog_file)
                    break
                    
                _ml_res = self.main_loop(ignore_event=[], timeout=50)
                #TODO : 
                # if _ml_res == "-close-"
                # if _ml_res == "-restart-"
                # if _ml_res == "-ignore-"
            
            if _models_2_upgrade:
                for up_model in _models_2_upgrade:
                    self.services_config["services_params"][up_model] = self.latest_services_config["services_params"][up_model]
            self.set_services_config()
            
            self.user_config = self.get_user_config()
            stop_wbm = WinBatManager(self.user_config, self.latest_services_config, self.user_config["models"])
            stop_wbm.update_models_stopper(only_selected=True)
            del stop_wbm
            
        _ok_res = psg.popup_ok(f"Instalation Completed!\n\nThe APP will restart!\n\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            return "-ignore-"
        
        return "-restart-"

    # - Tool Table row selected
    def tool_table_row_selected(self, values):
        print(f" [tool_table_row_selected] -> {json.dumps(self.tools_selected, indent=2)}")
        if self.tools_click:
            for _new_sel in values["tool_table"]:
                if _new_sel in self.tools_selected:
                    self.tools_selected.remove(_new_sel)
                else:
                    self.tools_selected.append(_new_sel)
            self.root['tool_table'].update(select_rows=self.tools_selected)
            self.tools_click = False
        else:
            self.tools_click = True
        return "-ignore-"
    
    # - Model Table row selected
    def model_table_row_selected(self, values):
        print(f" [model_table_row_selected] -> {json.dumps(self.models_selected, indent=2)}")
        if self.models_click:
            for _new_sel in values["model_table"]:
                if _new_sel in self.models_selected:
                    self.models_selected.remove(_new_sel)
                else:
                    self.models_selected.append(_new_sel)
            self.root['model_table'].update(select_rows=self.models_selected)
            self.models_click = False
        else:
            self.models_click = True
        return "-ignore-"

    # - Upgrade from GITHUB Services Configs
    def update_service_config(self, values):
        try:
            _curr_serv_conf, _last_serv_conf = self.get_services_config()
            self.services_config, self.latest_services_config = _curr_serv_conf, _last_serv_conf
            
            if self.services_config["services_params"] == self.latest_services_config["services_params"]:
                psg.popup("You are currently up to date!\n", title="", icon=self.icon)
                return "-ignore-"
            _ok_res = psg.popup_ok("The APP will restart with Updated Models\n\nPress Ok to proceed", title="", icon=self.icon)
            if _ok_res:
                return "-restart-"
            return "-ignore-"
        
        except:
            _manager_issue_url = self.services_config["manager_params"]["report_issue"]
            _err_res = psg.popup_error(f'Something went wrong while attempting to get lastest services config\nCheck/Report this on {_manager_issue_url}', title="", icon=self.icon)
            if _err_res:
                self.open_url(_manager_issue_url)
            return "-ignore-"

    # - Open Tools / Models Source Codes
    def open_models_sourcecode(self, values):
        self.set_installed_services()
        
        if "tool_table" in values:
            for _row in values["tool_table"]:
                _model_name = self.user_tools[_row]
                _model_source_code = self.services_config["services_params"][_model_name]["source_code"]
                webbrowser.open(_model_source_code, autoraise=False)

        if "model_table" in values:
            for _row in values["model_table"]:
                _model_name = self.user_models[_row]
                _model_source_code = self.services_config["services_params"][_model_name]["source_code"]
                webbrowser.open(_model_source_code, autoraise=False)

        return "-done-"
        
    # - Open Tools / Models Interface
    def model_ui_handle(self, model_name):
        _res = None
        if "model_ui" in self.services_config["services_params"][model_name] and self.services_config["services_params"][model_name]["model_ui"]:
            _model_params = self.services_config["services_params"][model_name]
            _model_ui_url = _model_params["model_ui"]
            _model_req_hs = _model_params["handshake_req"]
            _model_res_hs = _model_params["handshake_res"]

            if self.services_config["services_params"][model_name]["run_constantly"]:
                try:
                    _hs_req = requests.get(_model_req_hs)
                    if _hs_req.status_code == 200 and _hs_req.json() == _model_res_hs:
                        webbrowser.open(_model_ui_url, autoraise=False)
                        return _res
                except:
                    pass

                #Start Run Constantly Services
                _start_run_constantly_serv_path = os.path.join(config_folder, "Services", "models_starter.bat")
                _sproc = subprocess.Popen([_start_run_constantly_serv_path])
                _res = "-restart-"
                while True:
                    try:
                        if _sproc.poll() == 0:
                            _hs_req = requests.get(_model_req_hs)
                            if _hs_req.status_code == 200 and _hs_req.json() == _model_res_hs:
                                webbrowser.open(_model_ui_url)
                                return _res
                    except:
                        pass
                    _ml_res = self.main_loop(ignore_event=[], timeout=50)
                    #TODO : 
                    # if _ml_res == "-close-"
                    # if _ml_res == "-restart-"
                    # if _ml_res == "-ignore-"
            
            else:
                try:
                    _hs_req = requests.get(_model_req_hs)
                    if _hs_req.status_code == 200 and _hs_req.json() == _model_res_hs:
                        webbrowser.open(_model_ui_url, autoraise=False)
                        return _res
                except:
                    pass
            
                #Start Service?
                _str_serv = psg.popup_yes_no(
                    f"The Model '{model_name}' is hosted on a service that starts and stops mannualy!\n\nDo you want to Start the Service?\n(Don't forget to stop the service after closing the model UI)",  
                    title="", 
                    icon=self.icon
                )
                if _str_serv != "Yes":
                    return _res
                
                _started_manual_services = self.get_started_manual_services()
                if model_name not in _started_manual_services:
                    _started_manual_services.append(f"{model_name}\n")

                with open(self.started_manual_services_file, "w") as fw:
                    fw.writelines(_started_manual_services)

                self.root['stopManualServices'].update(disabled=False)
                #Start Service!
                _res = "-restart-"
                _model_serv_params = self.services_config["services_params"][model_name][self.system]
                _model_service_start_path = os.path.join(
                    user_path, 
                    _model_serv_params["service_path"],
                    _model_serv_params["starter"]
                )
                _sproc = subprocess.Popen([_model_service_start_path])

                while True:
                    try:
                        if _sproc.poll() == 0:
                            _hs_req = requests.get(_model_req_hs)
                            if _hs_req.status_code == 200 and _hs_req.json() == _model_res_hs:
                                webbrowser.open(_model_ui_url, autoraise=False)
                                return _res
                    except:
                        pass
                    _ml_res = self.main_loop(ignore_event=[], timeout=50)
                    #TODO : 
                    # if _ml_res == "-close-"
                    # if _ml_res == "-restart-"
                    # if _ml_res == "-ignore-"
        
        elif  "model_cli" in self.services_config["services_params"][model_name] and self.services_config["services_params"][model_name]["model_cli"]:
            cli_cmd = []
            for mc in self.services_config["services_params"][model_name][self.system][self.services_config["services_params"][model_name]["model_cli"]]:
                # PATH TEST (get files and arguments)
                _tmp_path = os.path.join(user_path, mc)
                if os.path.isfile(_tmp_path):
                    # Files
                    cli_cmd.append(_tmp_path)
                else:
                    # Arguments
                    cli_cmd.append(mc)
            
            print(f" [ DEBUG ] - CLI Model cmd: {cli_cmd}")
                
            _sproc = subprocess.Popen(
                cli_cmd,
                creationflags = subprocess.CREATE_NEW_CONSOLE
                ).poll()
            _res = "-done-"
            
        return _res
    def open_models_ui(self, values):
        self.set_installed_services()

        _model_ui_ret = "-done-"
        if "tool_table" in values:
            for _row in values["tool_table"]:
                _model_name = self.user_tools[_row]
                _ui_res = self.model_ui_handle(_model_name)
                if _ui_res:
                    _model_ui_ret = _ui_res 

        if "model_table" in values:
            for _row in values["model_table"]:
                _model_name = self.user_models[_row]
                _ui_res = self.model_ui_handle(_model_name)
                if _ui_res:
                    _model_ui_ret = _ui_res 

        return _model_ui_ret

    # - Uninstall Service
    def uninstall_services(self, values):
        self.set_installed_services()
        _models_2_uninstall = []
        if "tool_table" in values:
            for _row in values["tool_table"]:
                _models_2_uninstall.append(self.user_tools[_row])


        if "model_table" in values:
            for _row in values["model_table"]:
                _models_2_uninstall.append(self.user_models[_row])

        if not _models_2_uninstall:
            return "-ignore-"
        
        _str_serv = psg.popup_yes_no(
            f"Confirm you want to erase the following models: {json.dumps(_models_2_uninstall, indent=4)}",  
            title="", 
            icon=self.icon,
            image=os.path.join(app_path, "Assets", "ru-sure-about-that.gif")
        )
        if _str_serv != "Yes":
            return "-ignore-"
        
        _after_un_models = self.user_config["models"].copy()
        for _model in _models_2_uninstall:
            _after_un_models.pop(_model)

        if not _after_un_models:
            _after_un_models = None
        
        if self.system == "win":
            # Get user_config to update model starter
            if _after_un_models:
                self.user_config["models"] = _after_un_models.copy()
            else:
                self.user_config["models"] = _after_un_models
                
            end_wbm = WinBatManager(self.user_config, self.services_config, self.user_config["models"])
            end_wbm.update_models_starter()
            
            wbm = WinBatManager(self.user_config, self.services_config, _models_2_uninstall)
            uninstall_waiter_path = os.path.join(app_path, f"tmp_uninstaller_status{time.time()}.txt")
            wbm.create_services_unintalation(start_uninstall=True, waiter={uninstall_waiter_path: 1})
            del wbm
            
            while True:
                if os.path.isfile(uninstall_waiter_path):
                    with open(uninstall_waiter_path, "r") as fr:
                        _waiter_res = fr.read().replace("\n", "").strip()
                    if _waiter_res == "1":
                        break
                _ml_res = self.main_loop(ignore_event=[], timeout=50)
                #TODO : 
                # if _ml_res == "-close-"
                # if _ml_res == "-restart-"
                # if _ml_res == "-ignore-"

            
            os.remove(uninstall_waiter_path)
            
            end_wbm.update_models_stopper()
            del end_wbm
            
            with open(os.path.join(config_folder, "user.config.yaml"), 'w',) as fw:
                yaml.dump(self.user_config,fw,sort_keys=False)
            

        self.set_installed_services()
        _ok_res = psg.popup("Uninstalation Completed!\n\nThe APP will restart!\n\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            return "-ignore-"
        
        return "-restart-"

    # - Stop All Started Manual Start/Stop Services
    def stop_manual_services(self, values):
        _started_manual_services = self.get_started_manual_services()
        if not _started_manual_services:
            return "-ignore-"
        _started_manual_services = [m.replace("\n", "").strip() for m in _started_manual_services]
        _popup_ok = psg.popup_ok(
            f"You will stop the following manual controlled Services: {json.dumps(_started_manual_services, indent=4)}",  
            title="", 
            icon=self.icon
        )
        print(f" [ TODO ] -> _popup_ok = {_popup_ok} ")
        if not _popup_ok:
            return "-ignore-"
        
        wbm = WinBatManager(self.user_config, self.services_config, _started_manual_services)
        _target_tmp_stopper = os.path.join(app_path, f"tmp_manual_services_stopper{time.time()}.bat")
        wbm.update_models_stopper(only_selected=True, tmp_bat_target=_target_tmp_stopper)
        _sproc = subprocess.Popen([_target_tmp_stopper])
        while True:
            if _sproc.poll() == 0:
                break
            _ml_res = self.main_loop(ignore_event=[], timeout=50)
            #TODO : 
            # if _ml_res == "-close-"
            # if _ml_res == "-restart-"
            # if _ml_res == "-ignore-"

        wbm.update_models_stopper()
        os.remove(self.started_manual_services_file)
        os.remove(_target_tmp_stopper)

        return "-restart-"
    
    # - Window Bind Event
    def column_set_size(self, element, size):
        # retrieved from https://github.com/PySimpleGUI/PySimpleGUI/issues/4407#issuecomment-860863915
        # Only work for sg.Column when `scrollable=True` or `size not (None, None)`
        options = {'width':size[0], 'height':size[1]}
        if element.Scrollable or element.Size!=(None, None):
            element.Widget.canvas.configure(**options)
        else:
            element.Widget.pack_propagate(0)
            element.set_size(size)

    def window_configure(self, values):
        print(f"\n\n[ window_configure ] - Memory Size: {self.root_size}\n[ window_configure ] - Current Size: {self.root.size}\n\n")
        print(f"{self.root_size} != {self.root.size} : {self.root_size != self.root.size}")
        if self.root_size != self.root.size:
            _size_x, _size_y = self.root.size

            # (865, 529)
            if self.user_config['models']:
                self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-129))
            if self.exist_installer:
                self.column_set_size(self.root["_SCROLL_COL2_"], (_size_x-65, _size_y-129))

            self.root_size = self.root.size
    
    
    # Get Class Method From Event and Run Method
    def main_loop(self, ignore_event=[], timeout=None):
        try:
            # Check For APP UPGRADES
            if self.just_started:
                self.just_started = False
                _app_update, _app_curr_v, _app_last_v = self.get_app_update()
                if _app_update:
                    _app_upgrade = psg.popup_yes_no(
                        f"New release of the `DeSOTA - Manager Tools` is available!\nCurrent version: {_app_curr_v}\nLatest version : {_app_last_v}\n\nDo you want to upgrade the `DeSOTA - Manager Tools`?",
                        title="DeSOTA - Manager Tools",
                        icon=self.icon,
                    )
                    if _app_upgrade == "Yes":
                        wbm = WinBatManager(self.user_config, self.latest_services_config)
                        wbm.upgrade_app(start_upgrade=True)

                        self.services_config["manager_params"] = self.latest_services_config["manager_params"]
                        self.set_services_config()

                        self.set_app_status(0)
                        self.root.close()
                        return "-close-"
                    
            #Read  values entered by user
            _event, _values = self.root.read(timeout=timeout)
        except:
            _event = psg.WIN_CLOSED

        if _event == psg.WIN_CLOSED:
            self.close_manual_services()
            self.set_app_status(0)
            self.root.close()
            return "-close-"
        
        # if _event == psg.TITLEBAR_MAXIMIZE_KEY:
        #     if not self.root.maximized:
        #         self.root.maximize()
        #     else:
        #         self.root.normal()
        
        elif _event == psg.TIMEOUT_KEY:
            return "-timeout-"
        
        # HANDLE TAB CHANGE
        elif isinstance(_event, int):
            self.current_tab = _values[_event]
            return "-ignore-"
        
        #access all the values and if selected add them to a string
        print(f" [ DEBUG ] -> event = {_event}")
        print(f" [ DEBUG ] -> values = {_values}")

        try:    # Inspired in https://stackoverflow.com/questions/7936572/python-call-a-function-from-string-name
            # Analize Event
            if " " not in _event:
                _res_event = ''.join((ce for ce in _event if not ce.isdigit()))
                _res_values = _values
            else:
                _res_event = _event.split(" ")[0]
                _res_event = ''.join((ce for ce in _res_event if not ce.isdigit()))
                _res_values = _event.split(" ")[1]

            if _res_event in ignore_event:
                return "-ignore-"
            

            _method_str = self.event_to_method[_res_event]
            _res_method = getattr(self, _method_str)
            return _res_method(_res_values)


        except AttributeError:
            raise NotImplementedError("Class `{}` does not implement `{}`".format(self.__class__.__name__, _method_str))
        except KeyError:
            raise KeyError(f"Event `{_res_event}` not found in `self.event_to_method`: {list(self.event_to_method.keys())}")



def main():
    # Start APP
    sgui = SGui()
    # Get APP Status - Prevent Re-Open
    if sgui.get_app_status() == "1":
        return 0
    sgui.set_app_status(1)
    _tab_selected = False
    _mem_open_tab = sgui.current_tab
    while True:
        if not _tab_selected:
            _tab_selected = True
            sgui.main_loop(timeout=10)
            sgui.move_2_tab(_mem_open_tab)
        print('*'*80)
        _sgui_res = sgui.main_loop()
        print(f" [ DEBUG ] -> main_loop res = {_sgui_res}")
        if _sgui_res == "-ignore-":
            continue
        elif _sgui_res == "-restart-":
            _mem_open_tab = sgui.current_tab
            sgui.root.close()
            sgui = SGui(ignore_update=True)
            _tab_selected = False
            continue

        elif _sgui_res == "-close-":
            return 0
        
if __name__ == "__main__":
    main()