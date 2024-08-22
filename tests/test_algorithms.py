import pytest

from jobmatch.bipartite_graph_match import iterative_bipartite_matching_solver
from jobmatch.dataclasses import Course, Instructor
from jobmatch.linear_program_optimization import \
    iterative_linear_programming_solver
from jobmatch.preprocessing import create_preference_tuples
from jobmatch.stable_marriage import stable_marriage_solver


@pytest.fixture
def sample_instructors():
    return [
        Instructor(name='Alice', max_classes=2, degree='phd', preferences=['PS211', 'PS302']),
        Instructor(name='Bob', max_classes=2, degree='mas', preferences=['PS211', 'PS477']),
        Instructor(name='Charlie', max_classes=2, degree='phd', preferences=['SocSci311', 'PS302']),
    ]

@pytest.fixture
def sample_courses():
    return [
        Course(name='PS211', course_id='211', course_description='Politics, American Government', sections_available=2),
        Course(name='PS302', course_id='302', course_description='American Foreign Policy', sections_available=1),
        Course(name='PS477', course_id='477', course_description='Politics of the Middle East', sections_available=1),
        Course(name='SocSci311', course_id='311', course_description='International Security Studies', sections_available=1),
    ]

@pytest.fixture
def preference_tuples(sample_instructors, sample_courses):
    return create_preference_tuples(sample_instructors, sample_courses)



def test_iterative_bipartite_matching_solver(sample_instructors, sample_courses):
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    instructor_assignments, course_assignments, graphs = iterative_bipartite_matching_solver(
        sample_instructors, sample_courses, instructor_weighted=False
    )

    # Check that no instructor exceeds their max_classes
    for instructor in instructor_assignments:
        assert len(instructor.assigned_courses) <= instructor.max_classes
        assert len(instructor.unique_courses) <= 2  # No more than 2 unique courses

    # Check that no course is over-assigned
    for course in course_assignments:
        assert len(course.assigned_instructors) <= original_sections_available[course.name]

def test_stable_marriage_solver(sample_instructors, sample_courses):
    # Create the necessary course capacities and instructor max dicts
    course_capacities = {course.name: course.sections_available for course in sample_courses}
    instructor_max = {instructor.name: instructor.max_classes for instructor in sample_instructors}
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    instructor_assignments, course_assignments = stable_marriage_solver(
        sample_instructors, sample_courses
    )

    # Check that no instructor exceeds their max_classes
    for instructor in instructor_assignments:
        assert len(instructor.assigned_courses) <= instructor.max_classes
        assert len(instructor.unique_courses) <= 2  # No more than 2 unique courses

    # Check that no course is over-assigned
    for course in course_assignments:
        assert len(course.assigned_instructors) <= original_sections_available[course.name]


def test_iterative_linear_programming_solver(sample_instructors, sample_courses):
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    instructor_assignments, course_assignments = iterative_linear_programming_solver(
        sample_instructors, sample_courses, method='default'
    )

    # Check that no instructor exceeds their max_classes
    for instructor in instructor_assignments:
        assert len(instructor.assigned_courses) <= instructor.max_classes
        assert len(instructor.unique_courses) <= 2  # No more than 2 unique courses

    # Check that no course is over-assigned
    for course in course_assignments:
        assert len(course.assigned_instructors) <= original_sections_available[course.name]


if __name__ == "__main__":
    pytest.main([__file__])
