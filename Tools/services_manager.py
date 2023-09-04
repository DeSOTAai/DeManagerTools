import os
import json
import subprocess
user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
app_path=os.path.join(desota_root_path, "DeManagerTools")
out_bat_folder=os.path.join(app_path, "executables", "Windows")

# retieved from https://stackoverflow.com/a/11995662  && https://stackoverflow.com/a/10052222 && https://stackoverflow.com/a/40388766
GET_ADMIN = [
    "net session >NUL 2>NUL\n",
    "IF %errorLevel% NEQ 0 (\n",
    "\tgoto UACPrompt\n",
    ") ELSE (\n",
    "\tgoto gotAdmin\n",
    ")\n",
    ":UACPrompt\n",
    'powershell -Command "Start-Process -Wait -Verb RunAs -FilePath \'%0\' -ArgumentList \'am_admin\'" \n',
    "exit /B\n",
    ":gotAdmin\n",
    'pushd "%CD%"\n'
]

class WinBatManager:
    def __init__(self, user_conf, services_conf, models_list=None) -> None:
        self.system = "win"
        
        self.service_tools_folder = os.path.join(config_folder, "Services")
        self.services_conf = services_conf
        
        if not models_list:
            self.models_list = None
        elif isinstance(models_list, list):
            self.models_list = models_list
        if isinstance(models_list, dict):
            self.models_list = list(models_list.keys())
            
        self.user_conf = user_conf
        self.get_admin = GET_ADMIN + [f'CD /D "{desota_root_path}"\n']

    # Bat to Stop ALL Desota Services
    def update_models_stopper(self, only_selected=False, tmp_bat_target=None, autodelete=False):
        '''
        :param waiter: Specify a File To write a message when stopper as finished
        :type waiter: dict{ str(waiter_file_path): str(starter_completed_message) }
        '''
        if tmp_bat_target:
            _models_stopper_path = tmp_bat_target
        else:
            _models_stopper_path = os.path.join(self.service_tools_folder, "models_stopper.bat")
        
        if not self.models_list:
            if os.path.isfile(_models_stopper_path):
                os.remove(_models_stopper_path)
            return None

        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 1 - Compare user_models with new installed models
        if self.user_conf["models"] and not only_selected:
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
            
        if autodelete:
            _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')
        else:
            _tmp_file_lines.append("exit\n")
            
        # 4 - Create Stopper Bat
        with open(_models_stopper_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

    # Bat to Start models that run constantly
    def update_models_starter(self, from_installer=False):
        '''
        :param waiter: Specify a File To write a message when starter as finished
        :type waiter: dict{ str(waiter_file_path): str(starter_completed_message) }
        '''
        _models_starter_path = os.path.join(self.service_tools_folder, "models_starter.bat")

        if from_installer and self.user_conf["models"] and len(list(self.user_conf["models"].keys())) > 0:
            for _model, _v in self.user_conf["models"].items():
                if _model not in self.models_list:
                    self.models_list.append(_model)
                    
        if not self.models_list:
            if os.path.isfile(_models_starter_path):
                os.remove(_models_starter_path)
            return None

        if not os.path.exists(self.service_tools_folder):
            os.mkdir(self.service_tools_folder)
        # 2 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n"
        ]
        _tmp_file_lines += self.get_admin
        # 3 - Iterate thru instalation models
        _exist_run_constantly_model = False
        for _model in self.models_list:
            _model_param_run_constantly = self.services_conf["services_params"][_model]["run_constantly"]
            if not _model_param_run_constantly:
                continue

            if not _exist_run_constantly_model:
                _exist_run_constantly_model = True

            _model_param_path = self.services_conf["services_params"][_model][self.system]["service_path"]
            _model_param_start = self.services_conf["services_params"][_model][self.system]["starter"]
            _model_start_path = os.path.join(user_path, _model_param_path, _model_param_start)
            
            _tmp_file_lines.append(f"start /B /WAIT {_model_start_path}\n")

        if not _exist_run_constantly_model:
            if os.path.isfile(_models_starter_path):
                os.remove(_models_starter_path)
            return None
        
        _tmp_file_lines.append("exit\n")
            
        # 4 - Create Starter Bat
        if _exist_run_constantly_model:
            with open(_models_starter_path, "w") as fw:
                fw.writelines(_tmp_file_lines)

        # Return Start Models .BAT PATH 
        return _models_starter_path

    # Temp Bat to Install New Desota Services
    def create_models_instalation(self, target_bat_path, install_prog_path, start_install=False):
        '''
        :param waiter: Specify a File To write a message when starter as finished - Only Implemented if start_install=True
        :type waiter: dict{ str(waiter_file_path): str(starter_completed_message) }
        '''
        # 1 - Get Admin Previleges 
        _tmp_file_lines = ["@ECHO OFF\n"]
        _tmp_file_lines += self.get_admin
        
        # 2 - Create install_progrss.txt
        _tmp_file_lines.append(f'ECHO 0 > {install_prog_path}\n')

        # 3 - Stop All Services
        _gen_serv_stoper = os.path.join(self.service_tools_folder, "models_stopper.bat")
        if os.path.isfile(_gen_serv_stoper):
            _tmp_file_lines.append(f"start /B /WAIT {_gen_serv_stoper}\n")

        # 4 - Iterate thru instalation models
        for count, model in enumerate(self.models_list):
            # 4.1 - Append Models Installer
            _model_params = self.services_conf['services_params'][model][self.system]
            _installer_url = _model_params['installer']
            _installer_args = _model_params['installer_args']
            _model_version = _model_params['version']
            _installer_name = _installer_url.split('/')[-1]
            _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile ~\{_installer_name}" && start /B /WAIT %UserProfile%\{_installer_name} {" ".join(_installer_args)} && del %UserProfile%\{_installer_name}\n')
            # 4.2 - Update user models
            _new_model = json.dumps({
                model: _model_version
            }).replace(" ", "").replace('"', '\\"')
            _tmp_file_lines.append(f'call {app_path}\env\python {app_path}\Tools\SetUserConfigs.py --key models --value "{_new_model}"  > NUL 2>NUL\n')
            # 4.3 - update install_progrss.txt
            if count != len(self.models_list) - 1:
                _tmp_file_lines.append(f'ECHO {count+1} > {install_prog_path}\n')
        _mem_len_models = len(self.models_list)
        # 5 - Create Start Run Constantly Services
        _models_start_path = self.update_models_starter(from_installer=True)
            
        if _models_start_path:
            _tmp_file_lines.append(f"start /B /WAIT {_models_start_path}\n")
            
        _tmp_file_lines.append(f'ECHO {_mem_len_models} > {install_prog_path}\n')
        
        # 5 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')

        # 6 - Create Installer Bat
        with open(target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        # 7 - Start Installer
        if start_install:
            _sproc = subprocess.Popen([target_bat_path])
            _sproc.poll()

    # Bat to Uninstall Services
    def create_services_unintalation(self, start_uninstall=False, waiter={os.path.join(app_path, "tmp_uninstaller_status.txt"): 1}):
        _target_bat_path = os.path.join(app_path, "tmp_services_uninstaller.bat")
        _models_starter_path = os.path.join(self.service_tools_folder, "models_starter.bat")
        # 1 - Get Admin Previleges 
        _tmp_file_lines = [
            "@ECHO OFF\n"
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
        
        # 4 - Start Run Constantly Models
        if os.path.isfile(_models_starter_path):
            _tmp_file_lines.append(f"start /B /WAIT {_models_starter_path}\n")

        # 5 - Inform Completition
        for tmp_un, msg in waiter.items():
            _tmp_file_lines.append(f'ECHO {msg} >{tmp_un}\n')
        
        # 6 - Delete Bat at end of uninstalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append(f'(goto) 2>nul & del "{_target_bat_path}"\n')
            
        with open(_target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)
            
        # 7 - Start Uninstaller
        if start_uninstall:
            _sproc = subprocess.Popen([_target_bat_path])
            _sproc.poll()
    
    # Bat to Upgrade DeSOTA - Manager Tools
    def upgrade_app(self, start_upgrade=False):
        _target_bat_path = os.path.join(desota_root_path, "tmp_dmt_upgrade.bat")
        _app_params = self.services_conf['manager_params'][self.system]
        _installer_url = _app_params["installer"]
        _model_version = _app_params['version']
        _installer_name = _installer_url.split('/')[-1]
        # 1 - File Header
        _tmp_file_lines = [
            "@ECHO OFF\n",
            f'CD /D "{desota_root_path}"\n'
        ]

        # 3 - Crawl and Start APP Re-Instalation
        _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile ~\{_installer_name}" && start /B /WAIT %UserProfile%\{_installer_name} && del %UserProfile%\{_installer_name}\n')

        # 5 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
        _tmp_file_lines.append(f'(goto) 2>nul & del "{_target_bat_path}"\n')

        # 6 - Write Target File
        with open(_target_bat_path, "w") as fw:
            fw.writelines(_tmp_file_lines)

        if start_upgrade:
            _sproc = subprocess.Popen([_target_bat_path], close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
            _sproc.poll()

    # Bat to Uninstall Desota Completely
    def update_desota_uninstaller(self, target_bat_path):
        # 1 - Stop Models
        # 2 - Uninstall Models
        # 3 - Uninstall DeManager
        # 4 - Delete Config Folder & Portables Folder
        # 5 - Delete DeSOTA root folder
        print("unsinstall")