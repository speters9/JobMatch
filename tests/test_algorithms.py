import pytest

from jobmatch.bipartite_graph_match import bipartite_matching_solver
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


# def test_iterative_bipartite_matching_solver(sample_instructors, sample_courses):
#     original_sections_available = {course.name: course.sections_available for course in sample_courses}

#     instructor_assignments, course_assignments, graphs = bipartite_matching_solver(
#         sample_instructors, sample_courses, instructor_weighted=False
#     )

#     # Check that no instructor exceeds their max_classes
#     for instructor in instructor_assignments:
#         assert len(instructor.assigned_courses) <= instructor.max_classes
#         assert len(instructor.unique_courses) <= 2  # No more than 2 unique courses

#     # Check that no course is over-assigned
#     for course in course_assignments:
#         assert len(course.assigned_instructors) <= original_sections_available[course.name]



def test_bipartite_matching_solver(sample_instructors, sample_courses):
    # Store the original section availability for each course
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    final_instructors, final_courses, G = bipartite_matching_solver(sample_instructors, sample_courses, instructor_weighted=True)

    assert len(final_instructors) == 3
    assert len(final_courses) == 4

    # Verify that each instructor gets assigned no more than their max classes
    for instructor in final_instructors:
        assert len(instructor.assigned_courses) <= instructor.max_classes

    # Verify that each course does not exceed the original available sections
    for course in final_courses:
        assigned_instructors_count = len(course.assigned_instructors)
        assert assigned_instructors_count <= original_sections_available[course.name]

    # Check if all instructors have at least one valid assignment if possible
    for instructor in final_instructors:
        if instructor.name == "Alice":
            assert set(instructor.assigned_courses).issubset({"PS211", "PS302"})
        elif instructor.name == "Bob":
            assert set(instructor.assigned_courses).issubset({"PS211", "PS477"})
        elif instructor.name == "Charlie":
            assert set(instructor.assigned_courses).issubset({"SocSci311", "PS302"})

    # Check if all courses have their sections filled by valid instructors
    for course in final_courses:
        if course.name == "PS211":
            assert set(course.assigned_instructors).issubset({"Alice", "Bob"})
        elif course.name == "PS302":
            assert set(course.assigned_instructors).issubset({"Alice", "Charlie"})
        elif course.name == "PS477":
            assert set(course.assigned_instructors).issubset({"Bob"})
        elif course.name == "SocSci311":
            assert set(course.assigned_instructors).issubset({"Charlie"})



def test_stable_marriage_solver(sample_instructors, sample_courses):
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

    # Check that unassignable courses remain unassigned
    # Example: Bob prefers PS211, but if PS211 is fully assigned to others, check he is assigned to PS477
    if len(next(c.assigned_instructors for c in course_assignments if c.name == 'PS211')) == original_sections_available['PS211']:
        assert 'PS477' in next(i.assigned_courses for i in instructor_assignments if i.name == 'Bob')


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

    # Check that the assignments match expectations based on linear programming
    # Example: Alice might be expected to get her top choice based on LP optimization
    assert 'PS211' in next(i.assigned_courses for i in instructor_assignments if i.name == 'Alice')


if __name__ == "__main__":
    pytest.main([__file__])
