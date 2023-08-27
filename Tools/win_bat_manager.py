import os

user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

GET_ADMIN = [
    ":: retireved from https://stackoverflow.com/a/11995662\n",
    "net session >NUL 2>NUL\n",
    "IF %errorLevel% NEQ 0 (\n",
    "\tgoto UACPrompt\n",
    ") ELSE (\n",
    "\tgoto gotAdmin\n",
    ")\n",
    ":: retrieved from https://stackoverflow.com/a/10052222\n",
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
        _tmp_file_lines = [
            "@ECHO OFF\n",
            "cls\n"
        ]
        # Concat Admin Required Script
        _tmp_file_lines += self.get_admin

        for model in models_list:
            _model_params = services_conf['services_params'][model]
            _installer_url = _model_params[self.system]['installer']
            _installer_args = _model_params[self.system]['installer_args']
            _installer_name = _installer_url.split('/')[-1]
            _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile ~\{_installer_name}" && start /B /WAIT %UserProfile%\{_installer_name} {" ".join(_installer_args)} && del %UserProfile%\{_installer_name}\n')
        _tmp_file_lines.append("exit\n")
        with open(target_bat_path, "w") as fw:
            # Step 3: Use writelines() to write the list of strings to the file
            fw.writelines(_tmp_file_lines)

    # Bat 2 Stop ALL Desota Services
    def create_models_stopper(self):
        print("Stop")

    # Bat 2 Starter for models that run constantly
    def create_models_starter(self):
        print("Start")

    def create_desota_uninstaller(self):
        print("unsinstall")