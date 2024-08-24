from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jobmatch.dataclasses import Course, Instructor
from jobmatch.global_functions import set_all_seeds

# %%


def stable_marriage_solver(instructors: List[Instructor],
                           courses: List[Course]) -> Tuple[List[Instructor], List[Course]]:
    """Solve the matching problem using a modified stable marriage algorithm with sequential matching.

    Args:
        instructors (List[Instructor]): A list of Instructor objects.
        courses (List[Course]): A list of Course objects.

    Returns:
        Tuple[List[Instructor], List[Course]]:
            A tuple containing the updated list of Instructor objects with their assigned courses,
            and the updated list of Course objects with their assigned instructors.
    """
    # Create a dictionary to track the current proposals for each instructor
    current_proposals = {instructor.name: 0 for instructor in instructors}

    # Create a list to track free instructors (those not yet assigned or fully assigned)
    free_instructors = [instructor for instructor in instructors if instructor.preferences]
    iter_count = 0

    while free_instructors:
        iter_count += 1
        instructor = free_instructors.pop(0)  # Get the first free instructor

        # Skip if preferences are None or empty
        if not instructor.preferences:
            continue

        # Ensure the instructor hasn't reached their maximum number of classes
        if len(instructor.assigned_courses) < instructor.max_classes:
            # Check if the instructor has more preferences to propose to
            if current_proposals[instructor.name] < len(instructor.preferences):
                # The instructor proposes to their next preferred course
                preferred_course_name = instructor.preferences[current_proposals[instructor.name]]
                try:
                    course = next(crs for crs in courses if crs.name == preferred_course_name)
                except StopIteration:
                    print(f"Course not found: {preferred_course_name}")
                    raise KeyError(f"Course not found: {preferred_course_name}.\nPlease ensure correct naming conventions")

                if instructor.can_teach(preferred_course_name):
                    available_slots = min(instructor.max_classes - len(instructor.assigned_courses), course.sections_available)
                    if available_slots > 0:
                        instructor.assign_course(preferred_course_name, available_slots)
                        course.assigned_instructors.extend([instructor.name] * available_slots)
                        course.sections_available -= available_slots

                # Move to the next preference if the instructor still needs assignments
                if len(instructor.assigned_courses) < instructor.max_classes:
                    current_proposals[instructor.name] += 1
                    free_instructors.append(instructor)

    # Post-processing step: Assign unmatched instructors to available courses
    for instructor in instructors:
        while len(instructor.assigned_courses) < instructor.max_classes:
            available_courses = [course for course in courses if course.sections_available > 0]

            if not available_courses:
                break  # No courses left to assign

            assigned = False  # Track whether an assignment was made

            for course in available_courses:
                if instructor.can_teach(course.name):
                    instructor.assign_course(course.name, 1)
                    course.assigned_instructors.append(instructor.name)
                    course.sections_available -= 1
                    assigned = True
                    break  # Exit the for loop once an assignment is made

            if not assigned:
                break  # Exit the while loop if no valid assignment could be made


    print(f"Stable Marriage: Convergence after {iter_count} iterations")
    return instructors, courses


# %%


if __name__ == "__main__":
    from pprint import pprint

    import pandas as pd
    from pyprojroot.here import here

    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     course_slots, instructor_max)
    from jobmatch.preprocessing import (build_courses, build_instructors,
                                        create_preference_tuples,
                                        parse_preferences,
                                        print_matching_results)
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
        core_class = core_dict.get(item[6], 'PS211' if not item[0]==0 else item[7])
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    instructor_list = build_instructors(inst_df,individuals)
    course_list = build_courses(course_df)

    set_all_seeds(94305)
    # Solve using bipartite matching
    final_instructors, final_courses = stable_marriage_solver(instructor_list, course_list)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=False)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
