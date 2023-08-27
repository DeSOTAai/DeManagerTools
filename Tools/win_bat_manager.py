import os
import json
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

class BatManager:
    def __init__(self) -> None:
        self.system = "win"
        self.get_admin = GET_ADMIN
    def create_models_instalation(self, services_conf, models_list, target_bat_path):
        # 1 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        _tmp_file_lines += self.get_admin
        # 2 - Iterate thru instalation models
        for model in models_list:
            # 2.1 - Append Models Installer
            _model_params = services_conf['services_params'][model]
            _installer_url = _model_params[self.system]['installer']
            _installer_args = _model_params[self.system]['installer_args']
            _model_version = _model_params[self.system]['version']
            _installer_name = _installer_url.split('/')[-1]
            _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile ~\{_installer_name}" && start /B /WAIT %UserProfile%\{_installer_name} {" ".join(_installer_args)} && del %UserProfile%\{_installer_name}\n')
            # 2.2 - Update user models
            _new_model = json.dumps({
                model: _model_version
            }).replace(" ", "").replace('"', '\\"')
            _tmp_file_lines.append(f'call {app_path}\env\python {app_path}\Tools\SetUserConfigs.py --key models --value "{_new_model}"  > NUL 2>NUL\n')
            # env\python Tools\SetUserConfigs.py -k models -v "{\"test\":\"how are you\"}"
        # 4 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')
        # 5 - Create Installer Bat
        with open(target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

    # Bat 2 Stop ALL Desota Services
    def update_models_stopper(self, user_conf, services_conf, models_list, target_bat_path):
        # 1 - Compare user_models with new installed models
        print("Stop")

    # Bat 2 Starter for models that run constantly
    def update_models_starter(self, user_conf, services_conf, models_list, target_bat_path):
        print("Start")

    def update_desota_uninstaller(self, user_conf, services_conf, models_list, target_bat_path):
        # 1 - Stop Models
        # 2 - Uninstall Models
        # 3 - Uninstall DeManager
        # 4 - Delete Config Folder & Portables Folder
        # 5 - Delete DeSOTA root folder
        print("unsinstall")