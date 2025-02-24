import os
import time
import logging
import tkinter as tk
import tempfile
import subprocess
import threading
import customtkinter as ctk
from PIL import Image
from mail import EmailSender
from keyboard import Keyboard
from watermark import Watermark
from CTkMessagebox import CTkMessagebox
from typing import Union, Any, Optional, List
from file_manager import FileManager, MediaType
from camera_utils.camera_canon import CanonCamera

class UserInterface(ctk.CTkFrame):
    """Main application interface for the photo booth system.
    
    Handles UI layout, camera management, media processing, and user interactions.
    
    Args:
        master (tk.Tk): Root window instance
        login_cred: User credentials for email services
        logger (logging.Logger): Logger instance for diagnostics
    
    Attributes:
        camera_manager (CameraManager): Controls camera operations
        media_path (str): Path to last saved media file
        user_email (str): Email address entered by user
    """
    def __init__(self, master: tk.Tk, login_cred: Any, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(master)
        self.master = master
        self.mail = EmailSender(logger)
        self.watermark = Watermark(logger)
        self.cred = login_cred

        self.logger = logger.getChild(self.__class__.__name__)

        # Initialize counts file
        FileManager.initialize_counts_file()

        # Screen dimensions
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()

        # UI components
        self.main_frame = None
        self.pressed_button = None
        self.preview_frame = None
        self.preview_label = None
        self.review_frame = None
        self.review_label = None
        self.preview_size = None
        self.timer_label = None
        self.timer_start = None
        self.timer_end = None
        self.timer_thread = None

        self.camera = None

        # Media storage
        self.last_picture_frame = None
        self.boomerang_frames = []
        self.video_frames = []

        # Keyboard components
        self.keyboard_page_frame = None
        self.entry_frame = None
        self.keyboard_frame = None
        self.keyboard = None
        self.email_entry = None
        self.email_entry_text = None
        self.user_email = None

        # File paths
        self.media_path = None

        # Initialize home page
        self.home_page()

    def home_page(self) -> None:
        """Initialize and display the main landing page.
        
        Creates the primary interface with media selection buttons and title.
        Handles grid layout configuration for responsive design.
        """
        self.logger.info("Initializing home page")
        try:
            self.master.title("Darkroom Booth")
            self.master.attributes("-fullscreen", True)

            self.main_frame = ctk.CTkFrame(self.master, bg_color="red")
            self.main_frame.pack(expand=True, fill=ctk.BOTH)
            self._configure_grid(self.main_frame, rows=2, columns=3)

            title_label = ctk.CTkLabel(self.main_frame, text="Selfie Zone",
                                       font=("Helvetica", int(self.screen_height / 20), "bold"))
            title_label.grid(row=0, column=0, columnspan=3, pady=(0, self.screen_height / 10))

            button_data = [
                {"image_path": "./button_images/picture.png", "media_type": MediaType.PICTURE},
                {"image_path": "./button_images/boomerang.png", "media_type": MediaType.BOOMERANG},
                {"image_path": "./button_images/video.png", "media_type": MediaType.VIDEO},
            ]
            self._create_home_page_buttons(button_data)
        except Exception as e:
            self.logger.error(f"Error in home page initialization: {e}")

    def preview_page(self) -> None:
        """Transition to camera preview interface.
        
        Handles:
        - Destruction of home page elements
        - Camera initialization with retry logic
        - Countdown timer startup
        - Preview frame setup
        
        Raises:
            RuntimeError: If camera fails to initialize
        """
        try:
            self._destroy_frame(self.main_frame)
            self._setup_preview_frame()
            self._initialize_camera()

            if not self._wait_for_camera_ready():
                raise RuntimeError("Camera not ready after initialization")

            initial_frame = self.camera.capture_and_process_frame(
                preview_size=(int(self.preview_size), int(self.preview_size))
            )
            if initial_frame:
                ctk_image = ctk.CTkImage(dark_image=initial_frame,
                                         size=(self.preview_size, self.preview_size))
                self.preview_label.configure(image=ctk_image)
                self.preview_label.ctk_image = ctk_image

            self._start_timer()
            self.logger.info("Preview page initialized")
        except Exception as e:
            self._handle_camera_error(str(e))

    def review_page(self, media_content: Union[Image.Image, List[Image.Image]]) -> None:
        """Display captured media for user review.
        
        Args:
            media_content (Union[np.ndarray, List[np.ndarray]]): Captured media data
        
        Shows:
        - Image preview or video playback
        - Action buttons (Accept/Retake/Cancel)
        - Auto-plays video/boomerang content
        """
        self.logger.info("Initializing review page")
        try:
            self._destroy_frame(self.preview_frame)
            self._setup_review_frame()
            self._display_media_content(media_content)
            self._create_review_buttons()
            self.logger.info("Review page initialized")
        except Exception as e:
            self.logger.error(f"Error in review page initialization: {e}")

    def _setup_preview_frame(self) -> None:
        """Set up the preview frame and labels"""
        self.preview_frame = ctk.CTkFrame(self.master, width=self.screen_width, height=self.screen_height)
        self.preview_frame.pack(expand=True, fill=ctk.BOTH)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="", width=self.screen_width,
                                          height=self.screen_height)
        self.preview_label.grid(row=0, column=0, columnspan=3)

        self.timer_label = ctk.CTkLabel(self.preview_frame, text="", text_color="red",
                                        bg_color="transparent", font=("Helvetica", 25, "bold"))
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")

        self.preview_size = self.screen_height * 80 / 100

    def _initialize_camera(self) -> None:
        """Initialize camera hardware with error handling.
        
        Attempts to create CanonCamera instance first, falls back to OpenCV if needed.
        Implements USB reset and process cleanup for reliability.
        
        Raises:
            RuntimeError: If camera initialization fails after retries
        """
        try:
            self.camera = CanonCamera(logger=self.logger)
            if not self.camera.initialize():
                raise RuntimeError("Failed to initialize camera after multiple attempts")
        except Exception as e:
            raise RuntimeError(f"Camera initialization failed: {str(e)}")

    def _setup_review_frame(self) -> None:
        """Set up the review frame and label"""
        self.review_frame = ctk.CTkFrame(self.master, width=self.screen_width, height=self.screen_height)
        self.review_frame.pack(expand=True, fill=ctk.BOTH)
        self._configure_grid(self.review_frame, rows=2, columns=3)

        self.review_label = ctk.CTkLabel(self.review_frame, text="")
        self.review_label.grid(row=0, column=0, columnspan=3)

    def _display_media_content(self, content: Union[Image.Image, List[Image.Image]]) -> None:
        """Display the appropriate media content based on type"""
        display_methods = {
            MediaType.PICTURE: lambda: self._display_frame(content),
            MediaType.BOOMERANG: lambda: self.play_video_frame(content, 1),
            MediaType.VIDEO: lambda: self.play_video_frame(content, 1)
        }
        display_methods[self.pressed_button]()

    def update_preview(self) -> None:
        """Update live camera preview display.
        
        Continuously captures and processes frames from camera.
        Handles media type-specific capture logic.
        
        Returns:
            None: Updates UI elements directly
            
        Raises:
            CameraError: If frame capture fails consistently
        """
        try:
            pil_image = self.camera.capture_and_process_frame(
                preview_size=(int(self.preview_size), int(self.preview_size))
            )
            if pil_image is None:
                # Try to recover camera
                if self.camera.is_initialized():
                    self.camera.release()
                self._initialize_camera()
                if not self._wait_for_camera_ready():
                    raise ValueError("Failed to recover camera preview")
                return

            ctk_image = ctk.CTkImage(dark_image=pil_image,
                                   size=(self.preview_size, self.preview_size))
            self.preview_label.configure(image=ctk_image)
            self.preview_label.ctk_image = ctk_image  # avoid garbage collection

            current_time = time.time()
            self._handle_media_capture(current_time, pil_image)

        except Exception as e:
            self.logger.error(f"Error in showing {self.pressed_button} frames: {e}")
            self._handle_camera_error(f"Preview failed: {e}")

    def _handle_media_capture(self, current_time: float, frame: Image.Image) -> None:
        """Handle media capture based on type"""
        capture_handlers = {
            MediaType.PICTURE: self._handle_picture_capture,
            MediaType.BOOMERANG: self._handle_boomerang_capture,
            MediaType.VIDEO: self._handle_video_capture
        }
        capture_handlers[self.pressed_button](current_time, frame)

    def _handle_picture_capture(self, current_time, frame):
        """Handle picture capture timing and storage"""
        if current_time - self.timer_start > 3:
            camera_file = self.camera.capture_picture()
            # Store raw file temporarily
            self.media_path = None  # Will be set when saving
            if camera_file:
                temp_path = FileManager.get_temp_path(MediaType.PICTURE)
                camera_file.save(temp_path)
                self.last_picture_frame = Image.open(temp_path)

        if current_time <= self.timer_end:
            self.preview_label.after(33, self.update_preview)
        else:
            self.camera.release()
            self.review_page(self.last_picture_frame)

    def _handle_boomerang_capture(self, current_time, frame):
        """Handle boomerang capture timing and storage"""
        if current_time - self.timer_start > 0:
            self.boomerang_frames.append(frame)

        if current_time <= self.timer_end:
            self.preview_label.after(33, self.update_preview)
        else:
            self.camera.release()
            self.arrange_boomerang_frames()
            self.review_page(self.boomerang_frames)

    def _handle_video_capture(self, current_time, frame):
        """Handle video capture timing and storage"""
        if current_time - self.timer_start > 3:
            self.video_frames.append(frame)

        if current_time <= self.timer_end:
            self.preview_label.after(33, self.update_preview)
        else:
            self.camera.release()
            self.review_page(self.video_frames)

    # Save and send functions
    def save(self) -> None:
        """Save media and send email"""
        self.user_email = self.email_entry.get()
        save_thread = threading.Thread(target=self._save_and_send)
        save_thread.start()
        self._destroy_frame(self.keyboard_page_frame)
        self.home_page()

    def _save_and_send(self) -> None:
        """Save media content and send email in background thread"""
        try:
            count = FileManager.increment_count(self.pressed_button)
            self.media_path = FileManager.get_save_path(self.pressed_button, count)
            
            save_methods = {
                MediaType.PICTURE: self._save_picture,
                MediaType.BOOMERANG: self._save_boomerang,
                MediaType.VIDEO: self._save_video
            }
            
            # Save and watermark the media
            save_methods[self.pressed_button]()
            
            # Apply watermark based on media type
            if self.pressed_button == MediaType.PICTURE:
                self.watermark.apply_picture_watermark(self.media_path)
            else:
                self.watermark.apply_video_watermark(self.media_path)
                
            # Send email only after watermarking is complete
            self.send_email()
            
        except Exception as e:
            self.logger.error(f"Error in saving and sending media: {e}")
        finally:
            self.user_email = None

    def _save_boomerang(self) -> None:
        """Save boomerang frames using FFmpeg"""
        try:
            if not self.boomerang_frames:
                return

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save frames as individual images
                for i, frame in enumerate(self.boomerang_frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:04d}.jpg")
                    frame.save(frame_path)

                # Use FFmpeg to create the boomerang effect directly
                subprocess.run([
                    'ffmpeg', '-y', '-framerate', '30',
                    '-i', os.path.join(temp_dir, 'frame_%04d.jpg'),
                    '-filter_complex', "[0:v]reverse[r];[0:v][r]concat=n=2:v=1[v];[v]setpts=0.5*PTS[outv]",
                    '-map', "[outv]", '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-preset', 'ultrafast', self.media_path
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Verify the file was created
                if not os.path.exists(self.media_path) or os.path.getsize(self.media_path) == 0:
                    raise RuntimeError("Boomerang video file was not created successfully")

        except Exception as e:
            self.logger.error(f"Failed to save boomerang video: {e}")
            if os.path.exists(self.media_path):
                os.remove(self.media_path)
            raise



    def _save_picture(self) -> None:
        """Save picture with final path"""
        if self.last_picture_frame:
            self.last_picture_frame.save(self.media_path)

    def _save_video(self) -> None:
        """Save video frames using moviepy"""
        if not self.video_frames:
            return

        try:
            from moviepy.editor import ImageSequenceClip
            import numpy as np
            
            # Convert frames to numpy arrays
            frame_arrays = [np.array(frame) for frame in self.video_frames]
            
            # Create and write video
            clip = ImageSequenceClip(frame_arrays, fps=30)
            clip.write_videofile(self.media_path, codec='libx264', fps=30, threads=4, preset='ultrafast')

            # Verify the file was created
            if not os.path.exists(self.media_path) or os.path.getsize(self.media_path) == 0:
                raise RuntimeError("Video file was not created successfully")

        except Exception as e:
            self.logger.error(f"Failed to save video: {e}")
            if os.path.exists(self.media_path):
                os.remove(self.media_path)
            raise

    def send_email(self) -> None:
        """Send captured media to user's email address.
        
        Requires:
        - Valid user credentials
        - Saved media file path
        - Active internet connection
        
        Note:
            Runs in background thread to avoid UI blocking
        """
        if self.media_path and self.user_email:
            media_type = self.pressed_button.lower()
            self.mail.send_email(self.cred, self.user_email, self.media_path, media_type)
        self.user_email = None

    # UI Helper Methods
    def keyboard_page(self) -> None:
        """Set up keyboard page"""
        self._destroy_frame(self.review_frame)
        self._setup_keyboard()

    def _setup_keyboard(self) -> None:
        """Set up keyboard UI components"""
        keyboard_width = self.screen_width
        keyboard_height = int(self.screen_height * 70 / 100)

        self.keyboard_page_frame = ctk.CTkFrame(self.master)
        self.keyboard_page_frame.pack(side="bottom", fill=ctk.BOTH, expand=True)

        self.keyboard_frame = ctk.CTkFrame(self.keyboard_page_frame, width=keyboard_width, height=keyboard_height)
        self.keyboard_frame.pack(side="bottom", pady=(0, 10))

        self._setup_email_entry()
        self._setup_keyboard_buttons(keyboard_width, keyboard_height)

    def _setup_email_entry(self):
        """Set up email entry field"""
        self.entry_frame = ctk.CTkFrame(self.keyboard_frame)
        self.entry_frame.grid(row=0, column=0, columnspan=11, sticky="nsew")
        self.email_entry_text = tk.StringVar()
        self.email_entry = ctk.CTkEntry(self.entry_frame, textvariable=self.email_entry_text,
                                        width=self.screen_width, height=int(self.screen_height * 10 / 100))
        self.email_entry.focus()
        self.email_entry.pack(side="bottom")
        self.entry_frame.grid_columnconfigure(0, weight=1)

    def _setup_keyboard_buttons(self, keyboard_width, keyboard_height):
        """Set up keyboard buttons"""
        self.keyboard = Keyboard(master=self.keyboard_frame, width=keyboard_width, height=keyboard_height,
                                 entry_box=self.email_entry, cancel=self.cancel_button, enter=self.save)

    # Review button Actions
    def accept_button(self) -> None:
        """Handle accept button press"""
        self.keyboard_page()

    def retake_button(self) -> None:
        """Handle retake button press"""
        self._destroy_frame(self.review_frame)
        self._clear_media_buffers()
        self.preview_page()

    def cancel_button(self) -> None:
        """Handle cancel button press"""
        self._destroy_frame(self.keyboard_page_frame)
        self._destroy_frame(self.review_frame)
        self._clear_media_buffers()
        FileManager.cleanup_temp_files()
        self.home_page()

    def _clear_media_buffers(self):
        """Clear all media buffers and temporary files"""
        self.last_picture_frame = None
        self.boomerang_frames = []
        self.video_frames = []
        FileManager.cleanup_temp_files()

    # Helper Methods
    @staticmethod
    def _configure_grid(frame, rows, columns):
        """Configure grid layout"""
        for row in range(rows):
            frame.grid_rowconfigure(row, weight=1)
        for col in range(columns):
            frame.grid_columnconfigure(col, weight=1)

    @staticmethod
    def _destroy_frame(frame):
        """Safely destroy a frame"""
        if frame:
            frame.destroy()

    def _handle_camera_error(self, error_message):
        """Handle camera errors"""
        messagebox = CTkMessagebox(
            title="Camera Error",
            message=f"Camera error: {error_message}\nPlease check your camera connection.",
            icon="cancel"
        )
        if messagebox.get() == "OK":
            self._destroy_frame(self.preview_frame)
            self.home_page()

    def _start_timer(self):
        """Start the capture timer"""
        self.timer_start = time.time()
        timer_durations = {
            MediaType.PICTURE: 3,
            MediaType.BOOMERANG: 4,
            MediaType.VIDEO: 10
        }
        self.timer_end = time.time() + timer_durations[self.pressed_button]
        self.update_preview()
        self.timer_thread = threading.Thread(target=self._update_timer)
        self.timer_thread.start()

    def _update_timer(self):
        """Update the timer display"""

        while time.time() < self.timer_end:
            remaining_time = int(self.timer_end - time.time())
            if self.timer_label and self.timer_label.winfo_exists():
                self.timer_label.configure(text=f"{remaining_time}s")
            time.sleep(0.1)

        if self.timer_label and self.timer_label.winfo_exists():
            self.timer_label.after(0, self.timer_label.destroy())

    def arrange_boomerang_frames(self):
        """Process frames to create boomerang effect using FFmpeg"""
        try:
            import tempfile
            import subprocess
            from moviepy.editor import VideoFileClip

            # Create a temporary directory to store frames
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save collected frames as images
                for i, frame in enumerate(self.boomerang_frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:04d}.jpg")
                    frame.save(frame_path)

                # Create temporary output path for the boomerang video
                output_path = os.path.join(temp_dir, "boomerang.mp4")

                # Create boomerang effect directly from image sequence without intermediate video
                subprocess.run([
                    'ffmpeg', '-y', '-framerate', '30',
                    '-i', os.path.join(temp_dir, 'frame_%04d.jpg'),
                    '-filter_complex', "[0:v]reverse[r];[0:v][r]concat=n=2:v=1[v];[v]setpts=0.5*PTS[outv]",
                    '-map', "[outv]", '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-preset', 'ultrafast', output_path
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Load processed video back as frames
                video = VideoFileClip(output_path)
                fps = video.fps
                duration = video.duration
                frame_count = int(fps * duration)

                # Extract frames from processed video
                self.boomerang_frames = []
                for i in range(frame_count):
                    time = i / fps
                    img = video.get_frame(time)
                    pil_img = Image.fromarray(img)
                    self.boomerang_frames.append(pil_img)

        except Exception as e:
            self.logger.error(f"Error processing boomerang with FFmpeg: {e}")
            # Fallback to the simple frame reversal if FFmpeg fails
            collected_frames = self.boomerang_frames
            complete_boomerang = []
            for i in range(3):
                frames = collected_frames if i % 2 == 0 else collected_frames[::-1]
                complete_boomerang.extend(frames)
            self.boomerang_frames = complete_boomerang

    def play_video_frame(self, frames, index):
        """Play video frames sequentially"""
        if not frames:
            return

        if index < len(frames):
            frame = frames[index]
            img = frame  # frame is already a PIL Image
            ctk_image = ctk.CTkImage(dark_image=img, size=(self.screen_width, int(self.screen_height * 0.9)))
            self.review_label.ctk_image = ctk_image
            self.review_label.configure(image=ctk_image)
            self.review_label.after(33, self.play_video_frame, frames, index + 1)

    def _create_home_page_buttons(self, button_data):
        """Create home page buttons"""
        button_width = int(self.screen_width / 6)
        button_height = int(self.screen_height / 5)

        for i, data in enumerate(button_data):
            image = ctk.CTkImage(light_image=Image.open(data["image_path"]),
                                 size=(button_width, button_height))
            button = ctk.CTkButton(self.main_frame, text="", image=image)
            button.grid(row=1, column=i, padx=(self.screen_width / 30, 0))
            button.bind("<Button-1>",
                        lambda event, media_type=data["media_type"]: self._handle_button_press(event, media_type))
            button.bind("<ButtonRelease-1>",
                        lambda event, media_type=data["media_type"]: self._handle_button_press(event, media_type))

    def _handle_button_press(self, event, media_type):
        """Handle home page button press"""
        self.pressed_button = media_type
        self.preview_page()

    def _create_review_buttons(self):
        """Create review page buttons"""
        buttons = [
            {"text": "Accept", "command": self.accept_button, "col": 0,
             "padx": (self.screen_height / 30, 0)},
            {"text": "Retake", "command": self.retake_button, "col": 1,
             "padx": (self.screen_width / 30, self.screen_width / 30)},
            {"text": "Cancel", "command": self.cancel_button, "col": 2,
             "padx": (0, self.screen_width / 30)},
        ]
        for button in buttons:
            ctk.CTkButton(
                self.review_frame,
                text=button["text"],
                command=button["command"]
            ).grid(row=1, column=button["col"], padx=button["padx"])

    def _display_frame(self, frame):
        """Display a single frame"""
        try:
            if isinstance(frame, Image.Image):
                img = frame
            else:
                img = Image.fromarray(frame)
            ctk_image = ctk.CTkImage(dark_image=img,
                                     size=(self.screen_width, int(self.screen_height * 0.9)))
            self.review_label.ctk_image = ctk_image
            self.review_label.configure(image=ctk_image)
        except Exception as e:
            self.logger.error(f"Error in displaying frame: {e}")

    def _wait_for_camera_ready(self) -> bool:
        """Wait for camera to be fully initialized and able to capture frames.

        Returns:
            bool: True if camera is ready, False if timeout or error
        """
        max_attempts = 4
        delay = 0.5  # half second between attempts

        for _ in range(max_attempts):
            try:
                # Try to capture a test frame
                test_frame = self.camera.capture_and_process_frame(
                    preview_size=(int(self.preview_size), int(self.preview_size))
                )
                if test_frame is not None:
                    return True
            except Exception as e:
                self.logger.warning(f"Camera not yet ready: {e}")
            time.sleep(delay)

        return False
