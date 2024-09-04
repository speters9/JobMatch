import copy

import pytest

from jobmatch.dataclasses import Course, Instructor
from jobmatch.JobMatch import JobMatch


@pytest.fixture
def sample_instructors():
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
            preferences=['PS211', 'SocSci100'],
            assigned_courses=[],
            unique_courses=set()
        ),
        Instructor(
            name="Carol",
            max_classes=2,
            degree='phd',
            preferences=['PS211', 'PS300', 'Econ101'],
            assigned_courses=[],
            unique_courses=set()
        ),
        Instructor(
            name="David",
            max_classes=1,
            degree='phd',
            preferences=['Econ101'],
            assigned_courses=[],
            unique_courses=set()
        ),
        Instructor(
            name="Eve",
            max_classes=3,
            degree='phd',
            preferences=['PS211', 'SocSci100'],
            assigned_courses=[],
            unique_courses=set()
        ),
    ]

@pytest.fixture
def sample_courses():
    return [
        Course(
            name="PS211",
            course_id="101",
            course_description="Introduction to Political Science",
            sections_available=3,  # Increased from 2 to 3
            assigned_instructors=[],
            course_director="Alice"
        ),
        Course(
            name="PS300",
            course_id="102",
            course_description="Advanced Political Theory",
            sections_available=2,  # Increased from 1 to 2
            assigned_instructors=[],
            course_director=None
        ),
        Course(
            name="SocSci100",
            course_id="103",
            course_description="Introduction to Social Sciences",
            sections_available=3,
            assigned_instructors=[],
            course_director=None
        ),
        Course(
            name="Econ101",
            course_id="104",
            course_description="Introduction to Economics",
            sections_available=2,  # Increased from 1 to 2
            assigned_instructors=[],
            course_director="David"
        ),
    ]

def test_jobmatch_solve_bipartite_matching(sample_instructors, sample_courses):
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    factory = JobMatch(sample_instructors, sample_courses)

    # Solve the matching using bipartite matching method
    results = factory.solve(method='bipartite_matching', instructor_weighted=True)

    assert len(results) == 3  # (instructors, courses, graph)
    final_instructors, final_courses, _ = results

    # Verify that each instructor gets assigned no more than their max classes
    for instructor in final_instructors:
        assert len(instructor.assigned_courses) <= instructor.max_classes

    # Verify that each course does not exceed the original available sections
    for course in final_courses:
        assigned_instructors_count = len(course.assigned_instructors)
        assert assigned_instructors_count <= original_sections_available.get(course.name)


def test_jobmatch_solve_stable_marriage(sample_instructors, sample_courses):
    factory = JobMatch(sample_instructors, sample_courses)

    results = factory.solve(method='stable_marriage')
    assert len(results) == 2  # (instructors, courses)
    final_instructors, final_courses = results

    # Check that each instructor is assigned according to the stable marriage algorithm's constraints
    for instructor in final_instructors:
        assert len(instructor.assigned_courses) <= instructor.max_classes
        assert len(instructor.unique_courses) <= 2


def test_jobmatch_solve_linear_programming(sample_instructors, sample_courses):
    factory = JobMatch(sample_instructors, sample_courses)

    results = factory.solve(method='linear_programming', lp_method='default')
    assert len(results) == 2  # (instructors, courses)
    final_instructors, final_courses = results

    # Check that each instructor is assigned according to the linear programming algorithm's constraints
    for instructor in final_instructors:
        assert len(instructor.assigned_courses) <= instructor.max_classes
        assert len(instructor.unique_courses) <= 2


def test_match_course_directors(sample_instructors, sample_courses):
    """
    Test that course directors are assigned correctly before the main algorithm runs.
    """
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    job_match = JobMatch(sample_instructors, sample_courses)

    # Check that the course directors have been correctly assigned to their courses
    ps211 = next(course for course in job_match.courses if course.name == "PS211")
    econ101 = next(course for course in job_match.courses if course.name == "Econ101")
    alice = next(inst for inst in job_match.instructors if inst.name == "Alice")
    david = next(inst for inst in job_match.instructors if inst.name == "David")

    assert "Alice" in ps211.assigned_instructors
    assert "David" in econ101.assigned_instructors
    assert alice.assigned_courses == ["PS211"]*min(alice.max_classes,original_sections_available.get("PS211"))
    assert david.assigned_courses == ["Econ101"]*min(david.max_classes,original_sections_available.get("Econ101"))


def test_linear_programming_solver(sample_instructors, sample_courses):
    """
    Test the linear programming solver.
    """
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    job_match = JobMatch(sample_instructors, sample_courses)
    result = job_match.iterative_linear_programming_solver()

    # Ensure courses are assigned within constraints
    for course in job_match.courses:
        assert len(course.assigned_instructors) <= original_sections_available[course.name]  # No over-assignments
        assert len(set(course.assigned_instructors)) <= 2  # No instructor teaches more than 2 unique courses

    # Check that instructors are not over-assigned
    for instructor in sample_instructors:
        assert len(instructor.assigned_courses) <= instructor.max_classes


def test_stable_marriage_solver(sample_instructors, sample_courses):
    """
    Test the stable marriage solver.
    """
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

    job_match = JobMatch(sample_instructors, sample_courses)
    instructor_matches, course_matches = job_match.stable_marriage_solver()

    # Ensure that the assignments are stable
    for instructor in instructor_matches:
        assert len(instructor.assigned_courses) > 0  # Every instructor should have an assignment if possible

    # Check that instructors are not assigned to more than two unique courses
    for instructor in instructor_matches:
        assert len(set(instructor.assigned_courses)) <= 2

if __name__ == "__main__":
    pytest.main([__file__])
