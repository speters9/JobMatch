import pandas as pd
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from gui.gui_interface_new import JobMatchApp
from jobmatch.dataclasses import Course, Instructor


# --------------- Fixtures for mock instructors and courses --------------------------
@pytest.fixture
def mock_instructors():
    return [
        Instructor(
            name="Alice",
            max_classes=3,
            degree='phd',
            preferences=['PS211', 'PS300', 'PS400'],
            assigned_courses=[],
            unique_courses=set()
        ),
        Instructor(
            name="Bob",
            max_classes=2,
            degree='mas',
            preferences=['SocSci100', 'PS211'],
            assigned_courses=[],
            unique_courses=set()
        ),
        Instructor(
            name="Carol",
            max_classes=1,
            degree='phd',
            preferences=['Econ101'],
            assigned_courses=[],
            unique_courses=set()
        ),
    ]

@pytest.fixture
def mock_courses():
    return [
        Course(
            name="PS211",
            course_id="101",
            course_description="Introduction to Political Science",
            sections_available=2,
            assigned_instructors=[]
        ),
        Course(
            name="PS300",
            course_id="102",
            course_description="Advanced Political Theory",
            sections_available=1,
            assigned_instructors=[]
        ),
        Course(
            name="SocSci100",
            course_id="103",
            course_description="Introduction to Social Sciences",
            sections_available=3,
            assigned_instructors=[]
        ),
        Course(
            name="Econ101",
            course_id="104",
            course_description="Introduction to Economics",
            sections_available=1,
            assigned_instructors=[]
        ),
    ]

@pytest.fixture
def job_match_app(qapp, mock_instructors, mock_courses, tmp_path):
    """Fixture for creating an instance of the JobMatchApp with preloaded data."""
    # qapp manages the app lifecycle to ensure correct setup/teardown for resource management
    # Create temporary files to act as instructor and course files
    instructor_file_path = tmp_path / "instructors.xlsx"
    course_file_path = tmp_path / "courses.xlsx"

    window = JobMatchApp()
    window.instructors = mock_instructors
    window.courses = mock_courses
    window.instructor_file = str(instructor_file_path)
    window.course_file = str(course_file_path)
    window.show()
    yield window
    window.close()

@pytest.fixture
def empty_job_match_app(qapp, mock_instructors, mock_courses):
    """Fixture for creating an instance of the JobMatchApp with preloaded data."""

    window = JobMatchApp()
    window.instructors = None
    window.courses = None
    window.show()
    yield window
    window.close()

@pytest.fixture
def test_instructor_file(tmp_path):
    """Fixture for creating a test Excel file with instructor data."""
    instructor_data = {
        "Name": ["Instructor A", "Instructor B"],
        "Max Classes": [3, 2],
        'Degree': ['phd', 'mas'],
        "Pref_1": ["Course A", "Course B"],
        "Pref_2": ["Course C", "Course A"],
    }
    df_instructors = pd.DataFrame(instructor_data)

    excel_file_path = tmp_path / "instructor_data.xlsx"
    df_instructors.to_excel(excel_file_path, index=False)

    return excel_file_path


@pytest.fixture
def test_course_file(tmp_path):
    """Fixture for creating a test Excel file with course data."""
    course_data = {
        "Course Name": ["Course A", "Course B", "Course C"],
        "Course ID": ["101", "102", "103"],
        "Course Description": ["The first course", "The second course", "The Third course"],
        "Sections Available": [2, 1, 1],
    }
    df_courses = pd.DataFrame(course_data)

    excel_file_path = tmp_path / "course_data.xlsx"
    df_courses.to_excel(excel_file_path, index=False)

    return excel_file_path





# --------------- Testing load data logic --------------------

# --------------- Testing load data logic --------------------

def test_instructor_file_load_error(empty_job_match_app, qtbot, mocker, tmp_path):
    instructor_data = {
        "Name": ["Instructor A", "Instructor B"],
        "Preference_1": ["Course A", "Course B"],  # Incorrectly named column
    }
    df_instructors = pd.DataFrame(instructor_data)
    invalid_file_path = tmp_path / "invalid_instructors.xlsx"
    df_instructors.to_excel(invalid_file_path, index=False)

    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=None)

    empty_job_match_app.handle_file_drop(empty_job_match_app.instructor_label, str(invalid_file_path))

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once()
    assert "Missing required columns in instructor data: max_classes" in mock_msg_box.call_args[0][2]


def test_course_file_load_error(empty_job_match_app, qtbot, mocker, tmp_path):
    course_data = {
        "Course Name": ["Course A", "Course B"],
        "Course ID": ["101", "102"],
        "Course Description": ["The first course", "The second course"],
    }
    df_courses = pd.DataFrame(course_data)
    invalid_file_path = tmp_path / "invalid_courses.xlsx"
    df_courses.to_excel(invalid_file_path, index=False)

    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=None)

    empty_job_match_app.handle_file_drop(empty_job_match_app.course_label, str(invalid_file_path))

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once()
    assert "Failed to load course file: Missing required columns in course data: sections_available" in mock_msg_box.call_args[0][2]

