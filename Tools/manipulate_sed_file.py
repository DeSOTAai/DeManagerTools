import os

user_path=os.path.expanduser('~')
app_path=os.path.join(user_path, "Desota\DeManagerTools")    #DEV

def replace_sed_vars(orig_sed):
    # BAT TO EXE
    target_exe=os.path.join(app_path, "dist\Desota-ManagerTools.exe")
    file_title = "DeSOTA - Mamager Tools"
    app_launched="cmd /c dmt-run.bat"
    bat_file="dmt-run.bat"
    bat_folder=os.path.join(app_path, "executables\Windows")
    return orig_sed.replace(">TargetName<", target_exe)\
        .replace(">FileTitle<", file_title)\
        .replace(">TargetExe<", target_exe)\
        .replace(">AppLaunched<", app_launched)\
        .replace(">BatFile<", bat_file)\
        .replace(">BatFolder<", bat_folder)

def main():
    orig_sed_path = os.path.join(app_path, "executables\Windows\demanagertools.iexpress.SED")
    with open(orig_sed_path, 'r') as fr:
        orig_sed_cont = fr.read()
    with open(orig_sed_path, 'w') as fw:
        replace_sed_vars()
        fw.write(orig_sed_cont.replace("%UserProfile%", user_path))

if __name__ == "__main__":
    main()