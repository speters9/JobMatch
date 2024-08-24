import pandas as pd
import pytest

from gui.data_ingestion import load_courses, load_instructors


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

def test_load_instructors(sample_instructor_data, tmp_path):
    # Save the sample data to a temporary CSV file
    path_instructor_file = tmp_path / "instructors.csv"
    instructor_file = str(path_instructor_file)
    sample_instructor_data.to_csv(instructor_file, index=False)

    instructors = load_instructors(instructor_file)

    assert len(instructors) == 3
    assert instructors[0].name == 'Alice'
    assert instructors[1].preferences == ['PS302', 'SocSci311']

def test_load_courses(sample_course_data, tmp_path):
    # Save the sample data to a temporary CSV file
    path_course_file = tmp_path / "courses.csv"
    course_file = str(path_course_file)
    sample_course_data.to_csv(course_file, index=False)

    courses = load_courses(course_file)

    assert len(courses) == 3
    assert courses[0].name == 'PS211'
    assert courses[1].sections_available == 1


@pytest.fixture
def sample_instructor_data_with_missing_degree():
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'max_classes': [2, 2, 2],
        'degree': ['phd', None, 'phd'],  # Bob has no degree
        'pref_1': ['PS211', 'PS302', 'SocSci311'],
        'pref_2': ['PS302', 'SocSci311', 'PS302'],
    })

def test_load_instructors_with_missing_degree(sample_instructor_data_with_missing_degree, tmp_path):
    # Save the sample data to a temporary CSV file
    path_instructor_file = tmp_path / "instructors_missing_degree.csv"
    instructor_file = str(path_instructor_file)
    sample_instructor_data_with_missing_degree.to_csv(instructor_file, index=False)

    instructors = load_instructors(instructor_file)

    assert len(instructors) == 3
    assert instructors[0].name == 'Alice'
    assert instructors[0].degree == 'phd'
    assert instructors[1].name == 'Bob'
    assert pd.isna(instructors[1].degree) or instructors[1].degree is None  # Bob has no degree, so degree should be None
    assert instructors[2].name == 'Charlie'
    assert instructors[2].degree == 'phd'

if __name__ == "__main__":
    pytest.main([__file__])
