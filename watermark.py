import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


class Watermark:
    def __init__(self, logger=None):
        self.watermark_image_path = "watermark/watermark.png"
        self.watermark_text = "#RushClaremont"
        self.logger = logger.getChild(self.__class__.__name__)
        # self.accepted_image = accepted_image_path

    def apply_picture_watermark(self, accepted_picture_path: str) -> bool:
        """
        Apply watermark image and text to a picture.

        Args:
            accepted_picture_path (str): Path to the image file to watermark

        Returns:
            bool: True if watermark was applied successfully, False otherwise
        """
        try:
            # Validate input paths
            if not os.path.exists(accepted_picture_path):
                raise ValueError(f"Input image not found: {accepted_picture_path}")
            if not os.path.exists(self.watermark_image_path):
                raise ValueError(f"Watermark image not found: {self.watermark_image_path}")

            # Open images with context managers for proper resource handling
            with Image.open(accepted_picture_path) as accepted_image:
                # Create a copy to work with
                watermarked_image = accepted_image.convert('RGBA')

                # Process watermark image
                with Image.open(self.watermark_image_path) as watermark_image:
                    watermark_image = watermark_image.convert('RGBA')

                    # Calculate watermark size (25% of original image width)
                    watermark_width = int(accepted_image.width * 0.25)
                    watermark_height = int(watermark_image.height *
                                           (watermark_width / watermark_image.width))

                    # Resize watermark maintaining aspect ratio
                    watermark_resized = watermark_image.resize(
                        (watermark_width, watermark_height),
                        Image.Resampling.LANCZOS
                    )

                    # Calculate position for bottom right corner
                    watermark_position = (
                        watermarked_image.width - watermark_resized.width - 10,
                        watermarked_image.height - watermark_resized.height - 10
                    )

                    # Paste watermark image
                    watermarked_image.paste(
                        watermark_resized,
                        watermark_position,
                        watermark_resized
                    )

                # Add text watermark
                draw = ImageDraw.Draw(watermarked_image)

                try:
                    font_size = watermark_height // 7
                    watermark_font = ImageFont.truetype("./watermark/arial.ttf", font_size)
                except OSError:
                    self.logger.error("Failed to load font, using default")
                    watermark_font = ImageFont.load_default()

                # Get text size for positioning
                bbox = draw.textbbox((0, 0), self.watermark_text, font=watermark_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Calculate text position for far left corner
                text_position = (
                    10,  # 10px padding from left
                    watermark_position[1] + (watermark_height - text_height) // 2
                )

                # Add text with outline
                outline_color = (0, 0, 0)
                text_color = (255, 255, 255)
                outline_width = 2

                for offset_x in range(-outline_width, outline_width + 1):
                    for offset_y in range(-outline_width, outline_width + 1):
                        draw.text(
                            (text_position[0] + offset_x, text_position[1] + offset_y),
                            self.watermark_text,
                            font=watermark_font,
                            fill=outline_color
                        )

                draw.text(
                    text_position,
                    self.watermark_text,
                    font=watermark_font,
                    fill=text_color
                )

                # Convert back to RGB before saving as JPEG
                if watermarked_image.mode == 'RGBA':
                    watermarked_image = watermarked_image.convert('RGB')

                # Save with optimal quality
                watermarked_image.save(
                    accepted_picture_path,
                    'JPEG',
                    quality=95,
                    optimize=True
                )
                self.logger.info("Watermark applied to picture successfully!")
                return True

        except Exception as e:
            self.logger.error(f"Failed to apply watermark: {str(e)}")
            return False

    def apply_video_watermark(self, accepted_video_path: str) -> bool:
        """Apply watermark to video using OpenCV"""
        try:
            input_video = cv2.VideoCapture(accepted_video_path)
            if not input_video.isOpened():
                raise RuntimeError("Could not open video file")

            # Get video properties
            width = int(input_video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(input_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = input_video.get(cv2.CAP_PROP_FPS)

            # Load and resize watermark image
            watermark_img = cv2.imread(self.watermark_image_path, cv2.IMREAD_UNCHANGED)
            if watermark_img is None:
                raise RuntimeError("Could not load watermark image")

            # Calculate watermark size (25% of video width)
            watermark_width = int(width * 0.25)
            watermark_height = int(watermark_img.shape[0] * (watermark_width / watermark_img.shape[1]))
            watermark_img = cv2.resize(watermark_img, (watermark_width, watermark_height))

            # Create output video
            temp_path = accepted_video_path.replace('.mp4', '_temp.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_video = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            # Font settings for text watermark
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = watermark_height / 300
            font_thickness = 2

            text_y = height - watermark_height // 2 - 10

            while True:
                ret, frame = input_video.read()
                if not ret:
                    break

                # Image watermark at bottom right
                roi = frame[height - watermark_height - 10:height - 10, width - watermark_width - 10:width - 10]
                if watermark_img.shape[2] == 4:
                    alpha = watermark_img[:, :, 3] / 255.0
                    for c in range(3):
                        roi[:, :, c] = roi[:, :, c] * (1 - alpha) + watermark_img[:, :, c] * alpha

                # Text at far left aligned with image
                cv2.putText(frame, self.watermark_text, (10, text_y), font, font_scale, (0, 0, 0),
                            font_thickness + 2)
                cv2.putText(frame, self.watermark_text, (10, text_y), font, font_scale, (255, 255, 255),
                            font_thickness)

                out_video.write(frame)

            # Release resources
            input_video.release()
            out_video.release()

            # Replace original with watermarked version
            os.replace(temp_path, accepted_video_path)

            self.logger.info("Video watermark applied successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply video watermark: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return False
