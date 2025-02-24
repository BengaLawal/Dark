import json
import os


class MediaType:
    """Enum for media types"""
    PICTURE = "picture"
    BOOMERANG = "boomerang"
    VIDEO = "video"

class FileManager:
    """A class to manage file operations"""
    COUNTS_FILE = "media_counts.json"
    SAVE_DIRS = {
        MediaType.PICTURE: "saved_pictures",
        MediaType.BOOMERANG: "saved_boomerangs",
        MediaType.VIDEO: "saved_videos"
    }
    TEMP_DIR = "temp_media"

    @classmethod
    def initialize_counts_file(cls):
        """Initialize the counts file if it doesn't exist"""
        if not os.path.exists(cls.COUNTS_FILE):
            default_counts = {
                MediaType.PICTURE: 0,
                MediaType.BOOMERANG: 0,
                MediaType.VIDEO: 0
            }
            cls._save_counts(default_counts)

        # Ensure save and temp directories exist
        for directory in list(cls.SAVE_DIRS.values()) + [cls.TEMP_DIR]:
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def get_count(cls, media_type):
        """Get the current count for a specific media type"""
        counts = cls._load_counts()
        return counts.get(media_type, 0)

    @classmethod
    def increment_count(cls, media_type):
        """Increment the count for a specific media type"""
        counts = cls._load_counts()
        counts[media_type] = counts.get(media_type, 0) + 1
        cls._save_counts(counts)
        return counts[media_type]

    @classmethod
    def _load_counts(cls):
        """Load counts from JSON file"""
        try:
            with open(cls.COUNTS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cls.initialize_counts_file()
            return cls._load_counts()

    @classmethod
    def _save_counts(cls, counts):
        """Save counts to JSON file"""
        with open(cls.COUNTS_FILE, 'w') as f:
            json.dump(counts, f)

    @classmethod
    def get_temp_path(cls, media_type):
        """Get a temporary file path for a specific media type"""
        extension = ".mp4" if media_type == MediaType.VIDEO or MediaType.BOOMERANG else ".jpeg"
        import uuid
        return f"{cls.TEMP_DIR}/{uuid.uuid4()}{extension}"

    @classmethod
    def cleanup_temp_files(cls):
        """Remove all temporary files"""
        import shutil
        if os.path.exists(cls.TEMP_DIR):
            shutil.rmtree(cls.TEMP_DIR)
            os.makedirs(cls.TEMP_DIR, exist_ok=True)

    @classmethod
    def get_save_path(cls, media_type, count):
        """Get the save path for a specific media type and count"""
        extension = ".mp4" if media_type == MediaType.VIDEO or MediaType.BOOMERANG else ".jpeg"
        return f"{cls.SAVE_DIRS[media_type]}/{count}{extension}"
