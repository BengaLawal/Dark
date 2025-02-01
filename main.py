import logging
from config import configuration as config
from ui import UserInterface
import customtkinter as ctk


def setup_logging():
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('photobooth.log'),
            logging.StreamHandler()
        ]
    )


if __name__ == '__main__':
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Login and create application
        creds = config.login()
        root = ctk.CTk()
        app = UserInterface(root, creds, logger)
        root.mainloop()
    except Exception as e:
        logger.error(f"Application startup failed: {e}", exc_info=True)