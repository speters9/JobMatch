from pathlib import Path
from typing import Dict, List, Optional, Tuple

# %%


def stable_marriage_solver(instructor_preferences: Dict[str, List[Tuple[str, int]]],
                           course_capacities: Dict[str, int],
                           instructor_max: Dict[str, int]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Solve the matching problem using a modified stable marriage algorithm with sequential matching.

    Args:
        instructor_preferences (Dict[str, List[Tuple[str, int]]]):
            A dictionary where keys are instructor names and values are lists of tuples.
            Each tuple contains a course name and a rank indicating the instructor's preference for that course.
        course_capacities (Dict[str, int]):
            A dictionary where keys are course names and values are the number of available slots for each course.
        instructor_max (Dict[str, int]):
            A dictionary where keys are instructor last names and values are the maximum number of classes they can teach.

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
            A tuple containing two dictionaries:
            - The first dictionary maps each instructor to their assigned courses.
            - The second dictionary maps each course to a list of assigned instructors.
    """
    # Create dictionaries to track the proposals and assignments
    course_assignments = {course: [] for course in course_capacities}
    instructor_assignments = {instructor: [] for instructor in instructor_preferences}

    # Create a dictionary to track the current proposals for each instructor
    current_proposals = {instructor: 0 for instructor in instructor_preferences}

    # Create a list to track free instructors (those not yet assigned or fully assigned)
    free_instructors = list(instructor_preferences.keys())
    iter_count = 0

    while free_instructors:
        iter_count += 1
        instructor = free_instructors.pop(0)  # Get the first free instructor

        # Check if the instructor has reached their maximum number of classes
        if len(instructor_assignments[instructor]) < instructor_max.get(instructor, 2):  # Default to 2 if not found
            if current_proposals[instructor] < len(instructor_preferences[instructor]):
                # The instructor proposes to their next preferred course
                preferred_course = instructor_preferences[instructor][current_proposals[instructor]].course

                # Check if the instructor is already teaching two different courses
                if len(set(instructor_assignments[instructor])) < 2 or preferred_course in instructor_assignments[instructor]:
                    while len(course_assignments[preferred_course]) < course_capacities[preferred_course]:
                        # Assign the instructor to this course
                        course_assignments[preferred_course].append(instructor)
                        instructor_assignments[instructor].append(preferred_course)

                        # Check if the instructor has reached their max number of classes
                        if len(instructor_assignments[instructor]) >= instructor_max.get(instructor, 1):
                            break

                # Move to the next preference if the instructor still needs assignments
                if len(instructor_assignments[instructor]) < instructor_max.get(instructor, 1):
                    current_proposals[instructor] += 1
                    free_instructors.append(instructor)

    print(f"Convergence after {iter_count} iterations")
    return instructor_assignments, course_assignments

# %%


if __name__ == "__main__":
    from pprint import pprint

    import pandas as pd
    from nameparser import HumanName
    from pyprojroot.here import here

    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     course_slots, instructor_max)
    from jobmatch.preprocessing import (create_preference_tuples,
                                        parse_preferences,
                                        print_matching_results)
    wd = here()

    # load preferences df and order by instructor importance
    pref_df = pd.read_excel(wd / "data/raw/Teaching_Preferences_cao18Aug.xlsx")
    pref_df = pref_df.set_index('Name')
    pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

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

    all_courses = list(course_id_map.values())
    preferences_with_ranks = create_preference_tuples(individuals, all_courses)

    print("Test on real preferences:\n")
    instructor_assignments, course_assignments = stable_marriage_solver(preferences_with_ranks, course_slots, instructor_max)
    # pprint(instructor_assignments)

    match_ranks = print_matching_results(instructor_assignments, individuals)
