#%%
import re
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import Dict, List

import pandas as pd
from rapidfuzz import fuzz, process

from jobmatch.dataclasses import Course, Instructor


def build_instructors(df: pd.DataFrame, instructor_prefs: Dict[str, List[str]]) -> List[Instructor]:
    instructor_dict = df.to_dict(orient = "records")
    instructor_list = []
    for instructor in instructor_dict:
        instructor_list.append(Instructor(
                                        name=instructor['name'],
                                        max_classes=instructor['max_classes'],
                                        degree=instructor.get('degree', None), # should be robust to not having a degree
                                        preferences=instructor_prefs.get(instructor['name'])
                                        ))
    return instructor_list

def build_courses(df: pd.DataFrame) -> List[Course]:
    course_dict = df.to_dict(orient = "records")
    course_list = []
    for course in course_dict:
        course_list.append(Course(
                                name=course['course_name'],
                                course_id=course['course_id'],
                                course_description=course['course_description'],
                                sections_available=course['sections_available']
                                ))
    return course_list


def get_ordered_preferences(row, courses: List):
    ranked_courses = {course: row[course]
                      for course in courses if pd.notna(row[course])}
    # Sort by rank (ascending)
    sorted_courses = sorted(ranked_courses, key=ranked_courses.get)
    return sorted_courses


def create_preference_tuples(instructors: List[Instructor], courses: List[Course]) -> Dict[str, List[namedtuple]]:
    """Convert a dictionary of lists into a dictionary of lists of named tuples with rankings.

    Args:
        individuals (Dict[str, List[str]]): A dictionary of instructors and their course preferences.
        all_courses (List[str]): A list of all available courses.

    Returns:
        Dict[str, List[NamedTuple]]: A dictionary of instructors and their ranked preferences as named tuples.
    """
    # Define a named tuple to store course and its rank
    Preference = namedtuple('Preference', ['course', 'rank'])

    # Get the maximum rank to assign to non-listed courses
    max_rank = len(courses)
    all_courses = [course.name for course in courses]

    # Initialize the dictionary to store preferences as named tuples
    preferences_with_ranks = {}

    for instructor in instructors:
        # Create the list of Preference named tuples for this instructor
        ranked_preferences = []

        # skip if preferences are None
        if not instructor.preferences:
            preferences_with_ranks[instructor.name] = ranked_preferences
            continue

        # Add the listed courses with their specific rank
        for rank, course in enumerate(instructor.preferences, start=1):
            ranked_preferences.append(Preference(course=course, rank=rank))

        # Add any missing courses with the maximum rank
        missing_courses = set(all_courses) - set(instructor.preferences)
        for course in missing_courses:
            ranked_preferences.append(Preference(course=course, rank=max_rank))

        # if instructor.degree == 'phd':
        #     # Add any missing courses with the maximum rank
        #     missing_courses = set(all_courses) - set(instructor.preferences)
        #     for course in missing_courses:
        #         ranked_preferences.append(Preference(course=course, rank=max_rank))
        # elif instructor.degree == 'mas':
        #     mas_classes = ['PS211', 'PS211S', 'PS211FR', 'SocSci311', 'SocSci311S', 'SocSci212']
        #     missing_courses = set(mas_classes) - set(instructor.preferences)
        #     for course in missing_courses:
        #         ranked_preferences.append(Preference(course=course, rank=max_rank))

        # Sort the preferences by rank, then alphabetically by course name if ranks are tied
        ranked_preferences.sort(key=lambda pref: (pref.rank, pref.course))

        # Store the ranked preferences in the dictionary
        preferences_with_ranks[instructor.name] = ranked_preferences

    return preferences_with_ranks


def print_matching_results(instructor_assignments: Dict[str, List[str]],
                           individuals: Dict[str, List[str]]) -> Dict[str, List[int]]:
    """Calculate and print the matched courses and their ranks for each instructor.

    Args:
        instructor_assignments (Dict[str, List[str]]): A dictionary mapping instructors to their assigned courses.
        individuals (Dict[str, List[str]]): A dictionary mapping instructors to their list of preferred courses.

    Returns:
        Dict[str, List[int]]: A dictionary mapping instructors to a list of ranks corresponding to their matched courses.
    """
    match_ranks = {}

    for instructor, courses in instructor_assignments.items():
        instructor_ranks = []

        for course in courses:
            if course in individuals[instructor]:
                # Get the rank (1-indexed)
                rank = individuals[instructor].index(course) + 1
            else:
                # If the course wasn't listed, it gets the lowest possible rank
                rank = len(individuals[instructor]) + 1

            instructor_ranks.append(rank)

        match_ranks[instructor] = instructor_ranks

    # Print out the results with ranks
    for instructor, courses in sorted(instructor_assignments.items()):
        ranks = match_ranks[instructor]
        print(f"{instructor} is matched with {courses} (Ranks: {ranks})")

    return match_ranks



if __name__ == "__main__":

    from pprint import pprint

    import pandas as pd
    # set wd
    from pyprojroot.here import here

    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     course_slots, instructor_max)
    wd = here()


    # load preferences df and order by instructor importance
    pref_df = pd.read_csv(wd/ "data/03_processed/instructors_with_course_preferences.csv")
    pref_df = pref_df.set_index('name')
    pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

    course_df = pd.read_csv(wd / "data/03_processed/course_data_with_course_directors.csv")
    inst_df = pd.read_csv(wd / "data/00_reference/instructor_info.csv")

    # get individual preferences from free response, add in core preferences last, if not included
    individuals = {}
    for _, item in pref_df.iterrows():
        name = item[0]
        core_class = item[3]
        prefs = []
        for i in range(7, 13):
            if item[i] and pd.notna(item[i]):
                prefs.append(item[i].strip())
            else:
                continue
        if prefs and core_class not in prefs:
            prefs.append(core_class)
        if not prefs:
            prefs = []
        individuals[name] = prefs

    instructor_list = build_instructors(inst_df,individuals)
    course_list = build_courses(course_df)

    pprint(individuals)

    preferences_with_ranks = create_preference_tuples(instructor_list, course_list)
    pprint(preferences_with_ranks)

# %%
