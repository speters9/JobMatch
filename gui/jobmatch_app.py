"""
Run the app
"""

import logging

from gui.gui_interface import JobMatchApp


def main():
    logging.basicConfig(level=logging.DEBUG, filename="app.log", filemode="w")
    logging.debug("Starting application...")
    try:
        app = JobMatchApp()
        logging.debug("App initialized, entering main loop...")
        app.mainloop()
    except Exception as e:
        logging.error("An error occurred", exc_info=True)

if __name__ == "__main__":
    main()
