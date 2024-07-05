import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image
import time
import threading
import cv2
# from watermark import Watermark
from keyboard import Keyboard
from mail import EmailSender

PICTURE_COUNT_PATH = "saved_pictures/count.txt"
VIDEO_COUNT_PATH = "saved_videos/count.txt"


class UserInterface(ctk.CTkFrame):

    def __init__(self, master, login_cred):
        super().__init__(master)
        self.master = master
        # self.watermark = Watermark()
        self.mail = EmailSender()
        self.cred = login_cred

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()

        self.main_frame = None
        self.pressed_button = None
        self.home_page()  # initialise home page

        self.cap = None
        self.preview_frame = None
        self.preview_label = None
        self.review_frame = None
        self.review_label = None
        self.preview_size = None

        self.timer_label = None
        self.timer_start = None
        self.timer_end = None
        self.timer_thread = None

        self.last_picture_frame = None
        self.video_frames = []

        self.keyboard_page_frame = None
        self.entry_frame = None
        self.keyboard_frame = None
        self.keyboard = None
        self.email_entry = None
        self.email_entry_text = None
        self.user_email = None

        self.picture_path = None
        self.video_path = None

    # -------------------- PAGES --------------------#

    def home_page(self):
        """
        Set up the Main page
        """
        self.master.title("Darkroom Booth")
        self.master.attributes("-fullscreen", True)

        self.main_frame = ctk.CTkFrame(self.master, bg_color="red")
        self.main_frame.pack(expand=True, fill=ctk.BOTH)
        self._configure_grid(self.main_frame, rows=2, columns=3)  # Divide main_frame into a 2x3 grid

        # Top Row: Selfie Zone Title
        title_label = ctk.CTkLabel(self.main_frame, text="Selfie Zone",
                                   font=("Helvetica", int(self.screen_height / 20), "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, self.screen_height / 10))

        button_data = [
            {"image_path": "./button_images/picture.png"},
            {"image_path": "./button_images/boomerang.png"},
            {"image_path": "./button_images/video.png"},
        ]
        self._create_home_page_buttons(button_data)

    def preview_page(self):
        """handles what happens after the button on the homepage is pressed"""
        self._destroy_frame(self.main_frame)
        self.preview_frame = ctk.CTkFrame(self.master, width=self.screen_width, height=self.screen_height)
        self.preview_frame.pack(expand=True, fill=ctk.BOTH)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="", width=self.screen_width,
                                          height=self.screen_height)
        self.preview_label.grid(row=0, column=0, columnspan=3)

        self.timer_label = ctk.CTkLabel(self.preview_frame, text="", text_color="red", bg_color="transparent",
                                        font=("Helvetica", 25, "bold"))
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")  # place over preview_label

        self.preview_size = self.screen_height * 80 / 100

        # open camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()

        self._start_timer()

    def review_page(self, object_):
        """
        Review the image/video that was taken
        Show Accept, Retake and Return buttons
        :param object_: function takes a PIL image, or video frames
        """
        self._destroy_frame(self.preview_frame)
        self.review_frame = ctk.CTkFrame(self.master, width=self.screen_width, height=self.screen_height)
        self.review_frame.pack(expand=True, fill=ctk.BOTH)

        self.review_label = ctk.CTkLabel(self.review_frame, text="")
        self.review_label.grid(row=0, column=0, columnspan=3)

        if self.pressed_button == "picture":
            self._display_frame(object_)
        if self.pressed_button == "video":
            self._display_frame(object_[0])
            self.play_video_frame(object_, 1)  # Start playing the video frames recursively

        self._configure_grid(self.review_frame, rows=2, columns=3)
        self._create_review_buttons()

    def keyboard_page(self):
        """shows the keyboard"""
        # cancel button returns to homepage
        self._destroy_frame(self.review_frame)

        # calculate the desired dimensions of the keyboard
        keyboard_width = self.screen_width
        keyboard_height = self.screen_height * 70 / 100

        # create a new frame for keyboard and entry box
        self.keyboard_page_frame = ctk.CTkFrame(self.master, )
        self.keyboard_page_frame.pack(side="bottom", fill=ctk.BOTH, expand=True)

        # keyboard frame
        self.keyboard_frame = ctk.CTkFrame(self.keyboard_page_frame, width=keyboard_width, height=keyboard_height)
        self.keyboard_frame.pack(side="bottom", pady=(0, 10))

        # Entry box for email address
        self.entry_frame = ctk.CTkFrame(self.keyboard_frame)
        self.entry_frame.grid(row=0, column=0, columnspan=11, sticky="nsew")
        # entry box
        self.email_entry_text = tk.StringVar()
        self.email_entry = ctk.CTkEntry(self.entry_frame, textvariable=self.email_entry_text,
                                        width=self.screen_width, height=self.screen_height * 10 / 100)
        self.email_entry.focus()  # cursor goes to this input field
        self.email_entry.pack(side="bottom")

        # make keyboard buttons using Keyboard class
        self.keyboard = Keyboard(master=self.keyboard_frame, width=keyboard_width, height=keyboard_height,
                                 entry_box=self.email_entry, cancel=self.cancel_button, enter=self.save)

        self.entry_frame.grid_columnconfigure(0, weight=1)

    # -------------------- PREVIEW --------------------#
    def picture_preview(self):
        """show camera frames in preview_label"""
        try:
            # Get the latest frame and convert into Image
            ret, frame = self.cap.read()
            # if frame is read correctly ret is True
            if not ret:
                raise ValueError("Failed to capture video")

            # Convert the latest frame to RGB format
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert the NumPy array to PIL Image
            img = Image.fromarray(cv2image)
            ctk_image = ctk.CTkImage(dark_image=img, size=(self.preview_size, self.preview_size))
            self.preview_label.ctk_image = ctk_image  # avoid garbage collection
            self.preview_label.configure(image=ctk_image)

            if time.time() - self.timer_start > 3:  # start saving the frames after 3 seconds
                # self.last_frame will eventually be equal to the very last frame which will be displayed in the review
                self.last_picture_frame = frame

            if time.time() <= self.timer_end:
                # Repeat after an interval to capture continuously
                self.preview_label.after(10, self.picture_preview)
            else:
                self.cap.release()  # close the camera
                self.review_page(self.last_picture_frame)  # pass captured image for review
        except Exception as e:
            print(f"Error in showing picture frames: {e}")

    def video_preview(self):
        """show camera frames in preview_label"""
        try:
            # Capture frame-by-frame
            ret, frame = self.cap.read()
            # if frame is read correctly ret is True
            if not ret:
                raise ValueError("Failed to capture video")

            # Convert the latest frame to RGB format
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert the NumPy array to PIL Image
            img = Image.fromarray(cv2image)
            ctk_image = ctk.CTkImage(dark_image=img, size=(self.preview_size, self.preview_size))
            self.preview_label.ctk_image = ctk_image  # avoid garbage collection
            self.preview_label.configure(image=ctk_image)

            if time.time() - self.timer_start > 3:  # start saving the frames after 3 seconds
                self.video_frames.append(frame)

            if time.time() <= self.timer_end:
                # Repeat after an interval to capture continuously
                self.preview_label.after(20, self.video_preview)
            else:
                self.cap.release()  # close the camera
                self.review_page(self.video_frames)  # open the review page
        except Exception as e:
            print(f"Error in showing video frames: {e}")

    def play_video_frame(self, frames, index):
        """
        Play next frame in video_frames list.
        :param frames: list of video_frames
        :param index: index of next frame to play
        """
        if index < len(frames):
            # Convert the frame to RGB format
            cv2image = cv2.cvtColor(frames[index], cv2.COLOR_BGR2RGB)
            # Convert the NumPy array to PIL Image
            img = Image.fromarray(cv2image)

            # Create a ctk.CTkImage from the frame
            ctk_image = ctk.CTkImage(dark_image=img, size=(self.screen_width, self.screen_height * 0.9))
            self.review_label.ctk_image = ctk_image  # Avoid garbage collection
            self.review_label.configure(image=ctk_image)

            # Schedule the next frame to be played after a delay (e.g., 100 milliseconds)
            self.review_label.after(15, self.play_video_frame, frames, index + 1)

    # -------------------- SAVE FUNCTIONS --------------------#

    def save(self):
        """watermark and save picture and video when enter key on keyboard is pressed"""
        self.user_email = self.email_entry.get()  # get the typed in user password
        count = self._get_count()

        save_thread = threading.Thread(target=self._save_and_send, args=(count,))
        save_thread.start()

        # Destroy the existing keyboard frame if it exists and return home
        self._destroy_frame(self.keyboard_page_frame)
        self.home_page()

    def _save_and_send(self, count):
        """save picture or video and send email in a background thread"""
        if self.pressed_button == "picture":
            self._save_picture(count)
        if self.pressed_button == "video":
            self._save_video(count)

        # update the number in count.txt
        self._update_count(count=count)
        # send the email
        self.send_email()

    def _save_video(self, count):
        if self.video_frames:
            self.video_path = f"saved_videos/{count}.mp4"
            # Create a VideoWriter object to save the frames as a video file
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # VideoWriter args - path, fps, frame size
            video_writer = cv2.VideoWriter(self.video_path, fourcc, 20.0, (640, 480))
            # Write each frame to the video file
            for frame in self.video_frames:
                video_writer.write(frame)  # write the flipped frame
            # Release the video writer
            video_writer.release()
            # Apply watermark to the video file
            # self.watermark.apply_video_watermark(accepted_video_path=self.video_path)

    def _save_picture(self, count):
        if self.last_picture_frame is not None:
            # Resize the frame before saving
            resized_frame = cv2.resize(self.last_picture_frame, (
                1280, 853))
            # Convert the frame to RGB format
            # frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            # Save the resized frame as an image
            self.picture_path = f"saved_pictures/{count}.jpeg"
            cv2.imwrite(filename=self.picture_path, img=resized_frame)
            # Apply watermark to the image
            # self.watermark.apply_picture_watermark(accepted_picture_path=self.picture_path)

    def send_email(self):
        """send email containing picture"""
        # get email from entry box
        if self.pressed_button == "picture":
            self.mail.send_email(self.cred, self.user_email, self.picture_path)
        if self.pressed_button == "video":
            # watermarked_video_path = self.video_path.replace('.mp4', '_watermarked.mp4')
            self.mail.send_email(self.cred, self.user_email, self.video_path)

        self.user_email = None

    # -------------------- BUTTONS FUNCTIONS --------------------#

    def accept_button(self):
        """pressing the accept button leads to keyboard page"""
        self.keyboard_page()

    def retake_button(self):
        """Retake the picture"""
        if self.review_frame is not None:
            self.review_frame.destroy()
        if self.pressed_button == "picture":
            self.last_picture_frame = None  # get rid of the last picture taken
            self.preview_page()
        elif self.pressed_button == "video":
            self.video_frames = []  # get rid of the old video by making the list empty again
            self.preview_page()

    def cancel_button(self):
        """Return to main page"""
        if self.review_frame is not None:
            self.review_frame.destroy()
        if self.keyboard_page_frame is not None:
            self.keyboard_page_frame.destroy()
        self.last_picture_frame = None
        self.video_frames = []
        self.home_page()

    def _create_home_page_buttons(self, button_data):
        # Calculate the button width and height based on screen size
        button_width = int(self.screen_width / 6)  # Divide the width equally into 6 parts for 3 buttons and gaps
        button_height = int(self.screen_height / 5)  # Divide the height equally to create a square button

        for i, data in enumerate(button_data):
            image = ctk.CTkImage(light_image=Image.open(data["image_path"]), size=(button_width, button_height))
            button = ctk.CTkButton(self.main_frame, text="", image=image)
            button.grid(row=1, column=i, padx=(self.screen_width / 30, 0))
            button.bind("<Button-1>", lambda event, index=i: self._select_home_page_buttons(event, index))
            button.bind("<ButtonRelease-1>", lambda event, index=i: self._select_home_page_buttons(event, index))

    def _select_home_page_buttons(self, event, index):
        """
        select what functions to call - picture, boomerang, video
        :param event:
        :param index: The index of the button pressed
        """
        actions = {0: "picture", 1: "boomerang", 2: "video"}
        self.pressed_button = actions.get(index)
        self.preview_page()  # Go to preview page after button is clicked

    def _create_review_buttons(self):
        buttons = [
            {"text": "Accept", "command": self.accept_button, "col": 0, "padx": (self.screen_height / 30, 0)},
            {"text": "Retake", "command": self.retake_button, "col": 1,
             "padx": (self.screen_width / 30, self.screen_width / 30)},
            {"text": "Cancel", "command": self.cancel_button, "col": 2, "padx": (0, self.screen_width / 30)},
        ]
        for button in buttons:
            ctk.CTkButton(self.review_frame, text=button["text"],
                          command=button["command"]).grid(row=1, column=button["col"], padx=button["padx"])

    # -------------------- HELPER FUNCTIONS --------------------#

    @staticmethod
    def _configure_grid(frame, rows, columns):
        for row in range(rows):
            frame.grid_rowconfigure(row, weight=1)
        for col in range(columns):
            frame.grid_columnconfigure(col, weight=1)

    def _get_count(self):
        """Read count.txt"""
        count_file = ""
        if self.pressed_button == "picture":
            count_file = PICTURE_COUNT_PATH
        elif self.pressed_button == "video":
            count_file = VIDEO_COUNT_PATH

        if os.path.exists(count_file):
            with open(count_file, "r") as file:
                count_ = int(file.read())
                return count_
        else:
            with open(count_file, "x") as file:  # create a new file and open it for writing
                count_ = 0
                file.write(str(count_))
                return count_

    def _update_count(self, count):
        """update the count.txt"""
        count_file = int
        if self.pressed_button == "picture":
            count_file = PICTURE_COUNT_PATH
        elif self.pressed_button == "video":
            count_file = VIDEO_COUNT_PATH

        with open(count_file, "w") as file:
            file.write(str(count + 1))

    def _start_timer(self):
        self.timer_start = time.time()
        if self.pressed_button == "picture":
            self.timer_end = time.time() + 3  # timer for 3 seconds
            self.picture_preview()  # show camera frames in the preview_label
        elif self.pressed_button == "video":
            self.timer_end = time.time() + 10  # timer for 10 seconds
            self.video_preview()  # show camera frames in the preview_label

        self.timer_thread = threading.Thread(target=self._update_timer)
        self.timer_thread.start()

    def _update_timer(self):
        """
        Update timer for picture/video
        release camera and call review_picture()
        """
        if self.pressed_button == "picture":
            while time.time() < self.timer_end:
                remaining_time = int(self.timer_end - time.time())
                self.timer_label.configure(text=f"{remaining_time}s")
                time.sleep(0.1)
        elif self.pressed_button == "video":
            while time.time() < self.timer_end:
                remaining_time = int(self.timer_end - time.time())
                self.timer_label.configure(text=f"{remaining_time}s")
                time.sleep(0.1)

        # self.timer_label.destroy()

    def _display_frame(self, frame):
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert the frame to RGB format
        img = Image.fromarray(cv2image)  # Convert the NumPy array to PIL Image
        ctk_image = ctk.CTkImage(dark_image=img, size=(self.screen_width, self.screen_height * 0.9))
        self.review_label.ctk_image = ctk_image  # Avoid garbage collection
        self.review_label.configure(image=ctk_image)  # configure the label to show the image

    @staticmethod
    def _destroy_frame(frame):
        if frame:
            frame.destroy()
