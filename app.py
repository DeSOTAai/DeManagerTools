import os
import webbrowser
import json
import PySimpleGUI as sg
from Tools.win_bat_manager import BatManager
import subprocess

DEBUG = True
DESOTA_TOOLS_SERVICES = {    # Desc -> Service: Checkbox Disabled
    "desotaai/derunner": True
}

user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
# Open the file and load the file
with open(os.path.join(config_folder, "services.config.yaml")) as f:
    SERVICES_CONF = yaml.load(f, Loader=SafeLoader)

# Construct APP with PySimpleGui
class SGui():
    def __init__(self, in_theme) -> None:
        self.debug = DEBUG
        self.tools_services = DESOTA_TOOLS_SERVICES

        self.services_config = SERVICES_CONF
        with open(os.path.join(config_folder, "user.config.yaml")) as f:
            self.user_config = yaml.load(f, Loader=SafeLoader)
        self.system = self.user_config['system']
        
        #define theme
        sg.theme(in_theme)
        
        #define fonts
        self.header_f = ("Helvetica", 12, "bold")
        self.title_f = ("Helvetica", 10, "bold")
        self.default_f = sg.DEFAULT_FONT

        #define layout
        self.tab1 = self.construct_monitor_models_tab()
        self.tab2 = self.construct_install_tab()
        self.tab3 = self.construct_api_tab()

        #Define Layout with Tabs
        self.themes = sg.ListOfLookAndFeelValues()
        # print(f" [DEBUG ] -> themes = {self.themes}")
        self.tab_keys= [ '-TAB1-', '-TAB2-', '-TAB3-']
        self.tabgrp = [
            [sg.Text('Theme: ', font=self.default_f, pad=((410,0),(0,0))), sg.Combo(values=self.themes, default_value=in_theme, enable_events=True, key='selectTheme')],
            [sg.TabGroup(
                [[
                    sg.Tab('Models Dashboard', self.tab1, title_color='Red',border_width =10, background_color=None,tooltip='', element_justification= 'left', key=self.tab_keys[0]),
                    sg.Tab('Models Instalation', self.tab2,title_color='Blue',background_color=None, key=self.tab_keys[1]),
                    sg.Tab('DeSOTA API Key', self.tab3,title_color='Black',background_color=None,tooltip='', key=self.tab_keys[2])
                ]], 
                tab_location='topleft',
                title_color='Gray', 
                tab_background_color='White',
                selected_title_color='White',
                selected_background_color='Gray', 
                border_width=5
            )]
        ]
                
        #Define Window
        self.root = sg.Window("Desota - Manager Tools",self.tabgrp, icon=os.path.join(app_path, "Assets", "icon.ico"))

    ## Utils
    # TAB 1 - Models Dashboard
    def construct_monitor_models_tab(self):
        # No Models Available
        if not self.user_config['models']:
            return [
                [sg.Text('No Model Installed', font=self.header_f)],
                [sg.Button('Install Models', key="move2installTab")]
            ]
        # Models Available
        else:
            return []
    
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
                _install_layout.append([sg.Checkbox(_desota_serv, default=True, disabled=_cb_disabled, key=f"SERVICE {_desota_serv}")])

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
        
        # Available Uninstalled Services
        _available_models_header = False
        for _k, _v in self.services_config['services_params'].items():
            if (self.user_config['models'] and _k in self.user_config['models'] ) or (_v["submodel"] == True) or (_k in self.tools_services):
                continue
            if not _available_models_header:
                _available_models_header = True
                _install_layout.append([sg.Text('Available Models', font=self.title_f)])
            _install_layout.append([sg.Checkbox(_k, key=f"SERVICE {_k}")])

        
        return [
            [sg.Text('Select the services to be installed', font=self.header_f)],
            [sg.Column(_install_layout, size=(600,300), scrollable=True)],
            [sg.Button('Start Instalation', key="startInstall"), sg.ProgressBar(100, orientation='h', expand_x=True, size=(20, 20),  key='installPBAR')]
        ]

    # TAB 3 - DeSOTA API Key
    def construct_api_tab(self):
        # No Models Installed
        if not self.user_config['models']:
            return [
                [sg.Text('No Model Installed', font=self.header_f)],
                [sg.Button('Install Models', key="move2installTab0")]
            ]
        # TODO . Discuss w/ Kris what about if people have models installed but need key authenticato for new models...
        # Models Installed
        else:
            _strip_models = [ m.strip() for m, v in self.user_config['models'].items()]
            _str_models = ",".join(_strip_models)
            return [
                [sg.Text('Create your API Key', font=self.header_f)],  # Title
                [sg.Text('1. Log In DeSOTA ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'URL http://129.152.27.36/index.php')],    # Log In DeSOTA
                [sg.Text('2. Confirm you are logged in DeOTA API ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'URL http://129.152.27.36/assistant/api.php')],    # Confirm Log In DeSOTA
                [sg.Text('3. Get your DeSOTA API Key ', font=self.default_f), sg.Text("here", tooltip='', enable_events=True, font=self.default_f, text_color="blue", key=f'URL http://129.152.27.36/assistant/api.php?models_list={_str_models}')],    # SET API Key
                [sg.Text('4. Insert DeSOTA API Key', font=self.default_f),sg.Input('',key='inpKey')],
                [sg.Button('Set API Key', key="setAPIkey")]
            ]

    # Move Within Tkinter Tabs
    def move_2_tab2(self):
        self.root[ self.tab_keys[1] ].select()

    # Class - main
    def listener(self):
        #Read  values entered by user
        return self.root.read()

# Utils
def get_user_theme():
    if not os.path.isfile(os.path.join(app_path, "user_theme.txt")):
        with open(os.path.join(app_path, "user_theme.txt"), "w") as fw:
            fw.write("DarkBlue")
            return "DarkBlue"
    with open(os.path.join(app_path, "user_theme.txt"), "r") as fr:
        return fr.read().strip()
def set_user_theme(theme):
    with open(os.path.join(app_path, "user_theme.txt"), "w") as fw:
        fw.write(theme)
    
def get_app_status():
    if not os.path.isfile(os.path.join(app_path, "status.txt")):
        with open(os.path.join(app_path, "status.txt"), "w") as fw:
            fw.write("0")
            return "0"
    with open(os.path.join(app_path, "status.txt"), "r") as fr:
        return fr.read().strip()
def set_app_status(status):
    with open(os.path.join(app_path, "status.txt"), "w") as fw:
        fw.write(str(status))

def main():
    # Get APP Status - Prevent Re-Open
    if get_app_status() == "1":
        return 0
    set_app_status(1)

    # Start APP
    sgui = SGui(get_user_theme())
    while True:
        try:
            #Read  values entered by user
            _event, _values = sgui.listener()
        except:
            _event = sg.WIN_CLOSED
        if _event == sg.WIN_CLOSED or _event == "Close":
            set_app_status(0)
            sgui.root.close()    
            break
        #access all the values and if selected add them to a string
        print(f" [ DEBUG ] -> event = {_event}")
        print(f" [ DEBUG ] -> values = {_values}")
        # print(f" [ DEBUG ] ->  = {}")
        if "move2installTab" in _event:
            sgui.move_2_tab2()
        elif _event.startswith("URL "):
            url = _event.split(' ')[1].strip()
            webbrowser.open(url)
        elif _event == "selectTheme":
            sgui.root.close()
            sgui = SGui(_values["selectTheme"])
            set_user_theme(_values["selectTheme"])
        elif _event == "startInstall":
            _models_2_install = []
            for _k, _v in _values.items():
                if isinstance(_k, str) and "SERVICE" in _k and _v:
                    _models_2_install.append(_k.split(' ')[1].strip())
            print(f" [ DEBUG ] -> Models to install = {_models_2_install} ")
            _ammount_models = len(_models_2_install)
            if sgui.system == "win":
                bm = BatManager()
                bm.create_models_instalation(sgui.services_config, _models_2_install, os.path.join(out_bat_folder, "desota_tmp_installer.bat"))
                subprocess.call([f'{os.path.join(out_bat_folder, "desota_tmp_installer.bat")}'])
                sgui.root['startInstall'].update(disabled=True)
                sgui.root['installPBAR'].update(current_count=0)
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
                    sgui.root['installPBAR'].update(current_count=_curr_prog)
                    if _curr_prog == 100:
                        os.remove(_install_prog_file)
                        bm.update_models_stopper(sgui.user_config, sgui.services_config, _models_2_install)
                        break
                sgui.root.close()
                sgui = SGui(get_user_theme())



        
if __name__ == "__main__":
    main()