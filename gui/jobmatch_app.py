"""
Run the app
"""

import logging
import sys

from PyQt5.QtWidgets import QApplication

from gui.gui_interface import JobMatchApp


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("app.log"),
                            logging.StreamHandler()  # This will print to the console
                        ])
    logging.debug("Starting application...")
    try:
        # Ensure QApplication is initialized here
        app = QApplication(sys.argv)

        # Create the main window
        window = JobMatchApp()
        window.show()

        logging.debug("App initialized, entering main loop...")

        # Execute the application
        app.exec_()
    except Exception as e:
        logging.error("An error occurred", exc_info=True)
        sys.exit(1)  # Exit with an error code


if __name__ == "__main__":
    main()
