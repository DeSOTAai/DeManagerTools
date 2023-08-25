import sys
import os
import tkinter as tk
from tkinter import ttk
from pystray import MenuItem as item
import pystray
from PIL import Image

DEBUG = False

user_path=os.path.expanduser('~')
# app_path=os.path.join(user_path, "Documents\Projetos\DeSOTA\DeManagerTools")    #DEV
app_path=os.path.join(user_path, "Desota\DeManagerTools")                     #DEPLOY

# import pyyaml module
import yaml
from yaml.loader import SafeLoader
config_folder=os.path.join(app_path, "Configs")  # User | Services
# Open the file and load the file
with open(os.path.join(config_folder, "desota.config.yaml")) as f:
    DESOTA_CONF = yaml.load(f, Loader=SafeLoader)
with open(os.path.join(config_folder, "user.config.yaml")) as f:
    USER_CONF = yaml.load(f, Loader=SafeLoader)

class Ctkinter:
    def __init__(self) -> None:
        self.debug = DEBUG
        self.desota_config = DESOTA_CONF
        self.user_config = USER_CONF
        self.root=tk.Tk()
        self.root.title(" DeSOTA - Manager Tools ")
        # Setting up APP
        self.root.iconbitmap(os.path.join(app_path, "Assets\icon.ico"))
        self.root.geometry("600x400")

        # Minimize the window tkinter in the windows system tray - retieved from https://stackoverflow.com/a/54841035
        def quit_window(icon, item):
            icon.stop()
            self.root.destroy()

        def show_window(icon, item):
            icon.stop()
            self.root.after(0, self.root.deiconify)

        def withdraw_window():  
            self.root.withdraw()
            image = Image.open(os.path.join(app_path, "Assets\icon.ico"))
            menu = (item('Quit', quit_window), item('Show', show_window))
            icon = pystray.Icon("name", image, "title", menu)
            icon.run()
            
        if not self.debug:
            self.root.protocol('WM_DELETE_WINDOW', withdraw_window)

        # Creating Tabbed Widget With Python-Tkinter - retrieved from https://www.geeksforgeeks.org/creating-tabbed-widget-with-python-tkinter/
        # Creating Tab Control
        self.tabControl = ttk.Notebook(self.root)
        # Creating the tabs
        self.tab1 = ttk.Frame(self.tabControl)    # MONITOR SERVICES
        self.tab2 = ttk.Frame(self.tabControl)    # INSTALATION
        self.tab3 = ttk.Frame(self.tabControl)    # API KEY

        # Adding the tabs
        self.tabControl.add(self.tab1, text='Monitor Models')
        self.tabControl.add(self.tab2, text='Models Instalation')
        self.tabControl.add(self.tab3, text='DeSOTA API Key')
        # Packing the tab control to make the tabs visible - The pack() method is used to organize widgets in blocks before placing them in the parent widget. This can be done using various options like fill, expand and side.
        self.tabControl.pack(expand=1, fill="both")

    # UTILS
    # - Move Within Tkinter Tabs
    def move_2_tab1(self):
        self.tabControl.select(self.tab1)
    def move_2_tab2(self):
        self.tabControl.select(self.tab2)
    def move_2_tab3(self):
        self.tabControl.select(self.tab3)

    # TAB Constructors
    # TAB 1 - Monitor Models
    def monitor_tab(self):
        # No Models Available
        if not self.user_config['models']:
            frame = tk.LabelFrame(
                self.tab1,
                text='No Model Installed',
                bg='#f0f0f0',
                font=(20)
            )
            frame.pack(expand=True, fill="both")
            ttk.Button(
                frame, 
                text="Install Models",
                command = self.move_2_tab2
            ).grid(column=0, row=0, padx=10, pady=10)
        # Models Available
        else:
            pass

    # TAB 2 - Models Instalation
    def install_tab(self):
        ttk.Label(self.tab2, text="Availables Models").grid(column=0, row=0, padx=30, pady=30)

    # TAB 3 - DeSOTA API Key
    def api_tab(self):
        ttk.Label(self.tab2, text="Availables Models").grid(column=0, row=0, padx=30, pady=30)

def main():
    my_tk = Ctkinter()

    my_tk.monitor_tab()
    my_tk.install_tab()
    my_tk.api_tab()
    
    # Run the application
    my_tk.root.mainloop()


if __name__ == "__main__":
    main()