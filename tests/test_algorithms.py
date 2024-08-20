import pytest

from jobmatch.bipartite_graph_match import iterative_bipartite_matching_solver
from jobmatch.linear_program_optimization import \
    iterative_linear_programming_solver
from jobmatch.preprocessing import create_preference_tuples
from jobmatch.stable_marriage import stable_marriage_solver


@pytest.fixture
def sample_data():
    instructors = {
        'Alice': ['PS211', 'PS302'],
        'Bob': ['PS211','PS477'],
        'Charlie': ['SocSci311', 'PS302'],
    }
    course_capacities = {
        'PS211': 2,
        'PS302': 1,
        'PS477': 1,
        'SocSci311': 1,
    }
    instructor_max = {
        'Alice': 2,
        'Bob': 2,
        'Charlie': 2,
    }
    return instructors, course_capacities, instructor_max

@pytest.fixture
def instructor_preferences(sample_data):
    instructors, course_capacities, _ = sample_data
    all_courses = list(course_capacities.keys())
    return create_preference_tuples(instructors, all_courses)

def test_stable_marriage_solver(instructor_preferences, sample_data):
    _, course_capacities, instructor_max = sample_data
    instructor_assignments, course_assignments = stable_marriage_solver(
        instructor_preferences, course_capacities, instructor_max)

    assert len(instructor_assignments['Alice']) <= instructor_max['Alice']
    assert len(instructor_assignments['Bob']) <= instructor_max['Bob']
    assert len(instructor_assignments['Charlie']) <= instructor_max['Charlie']

def test_iterative_bipartite_matching_solver(sample_data):
    instructors, course_capacities, instructor_max = sample_data
    instructor_assignments, course_assignments, _ = iterative_bipartite_matching_solver(
        instructors, course_capacities, instructor_max)

    assert len(instructor_assignments['Alice']) <= instructor_max['Alice']
    assert len(instructor_assignments['Bob']) <= instructor_max['Bob']
    assert len(instructor_assignments['Charlie']) <= instructor_max['Charlie']

def test_iterative_linear_programming_solver(instructor_preferences, sample_data):
    _, course_capacities, instructor_max = sample_data
    instructor_assignments, course_assignments = iterative_linear_programming_solver(
        instructor_preferences, course_capacities, instructor_max)

    assert len(instructor_assignments['Alice']) <= instructor_max['Alice']
    assert len(instructor_assignments['Bob']) <= instructor_max['Bob']
    assert len(instructor_assignments['Charlie']) <= instructor_max['Charlie']

if __name__ == "__main__":
    pytest.main([__file__])
