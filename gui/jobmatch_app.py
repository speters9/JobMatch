"""
Run the app
"""

import logging
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox,
                             QProgressBar, QSplashScreen)

from gui import resources_rc  # image bundled for easy
from gui.gui_interface import JobMatchApp


class SplashScreen(QMainWindow):
    def __init__(self):
        super(SplashScreen, self).__init__()

        self.icon_path = ':/images/jobmatch_icon_rounded.png'

        # Set up the splash screen UI
        self.setWindowTitle("Loading JobMatch")
        self.setGeometry(100, 100, 300, 340)  # Window size adjusted to fit the image and progress bar
        self.setWindowIcon(QIcon(self.icon_path))

        # Splash image
        splash_pix = QPixmap(self.icon_path).scaled(300, 300, Qt.KeepAspectRatio)
        splash_label = QLabel(self)
        splash_label.setPixmap(splash_pix)
        splash_label.setGeometry(0, 0, 300, 300)  # Image fills the top of the window

        # Status label
        self.status = QLabel("Starting...", self)
        self.status.setGeometry(10, 290, 280, 20)  # Status label below the image

        # Progress bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(10, 310, 280, 20)  # Progress bar at the bottom of the window
        self.progress.setValue(0)  # Set initial value to 0

        # Timer for loading steps
        self.loading_steps = ["Loading resources...", "Initializing interface...", "Almost done...", "Ready!"]
        self.current_step = 0
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading)
        self.loading_timer.start(1000)

        # Show the splash screen
        self.show()

    def update_loading(self):
        if self.current_step < len(self.loading_steps):
            self.progress.setValue((self.current_step + 1) * 25)
            self.status.setText(self.loading_steps[self.current_step])
            self.current_step += 1
        else:
            self.loading_timer.stop()
            self.start_main_app()

    def start_main_app(self):
        # Start the main application
        self.close()  # Close the splash screen
        try:
            self.main_window = JobMatchApp()
            self.main_window.setWindowIcon(QIcon(self.icon_path))
            self.main_window.show()
        except Exception as e:
            logging.error("Failed to start the main application.", exc_info=True)
            self.close()
            QMessageBox.critical(self, "Error", f"{str(e)}")
            raise e

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("app.log"),
                            logging.StreamHandler()  # This will print to the console
                        ])
    logging.info("Starting application...")
    try:
        # Ensure QApplication is initialized here
        app = QApplication(sys.argv)

        # Start the splash screen
        splash = SplashScreen()

        logging.info("App initialized, entering main loop...")
        sys.exit(app.exec_())
    except Exception as e:
        logging.error("An error occurred", exc_info=True)
        sys.exit(1)  # Exit with an error code


if __name__ == "__main__":
    main()
