import os
import webbrowser
import json
import PySimpleGUI as sg
import yaml
from yaml.loader import SafeLoader
DEBUG = True
DESOTA_REQUIRED_SERVICES = ["desotaai/derunner"]

user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
app_path=os.path.join(desota_root_path, "DeManagerTools")

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
# Open the file and load the file
with open(os.path.join(config_folder, "services.config.yaml")) as f:
    SERVICES_CONF = yaml.load(f, Loader=SafeLoader)
with open(os.path.join(config_folder, "user.config.yaml")) as f:
    USER_CONF = yaml.load(f, Loader=SafeLoader)

# Construct APP with PySimpleGui
class SGui():
    def __init__(self, in_theme) -> None:
        self.debug = DEBUG
        self.services_config = SERVICES_CONF
        self.user_config = USER_CONF
        self.required_services = DESOTA_REQUIRED_SERVICES

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
            [sg.Text('Themes: ', font=self.default_f, pad=((410,0),(0,0))), sg.Combo(values=self.themes, default_value=in_theme, enable_events=True, key='selectTheme')],
            [sg.TabGroup(
                [[
                    sg.Tab('Monitor Models', self.tab1, title_color='Red',border_width =10, background_color=None,tooltip='', element_justification= 'left', key=self.tab_keys[0]),
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
    # TAB 1 - Monitor Models
    def construct_monitor_models_tab(self):
        # No Models Available
        if not self.user_config['models']:
            return [
                [sg.Text('No Model Installed', font=self.header_f)],
                [sg.Button('Install Models', key="move2installTab")]
            ]
        # Models Available
        else:
            pass
    
    # TAB 2 - Models Instalation
    def construct_install_tab(self):
        _install_layout = []
        # Required DeSOTA Services
        _req_serv = []
        for tmp_req_serv in self.required_services:
            if not self.user_config['models'] or tmp_req_serv not in self.user_config['models']:
                _req_serv.append(tmp_req_serv)
        if _req_serv:
            _install_layout.append([sg.Text('Required Desota Services', font=self.title_f)])
            for _r_q in _req_serv:
                _install_layout.append([sg.Checkbox(_r_q, default=True, disabled=True, key=f"SERVICE {_r_q}")])
            _install_layout.append([sg.HorizontalSeparator()])
            
            
        _install_layout.append([sg.Text('Available Models', font=self.title_f)])
        for _k, _v in self.services_config['desota_services'].items():
            if self.user_config['models'] and _k in self.user_config['models'] or _k in self.required_services:
                continue
            _install_layout.append([sg.Checkbox(_k, key=f"SERVICE {_k}")])

        return [
            # [sg.Slider(range=(1, 20), default_value=5, orientation='v', size=(10,20))],
            [sg.Text('Select the services to be installed', font=self.header_f)],
            [sg.Column(_install_layout, size=(600,300), scrollable=True)],
            [sg.Button('Start Instalation', key="startInstall")]
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
            _strip_models = [ m.strip() for m in self.user_config['models']]
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

    # Memorize User Theme
    user_theme = get_user_theme()

    # Start APP
    sgui = SGui(user_theme)
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
            with open(os.path.join(app_path, "user_theme.txt"), "w") as fw:
                fw.write(_values["selectTheme"])
        
        
if __name__ == "__main__":
    main()