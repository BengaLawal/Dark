import customtkinter as ctk
from ui import UserInterface

if __name__ == '__main__':
    root = ctk.CTk()
    app = UserInterface(root)
    root.mainloop()
