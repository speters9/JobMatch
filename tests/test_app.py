import sys
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox

from gui.gui_interface import JobMatchApp
from gui.jobmatch_app import \
    SplashScreen  # Replace 'main_script' with the name of your script file


@pytest.fixture
def app(qtbot):
    test_app = QApplication(sys.argv)
    yield test_app

def test_splash_screen_initialization(qtbot):
    """Validate splash screen starts."""
    splash = SplashScreen()

    # Ensure that the splash screen initializes with the correct values
    assert splash.progress.value() == 0
    assert splash.status.text() == "Starting..."

    qtbot.addWidget(splash)


def test_splash_screen_update_loading(qtbot):
    """Make sure progres bar works."""
    splash = SplashScreen()
    qtbot.addWidget(splash)

    # Mock the start_main_app to prevent it from being called during the test
    with patch.object(splash, 'start_main_app', return_value=None):
        splash.update_loading()
        assert splash.progress.value() == 25
        assert splash.status.text() == "Loading resources..."

        splash.update_loading()
        assert splash.progress.value() == 50
        assert splash.status.text() == "Initializing interface..."


def test_splash_screen_error_handling(qtbot):
    """Confirm errors raised in startup for user knowledge."""
    with patch.object(QMessageBox, 'critical') as mock_critical:
        splash = SplashScreen()
        qtbot.addWidget(splash)

        # Patch the JobMatchApp class to raise an exception when instantiated
        with patch.object(JobMatchApp, '__init__', side_effect=Exception("Test Error")):
            with pytest.raises(Exception, match="Test Error"):
                splash.start_main_app()

        # Ensure the critical message box was shown
        mock_critical.assert_called_once_with(splash, "Error", "Test Error")



if __name__ == "__main__":
    pytest.main([__file__])
