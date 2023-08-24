import os

# GET PROJECT LOCATION
user_path=os.path.expanduser('~')
# app_path=os.path.join(user_path, "Documents\Projetos\DeSOTA\DeManagerTools")    #DEV
app_path=os.path.join(user_path, "Desota\DeManagerTools")                       #DEPLOY

def replace_sed_vars(orig_sed):
    # GET SED VARS
    target_exe=os.path.join(app_path, "dist\Desota-ManagerTools.exe")
    file_title = "DeSOTA - Mamager Tools"
    bat_file="dmt-run.bat"
    app_launched=f"cmd /c {bat_file}"
    bat_folder=os.path.join(app_path, "executables\Windows")

    # REPLACE SED VARS
    return orig_sed.replace(">FileTitle<", file_title)\
        .replace(">TargetExe<", target_exe)\
        .replace(">AppLaunched<", app_launched)\
        .replace(">BatFile<", bat_file)\
        .replace(">BatFolder<", bat_folder)

def main():
    # GET SED LOCATION
    orig_sed_path = os.path.join(app_path, "executables\Windows\dmt-iexpress-tmp.SED")
    res_sed_path = os.path.join(app_path, "executables\Windows\dmt-iexpress.SED")
    with open(orig_sed_path, 'r') as fr:
        orig_sed_cont = fr.read()
    with open(res_sed_path, 'w') as fw:
        fw.write(replace_sed_vars(orig_sed_cont))

if __name__ == "__main__":
    main()