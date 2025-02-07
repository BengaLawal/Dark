import unittest
import os
import json
import shutil
from file_manager import FileManager, MediaType

class TestFileManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary counts file and directories for testing
        self.test_counts_file = "test_media_counts.json"
        FileManager.COUNTS_FILE = self.test_counts_file
        
        # Store original save directories and create test ones
        self.original_save_dirs = FileManager.SAVE_DIRS.copy()
        self.test_dirs = {
            MediaType.PICTURE: "test_saved_pictures",
            MediaType.BOOMERANG: "test_saved_boomerangs",
            MediaType.VIDEO: "test_saved_videos"
        }
        FileManager.SAVE_DIRS = self.test_dirs

    def tearDown(self):
        """Clean up test environment after each test"""
        # Remove test counts file
        if os.path.exists(self.test_counts_file):
            os.remove(self.test_counts_file)
        
        # Remove test directories
        for directory in self.test_dirs.values():
            if os.path.exists(directory):
                shutil.rmtree(directory)
        
        # Restore original save directories
        FileManager.SAVE_DIRS = self.original_save_dirs

    def test_initialize_counts_file(self):
        """Test counts file initialization"""
        FileManager.initialize_counts_file()
        
        # Check if counts file exists
        self.assertTrue(os.path.exists(self.test_counts_file))
        
        # Check if file contains correct default values
        with open(self.test_counts_file, 'r') as f:
            counts = json.load(f)
            self.assertEqual(counts[MediaType.PICTURE], 0)
            self.assertEqual(counts[MediaType.BOOMERANG], 0)
            self.assertEqual(counts[MediaType.VIDEO], 0)
        
        # Check if directories were created
        for directory in self.test_dirs.values():
            self.assertTrue(os.path.exists(directory))

    def test_get_count(self):
        """Test getting counts for different media types"""
        # Initialize with known values
        test_counts = {
            MediaType.PICTURE: 5,
            MediaType.BOOMERANG: 3,
            MediaType.VIDEO: 2
        }
        with open(self.test_counts_file, 'w') as f:
            json.dump(test_counts, f)
        
        # Test getting counts
        self.assertEqual(FileManager.get_count(MediaType.PICTURE), 5)
        self.assertEqual(FileManager.get_count(MediaType.BOOMERANG), 3)
        self.assertEqual(FileManager.get_count(MediaType.VIDEO), 2)
        
        # Test getting count for non-existent media type
        self.assertEqual(FileManager.get_count("invalid_type"), 0)

    def test_increment_count(self):
        """Test incrementing counts for different media types"""
        FileManager.initialize_counts_file()
        
        # Test incrementing counts
        self.assertEqual(FileManager.increment_count(MediaType.PICTURE), 1)
        self.assertEqual(FileManager.increment_count(MediaType.PICTURE), 2)
        self.assertEqual(FileManager.increment_count(MediaType.BOOMERANG), 1)
        self.assertEqual(FileManager.increment_count(MediaType.VIDEO), 1)
        
        # Verify final counts
        with open(self.test_counts_file, 'r') as f:
            counts = json.load(f)
            self.assertEqual(counts[MediaType.PICTURE], 2)
            self.assertEqual(counts[MediaType.BOOMERANG], 1)
            self.assertEqual(counts[MediaType.VIDEO], 1)

    def test_get_save_path(self):
        """Test getting save paths for different media types"""
        # Test picture path
        picture_path = FileManager.get_save_path(MediaType.PICTURE, 1)
        self.assertEqual(picture_path, f"{self.test_dirs[MediaType.PICTURE]}/1.jpeg")
        
        # Test video path
        video_path = FileManager.get_save_path(MediaType.VIDEO, 2)
        self.assertEqual(video_path, f"{self.test_dirs[MediaType.VIDEO]}/2.mp4")
        
        # Test boomerang path
        boomerang_path = FileManager.get_save_path(MediaType.BOOMERANG, 3)
        self.assertEqual(boomerang_path, f"{self.test_dirs[MediaType.BOOMERANG]}/3.jpeg")

    def test_file_operations_with_missing_file(self):
        """Test file operations when counts file is missing"""
        # Ensure file doesn't exist
        if os.path.exists(self.test_counts_file):
            os.remove(self.test_counts_file)
            
        # Test getting count (should initialize file)
        count = FileManager.get_count(MediaType.PICTURE)
        self.assertEqual(count, 0)
        self.assertTrue(os.path.exists(self.test_counts_file))

if __name__ == '__main__':
    unittest.main()
