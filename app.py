import PySimpleGUI as psg
import os, sys, time, requests, json
import subprocess, webbrowser

DEBUG = True

# DEPRECATED:
#
# DESOTA_TOOLS_SERVICES = {    # Desc -> Service: Checkbox Disabled = REQUIRED
#     "desotaai/derunner": True,
#     "franciscomvargas/deurlcruncher": False
# }

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
    "derunner_log_head": "un_fold_derunner_log"
}

if getattr(sys, "frozen", False):
    # The application is frozen
    DIST_PATH = os.path.dirname(sys.executable)
else:
    # The application is not frozen
    # Change this bit to match where you store your data files:
    DIST_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(DIST_PATH)
APP_PATH=os.path.dirname(DIST_PATH)
DESOTA_ROOT_PATH=os.path.dirname(APP_PATH)
USER_PATH=os.path.dirname(DESOTA_ROOT_PATH)
LOG_PATH=os.path.join(DESOTA_ROOT_PATH, "demanager.log")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
WHOAMI_PATH=os.path.join(APP_PATH, "whoami.json")

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
CONFIG_FOLDER=os.path.join(DESOTA_ROOT_PATH, "Configs")  # User | Services
if not os.path.isdir(CONFIG_FOLDER):
    os.mkdir(CONFIG_FOLDER)
USER_CONFIG_PATH=os.path.join(CONFIG_FOLDER, "user.config.yaml")
SERVICES_CONFIG_PATH=os.path.join(CONFIG_FOLDER, "services.config.yaml")
LAST_SERVICES_CONFIG_PATH=os.path.join(CONFIG_FOLDER, "latest_services.config.yaml")

# Services Configurations - Latest version URL
LATEST_SERV_CONF_RAW = "https://raw.githubusercontent.com/DeSOTAai/DeRunner/main/Assets/latest_services.config.yaml"

# retieved from https://stackoverflow.com/a/11995662  && https://stackoverflow.com/a/10052222 && https://stackoverflow.com/a/40388766
GET_WIN_ADMIN = [
    "net session >NUL 2>NUL\n",
    "IF %errorLevel% NEQ 0 (\n",
    "\tgoto UACPrompt\n",
    ") ELSE (\n",
    "\tgoto gotAdmin\n",
    ")\n",
    ":UACPrompt\n",
    'powershell -Command "Start-Process -Wait -Verb RunAs -FilePath \'%0\' -ArgumentList \'am_admin\'" \n',
    "exit /B\n",
    ":gotAdmin\n"
]

# inspired inhttps://stackoverflow.com/a/13874620
def get_platform():
    _platform = sys.platform
    _win_res=["win32", "cygwin", "msys"]
    _lin_res=["linux", "linux2"]
    _mac_res=["darwin"]
    _user_sys = "win" if _platform in _win_res else "lin" if _platform in _lin_res else "mac" if _platform in _mac_res else None
    if not _user_sys:
        raise EnvironmentError(f"Plataform `{_platform}` can not be parsed to DeSOTA. Options: Windows={_win_res}; Linux={_lin_res}; MacOS={_mac_res}")
    return _user_sys
USER_SYS=get_platform()
if USER_SYS=="win":
    EXECS_PATH = os.path.join(APP_PATH, "executables", "Windows")
    USER=str(USER_PATH).split("\\")[-1]
elif USER_SYS=="lin":
    EXECS_PATH = os.path.join(APP_PATH, "executables", "Linux")
    USER=str(USER_PATH).split("/")[-1]
