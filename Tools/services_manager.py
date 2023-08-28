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
    'CD /D "%~dp0"\n'
]

class WinBatManager:
    def __init__(self) -> None:
        self.system = "win"
        self.get_admin = GET_ADMIN
        self.service_tools_folder = os.path.join(app_path, "Tools", "Services")
    def create_models_instalation(self, services_conf, models_list, target_bat_path, start_installer=False):
        # 1 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        _tmp_file_lines += self.get_admin
        
        # 2 - Create install_progrss.txt
        _tmp_file_lines.append(f'ECHO 0 > {app_path}\install_progress.txt\n')

        # 3 - Stop All Services
        _gen_serv_stoper = os.path.join(self.service_tools_folder, "models_stopper.bat")
        if os.path.isfile(_gen_serv_stoper):
            _tmp_file_lines.append(f"start /B /WAIT {_gen_serv_stoper}\n")

        # 4 - Iterate thru instalation models
        for count, model in enumerate(models_list):
            # 4.1 - Append Models Installer
            _model_params = services_conf['services_params'][model]
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

        # 5 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')

        # 6 - Create Installer Bat
        with open(target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        # 7 - Start Installer
        if start_installer:
            subprocess.call([f'{target_bat_path}'])

    # Bat to Stop ALL Desota Services
    def update_models_stopper(self, user_conf, services_conf, models_list):
        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 1 - Compare user_models with new installed models
        if user_conf["models"]:
            _res_models = [ m for m,v in user_conf["models"].items()]
        else:
            _res_models = []
        
        for _new_service in models_list:
            if _new_service in _res_models:
                continue
            _res_models.append(_new_service)
        # 2 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        _tmp_file_lines += self.get_admin
        
        # 3 - Iterate thru instalation models
        for _model in _res_models:
            _model_param_path = services_conf["services_params"][_model][self.system]["service_path"]
            _model_param_stop = services_conf["services_params"][_model][self.system]["stoper"]

            _model_stop_path = os.path.join(user_path, _model_param_path, _model_param_stop)
            
            _tmp_file_lines.append(f"start /B /WAIT {_model_stop_path}\n")
            
        # 4 - Create Stopper Bat
        with open(os.path.join(self.service_tools_folder, "models_stopper.bat"), "w") as fw:
            fw.writelines(_tmp_file_lines)

    # Bat to Start models that run constantly
    def update_models_starter(self, user_conf, services_conf, models_list, start_models=False):
        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 1 - Compare user_models with new installed models
        if user_conf["models"]:
            _res_models = [ m for m,v in user_conf["models"].items()]
        else:
            _res_models = []
        
        for _new_service in models_list:
            if _new_service in _res_models:
                continue
            _res_models.append(_new_service)
        # 2 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        _tmp_file_lines += self.get_admin
        # 3 - Iterate thru instalation models
        _exist_run_constantly_model = False
        for _model in _res_models:
            _model_param_run_constantly = services_conf["services_params"][_model]["run_constantly"]
            if not _model_param_run_constantly:
                continue
            if not _exist_run_constantly_model:
                _exist_run_constantly_model = True
            _model_param_path = services_conf["services_params"][_model][self.system]["service_path"]
            _model_param_start = services_conf["services_params"][_model][self.system]["starter"]

            _model_start_path = os.path.join(user_path, _model_param_path, _model_param_start)
            
            _tmp_file_lines.append(f"start /B /WAIT {_model_start_path}\n")
            
        # 4 - Create Starter Bat
        if _exist_run_constantly_model:
            with open(os.path.join(self.service_tools_folder, "models_starter.bat"), "w") as fw:
                fw.writelines(_tmp_file_lines)

        # 5 - Start Models
        if start_models:
            subprocess.call([f'{os.path.join(self.service_tools_folder, "models_starter.bat")}'])

    def update_desota_uninstaller(self, user_conf, services_conf, models_list, target_bat_path):
        # 1 - Stop Models
        # 2 - Uninstall Models
        # 3 - Uninstall DeManager
        # 4 - Delete Config Folder & Portables Folder
        # 5 - Delete DeSOTA root folder
        print("unsinstall")