# ----- assuming no file loaded, these errors should populate --------

def test_run_matching_without_files(empty_job_match_app, mocker, qtbot):
    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=None)

    assert empty_job_match_app.courses is None
    assert empty_job_match_app.instructors is None

    empty_job_match_app.run_matching()

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once_with(
        empty_job_match_app, "Error", "Please load both instructor and course files before running the matching."
    )


def test_print_results_no_matching(empty_job_match_app, mocker, qtbot):
    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=None)

    assert empty_job_match_app.matching_results is None

    empty_job_match_app.view_matches()

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once_with(
        empty_job_match_app, "Error", "No matching results to display. Please run the matching algorithm first."
    )

# ----------------- test successful loading --------------------------

def test_successful_instructor_file_load(empty_job_match_app, qtbot, mocker, test_instructor_file):
    QTest.mousePress(empty_job_match_app.instructor_label, Qt.LeftButton)

    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=None)

    empty_job_match_app.handle_file_drop(empty_job_match_app.instructor_label, str(test_instructor_file))

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)

    mock_msg_box.assert_called_once()
    assert "File Loaded" in mock_msg_box.call_args[0][1]

    assert empty_job_match_app.instructor_file == str(test_instructor_file)
    assert empty_job_match_app.instructors is not None


def test_successful_course_file_load(empty_job_match_app, qtbot, mocker, test_course_file):
    QTest.mousePress(empty_job_match_app.course_label, Qt.LeftButton)

    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=None)

    empty_job_match_app.handle_file_drop(empty_job_match_app.course_label, str(test_course_file))

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)

    mock_msg_box.assert_called_once()
    assert "File Loaded" in mock_msg_box.call_args[0][1]

    assert empty_job_match_app.course_file == str(test_course_file)
    assert empty_job_match_app.courses is not None

## ------------------------- test matching --------------------


@pytest.mark.parametrize("method", ["bipartite_matching", "stable_marriage", "linear_programming"])
def test_run_matching_with_mock_data(job_match_app, mocker, method, qtbot):
    """
    Test the matching process when valid mock data is loaded, the method is selected,
    and `run_matching` is called directly.
    """
    # Ensure mock data is loaded
    assert job_match_app.instructors is not None
    assert job_match_app.courses is not None

    # Set the matching method (test all 3 with parametrization)
    job_match_app.method_menu.setCurrentText(method)

    # Validate that the correct method is selected
    assert job_match_app.method_menu.currentText() == method

    # Mock the QMessageBox to verify that it is called
    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=None)

    # Call run_matching directly
    job_match_app.run_matching()

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once()
    assert "Matching Results" in mock_msg_box.call_args[0][1]

    # Check if matching results are generated
    assert job_match_app.matching_results is not None


# -------------------------- other functions: theme, print, save ---------------------

def test_theme_toggle(job_match_app):
    initial_theme = job_match_app.is_light_theme
    job_match_app.toggle_theme()
    assert job_match_app.is_light_theme != initial_theme


def test_export_to_csv(job_match_app, tmp_path, mocker, qtbot):
    """
    Test the export_results_to_csv method by mocking the file dialog and ensuring the CSV file is saved correctly.
    """
    # Set up a file path using the temporary directory
    file_path = tmp_path / "output.csv"

    # Mock the file dialog to return the desired file path
    mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName', return_value=(str(file_path), 'CSV files (*.csv)'))

    # Preload mock matching results
    job_match_app.matching_results = [
        # Simulate instructor matching results
        [Instructor(name="Alice", max_classes=3, degree='phd', preferences=["PS211"], assigned_courses=["PS211"]),
         Instructor(name="Bob", max_classes=2, degree='mas', preferences=["PS300"], assigned_courses=["PS300"])],
        # Simulate course matching results
        [Course(name="PS211", course_id="101", course_description="Intro to Pol Sci", sections_available=1, assigned_instructors=["Alice"]),
         Course(name="PS300", course_id="102", course_description="Advanced Pol Theory", sections_available=1, assigned_instructors=["Bob"])]
    ]

    # Simulate setting the matching method
    job_match_app.method_menu.setCurrentText("bipartite_matching")

    # Mock the QMessageBox to verify that it is called
    mock_msg_box = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=None)

    # Call the method under test
    job_match_app.export_results_to_csv()

    qtbot.waitUntil(lambda: mock_msg_box.call_count > 0, timeout=1000)
    mock_msg_box.assert_called_once()
    assert "Export Successful" in mock_msg_box.call_args[0][1]

    # Assert that the file was created
    assert file_path.exists()

    # Optionally, you can open and inspect the file to ensure it was written correctly
    with open(file_path, 'r') as f:
        content = f.read()
        assert "Alice" in content
        assert "PS211" in content
        assert "Bob" in content
        assert "PS300" in content


if __name__ == "__main__":
    pytest.main([__file__])
