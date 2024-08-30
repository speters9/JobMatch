import copy
from pathlib import Path
from typing import List, Tuple

import pulp

from jobmatch.dataclasses import Course, Instructor
from jobmatch.preprocessing import create_preference_tuples

# %%


def iterative_linear_programming_solver(
    instructors: List[Instructor],
    courses: List[Course],
    method: str = 'default',
    verbose: bool = False
) -> Tuple[List[Instructor], List[Course]]:
    """
    Solve the matching problem using linear programming with iterative assignments.

    Args:
        instructors (List[Instructor]): A list of Instructor objects.
        courses (List[Course]): A list of Course objects.
        method (str): The method for solving the linear programming problem. Defaults to 'default'.
        verbose (bool): Whether to print detailed logs during execution. Defaults to False.

    Returns:
        Tuple[List[Instructor], List[Course]]: The updated lists of Instructor and Course objects with assignments.
    """
    iter_count = 0

    while True:
        iter_count += 1

        # Filter out instructors who have already reached their max classes or unique course limit
        eligible_instructors = [
            instructor for instructor in instructors
            if len(instructor.assigned_courses) < instructor.max_classes and len(instructor.unique_courses) < 2
        ]
        eligible_courses = [course for course in courses if course.sections_available > 0]

        # If no eligible instructors or courses remain, stop the loop
        if not eligible_instructors or not eligible_courses:
            print(f"Linear Programming: Convergence after {iter_count} iterations")
            break

        # Create preference tuples for the current iteration
        preference_tuples = {
            instructor.name: create_preference_tuples([instructor], eligible_courses)[instructor.name]
            for instructor in eligible_instructors
        }

        # Rebuild LP variables for choices
        choices = pulp.LpVariable.dicts(
            "Choice",
            ((instructor.name, course.name)
             for instructor in eligible_instructors for course in eligible_courses),
            cat='Binary'
        )
        if verbose:
            print(f"{choices.keys()=}")

        # Define the problem instance
        prob = pulp.LpProblem("Course_Assignment", pulp.LpMaximize)

        # Define the primary and secondary objectives based on the current iteration's data
        max_rank = len(courses)

        if method == 'default':
            prob += pulp.lpSum(
                # incorporate preference order as well, so big conditional statement,
                # iterating through instructors, and then their preferences to get the ranking
                # in order to weight each matching
                choices[instructor.name, pref.course] * (max_rank + 1 - pref.rank)
                for instructor in eligible_instructors
                if instructor.name in preference_tuples and preference_tuples[instructor.name]
                for pref in preference_tuples[instructor.name]
                if pref.course in [course.name for course in eligible_courses]
            )

        elif method == 'multi_objective':
            PRIMARY_WEIGHT = 1000
            SECONDARY_WEIGHT = 1
            prob += (
                PRIMARY_WEIGHT * pulp.lpSum(
                    choices[instructor.name, pref.course] * (max_rank + 1 - pref.rank)
                    for instructor in eligible_instructors
                    if instructor.name in preference_tuples and preference_tuples[instructor.name]
                    for pref in preference_tuples[instructor.name]
                    if pref.course in [course.name for course in eligible_courses]
                ) +
                SECONDARY_WEIGHT * pulp.lpSum(
                    choices[instructor.name, pref.course] * (len(eligible_instructors) - eligible_instructors.index(instructor))
                    for instructor in eligible_instructors
                    if instructor.name in preference_tuples and preference_tuples[instructor.name]
                    for pref in preference_tuples[instructor.name]
                    if pref.course in [course.name for course in eligible_courses]
                )
            )

        # Add constraints
        for instructor in eligible_instructors:
            prob += pulp.lpSum(
                choices[instructor.name, course.name] for course in eligible_courses
            ) <= instructor.max_classes - len(instructor.assigned_courses)

            prob += pulp.lpSum(
                choices[instructor.name, course.name] for course in eligible_courses if course.name in instructor.unique_courses or len(instructor.unique_courses) < 2
            ) <= 2 - len(instructor.unique_courses)

        for course in eligible_courses:
            prob += pulp.lpSum(
                choices[instructor.name, course.name] for instructor in eligible_instructors
            ) <= course.sections_available

        # Solve the LP problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        assignments_made = False

        for instructor in eligible_instructors:
            assigned_courses = [
                course.name for course in eligible_courses if pulp.value(choices[instructor.name, course.name]) == 1
            ]

            for course_name in assigned_courses:
                course = next(crs for crs in eligible_courses if crs.name == course_name)
                if instructor.can_teach(course_name):
                    available_slots = min(instructor.max_classes - len(instructor.assigned_courses), course.sections_available)
                    if available_slots > 0:
                        instructor.assign_course(course_name, available_slots)
                        course.assigned_instructors.extend([instructor.name] * available_slots)
                        course.sections_available -= available_slots
                        assignments_made = True

                        if verbose:
                            print(f"Assigned {available_slots} slots of {course_name} to {instructor.name}")

        # If no assignments were made, break the loop
        if not assignments_made:
            break

     # Post-processing step: Assign unassigned courses to available instructors
    for course in courses:
        while course.sections_available > 0:
            available_instructors = [
                instructor for instructor in instructors
                if len(instructor.assigned_courses) < instructor.max_classes and instructor.can_teach(course.name)
            ]
            if not available_instructors:
                break  # No instructors left to assign
            instructor = available_instructors[0]
            instructor.assign_course(course.name, 1)
            course.assigned_instructors.append(instructor.name)
            course.sections_available -= 1

            if verbose:
                print(f"Assigned {course.name} to {instructor.name} in post-processing.")

    print(f"Linear Programming: Convergence after {iter_count} iterations")

    return instructors, courses

# %%
if __name__ == "__main__":
    import pandas as pd
    from pyprojroot.here import here

    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     instructor_max)
    from jobmatch.preprocessing import (build_courses, build_instructors,
                                        create_preference_tuples,
                                        parse_preferences)
    wd = here()

    # load preferences df and order by instructor importance
    pref_df = pd.read_excel(wd / "data/raw/Teaching_Preferences_cao21Aug.xlsx")
    pref_df = pref_df.set_index('Name')
    pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

    course_df = pd.read_csv(wd / "data/raw/course_data.csv")
    inst_df = pd.read_csv(wd / "data/raw/instructor_info.csv")

    # get individual preferences from free response, add in core preferences last, if not included
    individuals = {}
    for item in pref_df.itertuples():
        name = item[1]
        core_class = core_dict.get(item[6], 'PS211' if not item[0]==0 else item[7])
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    instructor_list = build_instructors(inst_df, individuals)
    course_list = build_courses(course_df)

    # Solve using bipartite matching
    final_instructors, final_courses = iterative_linear_programming_solver(instructor_list, course_list, verbose = False, method='default')

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=False)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
