import os
import webbrowser
import json
import PySimpleGUI as sg
from Tools.services_manager import WinBatManager
import subprocess
import time

DEBUG = True
DESOTA_TOOLS_SERVICES = {    # Desc -> Service: Checkbox Disabled = REQUIRED
    "desotaai/derunner": True
}
EVENT_TO_METHOD = {
    "TABMOVE": "move_2_tab",
    "WEBREQUEST": "open_url",
    "selectTheme": "theme_select",
    "startInstall": "install_models",
    "tool_table": "tool_table_row_selected",
    "model_table": "model_table_row_selected"
}

user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services


# Construct APP with PySimpleGui
class SGui():
    def __init__(self) -> None:
        #Class Vars
        self.debug = DEBUG
        self.tools_services = DESOTA_TOOLS_SERVICES
        self.event_to_method = EVENT_TO_METHOD
        self.tab_keys= [ '-TAB1-', '-TAB2-', '-TAB3-']
        self.themes = sg.ListOfLookAndFeelValues()
        self.current_theme = self.get_user_theme()
        
        with open(os.path.join(config_folder, "services.config.yaml")) as f:
            self.services_config = yaml.load(f, Loader=SafeLoader)
        with open(os.path.join(config_folder, "user.config.yaml")) as f:
            self.user_config = yaml.load(f, Loader=SafeLoader)
        self.system = self.user_config['system']
        
        #define pysimplegui theme
        sg.theme(self.current_theme)
        
        #define open tab
        self.set_current_tab(self.tab_keys[0])

        #define pysimplegui fonts
        self.header_f = ("Helvetica", 12, "bold")
        self.title_f = ("Helvetica", 10, "bold")
        self.default_f = sg.DEFAULT_FONT

        #define tab layouts
        self.tab1 = self.construct_monitor_models_tab()
        self.tab2 = self.construct_install_tab()
        self.tab3 = self.construct_api_tab()
        
        #define Tab Group Layout
        self.tabgrp = [
            [sg.Text('Theme: ', font=self.default_f, pad=((410,0),(0,0))), sg.Combo(values=self.themes, default_value=self.current_theme, enable_events=True, key='selectTheme')],
            [sg.TabGroup(
                [[
                    sg.Tab('Models Dashboard', self.tab1, title_color='Red',border_width =10, background_color=None,tooltip='', element_justification= 'left', key=self.tab_keys[0]),
                    sg.Tab('Models Instalation', self.tab2,title_color='Blue',background_color=None, key=self.tab_keys[1]),
                    sg.Tab('DeSOTA API Key', self.tab3,title_color='Black',background_color=None,tooltip='', key=self.tab_keys[2])
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

        #Define Window
        self.root = sg.Window("Desota - Manager Tools",self.tabgrp, icon=os.path.join(app_path, "Assets", "icon.ico"))

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
        _target_status_res = os.path.join(app_path, "tmp_status_serv.txt")
        subprocess.call([get_status_path, _target_status_res])
        while not os.path.isfile(_target_status_res):
            time.sleep(.3)
            continue
        with open(_target_status_res, "r") as fr:
            _status = fr.read().replace("\n", "").strip()
        os.remove(_target_status_res)
        return _status

    # TAB Constructors
    # TAB 1 - Models Dashboard
    def construct_monitor_models_tab(self):
        # No Models Available
        if not self.user_config['models']:
            return [
                [sg.Text('No Model Installed', font=self.header_f)],
                [sg.Button('Install Models', key=f"TABMOVE {self.tab_keys[1]}")]
            ]
        # Models Available
        else: # Inspited in https://stackoverflow.com/a/65778327 
            _dashboard_layout = []

            _tools_data = []
            _tool_table_header = ["Tool", "Service Status", "Description"]
            for _k, _v in self.user_config['models'].items():
                if _k not in self.tools_services:
                    continue
                if not _tools_data:
                    _dashboard_layout.append([sg.Text('Installed Desota Tools', font=self.header_f)])
                _tool_params = self.services_config["services_params"][_k]
                _tool_desc = _tool_params["description"]
                _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"])
                _tool_status = self.get_service_status(_tool_status_path).lower()
                _tool_source = _tool_params["source_code"]
                _tools_data.append([_k, _tool_status, _tool_desc])
            if _tools_data:
                _dashboard_layout.append([sg.Table(
                    values=_tools_data, 
                    headings=_tool_table_header, 
                    max_col_width=40,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=len(_tools_data),
                    alternating_row_color='#000020',
                    select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                    enable_events=True,
                    row_height=25,
                    hide_vertical_scroll=True,
                    key='tool_table'
                )])
                # _dashboard_layout.append([sg.Graph()]) #TODO
                
            _models_data = []
            _model_table_header = ["AI Model", "Service Status", "Description"]
            for _k, _v in self.user_config['models'].items():
                if _k in self.tools_services:
                    continue
                if not _models_data:
                    _dashboard_layout.append([sg.Text('Installed AI Models', font=self.header_f, pad=(0, (20,0)) if _tools_data else (0, (0,0)))])
                _tool_params = self.services_config["services_params"][_k]
                _tool_desc = _tool_params["description"]
                _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"])
                _tool_status = self.get_service_status(_tool_status_path).lower()
                _tool_source = _tool_params["source_code"]
                _models_data.append([_k, _tool_status, _tool_desc])
            if _models_data:
                _dashboard_layout.append([sg.Table(
                    values=_models_data, 
                    headings=_model_table_header, 
                    max_col_width=40,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=len(_models_data),
                    alternating_row_color='#000020',
                    select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                    enable_events=True,
                    row_height=25,
                    hide_vertical_scroll=True,
                    key='model_table'
                )])
                # _dashboard_layout.append([sg.Graph()]) #TODO
                _dashboard_layout.append([sg.Button('Take a Peek', button_color=("Green","White"), key="openSource", pad=(5, (20,0))), sg.Button('Source Code', button_color=("Blue","White"), key="openSource", pad=(5, (20,0))), sg.Button('Uninstall', button_color=("Red","White"), key="startUninstall", pad=(5, (20,0)))])

            return _dashboard_layout
    
    # TAB 2 - Models Instalation
    def construct_install_tab(self):
        _install_layout = []
        # Desota Tools Services
        _req_services_header = False
        for _desota_serv, _cb_disabled in self.tools_services.items():
            if not self.user_config['models'] or _desota_serv not in self.user_config['models']:
                if not _req_services_header:
                    _req_services_header = True
                    _install_layout.append([sg.Text('Desota Tools Services', font=self.title_f)])
                _install_layout.append([sg.Checkbox(_desota_serv, default=_cb_disabled, disabled=_cb_disabled, key=f"SERVICE {_desota_serv}")])

        if _req_services_header:
            _install_layout.append([sg.HorizontalSeparator()])

        # TODO: Upgrade Models
        _upgrade_models_header = False
        for _k, _v in self.services_config['services_params'].items():
            if _v["submodel"] == True:
                continue
            _latest_model_version = _v[self.system]['version']
            if self.user_config['models'] and _k in self.user_config['models'] and self.user_config['models'][_k] != _latest_model_version:
                if not _upgrade_models_header:
                    _upgrade_models_header = True
                    _install_layout.append([sg.Text('Upgradable Services Availabe', font=self.title_f)])
                _install_layout.append([sg.Checkbox(_k, key=f"SERVICE {_k}")])

        if _upgrade_models_header:
            _install_layout.append([sg.HorizontalSeparator()])
        
        # Available Uninstalled Models
        _available_models_header = False
        for _k, _v in self.services_config['services_params'].items():
            if (self.user_config['models'] and _k in self.user_config['models'] ) or (_v["submodel"] == True) or (_k in self.tools_services):
                continue
            if not _available_models_header:
                _available_models_header = True
                _install_layout.append([sg.Text('Available Models', font=self.title_f)])
            _install_layout.append([sg.Checkbox(_k, key=f"SERVICE {_k}")])

        if not _install_layout:
            return [
                [sg.Text('You are an absolute LEGEND!', font=self.header_f)],
                [sg.Text('You have currently installed all DeSOTA Models!', font=self.default_f)],
                [sg.Button('Check 4 Upgrades', key="upgradeServConf")]
            ]
        return [
            [sg.Text('Select the services to be installed', font=self.header_f), sg.Button('Check 4 Upgrades', key="upgradeServConf0")],
            [sg.Column(_install_layout, size=(600,300), scrollable=True)],
            [sg.Button('Start Instalation', key="startInstall"), sg.ProgressBar(100, orientation='h', expand_x=True, size=(20, 20),  key='installPBAR')]
        ]

    # TAB 3 - DeSOTA API Key
    def construct_api_tab(self):
        # No Models Installed
        if not self.user_config['models']:
            return [
                [sg.Text('No Model Installed', font=self.header_f)],
                [sg.Button('Install Models', key=f"TABMOVE0 {self.tab_keys[1]}")]
            ]
        # TODO . Discuss w/ Kris what about if people have models installed but need key authenticato for new models...
        # Models Installed
        else:
            _strip_models = [ m.strip() for m, v in self.user_config['models'].items() if m not in self.tools_services]
            _str_models = ",".join(_strip_models)
            return [
                [sg.Text('Create your API Key', font=self.header_f)],  # Title
                [sg.Text('1. Log In DeSOTA ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/index.php')],    # Log In DeSOTA
                [sg.Text('2. Confirm you are logged in DeOTA API ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/assistant/api.php')],    # Confirm Log In DeSOTA
                [sg.Text('3. Get your DeSOTA API Key ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'WEBREQUEST http://129.152.27.36/assistant/api.php?models_list={_str_models}')],    # SET API Key
                [sg.Text('4. Insert DeSOTA API Key', font=self.default_f),sg.Input('',key='inpKey')],
                [sg.Button('Set API Key', key="setAPIkey")]
            ]


    # Methods
    # - Move Within Tkinter Tabs
    def move_2_tab(self, tab_name):
        self.root[tab_name].select()
        return "-done-"

    # - Open URL in Browser
    def open_url(self, url):
        webbrowser.open(url)
        return "-done-"

    # - Change APP Theme
    def theme_select(self, values):
        self.set_user_theme(values["selectTheme"])
        return "-restart-"
    
    # - Install Services
    def install_models(self, values):
        _models_2_install = []
        for _k, _v in values.items():
            if isinstance(_k, str) and "SERVICE " in _k and _v:
                _models_2_install.append(_k.split(' ')[1].strip())
        print(f" [ DEBUG ] -> Models to install = {_models_2_install} ")
        if not _models_2_install:
            return "-ignore-"
        _ammount_models = len(_models_2_install)
        if self.system == "win":
            wbm = WinBatManager(self.user_config, self.services_config, _models_2_install)
            _installer_tmp_path = os.path.join(out_bat_folder, "desota_tmp_installer.bat")
            wbm.create_models_instalation(_installer_tmp_path, start_install=True)
            self.root['startInstall'].update(disabled=True)
            self.root['installPBAR'].update(current_count=0)
            _install_prog_file = os.path.join(app_path, "install_progress.txt")
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
                    wbm.update_models_stopper()
                    break
                else:
                    _ml_res = self.main_loop(ignore_event=[], timeout=500)
                    #TODO : 
                    # if _ml_res == "-close-"
                    # if _ml_res == "-restart-"
                    # if _ml_res == "-ignore-"
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

    # Get Class Method From Event and Run Method
    def main_loop(self, ignore_event=[], timeout=None):
        try:
            #Read  values entered by user
            _event, _values = self.root.read(timeout=timeout)
        except:
            _event = sg.WIN_CLOSED

        if _event == sg.WIN_CLOSED:
            self.set_app_status(0)
            self.root.close()    
            return "-close-"
        elif _event == sg.TIMEOUT_KEY:
            return "-timeout-"
        # TAB CHANGED
        elif isinstance(_event, int):
            self.current_tab = _values[_event]
            return "-ignore-"
        #access all the values and if selected add them to a string
        print(f" [ DEBUG ] -> event = {_event}")
        print(f" [ DEBUG ] -> values = {_values}")

        try:    # Inspired in https://stackoverflow.com/questions/7936572/python-call-a-function-from-string-name
            # Analize Event
            if " " not in _event:
                _res_event = _event
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
        _sgui_res = sgui.main_loop()
        print(f" [ DEBUG ] -> main_loop res = {_sgui_res}")
        if _sgui_res == "-ignore-":
            continue
        elif _sgui_res == "-restart-":
            _mem_open_tab = sgui.current_tab
            sgui.root.close()
            sgui = SGui()
            _tab_selected = False
            continue

        elif _sgui_res == "-close-":
            break
        
if __name__ == "__main__":
    main()