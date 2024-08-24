from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from gui.gui_interface import JobMatchApp


#
@pytest.fixture
def app():
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'TkinterDnD2': MagicMock()}):
        from gui.gui_interface import JobMatchApp
        return JobMatchApp()

@pytest.fixture
def sample_instructor_data():
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'max_classes': [2, 2, 2],
        'degree': ['phd', 'mas', 'phd'],
        'pref_1': ['PS211', 'PS302', 'SocSci311'],
        'pref_2': ['PS302', 'SocSci311', 'PS302'],
    })

@pytest.fixture
def sample_course_data():
    return pd.DataFrame({
        'course_name': ['PS211', 'PS302', 'SocSci311'],
        'course_id': ['211', '302', '311'],
        'course_description': [
            'Politics, American Government',
            'American Foreign Policy',
            'International Security Studies'
        ],
        'sections_available': [2, 1, 1]
    })

@patch('tkinter.messagebox.showinfo')
@patch('tkinter.messagebox.showerror')
def test_gui_initialization(mock_showerror, mock_showinfo, app):
    assert app.title() == "Job Matching Tool"
    assert app.instructor_file is None
    assert app.course_file is None

@patch('tkinter.messagebox.showinfo')
@patch('tkinter.messagebox.showerror')
def test_load_instructor_file(mock_showerror, mock_showinfo, app, tmp_path):
    sample_instructor_data = tmp_path / "instructors.csv"
    sample_instructor_data.write_text("name,max_classes,degree,pref_1,pref_2\nAlice,2,phd,PS211,PS302")

    # Simulate drag-and-drop event
    app.load_instructor_file(event=type('test', (object,), {'data': str(sample_instructor_data)}))

    assert app.instructors is not None
    assert app.instructors[0].name == 'Alice'

@patch('tkinter.messagebox.showinfo')
@patch('tkinter.messagebox.showerror')
def test_load_course_file(mock_showerror, mock_showinfo, app, tmp_path):
    sample_course_data = tmp_path / "courses.csv"
    sample_course_data.write_text("course_name,course_id,course_description,sections_available\nPS211,211,Politics American Government,2")

    # Simulate drag-and-drop event
    app.load_course_file(event=type('test', (object,), {'data': str(sample_course_data)}))

    assert app.courses is not None
    assert app.courses[0].name == 'PS211'

@patch('tkinter.messagebox.showinfo')
@patch('tkinter.messagebox.showerror')
def test_run_matching(mock_showerror, mock_showinfo, app, sample_instructor_data, sample_course_data, tmp_path):
    # Prepare the app with sample data
    instructor_file = tmp_path / "instructors.csv"
    sample_instructor_data.to_csv(instructor_file, index=False)
    course_file = tmp_path / "courses.csv"
    sample_course_data.to_csv(course_file, index=False)

    app.load_instructor_file(event=type('test', (object,), {'data': str(instructor_file)}))
    app.load_course_file(event=type('test', (object,), {'data': str(course_file)}))

    # Simulate running the matching process
    app.run_matching()

    assert app.matching_results is not None
    assert len(app.matching_results[0]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
