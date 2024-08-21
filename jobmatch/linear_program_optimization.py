import copy
import random
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Tuple

import pulp

# %%



def iterative_linear_programming_solver(instructor_preferences: Dict[str, List[namedtuple]],
                                        course_capacities: Dict[str, int],
                                        instructor_max_full: Dict[str, int],
                                        method: str = 'default') -> List[Tuple[str, str, str]]:
    """Solve the course matching problem iteratively using linear programming with a greedy approach.

    Args:
        instructor_preferences (Dict[str, List[namedtuple]]): A dictionary of instructors and their ranked preferences.
        course_capacities (Dict[str, int]): A dictionary of courses and their respective capacities.
        instructor_max_full (Dict[str, int]): Maximum classes each instructor can teach.
        method (str): The method for solving the problem ('default', 'multi_objective'). Defaults to 'default'.

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
            A tuple containing two dictionaries:
            - The first dictionary maps each instructor to their assigned courses (as a list).
            - The second dictionary maps each course to a list of assigned instructors.
    """
    # Initialize dictionaries to track assignments
    instructor_assignments = {instructor: [] for instructor in instructor_preferences}
    course_assignments = {course: [] for course in course_capacities}
    iter_count = 0

    while any(len(assigned_courses) < instructor_max_full[instructor] for instructor, assigned_courses in instructor_assignments.items()):
        iter_count += 1
        # Create copies of the original dictionaries to ensure integrity during iterations
        current_course_capacities = copy.deepcopy(course_capacities)
        current_instructor_preferences = copy.deepcopy(instructor_preferences)

        # Define the problem instance
        prob = pulp.LpProblem("Course_Assignment", pulp.LpMaximize)

        # Define LP variables for choices, referencing only current data
        choices = pulp.LpVariable.dicts("Choice",
                                        ((i, c) for i in current_instructor_preferences for c in current_course_capacities),
                                        cat='Binary')

        # Define the primary and secondary objectives based on the current iteration's data
        max_rank = max(pref.rank for prefs in current_instructor_preferences.values() for pref in prefs)
        if method == 'default':
            prob += pulp.lpSum(choices[i, pref.course] * (max_rank + 1 - pref.rank)
                               for i in current_instructor_preferences
                               for pref in current_instructor_preferences[i])
        elif method == 'multi_objective':
            PRIMARY_WEIGHT = 1000
            SECONDARY_WEIGHT = 1
            prob += (PRIMARY_WEIGHT * pulp.lpSum(choices[i, pref.course] * (max_rank + 1 - pref.rank)
                                                 for i in current_instructor_preferences
                                                 for pref in current_instructor_preferences[i]) +
                     SECONDARY_WEIGHT * pulp.lpSum(choices[i, c] * (len(current_instructor_preferences) - list(current_instructor_preferences.keys()).index(i))
                                                   for i in current_instructor_preferences for c in current_course_capacities))

        # Constraints to ensure instructors do not exceed their maximum class load
        for i in current_instructor_preferences:
            prob += pulp.lpSum(choices[i, c] for c in current_course_capacities) <= instructor_max_full[i]

        # Constraints to ensure no instructor teaches more than 2 unique classes
        for i in current_instructor_preferences:
            prob += pulp.lpSum(choices[i, c] for c in current_course_capacities) <= 2

        # Ensure courses do not exceed their capacity
        for c in list(current_course_capacities.keys()):  # Iterate over a copy of the keys to avoid modification issues
            prob += pulp.lpSum(choices[i, c] for i in current_instructor_preferences) <= current_course_capacities[c]

        # Solve the LP problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        # Process the results and update assignments
        for i in current_instructor_preferences:
            assigned_courses = [c for c in list(current_course_capacities.keys()) if pulp.value(choices[i, c]) == 1]

            for c in assigned_courses:
                # Add the course multiple times until max is reached or capacity runs out
                while len(instructor_assignments[i]) < instructor_max_full[i] and current_course_capacities.get(c, 0) > 0:
                    instructor_assignments[i].append(c)
                    course_assignments[c].append(i)

                    # Reduce the course capacity for the next iteration
                    current_course_capacities[c] -= 1

            # Skip instructors who have reached their maximum load
            if len(instructor_assignments[i]) >= instructor_max_full[i]:
                continue  # Skip this instructor in the next iterations

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

    all_courses = list(course_slots.keys())
    preferences_with_ranks = create_preference_tuples(individuals, all_courses)

    print("Test on real preferences:\n")
    instructor_assignments, class_assignments = iterative_linear_programming_solver(
        preferences_with_ranks, course_slots, instructor_max, method='default')

    match_ranks = print_matching_results(instructor_assignments, individuals)
