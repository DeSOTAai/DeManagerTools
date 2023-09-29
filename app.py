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
    "windowConfigure": "window_configure",
    "searchDash_Enter": "search_dash",
    "searchDash_FocusIn": "focus_in_search_dash",
    "searchDash_FocusOut": "focus_out_search_dash",
    "searchInstall_Enter": "search_install",
    "searchInstall_FocusIn": "focus_in_search_install",
    "searchInstall_FocusOut": "focus_out_search_install",
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
    # Class INIT
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

        
        #Define APP Just Started (False after check APP Update)
        self.just_started = True

        #define invisible install elements
        self.created_elems = {}
        self.install_configs = {
            "at" : {},
            "up" : {},
            "am" : {},
            "api": {}
        }
        self.exist_at_sep = False
        self.exist_up_sep = False
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

        #Search Dashboard
        if self.exist_dash:
            self.root['searchDash'].bind("<Return>", "_Enter")
            
            self.root['searchDash'].Widget.config(takefocus=0)
            
            self.root['searchDash'].bind("<FocusIn>", "_FocusIn")
            self.root['searchDash'].bind("<FocusOut>", "_FocusOut")
            self.mem_dash_search = None
        #Search Install
        if self.exist_installer:
            self.root['searchInstall'].bind("<Return>", "_Enter")
            
            self.root['searchInstall'].Widget.config(takefocus=0)
            
            self.root['searchInstall'].bind("<FocusIn>", "_FocusIn")
            self.root['searchInstall'].bind("<FocusOut>", "_FocusOut")

            self.mem_install_search = None


    def sgui_exit(self) -> None:
        self.close_manual_services()
        self.set_app_status(0)
        self.root.close()



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

    def set_installed_services(self, user_tools=None, user_models=None):
        self.user_tools = []
        self.user_models = []
        if not ( (user_tools and user_models) or (isinstance(user_tools, list) and isinstance(user_models, list)) ):
            if self.user_config['models']:
                for _user_service, _v in self.user_config['models'].items():
                    if _user_service in self.tools_services:
                        self.user_tools.append(_user_service)
                    else:
                        self.user_models.append(_user_service)
            return
        self.user_tools += user_tools
        self.user_models += user_models

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
    
    

    # TAB Constructors
    # TAB 1 - Models Dashboard
    def get_tools_data(self, search_filter=None):
        _tools_data = []
        _tools = []
        for _k, _v in self.user_config['models'].items():
            if _k not in self.tools_services:
                continue
            _tool_params = self.services_config["services_params"][_k]
            _tool_desc = _tool_params["short_description"]
            _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"]) if _tool_params[self.system]["status"] else None
            _tool_status = self.get_service_status(_tool_status_path).lower() if _tool_status_path else "Not Service"
            if search_filter:
                if search_filter.lower() in _k.lower() or search_filter.lower() in _tool_desc.lower():
                    _tools_data.append([_k, _tool_status, _tool_desc])
                    _tools.append(_k)
            else:
                _tools_data.append([_k, _tool_status, _tool_desc])
                _tools.append(_k)
            
        return _tools_data, _tools
    def get_models_data(self, search_filter=None):
        _models_data = []
        _models = []
        for _k, _v in self.user_config['models'].items():
            if _k in self.tools_services:
                continue
            _tool_params = self.services_config["services_params"][_k]
            _tool_desc = _tool_params["short_description"]
            _tool_status_path = os.path.join(user_path, _tool_params[self.system]["service_path"], _tool_params[self.system]["status"]) if _tool_params[self.system]["status"] else None
            _tool_status = self.get_service_status(_tool_status_path).lower() if _tool_status_path else "Not a Service"
            if search_filter:
                if search_filter.lower() in _k.lower() or search_filter.lower() in _tool_desc.lower():
                    _models_data.append([_k, _tool_status, _tool_desc])
                    _models.append(_k)
            else:
                _models_data.append([_k, _tool_status, _tool_desc])
                _models.append(_k)
        return _models_data, _models
    def construct_monitor_models_tab(self):
        # No Models Available
        if not self.user_config['models']:
            self.exist_dash = False
            return [
                [psg.Text('No Model Installed', font=self.header_f)],
                [psg.Button('Install Models', key=f"TABMOVE {self.tab_keys[1]}")]
            ]
        # Models Available
        else: # Inspited in https://stackoverflow.com/a/65778327 
            self.exist_dash = True
            _dashboard_layout = []
            # Tools Table
            _tools_data, _tools = self.get_tools_data()
            if _tools_data:
                _tool_table_header = ["Tool", "Service Status", "Description"]
                _dashboard_layout.append([psg.Text('Installed Tools', font=self.header_f)])
                _dashboard_layout.append([psg.Table(
                    values=_tools_data, 
                    headings=_tool_table_header, 
                    max_col_width=100,
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
            _models_data, _models = self.get_models_data()
            if _models_data:
                _model_table_header = ["AI Model", "Service Status", "Description"]
                _dashboard_layout.append([psg.Text('Installed AI Models', font=self.header_f, pad=(0, (20,0)) if _models_data else (0, (0,0)))])
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

            self.set_installed_services(user_tools=_tools, user_models=_models)

            # Handle Stop Manual Services
            _started_malual_services = self.get_started_manual_services()
            if _started_malual_services:
                _disabled = False
            else:
                _disabled = True

            return [
                [psg.Input("Search", key='searchDash', expand_x=True)],
                [psg.Column(_dashboard_layout, size=(800, 400), scrollable=True, key="_SCROLL_COL1_")],
                [
                    psg.Button('Take a Peek', button_color=("Green","White"), key="openModelUI", pad=(5, 0)), 
                    psg.Button('Source Code', button_color=("Blue","White"), key="openSource", pad=(5, 0)),
                    psg.Button('Stop Manual Services', button_color=("Orange","White"), key="stopManualServices", disabled=_disabled,pad=(5, 0)),
                    psg.Button('Uninstall', button_color=("Red","White"), key="startUninstall", pad=(5, 0))
                ]
            ]
    

    # TAB 2 - Models Instalation
    def create_elem_key(self, key, identity):
        tab, cycle = identity
        _key_space = key.split(" ")
        _key_id, _key_ref = _key_space[0].strip(), f" {_key_space[-1].strip()}" if len(_key_space)>1 else ""

        if not _key_id in self.created_elems:
            self.created_elems[_key_id] = []
            
        if self.created_elems[_key_id] == []:
            _res_key = _key_id + '0' + _key_ref
            self.created_elems[_key_id].append(_res_key)

            return _res_key
        
        _buffer_id_key = sorted([int(_e.split(" ")[0].split(_key_id)[1]) for _e in self.created_elems[_key_id]])
        
        _res_key = _key_id + str( _buffer_id_key[-1] + 1 ) + _key_ref
        self.created_elems[_key_id].append(_res_key)
        
        return _res_key
    
    def set_elem_vis(self, key, identity, visibility):
        tab, cycle = identity
        if isinstance(key, str):
            _key_id = "".join((i for i in key.split(" ")[0] if not i.isdigit()))
            try:
                if not str(cycle) in self.install_configs[tab]:
                    self.install_configs[tab][str(cycle)] = {}
                if not _key_id in self.install_configs[tab][str(cycle)]:
                    self.install_configs[tab][str(cycle)][_key_id] = {}
                    
                self.install_configs[tab][str(cycle)][_key_id] = {
                    "event": key,
                    "visibility": visibility,
                }
            except Exception as e:
                print("IRROF: group = ", False)
                print("ARROF: tab = ", tab)
                print("ARROF: cycle = ", str(cycle))
                print("ARROF: _key_id = ", _key_id)
                print("IRROF: visibility = ", visibility)
                print("ERROF: install_configs[tab] = ", json.dumps(self.install_configs[tab], indent=2))
                print("Exception:", e)
        elif isinstance(key, list):
            for k in key:
                _key_id = "".join((i for i in k.split(" ")[0] if not i.isdigit()))
                try:
                    if _key_id in self.install_configs[tab][str(cycle)]:
                        self.install_configs[tab][str(cycle)][_key_id]["visibility"] = visibility
                except Exception as e:
                    print("IRROF: group = ", True)
                    print("ARROF: tab = ", tab)
                    print("ARROF: cycle = ", str(cycle))
                    print("ARROF: _key_id = ", _key_id)
                    print("IRROF: visibility = ", visibility)
                    print("ERROF: install_configs[tab] = ", json.dumps(self.install_configs[tab], indent=2))
                    print("Exception:", e)


        return visibility

    def get_install_tools(self, get_layout=True, search_filter=None):
        #TODO: Evolute from self.just_started into get_layout for init and the rest is only get visibility of elements
        '''Available Uninstalled Tools'''
        _install_tools = []
        _req_services_header = False
        if self.just_started:
            _at_header_event = self.create_elem_key('install_header_at', ("at", 0))
        else:
            if "0" in self.install_configs["at"] and "install_header_at" in self.install_configs["at"]["0"]:
                _at_header_event = self.install_configs["at"]["0"]["install_header_at"]["event"]
            else:
                return _install_tools       
             
        for count, (_desota_serv, _cb_disabled) in enumerate(self.tools_services.items()):
            if not self.user_config['models'] or _desota_serv not in self.user_config['models']:
                _desc = self.services_config["services_params"][_desota_serv]["short_description"]
                _source = self.services_config["services_params"][_desota_serv]["source_code"]
                
                if not search_filter or (search_filter.lower() in _desota_serv.lower() or search_filter.lower() in _desc):
                    if self.just_started:
                        _at_serv_event = self.create_elem_key(f"SERVICE {_desota_serv}", ("at", count))
                        _at_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("at", count))
                        _at_desc1_event = self.create_elem_key('install_desc_head_at', ("at", count))
                        _at_desc2_event = self.create_elem_key('install_desc_body_at', ("at", count))
                    else:
                        _at_serv_event = self.install_configs["at"][str(count)]["SERVICE"]["event"]
                        _at_req_event = self.install_configs["at"][str(count)]["WEBREQUEST"]["event"]
                        _at_desc1_event = self.install_configs["at"][str(count)]["install_desc_head_at"]["event"]
                        _at_desc2_event = self.install_configs["at"][str(count)]["install_desc_body_at"]["event"]


                    if not _req_services_header:
                        _req_services_header = True
                        _install_tools.append([
                            psg.Text(
                                'Available Tools', 
                                font=self.header_f, 
                                key=_at_header_event, 
                                visible=self.set_elem_vis(_at_header_event, ("at", 0), True)
                            )   
                        ])
                    _install_tools.append([
                        psg.Checkbox(_desota_serv, font=self.title_f, default=_cb_disabled, disabled=_cb_disabled, key=_at_serv_event, visible=self.set_elem_vis(_at_serv_event, ("at", count), True)),
                        psg.Button('Source Code', button_color=("Blue","White"), key=_at_req_event, visible=self.set_elem_vis(_at_req_event, ("at", count), True), pad=(5, 0))
                    ])
                    _install_tools.append(
                        [
                            psg.Text(f'Description:', font=self.bold_f, pad=(30, 0), key=_at_desc1_event, visible=self.set_elem_vis(_at_desc1_event, ("at", count), True)), 
                            psg.Text(f'{_desc}', font=self.default_f, key=_at_desc2_event, visible=self.set_elem_vis(_at_desc2_event, ("at", count), True))
                        ]
                    )
                else:
                    _at_serv_event = self.install_configs["at"][str(count)]["SERVICE"]["event"]
                    _at_req_event = self.install_configs["at"][str(count)]["WEBREQUEST"]["event"]
                    _at_desc1_event = self.install_configs["at"][str(count)]["install_desc_head_at"]["event"]
                    _at_desc2_event = self.install_configs["at"][str(count)]["install_desc_body_at"]["event"]
                    self.set_elem_vis([_at_serv_event, _at_req_event, _at_desc1_event, _at_desc2_event], ("at", count), False)

        if not _req_services_header:
            if _at_header_event in self.created_elems and self.just_started:
                self.created_elems.pop(_at_header_event)

            if not self.just_started:
                self.set_elem_vis(_at_header_event, ("at", 0), False)

        return _install_tools
    def get_upgrade_models(self, get_layout=True, search_filter=None):
        #TODO: Evolute from self.just_started inoy get_layout for init and the rest is only get visibility of elements
        '''Upgradable Models / Tools'''
        _upgrade_models = []
        _upgrade_models_header = False

        if self.just_started:
            _up_header_event = self.create_elem_key('install_header_up', ("up", 0))
        else:
            if "0" in self.install_configs["up"] and "install_header_up" in self.install_configs["up"]["0"]:
                _up_header_event = self.install_configs["up"]["0"]["install_header_up"]["event"]
            else:
                return _upgrade_models       

        for count, (_serv, _params) in enumerate(self.latest_services_config['services_params'].items()):
            if _params["submodel"] == True:
                continue
            _latest_model_version = _params[self.system]['version']

            if self.user_config['models'] and _serv in self.user_config['models'] and self.user_config['models'][_serv] != _latest_model_version:
                _desc = self.latest_services_config["services_params"][_serv]["short_description"]
                _source = self.latest_services_config["services_params"][_serv]["source_code"]
                if not search_filter or (search_filter.lower() in _serv.lower() or search_filter.lower() in _desc):
                    if self.just_started:
                        _up_upg_event = self.create_elem_key(f"SERVICE {_serv}", ("up", count))
                        _up_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("up", count))
                        _up_desc1_event = self.create_elem_key('install_desc_head_up', ("up", count))
                        _up_desc2_event = self.create_elem_key('install_desc_body_up', ("up", count))
                    else:
                        _up_upg_event = self.install_configs["up"][str(count)]["SERVICE"]["event"]
                        _up_req_event = self.install_configs["up"][str(count)]["WEBREQUEST"]["event"]
                        _up_desc1_event = self.install_configs["up"][str(count)]["install_desc_head_up"]["event"]
                        _up_desc2_event = self.install_configs["up"][str(count)]["install_desc_body_up"]["event"]


                    if not _upgrade_models_header:
                        _upgrade_models_header = True
                        _upgrade_models.append([
                            psg.Text('Availabe Upgrades', 
                                     font=self.header_f, 
                                     key=_up_header_event, 
                                     visible=self.set_elem_vis(_up_header_event, ("up", 0), True)
                            )
                        ])
                    _upgrade_models.append([
                        psg.Checkbox(_serv, font=self.title_f, key=_up_upg_event, visible=self.set_elem_vis(_up_upg_event, ("up", count), True)),
                        psg.Button('Source Code', button_color=("Blue","White"), key=_up_req_event, visible=self.set_elem_vis(_up_req_event, ("up", count), True), pad=(5, 0))
                    ])
                    _upgrade_models.append(
                        [
                            psg.Text(f'Description:', font=self.bold_f, pad=(30, 0), key=_up_desc1_event, visible=self.set_elem_vis(_up_desc1_event, ("up", count), True)), 
                            psg.Text(f'{_desc}', font=self.default_f, key=_up_desc2_event, visible=self.set_elem_vis(_up_desc2_event, ("up", count), True))
                        ]
                    )
                else:
                    _up_upg_event = self.install_configs["up"][str(count)]["SERVICE"]["event"]
                    _up_req_event = self.install_configs["up"][str(count)]["WEBREQUEST"]["event"]
                    _up_desc1_event = self.install_configs["up"][str(count)]["install_desc_head_up"]["event"]
                    _up_desc2_event = self.install_configs["up"][str(count)]["install_desc_body_up"]["event"]
                    self.set_elem_vis([_up_upg_event, _up_req_event, _up_desc1_event, _up_desc2_event], ("up", count), False)
        
        if not _upgrade_models_header:
            if _up_header_event in self.created_elems and self.just_started:
                self.created_elems.pop(_up_header_event)

            if not self.just_started:
                self.set_elem_vis(_up_header_event, ("up", 0), False)

        return _upgrade_models
    def get_install_models(self, get_layout=True, search_filter=None):
        #TODO: Evolute from self.just_started into get_layout for init and the rest is only get visibility of elements
        '''Available Uninstalled Models'''
        _install_models = []
        _available_models_header = False
        
        if self.just_started:
            _am_header_event = self.create_elem_key('install_header_am', ("am", 0))
        else:
            if "0" in self.install_configs["am"] and "install_header_am" in self.install_configs["am"]["0"]:
                _am_header_event = self.install_configs["am"]["0"]["install_header_am"]["event"]
            else:
                return _install_models  

        for count, (_k, _v)in enumerate(self.latest_services_config['services_params'].items()):
            if (self.user_config['models'] and _k in self.user_config['models'] ) or (_v["submodel"] == True) or (_k in self.tools_services):
                continue
            _desc = self.latest_services_config["services_params"][_k]["short_description"]
            _source = self.latest_services_config["services_params"][_k]["source_code"]

            if not search_filter or (search_filter.lower() in _k.lower() or search_filter.lower() in _desc):
                if self.just_started:
                    _am_serv_event = self.create_elem_key(f"SERVICE {_k}", ("am", count))
                    _am_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("am", count))
                    _am_desc1_event = self.create_elem_key('install_desc_head_am', ("am", count))
                    _am_desc2_event = self.create_elem_key('install_desc_body_am', ("am", count))
                else:
                    _am_serv_event = self.install_configs["am"][str(count)]["SERVICE"]["event"]
                    _am_req_event = self.install_configs["am"][str(count)]["WEBREQUEST"]["event"]
                    _am_desc1_event = self.install_configs["am"][str(count)]["install_desc_head_am"]["event"]
                    _am_desc2_event = self.install_configs["am"][str(count)]["install_desc_body_am"]["event"]


                if not _available_models_header:
                    _available_models_header = True
                    _install_models.append([
                        psg.Text(
                            'Available AI Models', 
                            font=self.header_f, 
                            key=_am_header_event, 
                            visible=self.set_elem_vis(_am_header_event, ("am", 0), True)
                        )
                    ])
                _install_models.append([
                    psg.Checkbox(_k, font=self.title_f, key=_am_serv_event, visible=self.set_elem_vis(_am_serv_event, ("am", count), True)),
                    psg.Button('Source Code', button_color=("Blue","White"), key=_am_req_event, visible=self.set_elem_vis(_am_req_event, ("am", count), True), pad=(5, 0))
                ])
                _install_models.append(
                    [
                        psg.Text(f'Description:', font=self.bold_f, pad=(30, 0), key=_am_desc1_event, visible=self.set_elem_vis(_am_desc1_event, ("am", count), True)), 
                        psg.Text(f'{_desc}', font=self.default_f, key=_am_desc2_event, visible=self.set_elem_vis(_am_desc2_event, ("am", count), True))
                    ]
                )
            else:
                _am_serv_event = self.install_configs["am"][str(count)]["SERVICE"]["event"]
                _am_req_event = self.install_configs["am"][str(count)]["WEBREQUEST"]["event"]
                _am_desc1_event = self.install_configs["am"][str(count)]["install_desc_head_am"]["event"]
                _am_desc2_event = self.install_configs["am"][str(count)]["install_desc_body_am"]["event"]
                self.set_elem_vis([_am_serv_event, _am_req_event, _am_desc1_event, _am_desc2_event], ("am", count), False)

        if not _available_models_header:
            if _am_header_event in self.created_elems and self.just_started:
                self.created_elems.pop(_am_header_event)
            if not self.just_started:
                self.set_elem_vis(_am_header_event, ("am", 0), False)
        return _install_models
    
    def get_install_layout(self, get_layout=True, search_filter=None):
        _install_layout = []
        # Available Uninstalled Tools
        _install_tools = self.get_install_tools(get_layout=get_layout, search_filter=search_filter)
        
        if _install_tools:
            _install_layout += _install_tools
            if self.just_started:
                self.exist_at_sep = True
                self.at_separator = self.create_elem_key('install_separator_at_up', ("at", 0))
            _install_layout.append([psg.Text('_'*80, pad=(0, 20), key=self.at_separator, visible=self.set_elem_vis(self.at_separator, ("at", 0), True))])
        elif self.exist_at_sep:
            self.set_elem_vis(self.at_separator, ("at", 0), False)

        # Upgradable Models / Tools
        _upgrade_models = self.get_upgrade_models(get_layout=get_layout, search_filter=search_filter)
        if _upgrade_models:
            _install_layout += _upgrade_models
            if self.just_started:
                self.exist_up_sep = True
                self.up_separator = self.create_elem_key('install_separator_up_am', ("up", 0))
            _install_layout.append([psg.Text('_'*80, pad=(0, 20), key=self.up_separator, visible=self.set_elem_vis(self.up_separator, ("up", 0), True))])
        elif self.exist_up_sep:
            self.set_elem_vis(self.up_separator, ("up", 0), False)

        # Available Uninstalled Models
        _install_models = self.get_install_models(get_layout=get_layout, search_filter=search_filter)
        if _install_models:
            _install_layout += _install_models
        
        print("INSTALL CONF:", json.dumps(self.install_configs, indent=2))
        return _install_layout
    def construct_install_tab(self):
        _install_layout = self.get_install_layout()
        if not _install_layout:
            self.exist_installer = False
            return [
                [psg.Text('You are an absolute LEGEND!', font=self.header_f)],
                [psg.Text('You have currently installed all DeSOTA Models!', font=self.default_f)],
                [psg.Button('Check 4 Upgrades', button_color=("White","Black"), key="upgradeServConf")]
            ]
        self.exist_installer = True
        return [
            [psg.Input("Search", key='searchInstall', expand_x=True, focus=False)],
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

            _req1_event = self.create_elem_key('WEBREQUEST http://129.152.27.36/index.php', ("api", 0))
            _req2_event = self.create_elem_key('WEBREQUEST http://129.152.27.36/assistant/api.php', ("api", 0))
            _req3_event = self.create_elem_key(f'WEBREQUEST http://129.152.27.36/assistant/api.php?models_list={_str_models}', ("api", 0))
            

            return [
                [psg.Text('Create your API Key', font=self.header_f)],  # Title
                [psg.Text('1. Log In DeSOTA ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=_req1_event)],    # Log In DeSOTA
                [psg.Text('2. Confirm you are logged in DeOTA API ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=_req2_event)],    # Confirm Log In DeSOTA
                [psg.Text('3. Get your DeSOTA API Key ', font=self.default_f), psg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=_req3_event)],    # SET API Key
                [psg.Text('4. Insert DeSOTA API Key', font=self.default_f),psg.Input('',key='inpKey')],
                [psg.Button('Set API Key', key="setAPIkey")]
            ]



    # Methods
    # - Move Within Tkinter Tabs
    def move_2_tab(self, tab_name):
        self.root[tab_name].select()
        self.root.refresh()
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
            if isinstance(_k, str) and "SERVICE" in _k and _v:
                _models_2_install.append(_k.split(' ')[1].strip())
            if isinstance(_k, str) and "UPGRADE" in _k and _v:
                _models_2_upgrade.append(_k.split(' ')[1].strip())
        _models_2_upgrade += _models_2_install
        print(f" [ DEBUG ] -> Models to install = {_models_2_upgrade} ")

        if not _models_2_upgrade:
            return "-ignore-"
        
        
        _ammount_models = len(_models_2_upgrade)
        
        _ok_res = psg.popup_ok(f"You will install the following models: {json.dumps(_models_2_upgrade, indent=4)}\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            print("OK RES", _ok_res)
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
        # print(f" [tool_table_row_selected] -> {json.dumps(self.tools_selected, indent=2)}")
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
        # print(f" [model_table_row_selected] -> {json.dumps(self.models_selected, indent=2)}")
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
        _ok_res = psg.popup("Uninstalation Completed!\n\nThe APP need to restart!\nPress Ok to proceed", title="", icon=self.icon)
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
        # print(f"\n\n[ window_configure ] - Memory Size: {self.root_size}\n[ window_configure ] - Current Size: {self.root.size}\n\n")
        # print(f"{self.root_size} != {self.root.size} : {self.root_size != self.root.size}")
        if self.root_size != self.root.size:
            _size_x, _size_y = self.root.size

            # (865, 529)
            if self.user_config['models']:
                self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-150))
            if self.exist_installer:
                self.column_set_size(self.root["_SCROLL_COL2_"], (_size_x-65, _size_y-150))

            self.root_size = self.root.size
    
    # - Search Dashboard
    def focus_in_search_dash(self, values):
        self.root["searchDash"].update('')
    def focus_out_search_dash(self, values):
        self.root["searchDash"].update(self.mem_dash_search if self.mem_dash_search else 'Search')

    def search_dash(self, values):
        _search_filter = values['searchDash']
        self.tools_selected = []
        self.tools_click = False
        self.models_selected = []
        self.models_click = False
        if _search_filter.strip() != "":
            self.mem_dash_search = _search_filter.strip()
            _tools_data, _tools = self.get_tools_data(search_filter=_search_filter)
            _models_data, _models = self.get_models_data(search_filter=_search_filter)
        else:
            self.mem_dash_search = "Search"
            _tools_data, _tools = self.get_tools_data()
            _models_data, _models = self.get_models_data()

        self.root['tool_table'].update(values=_tools_data)
        self.root['model_table'].update(values=_models_data)

        self.set_installed_services(user_tools=_tools, user_models=_models)

        return "-done-"
    
    # - Search Install
    def focus_in_search_install(self, values):
        print("DEBUG:", "Install Search Focus")
        self.root["searchInstall"].update('')
    def focus_out_search_install(self, values):
        print("DEBUG:", "Install Search Focus Out")
        self.root["searchInstall"].update(self.mem_install_search if self.mem_install_search else 'Search')

    def search_install(self, values):
        _search_filter = values['searchInstall']
        # print("SEARCH QUERY:", _search_filter)
        if _search_filter.strip() != "":
            self.mem_install_search = _search_filter.strip()
            self.get_install_layout(search_filter=_search_filter)
        else:
            self.mem_install_search = "Search"
            self.get_install_layout()

        _taget_dict = {key: self.install_configs[key] for key in ["at","up", "am"]}
        for _, _key in _taget_dict.items():
            for _, _cycle in _key.items():
                for _, _data in _cycle.items():
                    print("_data:", _data)
                    self.root.refresh()
                    _elem, _vis = _data["event"], _data["visibility"]
                    self.root[_elem].update(visible=_vis)
                
        return "-done-"
        

    

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
            self.sgui_exit()
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
                _res_space = _event.split(" ")
                _res_event, _res_values = _res_space[0], _res_space[-1]
                _res_event = ''.join((ce for ce in _res_event if not ce.isdigit()))

            if _res_event in ignore_event:
                return "-ignore-"
            

            _method_str = self.event_to_method[_res_event]
            _res_method = getattr(self, _method_str)
            return _res_method(_res_values)


        except AttributeError:
            self.close_manual_services()
            self.sgui_exit()
            raise NotImplementedError("Class `{}` does not implement `{}`".format(self.__class__.__name__, _method_str))
        except KeyError:
            self.close_manual_services()
            self.sgui_exit()
            raise KeyError(f"Event `{_res_event}` not found in `self.event_to_method`: {list(self.event_to_method.keys())}")



def main():
    # Start APP
    sgui = SGui()
    # Get APP Status - Prevent Re-Open
    if sgui.get_app_status() == "1":
        _app_upgrade = psg.popup_yes_no(
            f"This program is allready open or has not been properly closed!\nDo you wish to continue?",
            title="DeSOTA - Manager Tools",
            icon = sgui.icon,
        )
        if _app_upgrade != "Yes":
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