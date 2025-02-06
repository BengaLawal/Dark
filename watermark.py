import os
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
                    font_size = int(watermarked_image.width * 0.50)
                    watermark_font = ImageFont.truetype("arial.ttf", font_size)
                except OSError:
                    watermark_font = ImageFont.load_default()

                # Get text size for positioning
                bbox = draw.textbbox((0, 0), self.watermark_text, font=watermark_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Calculate text position
                text_position = (
                    text_width + 10,
                    watermarked_image.height - text_height - 30
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

    def apply_video_watermark(self, accepted_video_path):
        """
        Apply watermark to video.
        :param accepted_video_path: video path
        """
        # Open the accepted video clip
        video_clip = VideoFileClip(accepted_video_path)

        # # Load the watermark image
        # watermark_image = Image.open(self.watermark_image_path)
        # watermark_width = int(video_clip.w / 4)  # Adjust the width of the watermark image as desired
        # watermark_height = int(watermark_image.height * (watermark_width / watermark_image.width))
        # watermark_image = watermark_image.resize((watermark_width, watermark_height))

        # Load the watermark image and convert it to a numpy array
        watermark_image = np.array(Image.open(self.watermark_image_path))
        watermark_width = int(video_clip.w / 4)  # Adjust the width of the watermark image as desired
        watermark_height = int(watermark_image.shape[0] * (watermark_width / watermark_image.shape[1]))
        watermark_image = np.array(Image.fromarray(watermark_image).resize((watermark_width, watermark_height)))

        # Create a TextClip for the watermark text
        watermark_text_clip = TextClip(
            self.watermark_text,
            fontsize=30,  # Adjust the font size as desired
            color='white',
            font='Arial',  # Adjust the font family as desired
            method='label'
        )

        # Calculate the position for the watermark text
        text_position_x = video_clip.w - watermark_width - watermark_text_clip.w - 10
        text_position_y = video_clip.h - watermark_text_clip.h - 10

        # Set the watermark text position
        watermark_text_clip = watermark_text_clip.set_position((text_position_x, text_position_y))

        # Set the watermark image position
        watermark_image_clip = ImageClip(watermark_image)
        watermark_image_clip = watermark_image_clip.set_position(('right', 'bottom'))

        # Composite the watermark text and image on top of the video
        video_with_watermark = CompositeVideoClip([video_clip, watermark_text_clip, watermark_image_clip])

        # Set the duration of the video clip to be the same as the original video
        video_with_watermark = video_with_watermark.set_duration(video_clip.duration)

        # Set the audio of the watermarked video to be the same as the original video
        video_with_watermark = video_with_watermark.set_audio(video_clip.audio)

        # Save the watermarked video
        watermarked_video_path = accepted_video_path.replace('.mp4',
                                                             '_watermarked.mp4')  # replace .mp4 with _watermarked
        video_with_watermark.write_videofile(watermarked_video_path, codec='libx264')

        # Close the video clips
        video_clip.close()
        video_with_watermark.close()

        # trim the watermarked video to the same duration as the original video
        # original_duration = video_clip.duration
        # ffmpeg_extract_subclip(watermarked_video_path, 0, original_duration, targetname=watermarked_video_path)

        self.logger.info("Watermark applied to video successfully!")
