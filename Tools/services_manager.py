import os
import json
import subprocess
user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

# retieved from https://stackoverflow.com/a/11995662  && https://stackoverflow.com/a/10052222
GET_ADMIN = [
    "net session >NUL 2>NUL\n",
    "IF %errorLevel% NEQ 0 (\n",
    "\tgoto UACPrompt\n",
    ") ELSE (\n",
    "\tgoto gotAdmin\n",
    ")\n",
    ":UACPrompt\n",
    'ECHO Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"\n',
    "set params= %*\n"
    'ECHO UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"\n',
    '"%temp%\getadmin.vbs"\n',
    'del "%temp%\getadmin.vbs"\n',
    "exit /B\n",
    ":gotAdmin\n",
    'pushd "%CD%"\n'
]

class WinBatManager:
    def __init__(self, user_conf, services_conf, models_list) -> None:
        self.system = "win"
        
        self.service_tools_folder = os.path.join(config_folder, "Services")
        self.services_conf = services_conf
        
        if not models_list:
            self.models_list = None
        elif isinstance(models_list, list):
            self.models_list = models_list
        if isinstance(models_list, dict):
            self.models_list = list(models_list.keys())

        self.models_list = models_list
        self.user_conf = user_conf
        self.get_admin = GET_ADMIN + [f'CD /D "{desota_root_path}"\n']

    # Temp Bat to Install New Desota Services
    def create_models_instalation(self, target_bat_path, start_install=False):
        # 1 - Get Admin Previleges 
        _tmp_file_lines = ["@ECHO OFF\n"]
        _tmp_file_lines += self.get_admin
        
        # 2 - Create install_progrss.txt
        _tmp_file_lines.append(f'ECHO 0 > {app_path}\install_progress.txt\n')

        # 3 - Stop All Services
        _gen_serv_stoper = os.path.join(self.service_tools_folder, "models_stopper.bat")
        if os.path.isfile(_gen_serv_stoper):
            _tmp_file_lines.append(f"start /B /WAIT {_gen_serv_stoper}\n")

        # 4 - Iterate thru instalation models
        for count, model in enumerate(self.models_list):
            # 4.1 - Append Models Installer
            _model_params = self.services_conf['services_params'][model]
            _installer_url = _model_params[self.system]['installer']
            _installer_args = _model_params[self.system]['installer_args']
            _model_version = _model_params[self.system]['version']
            _installer_name = _installer_url.split('/')[-1]
            _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile ~\{_installer_name}" && start /B /WAIT %UserProfile%\{_installer_name} {" ".join(_installer_args)} && del %UserProfile%\{_installer_name}\n')
            # 4.2 - Update user models
            _new_model = json.dumps({
                model: _model_version
            }).replace(" ", "").replace('"', '\\"')
            _tmp_file_lines.append(f'call {app_path}\env\python {app_path}\Tools\SetUserConfigs.py --key models --value "{_new_model}"  > NUL 2>NUL\n')
            # 4.3 - update install_progrss.txt
            _tmp_file_lines.append(f'ECHO {count+1} > {app_path}\install_progress.txt\n')

        # 5 - Create Start Run Constantly Services
        _models_start_path = self.update_models_starter()
        _tmp_file_lines.append(f"start /B /WAIT {_models_start_path}\n")
        
        # 5 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')

        # 6 - Create Installer Bat
        with open(target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        # 7 - Start Installer
        if start_install:
            subprocess.call([f'{target_bat_path}'])

    # Bat to Stop ALL Desota Services
    def update_models_stopper(self):
        _models_stopper_path = os.path.join(self.service_tools_folder, "models_stopper.bat")
        
        if not self.models_list:
            if os.path.isfile(_models_stopper_path):
                os.remove(_models_stopper_path)
            return None

        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 1 - Compare user_models with new installed models
        if self.user_conf["models"]:
            _res_models = [ m for m,v in self.user_conf["models"].items()]
        else:
            _res_models = []

        for _new_service in self.models_list:
            if _new_service in _res_models:
                continue
            _res_models.append(_new_service)

        # 2 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n"
        ]
        _tmp_file_lines += self.get_admin
        
        # 3 - Iterate thru instalation models
        for _model in _res_models:
            _model_param_path = self.services_conf["services_params"][_model][self.system]["service_path"]
            _model_param_stop = self.services_conf["services_params"][_model][self.system]["stoper"]

            _model_stop_path = os.path.join(user_path, _model_param_path, _model_param_stop)
            
            _tmp_file_lines.append(f"start /B /WAIT {_model_stop_path}\n")
        _tmp_file_lines.append("exit\n")
            
        # 4 - Create Stopper Bat
        with open(_models_stopper_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

    # Bat to Start models that run constantly
    def update_models_starter(self):
        _models_starter_path = os.path.join(self.service_tools_folder, "models_starter.bat")
        
        if not self.models_list:
            if os.path.isfile(_models_starter_path):
                os.remove(_models_starter_path)
            return None

        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 1 - Compare user_models with new installed models
        if self.user_conf["models"]:
            _res_models = [ m for m,v in self.user_conf["models"].items()]
        else:
            _res_models = []
        
        for _new_service in self.models_list:
            if _new_service in _res_models:
                continue
            _res_models.append(_new_service)
        # 2 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n"
        ]
        _tmp_file_lines += self.get_admin
        # 3 - Iterate thru instalation models
        _exist_run_constantly_model = False
        for _model in _res_models:
            _model_param_run_constantly = self.services_conf["services_params"][_model]["run_constantly"]
            if not _model_param_run_constantly:
                continue
            if not _exist_run_constantly_model:
                _exist_run_constantly_model = True
            _model_param_path = self.services_conf["services_params"][_model][self.system]["service_path"]
            _model_param_start = self.services_conf["services_params"][_model][self.system]["starter"]

            _model_start_path = os.path.join(user_path, _model_param_path, _model_param_start)
            _tmp_file_lines.append(f"start /B /WAIT {_model_start_path}\n")
        _tmp_file_lines.append("exit\n")
            
        # 4 - Create Starter Bat
        if _exist_run_constantly_model:
            with open(_models_starter_path, "w") as fw:
                fw.writelines(_tmp_file_lines)

        # Return Start Models .BAT PATH 
        return _models_starter_path

    # Bat to Uninstall Services
    def create_services_unintalation(self, start_uninstall=False, waiter={os.path.join(app_path, "tmp_uninstaller_status.txt"): 1}, ):
        _target_bat_path = os.path.join(app_path, "tmp_services_uninstaller.bat")

        # 1 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        _tmp_file_lines += self.get_admin

        # 2 - Stop All Services
        _gen_serv_stoper = os.path.join(self.service_tools_folder, "models_stopper.bat")
        if os.path.isfile(_gen_serv_stoper):
            _tmp_file_lines.append(f"start /B /WAIT {_gen_serv_stoper}\n")

        # 3 - Iterate thru Uninstalation services
        for model in self.models_list:
            # 3.1 - Append services Uninstallers
            _model_service = self.services_conf["services_params"][model][self.system]
            _model_uninstall_name = _model_service["uninstaller"]
            _model_uninstall_path = os.path.join(user_path, _model_service["service_path"], _model_uninstall_name)
            
            _model_uninstall_cmd = [_model_uninstall_path]
            if "uninstaller_args" in _model_service and _model_service["uninstaller_args"]:
                _model_uninstall_cmd += _model_service["uninstaller_args"]
                
            _tmp_file_lines.append(f'call {" ".join(_model_uninstall_cmd)}\n')
            
        for tmp_un, msg in waiter.items():
            _tmp_file_lines.append(f'ECHO {msg} >{tmp_un}\n')
        # 4 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append(f'(goto) 2>nul & del "{_target_bat_path}"\n')

        with open(_target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)
            
        # 5 - Start Uninstaller
        if start_uninstall:
            subprocess.call([str(_target_bat_path)])

    # Bat to Uninstall Desota Completely
    def update_desota_uninstaller(self, target_bat_path):
        # 1 - Stop Models
        # 2 - Uninstall Models
        # 3 - Uninstall DeManager
        # 4 - Delete Config Folder & Portables Folder
        # 5 - Delete DeSOTA root folder
        print("unsinstall")