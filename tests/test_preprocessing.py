from collections import namedtuple

import pandas as pd
import pytest

from jobmatch.dataclasses import Course, Instructor
from jobmatch.preprocessing import (build_courses, build_instructors,
                                    create_preference_tuples,
                                    normalize_preferences, parse_preferences,
                                    print_matching_results)


@pytest.fixture
def sample_course_data():
    return pd.DataFrame({
        'course_name': ['PS211', 'PS302', 'SocSci311', 'PS477'],
        'course_id': ['211', '302', '311', '477'],
        'course_description': [
            'Politics, American Government',
            'American Foreign Policy',
            'International Security Studies',
            'Politics of the Middle East'
        ],
        'sections_available': [2, 1, 1, 1]
    })


@pytest.fixture
def sample_instructor_data():
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'max_classes': [2, 2, 2],
        'degree': ['phd', 'mas', 'phd']
    })


@pytest.fixture
def sample_preferences():
    return {
        'Alice': ['PS211', 'PS302'],
        'Bob': ['PS211', 'PS477'],
        'Charlie': ['SocSci311', 'PS302']
    }


@pytest.fixture
def sample_course_maps():
    course_id_map = {
        '211': 'PS211',
        '302': 'PS302',
        '311': 'SocSci311',
        '477': 'PS477'
    }
    course_map = {
        'PS211': 'PS211',
        'PS302': 'PS302',
        'SocSci311': 'SocSci311',
        'PS477': 'PS477'
    }
    return course_id_map, course_map


def test_build_instructors(sample_instructor_data, sample_preferences):
    instructors = build_instructors(sample_instructor_data, sample_preferences)
    assert len(instructors) == 3
    assert instructors[0].name == 'Alice'
    assert instructors[1].degree == 'mas'
    assert instructors[2].preferences == ['SocSci311', 'PS302']


def test_build_courses(sample_course_data):
    courses = build_courses(sample_course_data)
    assert len(courses) == 4
    assert courses[0].name == 'PS211'
    assert courses[1].sections_available == 1


def test_normalize_preferences():
    preference_string = "Pol Sci 211; FAS 211 (3), Soc Sci 311, PolSci 477 // Pol ScI 302"
    normalized = normalize_preferences(preference_string)
    assert normalized == ['PS211', 'FAS211', 'SocSci311', 'PS477', 'PS302']


def test_parse_preferences(sample_course_maps):
    course_id_map, course_map = sample_course_maps
    parsed = parse_preferences("Pol Sci 211, SocSci 311", course_id_map, course_map, 'PS211')
    assert parsed == ['PS211', 'SocSci311']


def test_create_preference_tuples(sample_instructor_data, sample_preferences, sample_course_data):

    instructors = build_instructors(sample_instructor_data, sample_preferences)
    courses = build_courses(sample_course_data)
    preference_tuples = create_preference_tuples(instructors, courses)

    assert 'Alice' in preference_tuples
    assert len(preference_tuples['Bob']) == len(courses)
    assert preference_tuples['Alice'][0].course == 'PS211'
    assert preference_tuples['Charlie'][0].rank == 1


def test_print_matching_results():
    instructor_assignments = {
        'Alice': ['PS211', 'PS302'],
        'Bob': ['PS211'],
        'Charlie': ['SocSci311']
    }
    individuals = {
        'Alice': ['PS211', 'PS302', 'SocSci311'],
        'Bob': ['PS211', 'PS477'],
        'Charlie': ['SocSci311', 'PS302']
    }
    match_ranks = print_matching_results(instructor_assignments, individuals)

    assert match_ranks['Alice'] == [1, 2]
    assert match_ranks['Bob'] == [1]
    assert match_ranks['Charlie'] == [1]





if __name__ == "__main__":
    pytest.main([__file__])
