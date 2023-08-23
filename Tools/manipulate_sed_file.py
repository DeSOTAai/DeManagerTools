import os

user_path=os.path.expanduser('~')
app_path=os.path.join(user_path, "Desota\DeManagerTools")    #DEV

def main():
    orig_sed_path = os.path.join(app_path, "executables\Windows\demanagertools.iexpress.SED")
    with open(orig_sed_path, 'r') as fr:
        orig_sed_cont = fr.read()
    with open(orig_sed_path, 'w') as fw:
        fw.write(orig_sed_cont.replace("%UserProfile%", user_path))

if __name__ == "__main__":
    main()