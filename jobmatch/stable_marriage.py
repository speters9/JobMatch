from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jobmatch.dataclasses import AssignmentTracker, Course, Instructor

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
    # Initialize trackers for each instructor
    trackers = {instructor.name: AssignmentTracker(instructor=instructor) for instructor in instructors}

    # Create a dictionary to track the current proposals for each instructor
    current_proposals = {instructor.name: 0 for instructor in instructors}

    # Create a list to track free instructors (those not yet assigned or fully assigned)
    free_instructors = list(trackers.keys())
    iter_count = 0

    while free_instructors:
        iter_count += 1
        instructor_name = free_instructors.pop(0)  # Get the first free instructor
        tracker = trackers[instructor_name]  # Get the corresponding tracker

        # Skip if preferences are None or empty
        if not tracker.instructor.preferences:
            continue

        # Ensure the instructor hasn't reached their maximum number of classes
        if tracker.course_count < tracker.instructor.max_classes:
            if current_proposals[instructor_name] < len(tracker.instructor.preferences):
                # The instructor proposes to their next preferred course
                preferred_course_name = tracker.instructor.preferences[current_proposals[instructor_name]]
                try:
                    course = next(crs for crs in courses if crs.name == preferred_course_name)
                except StopIteration:
                    print(f"Course not found: {preferred_course_name}")
                    raise KeyError(f"Course not found: {preferred_course_name}.\nPlease ensure correct naming conventions")

                if tracker.can_assign(preferred_course_name):
                    available_slots = min(tracker.instructor.max_classes - tracker.course_count, course.sections_available)
                    if available_slots > 0:
                        tracker.assign_course(preferred_course_name, available_slots)
                        course.assigned_instructors.extend([tracker.instructor.name] * available_slots)
                        course.sections_available -= available_slots

                # Move to the next preference if the instructor still needs assignments
                if tracker.course_count < tracker.instructor.max_classes:
                    current_proposals[instructor_name] += 1
                    free_instructors.append(instructor_name)

    # Transfer assignments from trackers to instructors
    for tracker in trackers.values():
        tracker.instructor.assigned_courses.extend(tracker.assigned_courses)
        tracker.instructor.unique_courses.update(tracker.unique_courses)

    print(f"Convergence after {iter_count} iterations")
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
        core_class = core_dict.get(item[6], 'PS211')
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    instructor_list = build_instructors(inst_df,individuals)
    course_list = build_courses(course_df)


    # Solve using bipartite matching
    final_instructors, final_courses = stable_marriage_solver(instructor_list, course_list)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=True)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
