from gui.load_data import (load_and_process_course_data,
                           load_and_process_instructor_data)
from jobmatch.dataclasses import Course, Instructor


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
    instructor_file_path = wd / 'data/processed/instructors_with_preferences.csv'

    course_file_path = wd / "data/raw/course_data.csv"

    # df to inspect
    df = load_and_process_instructor_data(str(instructor_file_path))

    # Load instructors and courses
    instructors = load_instructors(str(instructor_file_path))
    courses = load_courses(str(course_file_path))
    print(instructors)