print("USER:", USER)
# Construct APP with PySimpleGui
class SGui():
    # Class INIT
    def __init__(self, ignore_update=False) -> None:
        #Class Vars
        self.debug = DEBUG
        self.event_to_method = EVENT_TO_METHOD
        self.tab_keys= [ '-TAB1-', '-TAB2-', '-TAB3-']
        self.themes = psg.ListOfLookAndFeelValues()
        self.current_theme = self.get_user_theme()
        self.started_manual_services_file = os.path.join(TMP_PATH, "manual_services_started.txt")
        self.exist_log = os.path.isfile(LOG_PATH)

        if USER_SYS == 'win':
            self.icon = os.path.join(APP_PATH, "Assets", "icon.ico")
        else:
            self.icon = os.path.join(APP_PATH, "Assets", "icon.png")
        self.user_config = self.get_user_config()
        if not self.user_config:
            raise EnvironmentError()
        
        self.services_config, self.latest_services_config = self.get_services_config(ignore_update=ignore_update)
        if not self.services_config:
            raise EnvironmentError()
        
        self.tools_services = self.get_tools_services()
        
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
        self.default_f = ("Helvetica", 10)
        # self.default_f = psg.DEFAULT_FONT

        
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

        #define user models/tools
        self.user_tools = []
        self.user_models = []

        #define derunner log existence
        self.exist_derunner = False
        self.derunner_fold = True
        self.derunner_memory = ""

        
        print("Creating App Layots:")
        #define tab layouts
        self.tab1 = self.construct_monitor_models_tab()
        print("    Tab 1 Created")
        self.tab2 = self.construct_install_tab()
        print("    Tab 2 Created")
        self.tab3 = self.construct_api_tab()
        print("    Tab 3 Created")
        
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
        print("    Tab Group Created")


        #define dashboard selected rows
        self.tools_selected = []
        self.tools_click = True
        self.models_selected = []
        self.models_click = True

        #Define Window
        print("Creating App Window...")
        self.root = psg.Window(
            "Desota - Manager Tools",
            self.tabgrp, 
            icon=self.icon,
            default_element_size=(12, 1),
            resizable=True,
            finalize=True
        )
        
        print("Defining Window Binds and what not...")
        self.root_size, self.root.size = self.root.size, self.root.size
        self.root.bind('<Configure>',"windowConfigure")
        #Search Dashboard
        if self.exist_dash:
            self.root['searchDash'].Widget.config(takefocus=0)
            self.mem_dash_search = None

            self.root['searchDash'].bind("<Return>", "_Enter")
            self.root['searchDash'].bind("<FocusIn>", "_FocusIn")
            self.root['searchDash'].bind("<FocusOut>", "_FocusOut")
        #Search Install
        if self.exist_installer:
            self.root['searchInstall'].Widget.config(takefocus=0)
            self.mem_install_search = None

            self.root['searchInstall'].bind("<Return>", "_Enter")
            self.root['searchInstall'].bind("<FocusIn>", "_FocusIn")
            self.root['searchInstall'].bind("<FocusOut>", "_FocusOut")
        
        # INIT window size
        self.fresh_window_size()

    def sgui_exit(self) -> None:
        self.close_manual_services()
        self.set_app_status(0)
        self.root.close()


    ## Util Funks
    def get_user_theme(self):
        if not os.path.isfile(os.path.join(APP_PATH, "user_theme.txt")):
            with open(os.path.join(APP_PATH, "user_theme.txt"), "w") as fw:
                fw.write("DarkBlue")
                return "DarkBlue"
        with open(os.path.join(APP_PATH, "user_theme.txt"), "r") as fr:
            return fr.read().strip()
    def set_user_theme(self, theme):
        with open(os.path.join(APP_PATH, "user_theme.txt"), "w") as fw:
            fw.write(theme)

    def get_app_status(self):
        if not os.path.isfile(os.path.join(APP_PATH, "status.txt")):
            with open(os.path.join(APP_PATH, "status.txt"), "w") as fw:
                fw.write("0")
                return "0"
        with open(os.path.join(APP_PATH, "status.txt"), "r") as fr:
            return fr.read().strip()
    def set_app_status(self, status):
        with open(os.path.join(APP_PATH, "status.txt"), "w") as fw:
            fw.write(str(status))

    def set_current_tab(self, current_tab):
        self.current_tab = current_tab

    def get_service_status(self, get_status_path):
        if not os.path.isfile(get_status_path):
            return None
        _curr_epoch = time.time()
        asset_basename=os.path.basename(get_status_path).split(".")[0]
        _target_status_res = os.path.join(TMP_PATH, f"{asset_basename}_status{_curr_epoch}.txt")
        # retrieved from https://stackoverflow.com/a/62226026
        so = open(_target_status_res, "w")
        _status_cmd = [get_status_path, "/nopause"] if USER_SYS == "win" else ["bash", get_status_path] if USER_SYS == "lin" else []
        if USER_SYS=="win":
            _sproc = subprocess.Popen(
                _status_cmd,
                # stdout=subprocess.DEVNULL,
                stdout=so,
                stderr=so,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            _sproc = subprocess.Popen(
                _status_cmd,
                # stdout=subprocess.DEVNULL,
                stdout=so,
                stderr=so
            )

        returnCode = _sproc.wait()
        so.close()

        if not os.path.isfile(_target_status_res):
            return "unable to get status"
        
        with open(_target_status_res, "r") as fr:
            _status = fr.read().replace("\n", "").strip()
        if os.path.isfile(_target_status_res):
            os.remove(_target_status_res)
        
        return _status

    def set_installed_services(self, user_tools=None, user_models=None):
        if not (user_tools and user_models) or not (isinstance(user_tools, list) and isinstance(user_models, list)):
            if self.user_config['models']:
                for _user_service in list(self.user_config['models'].keys()):
                    if _user_service in self.tools_services:
                        if _user_service not in self.user_tools:
                            self.user_tools.append(_user_service)
                    else:
                        if _user_service not in self.user_models:
                            self.user_models.append(_user_service)
            return
        self.user_tools = user_tools
        self.user_models = user_models

    def get_started_manual_services(self):
        if os.path.isfile(self.started_manual_services_file):
            with open(self.started_manual_services_file, "r") as fr:
                return fr.readlines()
        return []
    def set_started_manual_services(self, content):
        if not content:
            return
        with open(self.started_manual_services_file, "w") as fw:
            if isinstance(content, list):
                fw.writelines(content)
            else:
                fw.write(f"{content}\n")
    
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
        for service in _started_manual_services:
            _service_sys_params=self.services_config["services_params"][service][USER_SYS]
            _stop_path=os.path.join(USER_PATH, _service_sys_params['project_dir'], _service_sys_params['execs_path'], _service_sys_params['stoper'])
            if USER_SYS == "win":
                _close_cmd=[_stop_path]
            elif USER_SYS == "lin":
                _close_cmd=["bash", _stop_path]
            subprocess.call(_close_cmd)
        
        if os.path.isfile(self.started_manual_services_file):
            os.remove(self.started_manual_services_file)
        
        return "-done-"
    
    def upddate_derunner_log(self):
        if not self.exist_derunner:
            return
        
        _gui_logger = self.root['derunner_log']

        _derunner_log_path = os.path.join(DESOTA_ROOT_PATH, "demanager.log")
        if not os.path.isfile(_derunner_log_path):
            _gui_logger.Update(f"DeRunner service.log not found!\nPath:{_derunner_log_path}")
            return
        
        _num_lines = 100

        last_lines = []
        with open(_derunner_log_path, 'rb') as f:
            try:  # catch OSError in case of a one line file 
                f.seek(-2, os.SEEK_END)
                while _num_lines > 1:
                    f.seek(-2, os.SEEK_CUR)
                    if f.read(1) == b'\n':
                        _num_lines -= 1
            except OSError:
                f.seek(0)
            last_lines = f.read().decode()
        if self.derunner_memory != last_lines:
            self.derunner_memory = last_lines
            _gui_logger.Update(last_lines)
            _gui_logger.set_vscroll_position(1)

    def fresh_window_size(self):
        if self.exist_dash and self.exist_log and self.derunner_fold:
            _size_x, _size_y = self.root.size
            self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-205))

    def user_chown(self, path):
        '''Remove root previleges for files and folders: Required for Linux'''
        if USER_SYS == "lin":
            #CURR_PATH=/home/[USER]/Desota/DeRunner
            USER=str(DESOTA_ROOT_PATH).split("/")[-2]
            os.system(f"chown -R {USER} {path}")
        return

    #   > Create Assets Script
    def create_install_script(self, model_ids, manage_configs_flag_path, asset_sucess_path, progress=None) -> str:
        '''
        Create model install|upgrade script

        return sript path
        '''
        # Before anything else:
        # 1 - Remove models from user configs
        self.edit_user_configs("models", model_ids, uninstall=True)
        # 2 - TODO: Check if DeRunner is running any of the requested models
        ##                     ##
        # Loading Stuff - Begin #
        l_download_weigth=5
        l_stop__weigth=8
        l_start__weigth=12
        l_uninstall_weigth=15
        l_setup_weigth=25
        _steps = None
        # Loading Stuff -   End #
        ##                     ##
        # 1 - INIT
        if "desotaai/derunner" in self.services_config["services_params"]:
            derunner_sys_params = self.services_config["services_params"]["desotaai/derunner"][USER_SYS]
        else:
            derunner_sys_params = self.latest_services_config["services_params"]["desotaai/derunner"][USER_SYS]
            
        derunner_stop_path = os.path.join(USER_PATH, derunner_sys_params["project_dir"], derunner_sys_params["execs_path"], derunner_sys_params["stoper"])
        derunner_status_path = os.path.join(USER_PATH, derunner_sys_params["project_dir"], derunner_sys_params["execs_path"], derunner_sys_params["status"])
        derunner_start_path = os.path.join(USER_PATH, derunner_sys_params["project_dir"], derunner_sys_params["execs_path"], derunner_sys_params["starter"])
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bat")
            _start_cmd="start /W /B "
            _call = "call "
            _copy = "copy "
            _rm = "del "
            _noecho=" >NUL 2>NUL"
            _log_prefix = "ECHO DeManagerTools.Install - "
            _manage_configs_loop = [
                f"ECHO 0 >{manage_configs_flag_path}\n",
                ":wait4demanager\n",
                f"SET /p fmanager=<{manage_configs_flag_path}\n"
                "IF NOT %fmanager% == 1 GOTO wait4demanager\n"
            ]
            
            # 1 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            _tmp_file_lines += GET_WIN_ADMIN
            
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bash")
            _start_cmd="bash "
            _call=""
            _copy = "cp "
            _rm = "rm -rf "
            _noecho=" &>/dev/nul"
            _log_prefix = "echo DeManagerTools.Install - "
            _manage_configs_loop = [
                f"echo 0 >{manage_configs_flag_path}\n",
                f"fmanager=$(cat {manage_configs_flag_path})\n",
                'while [ "$fmanager" != "1" ]\n',
                "do\n",
                f"\tfmanager=$(cat {manage_configs_flag_path})\n",
                "done\n",
            ]
            
             # 1 - BASH HEADER
            _tmp_file_lines = ["#!/bin/bash\n"]
            
        if isinstance(model_ids, str):
            model_ids = [model_ids]
        if isinstance(model_ids, dict):
            model_ids = list(model_ids.keys())
        if not isinstance(model_ids, list):
            return None
        
        # 2 - Uninstall <- Required Models
        for _model in model_ids:
            if _model in self.services_config["services_params"]:
                _asset_sys_params=self.services_config["services_params"][_model][USER_SYS]
            else:
                _asset_sys_params=self.latest_services_config["services_params"][_model][USER_SYS]

            _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
            _uninstaller_bn = os.path.basename(_asset_uninstaller)
            _tmp_uninstaller = os.path.join(TMP_PATH, f'{int(time.time())}{_uninstaller_bn}')
            if os.path.isfile(_asset_uninstaller):
                _tmp_file_lines += [
                    f"{_log_prefix}Uninstalling '{_model}'...>>{LOG_PATH}\n",
                    f"{_copy}{_asset_uninstaller} {_tmp_uninstaller}\n",
                    f'{_start_cmd}{_tmp_uninstaller} {" ".join(_asset_sys_params["uninstaller_args"] if "uninstaller_args" in _asset_sys_params and _asset_sys_params["uninstaller_args"] else [])}{f" /automatic {USER_PATH}" if USER_SYS=="win" else " -a" if USER_SYS=="lin" else ""}\n',
                    f'{_rm}{_tmp_uninstaller}{_noecho}\n'
                ]
                _steps = l_uninstall_weigth if _steps == None else _steps+l_uninstall_weigth
                _tmp_file_lines.append(f'echo {_steps} > {progress}\n')
                


        # 3 - Download + Uncompress to target folder <- Required Models
        _target_folders = []
        for _count, _model in enumerate(model_ids):
            _asset_params=self.latest_services_config["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            _asset_repo=_asset_params["source_code"]
            _asset_commit=_asset_sys_params["commit"]
            _asset_project_dir = os.path.join(USER_PATH, _asset_sys_params["install_dir"] if "install_dir" in _asset_sys_params else _asset_sys_params["project_dir"])
            _target_folders += [_asset_project_dir]
            _tmp_repo_dwnld_path=os.path.join(TMP_PATH, f"DeRunner_Dwnld_{_count}.zip")
            ## Download Commands
            if USER_SYS == "win":
                _mkdir="mkdir "
                _download_cmd=f'powershell -command "Invoke-WebRequest -Uri {_asset_repo}/archive/{_asset_commit}.zip -OutFile {_tmp_repo_dwnld_path} -erroraction \'silentlycontinue\'"{_noecho}\n'
                _uncompress_cmd=f'tar -xzvf {_tmp_repo_dwnld_path} -C {_asset_project_dir} --strip-components 1{_noecho}\n'
            elif USER_SYS=="lin":
                _mkdir="mkdir -p "
                _download_cmd=f'wget {_asset_repo}/archive/{_asset_commit}.zip -O {_tmp_repo_dwnld_path}{_noecho}\n'
                _uncompress_cmd=f'apt install libarchive-tools -y && bsdtar -xzvf {_tmp_repo_dwnld_path} -C {_asset_project_dir} --strip-components=1{_noecho}\n'
            _tmp_file_lines += [
                "echo Download InFo:\n",
                f"echo         Model ID: {_model}\n",
                f"echo     Model Source: {_asset_repo}\n",
                f"echo     Model Commit: {_asset_commit}\n",
                f"{_log_prefix}Downlading '{_model}'... >>{LOG_PATH}\n",
                f"{_mkdir}{_asset_project_dir}{_noecho}\n", # Create Asset Folder
                _download_cmd,
                "echo Uncompressing Project to target folder:\n",
                f"echo     {_asset_project_dir}\n",
                _uncompress_cmd,
                f'{_rm}{_tmp_repo_dwnld_path}{_noecho}\n'
            ]
            _steps = l_download_weigth if _steps == None else _steps+l_download_weigth
            _tmp_file_lines.append(f'echo {_steps} > {progress}\n')


        # 4 - Setup <- Required Models
        for _model in model_ids:
            _asset_sys_params=self.latest_services_config["services_params"][_model][USER_SYS]
            _asset_setup = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["setup"])
            _tmp_file_lines += [
                f"{_log_prefix}Installing '{_model}'... >>{LOG_PATH}\n",
                f'{_start_cmd}{_asset_setup} {" ".join(_asset_sys_params["setup_args"] if "setup_args" in _asset_sys_params and _asset_sys_params["setup_args"] else [])}\n'
            ]
            _tmp_file_lines.append(f'echo {_model} >> {asset_sucess_path}\n')
            _steps = l_setup_weigth if _steps == None else _steps+l_setup_weigth
            _tmp_file_lines.append(f'echo {_steps} > {progress}\n')

        # 5 - Start `run_constantly` Models <- Required Models
        for _model in model_ids:
            if _model == "desotaai/derunner":
                continue
            _asset_params=self.latest_services_config["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            if _asset_params["run_constantly"]:
                _asset_start = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
                _tmp_file_lines += [
                    f"{_log_prefix}Starting '{_model}'... >>{LOG_PATH}\n",
                    f'{_start_cmd}{_asset_start}\n'
                ]
                _steps = l_start__weigth if _steps == None else _steps+l_start__weigth
                _tmp_file_lines.append(f'echo {_steps} > {progress}\n')

        
        #     Update user.config model && services.config model
        #     Everything relies on what is writen into `asset_sucess_path`
        open(asset_sucess_path, "w").close # Clean
        _tmp_file_lines += _manage_configs_loop
        
        # Force DeRunner Restart
        f"{_log_prefix}Restarting DeRunner... >>{LOG_PATH}\n",
        if USER_SYS == "win":
            _tmp_file_lines += [
                f' IF NOT EXIST {derunner_start_path} GOTO noderunnerstart\n',
                f'{_start_cmd}{derunner_start_path}\n',
                ":noderunnerstart\n"
            ]
        elif USER_SYS == "lin":
            _tmp_file_lines += [
                f'if [ -f "{derunner_start_path}" ]; then\n',
                f'\t{_start_cmd}{derunner_start_path}\n',
                "fi\n"
            ]
        _steps = l_start__weigth if _steps == None else _steps+l_start__weigth
        _tmp_file_lines.append(f'echo {_steps} > {progress}\n')

        if USER_SYS == "lin":
            _target_folders += [
                TMP_PATH,
                LOG_PATH,
                CONFIG_FOLDER
            ]
            [ _tmp_file_lines.append(f'chown -R {USER} {_path}\n') for _path in _target_folders]

        ## END OF FILE
        _tmp_file_lines.append('exit 0\n')


        # 6 - Create Installer Bat
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        return target_path, _steps

    def create_uninstall_script(self, model_ids, manage_configs_flag_path) -> str:
        '''
        Create models uninstalation script

        return sript path
        '''
        # Before anything else:
        # 1 - Remove models from user configs
        self.edit_user_configs("models", model_ids, uninstall=True)
        # 2 - TODO: Check if DeRunner is running any of the requested models
        # 1 - INIT + Scripts HEADER
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_uninstall{int(time.time())}.bat")
            _start_cmd="start /W /B "
            _copy = "copy "
            _rm = "del "
            _noecho=" >NUL 2>NUL"
            _log_prefix = "ECHO DeManagerTools.Uninstall - "
            _manage_configs_loop = [
                f"ECHO 0 >{manage_configs_flag_path}\n",
                ":wait4demanager\n",
                f"SET /p fmanager=<{manage_configs_flag_path}\n"
                "IF NOT %fmanager% == 1 GOTO wait4demanager\n"
            ]
            
            # 1 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            _tmp_file_lines += GET_WIN_ADMIN
            
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_uninstall{int(time.time())}.bash")
            _start_cmd="bash "
            _copy = "cp "
            _rm = "rm -rf "
            _noecho=" &>/dev/nul"
            _log_prefix = "echo DeManagerTools.Uninstall - "
            _manage_configs_loop = [
                f"echo 0 >{manage_configs_flag_path}\n",
                f"fmanager=$(cat {manage_configs_flag_path})\n",
                'while [ "$fmanager" != "1" ]\n',
                "do\n",
                f"\tfmanager=$(cat {manage_configs_flag_path})\n",
                "done\n",
            ]

            # 1 - BASH HEADER
            _tmp_file_lines = ["#!/bin/bash\n"]
            

        if isinstance(model_ids, str):
            model_ids = [model_ids]
        if isinstance(model_ids, dict):
            model_ids = list(model_ids.keys())
        if not isinstance(model_ids, list):
            return None
        
        # 2 - Uninstall <- Required Models
        for _model in model_ids:
            if _model in self.services_config["services_params"]:
                _asset_sys_params=self.services_config["services_params"][_model][USER_SYS]
            else:
                _asset_sys_params=self.latest_services_config["services_params"][_model][USER_SYS]

            _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
            _uninstaller_bn = os.path.basename(_asset_uninstaller)
            _tmp_uninstaller = os.path.join(TMP_PATH, f'{int(time.time())}{_uninstaller_bn}')
            if os.path.isfile(_asset_uninstaller):
                _tmp_file_lines += [
                    f"{_log_prefix}Uninstalling '{_model}'...>>{LOG_PATH}\n",
                    f"{_copy}{_asset_uninstaller} {_tmp_uninstaller}\n",
                    f'{_start_cmd}{_tmp_uninstaller} {" ".join(_asset_sys_params["uninstaller_args"] if "uninstaller_args" in _asset_sys_params and _asset_sys_params["uninstaller_args"] else [])}{f" /automatic {USER_PATH}" if USER_SYS=="win" else " -a" if USER_SYS=="lin" else ""}\n',
                    f'{_rm}{_tmp_uninstaller}{_noecho}\n'
                ]

        #     Update user.config model && services.config model
        _tmp_file_lines += _manage_configs_loop
        
        if USER_SYS == "lin":
            _target_folders = [
                TMP_PATH,
                LOG_PATH,
                CONFIG_FOLDER
            ]
            [ _tmp_file_lines.append(f'chown -R {USER} {_path}\n') for _path in _target_folders]

        ## END OF FILE
        _tmp_file_lines.append('exit 0\n')
        
        # 6 - Create Uninstaller Script
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        return target_path

    def create_startstop_script(self, model_ids, state) -> str:
        '''
        Create models start|stop script

        state argument [bool]:

            False = Stop

            True = Start

        return sript path
        '''
        
        # 1 - INIT + Scripts HEADER
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bat")
            _start_cmd="start /W /B "
            _log_prefix = "ECHO DeManagerTools." + "Stop" if not state else "Start" +  " - "
            # 1 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            _tmp_file_lines += GET_WIN_ADMIN
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bash")
            _start_cmd="bash "
            _log_prefix = "echo DeManagerTools." + "Stop" if not state else "Start" +  " - "
            # 1 - BASH HEADER
            _tmp_file_lines = ["#!/bin/bash\n"]

        if isinstance(model_ids, str):
            model_ids = [model_ids]
        if isinstance(model_ids, dict):
            model_ids = list(model_ids.keys())
        if not isinstance(model_ids, list):
            return None
        
        # 2 - Start|Stop <- Required Models
        for _model in model_ids:
            _asset_sys_params=self.services_config["services_params"][_model][USER_SYS]
            if state:
                _log="Starting"
                _asset_state = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
            else:
                _log="Stoping"
                _asset_state = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["stoper"])

            if os.path.isfile(_asset_state):
                _tmp_file_lines += [
                    f"{_log_prefix}{_log} '{_model}'...>>{LOG_PATH}\n",
                    f'{_start_cmd}{_asset_state}\n',
                ]
        if USER_SYS == "lin":
            _target_folders += [
                TMP_PATH,
                LOG_PATH
            ]
            [ _tmp_file_lines.append(f'chown -R {USER} {_path}\n') for _path in _target_folders]

        ## END OF FILE - Delete Bat at end of instalation 
        ### WINDOWS - retrieved from https://stackoverflow.com/a/20333152
        ### LINUX   - ...
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n'if USER_SYS == "win" else f'rm -rf {target_path}\n' if USER_SYS == "lin" else "")

        # 6 - Create Start|Stop Script
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        return target_path

    def create_dmt_lauch_script(self, launch_res_path, dmt_exe) -> str:
        '''
        Required only for Linux - gnome-terminal
        '''
        _time = int(time.time())
        target_path=os.path.join(TMP_PATH, f"dmt_start_wait{_time}.bash")
        dmt_launch_template_path = os.path.join(EXECS_PATH, "launch_template.bash")
        dmt_exe_dir = os.path.dirname(dmt_exe)
        
        ## DEBUG
        debub_path=os.path.join(TMP_PATH, f"UPG_DEBUG{_time}.txt")
        ## DEBUG

        # Read Template
        with open(dmt_launch_template_path, "r") as fr:
            dmt_launch = fr.read()
        # Construct DMT upgrade script from template
        _translate_dic={
            "__exe_dir__": dmt_exe_dir,
            "__exe_path__": dmt_exe,
            "__launch_flag__": launch_res_path,
            "__debug__": debub_path
        }
        for k, v in _translate_dic.items():
            dmt_launch = dmt_launch.replace(k, v)

        with open(target_path, "w") as fw:
            fw.write(dmt_launch)
            
        return target_path
    def create_dmp_upgrade_script(self, confirm=False) -> str:
        '''
        Create DeManagerTools Upgrade script

        `confirm` : Shortwire User Confirm Upgrade 

        Returns script path
        '''
        _time=int(time.time())
        # Retrieve Identity
        whoami=None
        if os.path.isfile(WHOAMI_PATH):
            with open(WHOAMI_PATH) as fr:
                try:
                    whoami=json.load(fr)
                except:
                    pass
        if not whoami:
            whoami = {
                "version": "0.0.3",
                "developer":"Francisco Vargas",
                "github":"https://github.com/desotaai/demanagertools/",
                "platform":"https://desota.net/"
            }
            with open(WHOAMI_PATH, "w") as fw:
                json.dump(whoami, fw, indent=2)

        #Compare Version with latest manager params
        manager_sys_params = self.latest_services_config["manager_params"][USER_SYS]
        latest_version = manager_sys_params["version"]
        if whoami["version"] != latest_version:
            # Confirm User Wants to upgrade:
            if not confirm:
                _app_upgrade = psg.popup_yes_no(
                    f"New release of the `DeSOTA - Manager Tools` is available!\nCurrent version: {whoami['version']}\nLatest version : {latest_version}\nDescription: {manager_sys_params['release_desc']}\n\nProceed with upgrade?",
                    title="DeSOTA - Manager Tools",
                    icon=self.icon,
                )
                if _app_upgrade != "Yes":
                    return None

            # System VARS
            tmp_zip_download = os.path.join(TMP_PATH, f"upgrade_dmt_v{latest_version}_{_time}.zip")
            dmt_exe_dir = os.path.join(APP_PATH, "dist")
            if USER_SYS == "win":
                dmt_upgrade_template_path = os.path.join(EXECS_PATH, "update.template.bat")
                dmt_upgrade_target = os.path.join(TMP_PATH, f"upgrade_dmt_v{latest_version}_{_time}.bat")
                dmt_exe_path = os.path.join(dmt_exe_dir,  '"Desota - Manager Tools.exe"')
                dmt_launch_flag_path=None
            elif USER_SYS == "lin":
                dmt_upgrade_template_path = os.path.join(EXECS_PATH, "update.template.bash")
                dmt_upgrade_target = os.path.join(TMP_PATH, f"upgrade_dmt_v{latest_version}_{_time}.bash")
                dmt_exe_path = os.path.join(dmt_exe_dir,  '"Desota - Manager Tools"')
                dmt_launch_flag_path = os.path.join(TMP_PATH, f"dmt_lauch_wait_flag{_time}.txt")
                dmt_launch_path=self.create_dmt_lauch_script(dmt_launch_flag_path, dmt_exe_path)
                pid=os.fork()
                if pid==0: # new process
                    os.system(f'timeout 90s bash -c "/bin/bash {dmt_launch_path}" && rm -rf {dmt_launch_path}')
                    exit()
            
            # Read Template
            with open(dmt_upgrade_template_path, "r") as fr:
                dmt_upgrade = fr.read()
            # Construct DMT upgrade script from template
            _backup_path = os.path.join(TMP_PATH, f"dmt_bckup{_time}")
            _translate_dic={
                "__program_dir__": APP_PATH,
                "__backup_dir__": _backup_path,
                "__program_exe__": dmt_exe_path,
                "__download_url__": manager_sys_params["build_url"],
                "__tmp_compress_file__": tmp_zip_download,
                "__version__": latest_version,
                "__demanager_log__": LOG_PATH,
                "__upgrade_path__": dmt_upgrade_target,
                "__user__": USER, # only required for linux
                "__launch_flag__": dmt_launch_flag_path # only required for linux
            }
            for k, v in _translate_dic.items():
                if not v:
                    continue
                dmt_upgrade = dmt_upgrade.replace(k, v)
            with open(dmt_upgrade_target, "w") as fw:
                fw.write(dmt_upgrade)
            
            return dmt_upgrade_target
        
        return None
    

    #   > Grab User Configurations
    def get_user_config(self) -> dict:
        if not os.path.isfile(USER_CONFIG_PATH):
            _template_user_conf={
                "user_api": None,
                "models":None,
                "system": USER_SYS
            }
            with open(USER_CONFIG_PATH, 'w',) as fw:
                yaml.dump(_template_user_conf,fw,sort_keys=False)
            self.user_chown(USER_CONFIG_PATH)
            return _template_user_conf
        with open( USER_CONFIG_PATH ) as f_user:
            return yaml.load(f_user, Loader=SafeLoader)
    
    #   > Return latest_services.config.yaml(write if not ignore_update)
    def get_services_config(self, ignore_update=False) -> (dict, dict):
        _req_res = None
        if not ignore_update:
            _req_res = requests.get(LATEST_SERV_CONF_RAW)
        if ignore_update or ( isinstance(_req_res, requests.Response) and _req_res.status_code != 200 ):
            if not (os.path.isfile(SERVICES_CONFIG_PATH) or os.path.isfile(LAST_SERVICES_CONFIG_PATH)):
                print(f" [SERV_CONF] Not found-> {SERVICES_CONFIG_PATH}")
                print(f" [LAST_SERV_CONF] Not found-> {LAST_SERVICES_CONFIG_PATH}")
                raise EnvironmentError()
            else:
                with open( SERVICES_CONFIG_PATH ) as f_curr:
                    with open(LAST_SERVICES_CONFIG_PATH) as f_last:
                        return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
                    
        # Create Latest Services Config File
        with open(LAST_SERVICES_CONFIG_PATH, "w") as fw:
            fw.write(_req_res.text)
        self.user_chown(LAST_SERVICES_CONFIG_PATH)

        # Create Services Config File if don't exist
        if not os.path.isfile(SERVICES_CONFIG_PATH):
            with open(LAST_SERVICES_CONFIG_PATH) as fls:
                _template_serv=yaml.load(fls, Loader=SafeLoader)
             
            _user_models = self.get_user_config()["models"]
            _user_serv_params = {}
            if _user_models:
                for _model in _user_models:
                    _params = _template_serv["services_params"][_model]
                    _user_serv_params[_model] = _params
                    if "child_models" in _params and _params["child_models"]:
                        for _child in  _params["child_models"]:
                            if _child in _template_serv["services_params"]:
                                _user_serv_params[_child] = _template_serv["services_params"][_child]

            _template_serv["services_params"] = _user_serv_params
            with open(SERVICES_CONFIG_PATH, "w") as fw:
                yaml.dump(_template_serv,fw,sort_keys=False)
            self.user_chown(SERVICES_CONFIG_PATH)

        with open( SERVICES_CONFIG_PATH ) as f_curr:
            with open(LAST_SERVICES_CONFIG_PATH) as f_last:
                return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
    
    #   > Return parsed tools_services {"service":"required", ...}
    def get_tools_services(self) -> dict:
        _tools_services = {}
        for service, params in self.latest_services_config["services_params"].items():
            if not params["submodel"] and params["service_type"] == "tool":
                _tools_services[service] = params["required"]
        return _tools_services
    
    # Edit User Configs
    def edit_user_configs(self, key, value, uninstall=False):
        user_config = self.get_user_config()

        # param "models" consist of the name of the model as key and is version as value
        if key == "models":
            # Get allready installed models
            _old_models = user_config["models"]
            # Instatiate result models
            if _old_models:
                _res_models = dict(_old_models)
            else:
                _res_models = {}

            # Uninstall FLAG
            if uninstall:
                if _res_models:
                    if isinstance(value, str):
                        _rem_models = [value]
                    else:
                        _rem_models = value
                    for _model in _rem_models:
                        if _model in _res_models:
                            _res_models.pop(_model)
            else:
                _new_models = value
                for _model, _version in _new_models.items():
                    if _model in _res_models:
                        if _res_models[_model] == _version:
                            continue
                        _res_models[_model] = _version
                        continue
                    _res_models.update({_model:_version})

            # Update user_config `models`
            user_config[key] = _res_models
        else:
            user_config[key] = value
        
        with open(USER_CONFIG_PATH, 'w',) as fw:
            yaml.dump(user_config,fw,sort_keys=False)
    
    # Edit Services Configs
    def upd_services_params(self):
        '''
        Update Services Config with params from Latest Services Config
        
        Updates based on User Config Models, so, edit it before calling this funk
        '''
        _res_serv_conf, _ = self.get_services_config(ignore_update=True)
        _res_serv_conf["services_params"]={}
        
        _user_models = self.get_user_config()["models"]
        for model_id, model_v in _user_models.items():
            _last_service_params = self.latest_services_config["services_params"]
            if _last_service_params[model_id][USER_SYS]["version"] == model_v or model_id not in _res_serv_conf["services_params"]:
                _res_serv_conf["services_params"][model_id] = _last_service_params[model_id]
            if "child_models" in _res_serv_conf["services_params"][model_id] and _res_serv_conf["services_params"][model_id]["child_models"]:
                for child in _res_serv_conf["services_params"][model_id]["child_models"]:
                    if child in _last_service_params:
                        _res_serv_conf["services_params"][child] = _last_service_params[child]

        with open(SERVICES_CONFIG_PATH, 'w',) as fw:
            yaml.dump(_res_serv_conf,fw,sort_keys=False)

        return


    # TAB Constructors
    # TAB 1 - Models Dashboard
    def get_tools_data(self, search_filter=None):
        _tools_data = []
        _tools = []
        for _k, _v in self.user_config['models'].items():
            if _k not in self.tools_services:
                continue
            _tool_params = self.services_config["services_params"][_k]
            _tool_sys_params = _tool_params[USER_SYS]
            _tool_desc = _tool_params["short_description"]
            _tool_status_path = os.path.join(USER_PATH, _tool_sys_params["project_dir"], _tool_sys_params["execs_path"], _tool_sys_params["status"]) if _tool_sys_params["status"] else None

            if _tool_status_path==None:
                _tool_status = "-"
            else:
                _tool_status = self.get_service_status(_tool_status_path).lower()
                _tool_status = "-" if _tool_status==None else _tool_status

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
            _model_params = self.services_config["services_params"][_k]
            _model_sys_params = _model_params[USER_SYS]
            _model_desc = _model_params["short_description"]
            _model_status_path = os.path.join(USER_PATH, _model_sys_params["project_dir"], _model_sys_params["execs_path"], _model_sys_params["status"]) if "status" in _model_sys_params and _model_sys_params["status"] else None
            if _model_status_path==None:
                _model_status = "-"
            else:
                _model_status = self.get_service_status(_model_status_path).lower()
                _model_status = "-" if _model_status==None else _model_status

            if search_filter:
                if search_filter.lower() in _k.lower() or search_filter.lower() in _model_desc.lower():
                    _models_data.append([_k, _model_status, _model_desc])
                    _models.append(_k)
            else:
                _models_data.append([_k, _model_status, _model_desc])
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
            
            ## DeRunner Logger
            if self.exist_log:
                self.exist_derunner = True
                return [
                    [psg.Input("Search", key='searchDash', expand_x=True)],
                    [psg.Text('DeSOTA  Log ▲', tooltip="live log of models requests", key="derunner_log_head", enable_events=True, font=self.title_f)],
                    [psg.Multiline(size=(None, 8), reroute_cprint=True, key='derunner_log', expand_x=True, expand_y=False, visible=False), psg.Text('', key="derunner_log_clear", visible=True)],
                    [psg.Column(_dashboard_layout, size=(800, 238), scrollable=True, key="_SCROLL_COL1_")],
                    [
                        psg.Button('Take a Peek', button_color=("Green","White"), key="openModelUI", pad=(5, 0)), 
                        psg.Button('Source Code', button_color=("Blue","White"), key="openSource", pad=(5, 0)),
                        psg.Button('Stop Manual Services', button_color=("Orange","White"), key="stopManualServices", disabled=_disabled,pad=(5, 0)),
                        psg.Button('Uninstall', button_color=("Red","White"), key="startUninstall", pad=(5, 0))
                    ]
                ]
            else:
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
                    "key": key,
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
        '''Available Uninstalled Tools'''
        _install_tools = []
        _req_services_header = False
        if get_layout:
            _at_header_event = self.create_elem_key('install_header_at', ("at", 0))
        else:
            if "0" in self.install_configs["at"] and "install_header_at" in self.install_configs["at"]["0"]:
                _at_header_event = self.install_configs["at"]["0"]["install_header_at"]["key"]
            else:
                return _install_tools       
             
        for count, (_desota_serv, _cb_disabled) in enumerate(self.tools_services.items()):
            if not self.user_config['models'] or _desota_serv not in self.user_config['models']:
                _platform_params = self.latest_services_config["services_params"][_desota_serv][USER_SYS]
                if not "commit" in _platform_params or not _platform_params["commit"]:
                    continue
                _commit = self.latest_services_config["services_params"][_desota_serv][USER_SYS]
                _desc = self.latest_services_config["services_params"][_desota_serv]["short_description"]
                _source = self.latest_services_config["services_params"][_desota_serv]["source_code"]
                
                if not search_filter or (search_filter.lower() in _desota_serv.lower() or search_filter.lower() in _desc.lower()):
                    if get_layout:
                        _at_serv_event = self.create_elem_key(f"SERVICE {_desota_serv}", ("at", count))
                        _at_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("at", count))
                        _at_desc1_event = self.create_elem_key('install_desc_head_at', ("at", count))
                        _at_desc2_event = self.create_elem_key('install_desc_body_at', ("at", count))
                    else:
                        _at_serv_event = self.install_configs["at"][str(count)]["SERVICE"]["key"]
                        _at_req_event = self.install_configs["at"][str(count)]["WEBREQUEST"]["key"]
                        _at_desc1_event = self.install_configs["at"][str(count)]["install_desc_head_at"]["key"]
                        _at_desc2_event = self.install_configs["at"][str(count)]["install_desc_body_at"]["key"]


                    if not _req_services_header:
                        _req_services_header = True
                        if get_layout:
                            _install_tools.append([
                                psg.Text(
                                    'Available Tools', 
                                    font=self.header_f, 
                                    key=_at_header_event, 
                                    visible=self.set_elem_vis(_at_header_event, ("at", 0), True)
                                )   
                            ])
                        else:
                            self.set_elem_vis(_at_header_event, ("at", 0), True)
                    if get_layout:
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
                        self.set_elem_vis([_at_serv_event, _at_req_event, _at_desc1_event, _at_desc2_event], ("at", count), True)
                else:
                    _at_serv_event = self.install_configs["at"][str(count)]["SERVICE"]["key"]
                    _at_req_event = self.install_configs["at"][str(count)]["WEBREQUEST"]["key"]
                    _at_desc1_event = self.install_configs["at"][str(count)]["install_desc_head_at"]["key"]
                    _at_desc2_event = self.install_configs["at"][str(count)]["install_desc_body_at"]["key"]
                    self.set_elem_vis([_at_serv_event, _at_req_event, _at_desc1_event, _at_desc2_event], ("at", count), False)

        if not _req_services_header:
            if _at_header_event in self.created_elems and get_layout:
                self.created_elems.pop(_at_header_event)

            if not get_layout:
                self.set_elem_vis(_at_header_event, ("at", 0), False)

        if not get_layout:
            return True if _req_services_header else False
        return _install_tools
    def get_upgrade_models(self, get_layout=True, search_filter=None):
        '''Upgradable Models / Tools'''
        _upgrade_models = []
        _upgrade_models_header = False

        if get_layout:
            _up_header_event = self.create_elem_key('install_header_up', ("up", 0))
        else:
            if "0" in self.install_configs["up"] and "install_header_up" in self.install_configs["up"]["0"]:
                _up_header_event = self.install_configs["up"]["0"]["install_header_up"]["key"]
            else:
                return _upgrade_models       

        for count, (_serv, _params) in enumerate(self.latest_services_config['services_params'].items()):
            if _params["submodel"] == True:
                continue
            _latest_model_version = _params[USER_SYS]['version']

            if self.user_config['models'] and _serv in self.user_config['models'] and self.user_config['models'][_serv] != _latest_model_version:
                _desc = self.latest_services_config["services_params"][_serv]["short_description"]
                _source = self.latest_services_config["services_params"][_serv]["source_code"]
                if not search_filter or (search_filter.lower() in _serv.lower() or search_filter.lower() in _desc.lower()):
                    if get_layout:
                        _up_upg_event = self.create_elem_key(f"SERVICE {_serv}", ("up", count))
                        _up_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("up", count))
                        _up_desc1_event = self.create_elem_key('install_desc_head_up', ("up", count))
                        _up_desc2_event = self.create_elem_key('install_desc_body_up', ("up", count))
                    else:
                        _up_upg_event = self.install_configs["up"][str(count)]["SERVICE"]["key"]
                        _up_req_event = self.install_configs["up"][str(count)]["WEBREQUEST"]["key"]
                        _up_desc1_event = self.install_configs["up"][str(count)]["install_desc_head_up"]["key"]
                        _up_desc2_event = self.install_configs["up"][str(count)]["install_desc_body_up"]["key"]


                    if not _upgrade_models_header:
                        _upgrade_models_header = True
                        if get_layout:
                            _upgrade_models.append([
                                psg.Text('Availabe Upgrades', 
                                        font=self.header_f, 
                                        key=_up_header_event, 
                                        visible=self.set_elem_vis(_up_header_event, ("up", 0), True)
                                )
                            ])
                        else:
                            self.set_elem_vis(_up_header_event, ("up", 0), True)
                    
                    if get_layout:
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
                        self.set_elem_vis([_up_upg_event, _up_req_event, _up_desc1_event, _up_desc2_event], ("up", count), True)
                else:
                    _up_upg_event = self.install_configs["up"][str(count)]["SERVICE"]["key"]
                    _up_req_event = self.install_configs["up"][str(count)]["WEBREQUEST"]["key"]
                    _up_desc1_event = self.install_configs["up"][str(count)]["install_desc_head_up"]["key"]
                    _up_desc2_event = self.install_configs["up"][str(count)]["install_desc_body_up"]["key"]
                    self.set_elem_vis([_up_upg_event, _up_req_event, _up_desc1_event, _up_desc2_event], ("up", count), False)
        
        if not _upgrade_models_header:
            if _up_header_event in self.created_elems and get_layout:
                self.created_elems.pop(_up_header_event)

            if not get_layout:
                self.set_elem_vis(_up_header_event, ("up", 0), False)

        if not get_layout:
            return True if _upgrade_models_header else False
        return _upgrade_models
    def get_install_models(self, get_layout=True, search_filter=None):
        '''Available Uninstalled Models'''
        _install_models = []
        _available_models_header = False
        
        if get_layout:
            _am_header_event = self.create_elem_key('install_header_am', ("am", 0))
        else:
            if "0" in self.install_configs["am"] and "install_header_am" in self.install_configs["am"]["0"]:
                _am_header_event = self.install_configs["am"]["0"]["install_header_am"]["key"]
            else:
                return _install_models  

        for count, (_k, _v)in enumerate(self.latest_services_config['services_params'].items()):
            if (self.user_config['models'] and _k in self.user_config['models'] ) or (_v["submodel"] == True) or (_k in self.tools_services):
                continue
            _platform_params = self.latest_services_config["services_params"][_k][USER_SYS]
            if not "commit" in _platform_params or not _platform_params["commit"]:
                continue
            _desc = self.latest_services_config["services_params"][_k]["short_description"]
            _source = self.latest_services_config["services_params"][_k]["source_code"]

            if not search_filter or (search_filter.lower() in _k.lower() or search_filter.lower() in _desc.lower()):
                if get_layout:
                    _am_serv_event = self.create_elem_key(f"SERVICE {_k}", ("am", count))
                    _am_req_event = self.create_elem_key(f'WEBREQUEST {_source}', ("am", count))
                    _am_desc1_event = self.create_elem_key('install_desc_head_am', ("am", count))
                    _am_desc2_event = self.create_elem_key('install_desc_body_am', ("am", count))
                else:
                    _am_serv_event = self.install_configs["am"][str(count)]["SERVICE"]["key"]
                    _am_req_event = self.install_configs["am"][str(count)]["WEBREQUEST"]["key"]
                    _am_desc1_event = self.install_configs["am"][str(count)]["install_desc_head_am"]["key"]
                    _am_desc2_event = self.install_configs["am"][str(count)]["install_desc_body_am"]["key"]


                if not _available_models_header:
                    _available_models_header = True
                    if get_layout:
                        _install_models.append([
                            psg.Text(
                                'Available AI Models', 
                                font=self.header_f, 
                                key=_am_header_event, 
                                visible=self.set_elem_vis(_am_header_event, ("am", 0), True)
                            )
                        ])
                    else:
                        self.set_elem_vis(_am_header_event, ("am", 0), True)
                
                if get_layout:
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
                    self.set_elem_vis([_am_serv_event, _am_req_event, _am_desc1_event, _am_desc2_event], ("am", count), True)
            else:
                _am_serv_event = self.install_configs["am"][str(count)]["SERVICE"]["key"]
                _am_req_event = self.install_configs["am"][str(count)]["WEBREQUEST"]["key"]
                _am_desc1_event = self.install_configs["am"][str(count)]["install_desc_head_am"]["key"]
                _am_desc2_event = self.install_configs["am"][str(count)]["install_desc_body_am"]["key"]
                self.set_elem_vis([_am_serv_event, _am_req_event, _am_desc1_event, _am_desc2_event], ("am", count), False)

        if not _available_models_header:
            if _am_header_event in self.created_elems and get_layout:
                self.created_elems.pop(_am_header_event)
            if not get_layout:
                self.set_elem_vis(_am_header_event, ("am", 0), False)
        
        if not get_layout:
            return True if _available_models_header else False
        return _install_models
    
    def get_install_layout(self, get_layout=False, search_filter=None):
        '''
        GET LAYOUT ONLY ON CLASS INIT!!! > self.construct_install_tab
        '''
        _install_layout = []
        # Available Uninstalled Tools
        _install_tools = self.get_install_tools(get_layout=get_layout, search_filter=search_filter)
        
        if _install_tools:
            if get_layout:
                _install_layout += _install_tools
                self.exist_at_sep = True
                self.at_separator = self.create_elem_key('install_separator_at_up', ("at", 0))
                _install_layout.append([psg.Text('_'*80, pad=(0, 20), key=self.at_separator, visible=self.set_elem_vis(self.at_separator, ("at", 0), True))])
            else:
                self.set_elem_vis(self.at_separator, ("at", 0), True)
        elif self.exist_at_sep:
            self.set_elem_vis(self.at_separator, ("at", 0), False)

        # Upgradable Models / Tools
        _upgrade_models = self.get_upgrade_models(get_layout=get_layout, search_filter=search_filter)
        if _upgrade_models:
            if get_layout:
                _install_layout += _upgrade_models
                self.exist_up_sep = True
                self.up_separator = self.create_elem_key('install_separator_up_am', ("up", 0))
                _install_layout.append([psg.Text('_'*80, pad=(0, 20), key=self.up_separator, visible=self.set_elem_vis(self.up_separator, ("up", 0), True))])
            else:
                self.set_elem_vis(self.up_separator, ("up", 0), True)
        elif self.exist_up_sep:
            self.set_elem_vis(self.up_separator, ("up", 0), False)


        # Available Uninstalled Models
        _install_models = self.get_install_models(get_layout=get_layout, search_filter=search_filter)
        if _install_models:
            if get_layout:
                _install_layout += _install_models
        
        # if DEBUG:
        if get_layout:
            return _install_layout
    def construct_install_tab(self):
        _install_layout = self.get_install_layout(get_layout=True)
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
        _time = int(time.time())
        for _k, _v in values.items():
            if isinstance(_k, str) and "SERVICE" in _k and _v:
                _models_2_install.append(_k.split(' ')[1].strip())
            if isinstance(_k, str) and "UPGRADE" in _k and _v:
                _models_2_upgrade.append(_k.split(' ')[1].strip())
        _models_2_upgrade += _models_2_install
        print(f" [ DEBUG ] -> Models to install = {_models_2_upgrade} ")

        if not _models_2_upgrade:
            return "-ignore-"
                
        _ok_res = psg.popup_ok(f"You will install the following models: {json.dumps(_models_2_upgrade, indent=4)}\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            return "-ignore-"
        
        _install_prog_file = os.path.join(TMP_PATH, "install_progress.txt")
        _wait_path=os.path.join(TMP_PATH, f"{_time}install_waiter.txt")
        _sucess_path=os.path.join(TMP_PATH, f"{_time}install_result.txt")
        _install_script_path, _install_steps = self.create_install_script(_models_2_upgrade, _wait_path, _sucess_path, progress=_install_prog_file)
        if not os.path.isfile(_install_script_path):
            return "-ignore-"

        if USER_SYS == "win":
            tmp_install_script=None
            _child_proc = subprocess.Popen([_install_script_path])

        if USER_SYS == "lin":
            tmp_install_script= os.path.join(TMP_PATH, f"delete{int(time.time())}.bat")
            with open(tmp_install_script, "w") as fw:
                fw.writelines([
                    "#!/bin/bash\n",
                    f'gnome-terminal --wait -- bash -c "pkexec /bin/bash {_install_script_path}"\n',
                    f"exit 0"
                ])
            _child_proc = subprocess.Popen(['bash', tmp_install_script])
            
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
                
            _curr_prog = (_curr_prog_file/_install_steps) * 100
            self.root['installPBAR'].update(current_count=_curr_prog)
            
            if os.path.isfile(_wait_path):
                with open(_wait_path, "r") as fr:
                    _wait_state_read = fr.read().replace("\n", "").strip()
                if _wait_state_read == "0":
                    with open(_sucess_path, "r") as fr:
                        _install_res = fr.read().splitlines()
                    if _install_res:
                        # Create dict with model, version pairs
                        _install_conf= {}
                        for _line in _install_res:
                            _model=_line.strip()
                            # if _model in self.latest_services_config["services_params"]:
                            _new_version = self.latest_services_config["services_params"][_model][USER_SYS]["version"]
                            _install_conf[_model] = _new_version
                            print("NEW USER MODELS:")
                            print("    Model:", _model)
                            print("  Version:", _new_version)
                        if _install_conf:
                            self.edit_user_configs("models", _install_conf)
                            self.upd_services_params()
                    try:
                        with open(_wait_path, "w") as fw:
                            fw.write("1")
                    except:
                        if os.path.isfile(_wait_path):
                            os.remove(_wait_path)
                        with open(_wait_path, "w") as fw:
                            fw.write("1")

            if _child_proc.poll() == 0:
                for _file in [_install_prog_file, _wait_path, _sucess_path, tmp_install_script]:
                    if not _file:
                        continue
                    if os.path.isfile(_file):
                        os.remove(_file)
                break
                
            _ml_res = self.main_loop(ignore_event=[], timeout=50)
            #TODO : 
            # if _ml_res == "-close-"
            # if _ml_res == "-restart-"
            # if _ml_res == "-ignore-"
            
        _ok_res = psg.popup_ok(f"Instalation Completed!\n\nThe APP will restart!\n\nPress Ok to proceed", title="", icon=self.icon)
        if not _ok_res:
            return "-ignore-"
        return "-restart-"

    # - Tool Table row selected
    def tool_table_row_selected(self, values):
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
            
            if _last_serv_conf["services_params"] == self.latest_services_config["services_params"]:
                psg.popup("You are currently up to date!\n", title="", icon=self.icon)
                return "-ignore-"

            self.services_config, self.latest_services_config = _curr_serv_conf, _last_serv_conf

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
        _model_params = self.services_config["services_params"][model_name]
        _model_sys_params = _model_params[USER_SYS]
        if "model_ui" in _model_params and _model_params["model_ui"]:
            _model_ui_url = _model_params["model_ui"]
            _model_req_hs = _model_params["handshake_req"]
            _model_res_hs = _model_params["handshake_res"]

            if _model_params["run_constantly"]:
                try:
                    _hs_req = requests.get(_model_req_hs)
                    if _hs_req.status_code == 200 and _hs_req.json() == _model_res_hs:
                        webbrowser.open(_model_ui_url, autoraise=False)
                        return _res
                except:
                    pass

                #Start Run Constantly Services
                _start_run_constantly_serv_path = os.path.join(USER_PATH, _model_sys_params["project_dir"], _model_sys_params["execs_path"], _model_sys_params["starter"])
                if USER_SYS == "win":
                    _sproc = subprocess.Popen([_start_run_constantly_serv_path])
                elif USER_SYS == "lin":
                    _sproc = subprocess.Popen(["pkexec", "bash", _start_run_constantly_serv_path])

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

                self.set_started_manual_services(_started_manual_services)

                self.root['stopManualServices'].update(disabled=False)
                #Start Service!
                _start_run_constantly_serv_path = os.path.join(USER_PATH, _model_sys_params["project_dir"], _model_sys_params["execs_path"], _model_sys_params["starter"])
                if USER_SYS == "win":
                    _sproc = subprocess.Popen([_start_run_constantly_serv_path])
                elif USER_SYS == "lin":
                    _sproc = subprocess.Popen(["pkexec", "bash", _start_run_constantly_serv_path])

                _res = "-restart-"
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
        
        elif  "model_cli" in _model_params and _model_params["model_cli"]:
            cli_cmd = []
            for mc in _model_params[USER_SYS][_model_params["model_cli"]]:
                # PATH TEST (get files and arguments)
                if not isinstance(mc, str):
                    mc = str(mc)
                _tmp_path = os.path.join(USER_PATH, mc)
                if os.path.isfile(_tmp_path):
                    # Files
                    cli_cmd.append(_tmp_path)
                else:
                    # Arguments
                    cli_cmd.append(mc)
            
            if USER_SYS == "win":
                _sproc = subprocess.Popen(
                    cli_cmd,
                    creationflags = subprocess.CREATE_NEW_CONSOLE
                ).poll()
            else:
                tmp_cli_script= os.path.join(TMP_PATH, f"delete{int(time.time())}.bash")
                cli_cmd_str=" ".join(cli_cmd)
                with open(tmp_cli_script, "w") as fw:
                    fw.writelines([
                        "#!/bin/bash\n",
                        f'gnome-terminal --wait -- bash -c "{cli_cmd_str}; exec bash"\n',
                        f'rm -- "{tmp_cli_script}" & exit 0'
                    ])
                _sproc = subprocess.Popen(
                    ['bash', tmp_cli_script]
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
        _time=int(time.time())
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
            image=os.path.join(APP_PATH, "Assets", "ru-sure-about-that.gif")
        )
        if _str_serv != "Yes":
            return "-ignore-"
        
        # - UNINSTALL CONFIRMED BELLOW
        _wait_path=os.path.join(TMP_PATH, f"{_time}uninstall_waiter.txt")
        _uninstall_script_path = self.create_uninstall_script(_models_2_uninstall, _wait_path)
        if not os.path.isfile(_uninstall_script_path):
            return "-ignore-"
        
        if USER_SYS == "win":
            tmp_uninstall_script = None
            _child_proc = subprocess.Popen([_uninstall_script_path])

        if USER_SYS == "lin":
            tmp_uninstall_script= os.path.join(TMP_PATH, f"delete{int(time.time())}.bat")
            with open(tmp_uninstall_script, "w") as fw:
                fw.writelines([
                    "#!/bin/bash\n",
                    f'gnome-terminal --wait -- bash -c "pkexec /bin/bash {_uninstall_script_path}"\n',
                    f"exit 0\n"
                ])
            _child_proc = subprocess.Popen(['bash', tmp_uninstall_script])
            

        while True:
            if os.path.isfile(_wait_path):
                with open(_wait_path, "r") as fr:
                    _wait_state_read = fr.read().replace("\n", "").strip()
                if _wait_state_read == "0":
                    self.edit_user_configs("models", _models_2_uninstall, uninstall=True)
                    self.upd_services_params()
                    if tmp_uninstall_script and os.path.isfile(tmp_uninstall_script):
                        os.remove(tmp_uninstall_script)

                    try:
                        with open(_wait_path, "w") as fw:
                            fw.write("1")
                    except:
                        if os.path.isfile(_wait_path):
                            os.remove(_wait_path)
                        with open(_wait_path, "w") as fw:
                            fw.write("1")

            if _child_proc.poll() == 0:
                if os.path.isfile(_wait_path):
                    os.remove(_wait_path)
                break
            
            _ml_res = self.main_loop(ignore_event=[], timeout=50)
            #TODO : 
            # if _ml_res == "-close-"
            # if _ml_res == "-restart-"
            # if _ml_res == "-ignore-"

        # self.set_installed_services()
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
        if not _popup_ok:
            return "-ignore-"
        
        if USER_SYS == "win":
            _cmd_prefix=[]
        if USER_SYS == "lin":
            _cmd_prefix=["pkexec", "bash"]
        
        for model in _started_manual_services:
            _model_sys_params = self.services_config["services_params"][model][USER_SYS]
            _stop_model_path = os.path.join(USER_PATH, _model_sys_params["project_dir"], _model_sys_params["execs_path"], _model_sys_params["stoper"])
        
        _stop_model_path = self.create_startstop_script(_started_manual_services, False)
        _stop_model_cmd = _cmd_prefix + [_stop_model_path]
        _sproc = subprocess.Popen(_stop_model_cmd)
        while True:
            if _sproc.poll() == 0:
                break
            _ml_res = self.main_loop(ignore_event=[], timeout=50)
            #TODO : 
            # if _ml_res == "-close-"
            # if _ml_res == "-restart-"
            # if _ml_res == "-ignore-"
        if os.path.isfile(self.started_manual_services_file):
            os.remove(self.started_manual_services_file)

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
        if self.root_size != self.root.size:
            _size_x, _size_y = self.root.size

            # (865, 529)
            if self.user_config['models']:
                if self.derunner_fold:
                    self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-205))
                else:
                    self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-317))
            if self.exist_installer:
                self.column_set_size(self.root["_SCROLL_COL2_"], (_size_x-65, _size_y-150))

            # Trust me !
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
        self.root["searchInstall"].update('')
    def focus_out_search_install(self, values):
        self.root["searchInstall"].update(self.mem_install_search if self.mem_install_search else 'Search')

    def search_install(self, values):
        _search_filter = values['searchInstall']
        if _search_filter.strip() != "":
            self.mem_install_search = _search_filter.strip()
            self.get_install_layout(get_layout=False, search_filter=_search_filter)
        else:
            self.mem_install_search = "Search"
            self.get_install_layout(get_layout=False)

        _taget_dict = {key:values for key, values in self.install_configs.items() if key in ["at","up", "am"]}
        for _, _key in _taget_dict.items():
            for _, _cycle in _key.items():
                for _, _data in _cycle.items():
                    self.root.refresh()
                    _elem, _vis = _data["key"], _data["visibility"]
                    self.root[_elem].update(visible=_vis)
                
        return "-done-"
        
    # - Fold / Unfold DeRunner Log
    def un_fold_derunner_log(self, values):
        _head = self.root["derunner_log_head"]
        _body = self.root["derunner_log"]
        _clear = self.root["derunner_log_clear"]
        _size_x, _size_y = self.root.size
        if self.derunner_fold:
            self.derunner_fold = False
            _head.Update('DeSOTA  Log ▼')
            _body.Update(visible=True)
            _clear.Update(visible=False)

            # RESIZE
            self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-317))
        else:
            self.derunner_fold = True
            _head.Update('DeSOTA  Log ▲')
            _body.Update(visible=False)
            _clear.Update(visible=True)
            # RESIZE
            self.column_set_size(self.root["_SCROLL_COL1_"], (_size_x-65, _size_y-205))
        return "-done-"


    # Get Class Method From Event and Run Method
    def main_loop(self, ignore_event=[], timeout=None):
        try:
            # Check For APP UPGRADES
            if self.just_started:
                self.just_started = False
                    
            #Read  values entered by user
            _event, _values = self.root.read(timeout=timeout)
        except:
            _event = psg.WIN_CLOSED

        if _event == psg.WIN_CLOSED:
            self.sgui_exit()
            return "-close-"
        elif _event == psg.TIMEOUT_KEY:
            self.upddate_derunner_log()
            return "-timeout-"
        
        # HANDLE TAB CHANGE
        elif isinstance(_event, int):
            self.current_tab = _values[_event]
            return "-ignore-"
        
        #access all the values and if selected add them to a string
        if DEBUG and _event != "windowConfigure":
            print(f" [ DEBUG ] -> event = {_event}")
            # print(f" [ DEBUG ] -> values = {_values}")

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
    print("DeManager Just Opened!")
    # Start APP
    sgui = SGui()
    print("App Started!")


    # Get APP Status - Prevent Re-Open
    if sgui.get_app_status() == "1":
        _app_upgrade = psg.popup_yes_no(
            f"This program is allready open or has not been properly closed!\nDo you want to continue?",
            title="DeSOTA - Manager Tools",
            icon = sgui.icon,
        )
        if _app_upgrade != "Yes":
            return 0
    else:
        sgui.set_app_status(1)


    # Search 4 Upg at startup
    print("Search 4 Upgrades")
    _upgrade_sript_path = sgui.create_dmp_upgrade_script()
    if _upgrade_sript_path:
        # retrieved from https://stackoverflow.com/a/14797454
        if USER_SYS == "win":
            os.system("start " + _upgrade_sript_path)
        elif USER_SYS == "lin":
            tmp_script= os.path.join(TMP_PATH, f"delete{int(time.time())}_dmt_upg.bat")
            with open(tmp_script, "w") as fw:
                fw.writelines([
                    "#!/bin/bash\n",
                    f'gnome-terminal --wait -- bash -c "pkexec /bin/bash {_upgrade_sript_path}; exec bash" & \
                    rm -- "{tmp_script}" & \
                    exit 0'
                ])
            pid=os.fork()
            if pid==0: # new process
                os.system(f"/bin/bash {tmp_script} &")
                exit()
        sgui.sgui_exit()
        return 0


    
    _tab_selected = False
    _mem_open_tab = sgui.current_tab
    while True:
        if not _tab_selected:
            _tab_selected = True
            sgui.main_loop(timeout=10)
            sgui.move_2_tab(_mem_open_tab)
        _sgui_res = sgui.main_loop(timeout=100)
        if DEBUG and _sgui_res != "-ignore-" and _sgui_res != "-timeout-":
            print(f" [ DEBUG ] -> main_loop res = {_sgui_res}")
            print('*'*80)

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
