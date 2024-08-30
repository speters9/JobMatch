import re

import numpy as np
import pandas as pd

from jobmatch.dataclasses import Course, Instructor


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the column names of the DataFrame by converting them to lowercase,
    replacing spaces with underscores, and removing any leading/trailing whitespace.

    Args:
        df (pd.DataFrame): The DataFrame with raw column names.

    Returns:
        pd.DataFrame: The DataFrame with normalized column names.
    """
    wdf = df.copy()
    df.columns = (
        df.columns.str.strip()  # Remove leading/trailing whitespace
        .str.lower()            # Convert to lowercase
        .str.replace(r'\s+', '_', regex=True)  # Replace spaces with underscores
        .str.replace(r'[^a-z0-9_]', '', regex=True)  # Remove non-alphanumeric characters
    )

    if len(df.columns) != len(wdf.columns):
        raise ValueError("Duplicate columns detected. Please check naming patterns")

    return df


def identify_and_normalize_preferences(df: pd.DataFrame, base_name: str = 'pref') -> pd.DataFrame:
    """
    Identify preference columns based on the `_1`, `_2`, etc., suffix, and normalize their names to `pref_1`, `pref_2`, etc.

    Args:
        df (pd.DataFrame): The DataFrame with normalized column names.
        base_name (str): Base name for preferences, default is 'pref'.

    Returns:
        pd.DataFrame: The DataFrame with normalized preference column names.

    Raises:
        ValueError: If duplicate preference columns are detected after normalization.
    """
    # Identify all columns that end with '_1', '_2', etc.
    preference_columns = [col for col in df.columns if re.search(r'_\d+$', col)]

    if not preference_columns:
        raise ValueError("No preference columns ending in '_1', '_2', etc., found in the dataset.")

    normalized_columns = {}
    duplicates = []

    # Extract the numeric suffix and normalize the column names to pref_1, pref_2, etc.
    for col in preference_columns:
        match = re.search(r'_(\d+)$', col)
        if match:
            index = match.group(1)
            new_name = f'{base_name}_{index}'

            if new_name in normalized_columns.values():
                duplicates.append(new_name)
            else:
                normalized_columns[col] = new_name

    if duplicates:
        raise ValueError(f"Duplicate normalized preference columns detected: {', '.join(duplicates)}")

    # Rename columns based on the normalization map
    df = df.rename(columns=normalized_columns)

    return df


def validate_columns(df: pd.DataFrame, required_columns: list, data_type: str = 'instructor') -> None:
    """
    Validate that the required columns exist in the DataFrame. Raise an error if any are missing.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        required_columns (list): A list of column names that are required.
        data_type (str): Type of data being processed, either 'instructor' or 'course'.

    Raises:
        ValueError: If any of the required columns are missing.
    """
    if data_type == 'instructor':
        # Instructor-specific validation
        non_pref_columns = [col for col in required_columns if not col.startswith('pref_')]

        missing_columns = [col for col in non_pref_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in {data_type} data: {', '.join(missing_columns)}")

        # Check for at least one preference column
        pref_columns = [col for col in df.columns if col.startswith('pref_')]
        if not pref_columns:
            raise ValueError(f"No valid preference columns found in {data_type} data.")

        # Extract and validate the numbering of preference columns
        pref_numbers = sorted(int(re.search(r'\d+$', col).group()) for col in pref_columns)

        # Check for gaps and duplicates in preference numbering
        if pref_numbers != list(range(1, len(pref_numbers) + 1)):
            raise ValueError(f"Preference columns in {data_type} data are not sequential or contain duplicates.")

    elif data_type == 'course':
        # Course-specific validation
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in {data_type} data: {', '.join(missing_columns)}")

        # Ensure that sections_available is of integer type
        if 'sections_available' in df.columns and not np.issubdtype(df['sections_available'].dtype, np.integer):
            raise ValueError(f"'sections_available' column in {data_type} data must be of integer type.")

    else:
        raise ValueError(f"Unknown data type: {data_type}. Valid options are 'instructor' and 'course'.")


def load_and_process_instructor_data(file_path: str) -> pd.DataFrame:
    """
    Load and process Instructor data from an Excel or CSV file.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        pd.DataFrame: The processed Instructor DataFrame with normalized column names and organized preferences.
    """
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

    # Normalize column names
    df = normalize_column_names(df)

    # Identify and normalize preferences for Instructors
    df = identify_and_normalize_preferences(df, base_name='pref')

    # Validate required columns for Instructors
    required_columns = ['name', 'max_classes', 'pref_1']
    validate_columns(df, required_columns, data_type='instructor')

    return df


def load_and_process_course_data(file_path: str) -> pd.DataFrame:
    """
    Load and process Course data from an Excel or CSV file.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        pd.DataFrame: The processed Course DataFrame with normalized column names and organized preferences.
    """
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

    # Normalize column names
    df = normalize_column_names(df)

    # Validate required columns for Courses
    required_columns = ['course_name', 'course_id', 'sections_available']
    validate_columns(df, required_columns, data_type='course')

    return df


## ----------- create instructor objects from processed data --------------

def load_instructors(file_path: str) -> list[Instructor]:
    """
    Load and process the instructors data from an Excel or CSV file.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        list[Instructor]: A list of Instructor objects created from the file data.
    """
    df = load_and_process_instructor_data(file_path)

    instructors = []
    for _, row in df.iterrows():
        # Extract preference columns
        preferences = [row[f'pref_{i+1}'] for i in range(len(row)) if f'pref_{i+1}' in row and isinstance(row[f'pref_{i+1}'], str)]

        instructors.append(Instructor(
            name=row['name'],
            max_classes=row['max_classes'],
            degree=row['degree'] if row['degree'] else None,
            preferences=preferences
        ))
    return instructors


def load_courses(file_path: str) -> list[Course]:
    """
    Load and process the courses data from an Excel or CSV file.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        list[Course]: A list of Course objects created from the file data.
    """
    df = load_and_process_course_data(file_path)

    courses = []
    for _, row in df.iterrows():
        courses.append(Course(
            name=row['course_name'],
            course_id=row['course_id'],
            course_description=row['course_description'],
            sections_available=row['sections_available']
        ))
    return courses



if __name__ == "__main__":
    # set wd
    from pyprojroot.here import here

    wd = here()

    # Example file path
    inst_file_path = wd / 'data/test/instructors_with_preferences.csv'
    crs_file_path = wd / 'data/test/course_data.csv'

    # Load and process the data
    inst_df = None
    crs_df = None
    inst_df = load_and_process_instructor_data(str(inst_file_path))
    crs_df = load_and_process_course_data(str(crs_file_path))
    assert inst_df is not None
    assert crs_df is not None

    instructors = []
    courses = []
    instructors = load_instructors(str(inst_file_path))
    courses = load_courses(str(crs_file_path))
    assert len(instructors) > 0
    assert len(courses) > 0

    # Display the processed DataFrame
    print(inst_df.head())
