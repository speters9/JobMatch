from collections import namedtuple

import pytest

from jobmatch.preprocessing import (create_preference_tuples,
                                    normalize_preferences, parse_preferences)


def test_normalize_preferences():
    # Test cases for normalize_preferences function
    input_str = "Pol Sci 421 (1); SocSci 311 (2); FAS 440 (3)"
    expected_output = ['PS421', 'SocSci311', 'FAS440']
    assert normalize_preferences(input_str) == expected_output

    input_str = "PolSci 211; PoliSci 302; FAS320"
    expected_output = ['PS211', 'PS302', 'FAS320']
    assert normalize_preferences(input_str) == expected_output


def test_parse_preferences():
    # Example mappings
    course_id_map = {
        '211': 'PS211',
        '311': 'SocSci311',
    }
    course_map = {
        "Politics, American Government, and National Security": "PS211",
        "International Security Studies": "SocSci311",
    }
    core_class = 'PS211'

    input_str = "Pol Sci 211; SocSci 311"
    expected_output = ['PS211', 'SocSci311']
    assert parse_preferences(input_str, course_id_map, course_map, core_class) == expected_output

    # Test with missing core class
    input_str = "SocSci 311"
    expected_output = ['SocSci311', 'PS211']
    assert parse_preferences(input_str, course_id_map, course_map, core_class) == expected_output



def test_create_preference_tuples():
    instructors = {
        'Alice': ['PS211', 'PS302'],
        'Bob': ['PS211','PS477'],
        'Charlie': ['SocSci311', 'PS302', 'PS477',]
    }

    all_courses = ['PS211', 'PS302', 'PS477', 'SocSci311']

    # Expected output
    Preference = namedtuple('Preference', ['course', 'rank'])
    expected_output = {
        'Alice': [Preference(course='PS211', rank=1), Preference(course='PS302', rank=2), Preference(course='PS477', rank=4), Preference(course='SocSci311', rank=4)],
        'Bob': [Preference(course='PS211', rank=1), Preference(course='PS477', rank=2), Preference(course='PS302', rank=4), Preference(course='SocSci311', rank=4)],
        'Charlie': [Preference(course='SocSci311', rank=1), Preference(course='PS302', rank=2), Preference(course='PS477', rank=3), Preference(course='PS211', rank=4)],
    }

    result = create_preference_tuples(instructors, all_courses)

    assert result == expected_output





if __name__ == "__main__":
    pytest.main([__file__])
