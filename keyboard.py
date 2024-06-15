import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from validate_email import validate_email

class Keyboard:
    def __init__(self, master, width, height, entry_box, cancel, enter):
        self.master = master
        self.keyboard_width = width
        self.keyboard_height = height
        self.entry_box = entry_box
        self.cancel = cancel
        self.enter = enter

        self.number_row_frame = None
        self.is_upper = False

        self.alpha = {
            'row1': ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'Backspace'],
            'row2': ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '_', "Enter"],
            'row3': ['↑', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '-', '.', 'Cancel'],
            'row4': ["123", '@', '.com', '[ space ]', 'gmail', 'hotmail', 'yahoo']
        }
        self.number = {
            'row0': [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
        }

        # self.row1 = ctk.CTkFrame(self.master)
        # self.row2 = ctk.CTkFrame(self.master)
        # self.row3 = ctk.CTkFrame(self.master)
        # self.row4 = ctk.CTkFrame(self.master)

        self.keysize_height = None
        self.keysize_width = None
        self.configure_key_size()

        # self.row1.grid(row=1)
        # self.row2.grid(row=2)
        # self.row3.grid(row=3)
        # self.row4.grid(row=4)

        self.buttons(self.alpha)

    def buttons(self, letters):
        """show buttons"""
        row_ = 2  # row in grid
        for row in letters.keys():
            column_ = 0  # column in grid
            for alphabet in letters[row]:
                btn_ = ctk.CTkButton(self.master, text=alphabet, width=self.keysize_width, height=self.keysize_height,
                                     command= lambda k_=alphabet: self.attach_key_press(k_))
                btn_.grid(row=row_, column=column_, sticky="nsew")
                column_ += 1
            row_ += 1

    def attach_key_press(self, k_):
        """Assign the right function for the button pressed"""
        key_handlers = {
            "Backspace": self.handle_backspace,
            "Enter": self.handle_enter,
            "Cancel": self.handle_cancel,
            "↑": self.handle_upper,
            "123": self.handle_numbers,
            "[ space ]": self.handle_space,
            "gmail": self.handle_mail_com,
            "yahoo": self.handle_mail_com,
            "hotmail": self.handle_mail_com,
            ".com": self.handle_mail_com
        }

        if k_ in key_handlers:
            handler = key_handlers[k_]
            handler(k_) if k_ in ["gmail", "yahoo", "hotmail", ".com"] else handler()
        else:
            if isinstance(k_, int):  # if this isn't here, the keyboard will throw error saying ints can't be upper or lowercase
                self.handle_key(k_)
            else:
                if self.is_upper:  # if keys appear as uppercase on keyboard
                    k_ = k_.upper()  # the key should show as uppercase in the entry box when pressed
                else:
                    k_ = k_.lower()
                self.handle_key(k_)

    def configure_key_size(self):
        """
        calculate button height and width
        based on the screen width and height and number of button per row
        """
        items_per_row = max(len(row) for row in self.alpha.values())  # about 11 buttons per row
        self.keysize_width = int(self.keyboard_width / items_per_row)
        self.keysize_height = int(self.keyboard_height / 6)

    def handle_backspace(self):
        """
        Handles the backspace button
        """
        if isinstance(self.entry_box, ctk.CTkEntry):  #check if the entry box is an instance of ctk.CTkEntry
            current_text = self.entry_box.get()
            cursor_index = self.entry_box.index("insert")
            if cursor_index > 0:
                new_text = current_text[:cursor_index - 1] + current_text[cursor_index:]
                self.entry_box.delete(0, "end")
                self.entry_box.insert("end", new_text)
                # Set the cursor position to one character before the original position
                self.entry_box.icursor(cursor_index - 1)

    def handle_enter(self):
        """
        Handle Enter key press
        """
        entered_text = self.entry_box.get()
        # check the validity of the email
        is_valid = validate_email(entered_text,
                                  check_format=True,
                                  check_blacklist=True,
                                  check_dns=True,
                                  dns_timeout=10,
                                  check_smtp=True)
        if is_valid:
            self.enter()
        else:
            messagebox = CTkMessagebox(title="Invalid email", message="The email you have entered is invalid",
                          icon="question", option_1="Try again", option_2="Cancel")
            response = messagebox.get()
            if response == "Try again":
                messagebox.destroy()
            elif response == "Cancel":
                messagebox.destroy()
                self.cancel()

    def handle_cancel(self):
        """
        handles cancel button
        returns to home_page
        """
        self.cancel()

    def handle_numbers(self):
        """Handle 123 number key press"""
        if isinstance(self.entry_box, ctk.CTkEntry):
            if not self.number_row_frame:  # if number row frame is not activated/visible
                # create the number row
                self.number_row_frame = ctk.CTkFrame(self.master)
                self.number_row_frame.grid(row=1, column=0, columnspan=len(self.number['row0']), sticky="nsew")
                row_ = 0  # row in grid
                for row in self.number.keys():
                    column_ = 1  # column in grid
                    for number in self.number[row]:
                        btn_ = ctk.CTkButton(self.number_row_frame, text=number, width=self.keysize_width, height=self.keysize_height,
                                             command=lambda n_=number: self.attach_key_press(n_))
                        btn_.grid(row=row_, column=column_, sticky="nsew")
                        column_ += 1
                    row_ += 1
            else:
                # Remove the number row if it exists
                self.number_row_frame.destroy()
                self.number_row_frame = None

    def handle_upper(self):
        """
        Handle Upper key press
        Turns the key shown on keyboard into uppercase
        """
        # handle_upper was initially written to delete all button and then rebuild the button with keys with uppercase char
        # now it looks at the already made keyboard and turns all char into uppercase and vice versa
        # keep in mind the char may look like uppercase on keyboard but not show uppercase in the entry box when clicked
        # look at the else statement in attach_key_press() to see how the uppercase is implemented
        for widget in self.master.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") not in \
                    ["gmail", "yahoo", "hotmail", ".com", "Enter", "Backspace", "Cancel", "123",]:  # if widget is a button
                    widget.configure(text=widget.cget("text").swapcase())
        self.is_upper = not self.is_upper

    def handle_space(self):
        """handle space key press"""
        if isinstance(self.entry_box, ctk.CTkEntry):
            current_text = self.entry_box.get()
            cursor_index = self.entry_box.index("insert")
            new_text = current_text[:cursor_index] + " " + current_text[cursor_index:]
            self.entry_box.delete(0, "end")
            self.entry_box.insert("end", new_text)
            # Set the cursor position to one character after the inserted space
            self.entry_box.icursor(cursor_index + 1)

    def handle_mail_com(self, key):
        """handle .com, gmail, hotmail, yahoo key press"""
        if isinstance(self.entry_box, ctk.CTkEntry):
            current_text = self.entry_box.get()
            cursor_index = self.entry_box.index("insert")
            new_text = current_text[:cursor_index] + key + current_text[cursor_index:]
            self.entry_box.delete(0, "end")
            self.entry_box.insert("end", new_text)
            # Set the cursor position to one character after the inserted key
            self.entry_box.icursor(cursor_index + len(key))

    def handle_key(self, key):
        """handles every other key press including numbers"""
        # Handle other key presses
        # Perform the desired action
        if isinstance(self.entry_box, ctk.CTkEntry):
            current_text = self.entry_box.get()
            cursor_index = self.entry_box.index("insert")
            new_text = current_text[:cursor_index] + str(key) + current_text[cursor_index:]
            self.entry_box.delete(0, "end")
            self.entry_box.insert("end", new_text)
            # Set the cursor position to one character after the inserted key
            self.entry_box.icursor(cursor_index + 1)
