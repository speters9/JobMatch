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
                                        degree=instructor['degree'],
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


def normalize_preferences(preference_string: str) -> List[str]:
    """
    Normalize a preference string by standardizing course identifiers, removing extraneous characters,
    and splitting the string into a list of preferences.

    Args:
        preference_string (str): The raw preference string to be normalized.

    Returns:
        List[str]: A list of normalized preferences.
    """
    # normalize string dividers
    preference_string = preference_string.replace('//', ';')

    # Normalize course identifiers by replacing variations of "Pol Sci", SocSci or FAS
    preferences = re.sub(r"pol(i)?\s*sc(i)?\s*", "PS", preference_string, flags=re.IGNORECASE)
    preferences = re.sub(r"soc\s*sc(i)?\s*", "SocSci", preferences, flags=re.IGNORECASE)
    preferences = re.sub(r"fas\s?", "FAS", preferences, flags=re.IGNORECASE)

    # Split the preferences by semicolons or commas
    preferences_list = re.split(r"[;,]", preferences)

    # Process each preference individually
    processed_preferences = []
    for pref in preferences_list:
        # Remove numbers in parentheses
        pref = re.sub(r"\s*\(\d+\)\s*", "", pref.strip())

        # Remove any extraneous characters
        pref = re.sub(r"[^a-zA-Z0-9\s?:/-]", "", pref.strip())

        # Normalize spacing
        pref = re.sub(r"\s+", " ", pref).strip()

        # Add to the list if it starts with 'PS', 'SocSci', 'FAS', or a number
        if re.match(r"^(PS|SocSci|FAS|\d)", pref, flags=re.IGNORECASE):
            processed_preferences.append(pref)

    return processed_preferences

# Step 2: Function to normalize and parse input strings


def parse_preferences(preference_string: str, course_id_map: Dict[str, str], course_map: Dict[str, str], core_class: str) -> List[str]:
    """
    Parse a preference string, standardize course names using a course ID map, and optionally add a core class
    if it is not already included.

    Args:
        preference_string (str): The raw preference string to be parsed.
        course_id_map (Dict[str, str]): A dictionary mapping course identifiers to standardized course names.
        course_map (Dict[str, str]): A dictionary mapping course names to standardized course identifiers.
        core_class (str): The core class that should be included in the preferences list.

    Returns:
        List[str]: A list of standardized course preferences.
    """
    # Replace // with semicolon for consistent splitting
    preferences = normalize_preferences(preference_string)

    # Standardize course names
    standardized_preferences = []
    for pref in preferences:
        pref = pref.strip()
        matched = False

        # First, check if any course number is in the string
        for course_id, course_name in course_id_map.items():
            if course_id in pref:
                standardized_preferences.append(course_name)
                matched = True
                break

        # If no course number is found, use fuzzy matching on the course name
        if not matched:
            possible_match, score, idx = process.extractOne(pref, course_map.keys(), scorer=fuzz.partial_ratio)
            if score > 90:  # 90 works well as a threshold
                standardized_preferences.append(course_map[possible_match])
                matched = True
            else:
                # Ask user for input if the match is not found
                print(f"\n'{pref}' could not be matched automatically.")
                user_input = input("Please enter the correct course identifier or name (or press Enter to skip): \n").strip()

                if user_input:
                    # Check if the user input corresponds to an existing course_id or course_name
                    if user_input in course_id_map:
                        standardized_preferences.append(course_id_map[user_input])
                    elif user_input in course_map:
                        standardized_preferences.append(course_map[user_input])
                    else:
                        # Add user input to course_map and course_id_map
                        new_course_name = user_input
                        new_course_id = input(
                            f"Name not recognized. Entering as a new course ID. \nPlease enter the identifier for '{new_course_name}': \n").strip()
                        course_map[new_course_name] = new_course_id
                        course_id_map[new_course_id] = new_course_id
                        standardized_preferences.append(new_course_id)
                        print(f"Added '{new_course_name}' with identifier '{new_course_id}' to the course map.")
                else:
                    standardized_preferences.append("UNKNOWN")

    # add preferred primary core class if not in list
    if core_class and core_class not in standardized_preferences:
        standardized_preferences.append(core_class)

    return standardized_preferences


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
    pref_df = pd.read_excel(wd/ "data/raw/Teaching_Preferences_cao21Aug.xlsx")
    pref_df = pref_df.set_index('Name')
    pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

    course_df = pd.read_csv(wd / "data/raw/course_data.csv")
    inst_df = pd.read_csv(wd / "data/raw/instructor_info.csv")

    # get individual preferences from free response, add in core preferences last, if not included
    individuals = {}
    for item in pref_df.itertuples():
        name = item[1]
        core_class = core_dict.get(item[6], 'SocSci311')
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    instructor_list = build_instructors(inst_df,individuals)
    course_list = build_courses(course_df)

    pprint(individuals)

    preferences_with_ranks = create_preference_tuples(instructor_list, course_list)
    pprint(preferences_with_ranks)
