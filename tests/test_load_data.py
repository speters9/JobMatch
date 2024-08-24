import pandas as pd
import pytest

from gui.load_data import (identify_and_normalize_preferences,
                           load_and_process_course_data,
                           load_and_process_instructor_data,
                           normalize_column_names, validate_columns)


# Sample data for testing
@pytest.fixture
def sample_instructor_data():
    return pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Max classes': [2, 3],
        'degree': ['phd', 'mas'],
        'preference_1': ['PS101', 'PS102'],
        'class_2': ['PS103', 'PS104'],
        'extra_column': ['extra1', 'extra2']  # Extraneous column
    })

@pytest.fixture
def sample_course_data():
    return pd.DataFrame({
        'course_name': ['PS101', 'PS102'],
        'course_id': ['101', '102'],
        'sections_available': [2, 1],
        'extra_column': ['extra1', 'extra2']  # Extraneous column
    })


# Test for normalizing column names
def test_normalize_column_names(sample_instructor_data):
    df_normalized = normalize_column_names(sample_instructor_data)
    # names should be lowercased and '_'.joined
    expected_columns = ['name', 'max_classes', 'degree', 'preference_1', 'class_2', 'extra_column']
    assert all(col in df_normalized.columns for col in expected_columns)


# Test for extracting preferences
def test_identify_and_normalize_preferences(sample_instructor_data):
    df_normalized = normalize_column_names(sample_instructor_data)
    df_ordered = identify_and_normalize_preferences(df_normalized)
    # names should be changed to a normalized preference nomenclature
    expected_columns = ['name', 'max_classes', 'degree', 'pref_1', 'pref_2', 'extra_column']
    assert all(col in df_ordered.columns for col in expected_columns)


# Test for validating instructor columns
def test_validate_instructor_columns(sample_instructor_data):
    df_normalized = normalize_column_names(sample_instructor_data)
    df_ordered = identify_and_normalize_preferences(df_normalized)
    required_columns = ['name', 'max_classes', 'degree', 'pref_1']
    validate_columns(df_ordered, required_columns, data_type='instructor')


# Test for missing instructor columns - non-preference columns
def test_validate_instructor_missing_columns():
    df_missing = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Degree': ['phd', 'mas'],
    })
    df_normalized = normalize_column_names(df_missing)
    required_columns = ['name', 'max_classes', 'degree', 'pref_1']

    with pytest.raises(ValueError, match="Missing required columns in instructor data"):
        validate_columns(df_normalized, required_columns, data_type='instructor')

# Test for missing instructor columns - preferences
def test_validate_instructor_missing_preferences():
    df_missing = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Degree': ['phd', 'mas'],
        'Max Classes': [2,7]
    })
    df_normalized = normalize_column_names(df_missing)
    required_columns = ['name', 'max_classes', 'degree', 'pref_1']

    with pytest.raises(ValueError, match="No valid preference columns found in instructor data."):
        validate_columns(df_normalized, required_columns, data_type='instructor')


# Test for validating course columns
def test_validate_course_columns(sample_course_data):
    df_normalized = normalize_column_names(sample_course_data)
    required_columns = ['course_name', 'course_id', 'sections_available']
    validate_columns(df_normalized, required_columns, data_type='course')


# Test for incorrect section type in course columns
def test_validate_course_incorrect_sections_type():
    df_incorrect = pd.DataFrame({
        'Course Name': ['Course 1', 'Course 2'],
        'Course ID': ['C1', 'C2'],
        'sections_available': ['two', 'three'],  # Should raise an error
    })
    df_normalized = normalize_column_names(df_incorrect)
    required_columns = ['course_name', 'course_id', 'sections_available']

    with pytest.raises(ValueError, match="'sections_available' column in course data must be of integer type."):
        validate_columns(df_normalized, required_columns, data_type='course')


# Test for loading and processing instructor data
def test_load_and_process_instructor_data(sample_instructor_data, tmp_path):
    file_path = tmp_path / "sample_instructors.csv"
    sample_instructor_data.to_csv(file_path, index=False)

    df_processed = load_and_process_instructor_data(str(file_path))
    required_columns = ['name', 'max_classes', 'degree', 'pref_1', 'pref_2']

    assert all(col in df_processed.columns for col in required_columns)


# Test for loading and processing course data
def test_load_and_process_course_data(sample_course_data, tmp_path):
    file_path = tmp_path / "sample_courses.csv"
    sample_course_data.to_csv(file_path, index=False)

    df_processed = load_and_process_course_data(str(file_path))
    required_columns = ['course_name', 'course_id', 'sections_available']

    assert all(col in df_processed.columns for col in required_columns)



def test_mixed_types_in_preference_columns():
    df_mixed = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Max classes': [2, 3],
        'degree': ['phd', 'mas'],
        'preference_1': ['PS101', 102],  # Mixed types
        'preference_2': ['PS103', 'PS104']
    })
    df_normalized = normalize_column_names(df_mixed)
    df_ordered = identify_and_normalize_preferences(df_normalized)
    assert df_ordered['pref_1'].dtype == 'object'  # Ensures that mixed types are handled correctly


def test_unconventional_column_names():
    df_unconventional = pd.DataFrame({
        '  Name ': ['Alice', 'Bob'],
        'MAX CLASSES!!!': [2, 3],
        'degree@#': ['phd', 'mas'],
        'Prefer 1': ['PS101', 'PS102'],
        'CLASS  2': ['PS103', 'PS104']
    })
    # check normalization
    df_normalized = normalize_column_names(df_unconventional)
    expected_columns = ['name', 'max_classes', 'degree', 'prefer_1', 'class_2']
    assert all(col in df_normalized.columns for col in expected_columns)

    # check everything is renamed correctly
    df_ordered = identify_and_normalize_preferences(df_normalized)
    expected_columns = ['name', 'max_classes', 'degree', 'pref_1', 'pref_2']
    assert all(col in df_ordered.columns for col in expected_columns)


def test_duplicate_preference_columns():
    df_duplicate = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Max classes': [2, 3],
        'degree': ['phd', 'mas'],
        'preference_1': ['PS101', 'PS102'],
        'class_preference_1': ['PS103', 'PS104']  # Duplicate column
    })

    df_normalized = normalize_column_names(df_duplicate)

    with pytest.raises(ValueError, match="Duplicate normalized preference columns detected: pref_1"):
        df_ordered = identify_and_normalize_preferences(df_normalized)




if __name__ == "__main__":
    pytest.main([__file__])
