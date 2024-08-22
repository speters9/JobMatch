import copy
from pathlib import Path
from typing import List, Tuple

import pulp

from jobmatch.dataclasses import AssignmentTracker, Course, Instructor
from jobmatch.preprocessing import create_preference_tuples

# %%

def add_constraints(prob, current_trackers, current_courses, choices):
    """Add the required constraints to the linear programming problem."""
    for tracker in current_trackers.values():
        prob += pulp.lpSum(choices[tracker.instructor.name, course.name]
                           for course in current_courses) <= tracker.instructor.max_classes - tracker.course_count

    for tracker in current_trackers.values():
        prob += pulp.lpSum(choices[tracker.instructor.name, course.name]
                           for course in current_courses if tracker.can_assign(course.name)) <= 2 - len(tracker.unique_courses)

    for course in current_courses:
        prob += pulp.lpSum(choices[tracker.instructor.name, course.name] for tracker in current_trackers.values()) <= course.sections_available




def iterative_linear_programming_solver(instructors: List[Instructor], courses: List[Course], method: str = 'default', verbose: bool = False) -> Tuple[List[Instructor], List[Course]]:
    """
    Solve the instructor-course assignment problem using an iterative linear programming approach.

    Args:
        instructors (List[Instructor]): A list of Instructor objects representing instructors.
        courses (List[Course]): A list of Course objects representing courses.
        method (str, optional): The linear programming method to use ('default' or 'multi_objective'). Defaults to 'default'.
        verbose (bool, optional): If True, print detailed debug information. Defaults to False.

    Returns:
        Tuple[List[Instructor], List[Course]]: Updated instructors and courses after assignment.
    """
    iter_count = 0

    # Initialize eligible instructors and courses
    eligible_instructors = [
        copy.deepcopy(instructor)
        for instructor in instructors
        if instructor.max_classes > len(instructor.assigned_courses) or len(set(instructor.assigned_courses)) < 2
    ]

    eligible_courses = [copy.deepcopy(course) for course in courses if course.sections_available > 0]

    while True:
        iter_count += 1

        # If no eligible instructors or courses remain, stop the loop
        if not eligible_instructors or not eligible_courses:
            print(f"Convergence after {iter_count} iterations")
            break

        # Create deep copies of the trackers and course capacities for the current iteration
        current_trackers = {
            instructor.name: AssignmentTracker(instructor=instructor)
            for instructor in eligible_instructors
        }
        current_courses = copy.deepcopy(eligible_courses)

        # Create preference tuples for the current iteration
        preference_tuples = {tracker.instructor.name: create_preference_tuples([tracker.instructor], current_courses)[tracker.instructor.name]
                             for tracker in current_trackers.values()}


        # Define the problem instance
        prob = pulp.LpProblem("Course_Assignment", pulp.LpMaximize)

        # Define LP variables for choices, referencing only current data
        choices = pulp.LpVariable.dicts("Choice",
                                        ((tracker.instructor.name, course.name)
                                         for tracker in current_trackers.values() for course in current_courses),
                                        cat='Binary')

        # Define the primary and secondary objectives based on the current iteration's data
        max_rank = len(courses)

        if method == 'default':
            prob += pulp.lpSum(choices.get((tracker.instructor.name, pref.course), 0) * (max_rank + 1 - pref.rank)
                               for tracker in current_trackers.values()
                               for pref in preference_tuples[tracker.instructor.name])

        elif method == 'multi_objective':
            PRIMARY_WEIGHT = 1000
            SECONDARY_WEIGHT = 1
            prob += (PRIMARY_WEIGHT * pulp.lpSum(choices[tracker.instructor.name, pref.course] * (max_rank + 1 - pref.rank)
                                                 for tracker in current_trackers.values()
                                                 for pref in preference_tuples[tracker.instructor.name]) +
                     SECONDARY_WEIGHT * pulp.lpSum(choices[tracker.instructor.name, course.name] * (len(current_trackers) - list(current_trackers.keys()).index(tracker.instructor.name))
                                                   for tracker in current_trackers.values() for course in current_courses))

        # Add constraints
        add_constraints(prob, current_trackers, current_courses, choices)

        # Solve the LP problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        # assign courses to instructors if able
        assignments_made = False
        for tracker in current_trackers.values():
            # Start with tracker.course_count < max_classes, etc.
            if len(tracker.instructor.assigned_courses) < tracker.instructor.max_classes:
                # check if a preferences is in the current courses - ensures assignments are ordered by preference
                for pref in preference_tuples[tracker.instructor.name]:
                    preferred_course_name = pref.course
                    try:
                        course = next(crs for crs in current_courses if crs.name == preferred_course_name)
                    except StopIteration:
                        #print(f"Course not found: {preferred_course_name}, {tracker.instructor.name}")
                        continue
                    # double check assignment restrictions
                    if (len(tracker.instructor.unique_courses) < 2) or (preferred_course_name in tracker.instructor.unique_courses):
                        if tracker.can_assign(preferred_course_name):
                            available_slots = min(tracker.instructor.max_classes - tracker.course_count, course.sections_available)
                            if available_slots > 0:
                                tracker.assign_course(preferred_course_name, available_slots)
                                course.assigned_instructors.extend([tracker.instructor.name] * available_slots)
                                course.sections_available -= available_slots
                                assignments_made = True

                                if verbose:
                                    print(f"Assigned {available_slots} slots of {preferred_course_name} to {tracker.instructor.name}")
                            else:
                                if verbose:
                                    print(f"No available slots for {tracker.instructor.name} in {preferred_course_name}.")
                        else:
                            if verbose:
                                print(f"{tracker.instructor.name} cannot be assigned to {preferred_course_name} (Max classes: {tracker.instructor.max_classes}, Current: {tracker.course_count}, Unique courses: {len(tracker.unique_courses)}).")

        if verbose:
            for tracker in current_trackers.values():
                print(f"Tracker for {tracker.instructor.name}: Courses Assigned = {tracker.assigned_courses}, Course Count = {tracker.course_count}")

            for course in current_courses:
                print(f"Course {course.name}: Sections Available = {course.sections_available}, Assigned Instructors = {course.assigned_instructors}")

        # Transfer assignments from trackers to original instructors and courses
        for tracker in current_trackers.values():
            original_instructor = next(ins for ins in instructors if ins.name == tracker.instructor.name)
            original_instructor.assigned_courses.extend(tracker.assigned_courses)
            original_instructor.unique_courses.update(tracker.unique_courses)

        for course in current_courses:
            original_course = next(crs for crs in courses if crs.name == course.name)
            original_course.sections_available = course.sections_available
            original_course.assigned_instructors.extend(course.assigned_instructors)

        # After assignments are made:
        eligible_instructors = [
            instructor
            for instructor in instructors
            if instructor.max_classes > len(instructor.assigned_courses)
        ]
        eligible_courses = [course for course in current_courses if course.sections_available > 0]

        if verbose:
            print(f"{iter_count=}\n{eligible_instructors=}")

        # If no assignments were made, break the loop
        if not assignments_made:
            print(f"Convergence after {iter_count} iterations")
            break

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
        core_class = core_dict.get(item[6], 'PS211')
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    instructor_list = build_instructors(inst_df, individuals)
    course_list = build_courses(course_df)

    # Solve using bipartite matching
    final_instructors, final_courses = iterative_linear_programming_solver(instructor_list, course_list, verbose = False)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=True)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
