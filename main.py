from config import configuration as config
from ui import UserInterface
import customtkinter as ctk

if __name__ == '__main__':
    creds = config.login()
    root = ctk.CTk()
    app = UserInterface(root, creds)
    root.mainloop()
