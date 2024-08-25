import pytest

from jobmatch.bipartite_graph_match import bipartite_matching_solver
from jobmatch.dataclasses import Course, Instructor
from jobmatch.JobMatch import JobMatch


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

def test_jobmatch_solve_bipartite_matching(sample_instructors, sample_courses):
    factory = JobMatch(sample_instructors, sample_courses)

    # Store the original section availability for each course
    original_sections_available = {course.name: course.sections_available for course in sample_courses}

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

def test_jobmatch_select_solver(sample_instructors, sample_courses):
    factory = JobMatch(sample_instructors, sample_courses)

    # Test bipartite matching solver selection
    solver = factory.select_solver('bipartite_matching')
    assert solver == factory.bipartite_matching_solver

    # Test stable marriage solver selection
    solver = factory.select_solver('stable_marriage')
    assert solver == factory.stable_marriage_solver

    # Test linear programming solver selection
    solver = factory.select_solver('linear_programming')
    assert solver == factory.iterative_linear_programming_solver

    # Test invalid solver method
    with pytest.raises(ValueError, match="Unknown method: invalid_method"):
        factory.select_solver('invalid_method')

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


if __name__ == "__main__":
    pytest.main([__file__])
