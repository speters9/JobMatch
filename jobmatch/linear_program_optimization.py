from pathlib import Path
from typing import List, Tuple

import pulp

from jobmatch.dataclasses import Course, Instructor
from jobmatch.preprocessing import create_preference_tuples

# %%

def iterative_linear_programming_solver(
    instructors: List[Instructor],
    courses: List[Course],
    verbose: bool = False
) -> Tuple[List[Instructor], List[Course]]:
    """
    Solve the matching problem using linear programming with iterative assignments
    and factorized instructor sections.

    Args:
        instructors (List[Instructor]): A list of Instructor objects.
        courses (List[Course]): A list of Course objects.
        method (str): The method for solving the linear programming problem. Defaults to 'default'.
        verbose (bool): Whether to print detailed logs during execution. Defaults to False.

    Returns:
        Tuple[List[Instructor], List[Course]]: The updated lists of Instructor and Course objects with assignments.
    """
    iter_count = 0
    instructor_sections = []
    section_to_instructor_map = {}

    # Factorize instructors into individual sections
    for instructor in instructors:
        for i in range(instructor.max_classes):
            section_name = f"{instructor.name}_section_{i+1}"
            instructor_sections.append(section_name)
            section_to_instructor_map[section_name] = instructor

    while True:
        iter_count += 1

        # Filter out instructor sections that are already fully assigned or have reached unique course limit
        eligible_instructor_sections = [
            section for section in instructor_sections
            if len(section_to_instructor_map[section].assigned_courses) < section_to_instructor_map[section].max_classes
            and len(section_to_instructor_map[section].unique_courses) < 2
        ]
        eligible_courses = [course for course in courses if course.sections_available > 0]

        # If no eligible instructor sections or courses remain, stop the loop
        if not eligible_instructor_sections or not eligible_courses:
            break

        # Create preference tuples for the current iteration
        preference_tuples = {
            section: create_preference_tuples([section_to_instructor_map[section]], eligible_courses)[section_to_instructor_map[section].name]
            for section in eligible_instructor_sections
        }

        # Rebuild LP variables for choices
        choices = pulp.LpVariable.dicts(
            "Choice",
            ((section, course.name) for section in eligible_instructor_sections for course in eligible_courses),
            cat='Binary'
        )
        if verbose:
            print(f"{choices.keys()=}")

        # Define the problem instance
        prob = pulp.LpProblem("Course_Assignment", pulp.LpMaximize)

        # Define the primary and secondary objectives based on the current iteration's data
        max_rank = len(courses)

        prob += pulp.lpSum(
            choices[section, pref.course] * (max_rank + 1 - pref.rank)
            for section in eligible_instructor_sections
            if section in preference_tuples and preference_tuples[section]
            for pref in preference_tuples[section]
            if pref.course in [course.name for course in eligible_courses]
            )


        # Add constraints
        for section in eligible_instructor_sections:
            instructor = section_to_instructor_map[section]
            prob += pulp.lpSum(
                choices[section, course.name] for course in eligible_courses
            ) <= 1

            prob += pulp.lpSum(
                choices[section, course.name] for course in eligible_courses if course.name in instructor.unique_courses or len(instructor.unique_courses) < 2
            ) <= 2 - len(instructor.unique_courses)

        for course in eligible_courses:
            prob += pulp.lpSum(
                choices[section, course.name] for section in eligible_instructor_sections
            ) <= course.sections_available

        # Solve the LP problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        assignments_made = False

        for section in eligible_instructor_sections:
            assigned_courses = [
                course.name for course in eligible_courses if pulp.value(choices[section, course.name]) == 1
            ]

            instructor = section_to_instructor_map[section]
            for course_name in assigned_courses:
                course = next(crs for crs in eligible_courses if crs.name == course_name)
                if instructor.can_teach(course_name):
                    available_slots = min(1, course.sections_available)
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
                section_to_instructor_map[section] for section in instructor_sections
                if len(section_to_instructor_map[section].assigned_courses) < section_to_instructor_map[section].max_classes and section_to_instructor_map[section].can_teach(course.name)
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

    from gui.load_data import load_courses, load_instructors
    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     instructor_max)
    from jobmatch.preprocessing import (build_courses, build_instructors,
                                        create_preference_tuples,
                                        parse_preferences)
    wd = here()


    instructor_list = load_instructors(str(wd / "data/validate/instructors_with_preferences.csv"))
    course_list = load_courses(str(wd / "data/validate/course_data_with_course_directors.csv"))


    # Solve using bipartite matching
    final_instructors, final_courses = iterative_linear_programming_solver(instructor_list, course_list, verbose = False)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=False)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
