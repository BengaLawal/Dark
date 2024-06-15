import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

class Watermark:
    def __init__(self):
        self.watermark_image_path = "watermark/watermark.png"
        self.watermark_text = "#RushClaremont"
        # self.accepted_image = accepted_image_path

    def apply_picture_watermark(self, accepted_picture_path):
        """
        Apply watermark to picture.
        :param accepted_picture_path: picture path
        """
        # Open the accepted image
        accepted_image = Image.open(accepted_picture_path)

        # Resize the watermark image to a desired size
        watermark_image = Image.open(self.watermark_image_path)
        watermark_width = int(accepted_image.width / 4)  # Adjust the width of the watermark image as desired
        watermark_height = int(watermark_image.height * (watermark_width / watermark_image.width))
        watermark_image = watermark_image.resize((watermark_width, watermark_height))

        # Add the watermark image to the bottom right corner of the image
        watermark_position = (accepted_image.width - watermark_image.width, accepted_image.height - watermark_image.height)
        accepted_image.paste(watermark_image, watermark_position, mask=watermark_image)

        # Calculate the position for the watermark text
        watermark_font = ImageFont.load_default()  # Adjust the font and size as desired
        text_width, text_height = watermark_font.getsize(self.watermark_text)
        text_position_x = accepted_image.width - watermark_image.width - text_width - 10
        text_position_y = accepted_image.height - text_height - 10

        # Add the watermark text to the bottom left corner of the image
        draw = ImageDraw.Draw(accepted_image)  # Create a draw object

        # Load the default font provided by PIL
        watermark_font = ImageFont.load_default()  # Adjust the font and size as desired

        # Add the watermark text to the image
        draw.text((text_position_x, text_position_y), self.watermark_text, fill=(255, 255, 255), font=watermark_font)

        # Save the watermarked image
        accepted_image.save(accepted_picture_path)

        print("Watermark applied to picture successfully!")


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
        watermarked_video_path = accepted_video_path.replace('.mp4', '_watermarked.mp4')  # replace .mp4 with _watermarked
        video_with_watermark.write_videofile(watermarked_video_path, codec='libx264')

        # Close the video clips
        video_clip.close()
        video_with_watermark.close()

        # trim the watermarked video to the same duration as the original video
        # original_duration = video_clip.duration
        # ffmpeg_extract_subclip(watermarked_video_path, 0, original_duration, targetname=watermarked_video_path)

        print("Watermark applied to video successfully!")
