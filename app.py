import sys
import os
import tkinter as tk
from tkinter import ttk
from pystray import MenuItem as item
import pystray
from PIL import Image

user_path=os.path.expanduser('~')
app_path=os.path.join(user_path, "Documents\Projetos\DeSOTA\DeManagerTools")    #DEV
# app_path=os.path.join(user_path, "Desota\DeManagerTools")                     #DEPLOY

def main():
    root=tk.Tk()
    root.title(" DeSOTA - Manager Tools ")
    # Setting up APP
    root.iconbitmap(os.path.join(app_path, "Assets\icon.ico"))
    root.geometry("600x400")

    # Minimize the window tkinter in the windows system tray - retieved from https://stackoverflow.com/a/54841035
    def quit_window(icon, item):
        icon.stop()
        root.destroy()

    def show_window(icon, item):
        icon.stop()
        root.after(0,root.deiconify)

    def withdraw_window():  
        root.withdraw()
        image = Image.open(os.path.join(app_path, "Assets\icon.ico"))
        menu = (item('Quit', quit_window), item('Show', show_window))
        icon = pystray.Icon("name", image, "title", menu)
        icon.run()
    root.protocol('WM_DELETE_WINDOW', withdraw_window)

    # Creating Tabbed Widget With Python-Tkinter - retrieved from https://www.geeksforgeeks.org/creating-tabbed-widget-with-python-tkinter/
    # Creating Tab Control
    tabControl = ttk.Notebook(root)
    # Creating the tabs
    tab1 = ttk.Frame(tabControl)    # MONITOR SERVICES
    tab2 = ttk.Frame(tabControl)    # INSTALATION
    tab3 = ttk.Frame(tabControl)    # API KEY
    # Adding the tab
    tabControl.add(tab1, text='Monitor Services')
    tabControl.add(tab2, text='Models Instalation')
    tabControl.add(tab3, text='DeSOTA API Key')
    # Packing the tab control to make the tabs visible - The pack() method is used to organize widgets in blocks before placing them in the parent widget. This can be done using various options like fill, expand and side.
    tabControl.pack(expand=1, fill="both")
    # Creating Label widget as a child of the parent window (root)
    ttk.Label(tab1, text="This are the current installed AI Models").grid(column=0, row=0, padx=30, pady=30)
    ttk.Label(tab2, text="Availables Models").grid(column=0, row=0, padx=30, pady=30)
    ttk.Label(tab3, text="Create your API KEY").grid(column=0, row=0, padx=30, pady=30)
    
    

    # newlabel = tk.Label(text = f" Current Folder = {app_path} ")
    # newlabel.grid(column=0,row=0)
    
    # Run the application
    root.mainloop()


if __name__ == "__main__":
    main()