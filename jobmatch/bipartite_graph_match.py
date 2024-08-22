from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

# build and plot graph
import networkx as nx

from jobmatch.dataclasses import AssignmentTracker, Course, Instructor

# %%



def build_network(instructors: List[Instructor], courses: List[Course], instructor_weighted: bool = False) -> nx.Graph:
    """Build a bipartite graph with adjusted weights for instructor rank and course preferences."""
    G = nx.Graph()

    instructor_names = [instructor.name for instructor in instructors]
    course_names = [f"{course.name}_{i+1}" for course in courses for i in range(course.sections_available)]

    G.add_nodes_from(instructor_names, bipartite=0)
    G.add_nodes_from(course_names, bipartite=1)

    unlisted_rank = 1 / (len(course_names) + 1)
    instructor_ranks = {instructor.name: idx + 1 for idx, instructor in enumerate(instructors)}

    for instructor in instructors:
        # skip empty instructors
        if not instructor.preferences:
            continue
        instructor_rank = instructor_ranks[instructor.name]
        for course_name in course_names:
            course_base = course_name.split('_')[0]
            if course_base in instructor.preferences:
                preference_rank = 1 / (instructor.preferences.index(course_base) + 1)
            else:
                preference_rank = unlisted_rank

            rank = preference_rank
            if instructor_weighted:
                rank = preference_rank + (1 / instructor_rank)

            G.add_edge(instructor.name, course_name, weight=rank)

    return G




def iterative_bipartite_matching_solver(instructors: List[Instructor], courses: List[Course], instructor_weighted: bool = False, verbose: bool = False) -> Tuple[List[Instructor], List[Course], List[nx.Graph]]:
    trackers = {instructor.name: AssignmentTracker(instructor=instructor) for instructor in instructors}
    graphs = []
    iter_count = 0

    while True:
        iter_count += 1
        if verbose:
            print(f"\n--- Iteration {iter_count} ---")

        # Filter out instructors who have reached their max classes or max unique courses
        eligible_instructors = [
            tracker.instructor for tracker in trackers.values()
            if tracker.course_count < tracker.instructor.max_classes and len(tracker.unique_courses) < 2
        ]

        # Filter out courses that are already fully assigned
        eligible_courses = [course for course in courses if course.sections_available > 0]

        if not eligible_instructors or not eligible_courses:
            print(f"All instructors or courses are exhausted after iteration {iter_count}. Ending loop.")
            break

        # Build the network with eligible instructors and available courses
        G = build_network(eligible_instructors, eligible_courses, instructor_weighted)
        graphs.append(G)

        matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)

        if verbose:
            print(f"Matching in this iteration: {matching}")

        assignments_made = False

        for instructor_name, course_name in matching:
            if instructor_name in trackers:
                tracker = trackers[instructor_name]
                course = next(crs for crs in courses if crs.name == course_name.split('_')[0])
            else:
                tracker = trackers[course_name]
                course = next(crs for crs in courses if crs.name == instructor_name.split('_')[0])

            course_base = course.name

            if verbose:
                print(f"Trying to assign {tracker.instructor.name} to {course_base}...")

            if tracker.can_assign(course_base):
                available_slots = min(tracker.instructor.max_classes - tracker.course_count, course.sections_available)

                if available_slots > 0:
                    if verbose:
                        print(f"Assigning {tracker.instructor.name} to {course_base} ({available_slots} slots)...")
                    tracker.assign_course(course_base, available_slots)
                    course.assigned_instructors.extend([tracker.instructor.name] * available_slots)
                    course.sections_available -= available_slots
                    assignments_made = True
                else:
                    if verbose:
                        print(f"No available slots for {tracker.instructor.name} in {course_base}.")
            else:
                if verbose:
                    print(f"{tracker.instructor.name} cannot be assigned to {course_base} (Max classes: {tracker.instructor.max_classes}, Current: {tracker.course_count}, Unique courses: {len(tracker.unique_courses)}).")

        if not assignments_made:
            print(f"No assignments made in iteration {iter_count}. Ending loop.")
            break

    # Transfer assignments from trackers to instructor objects
    for tracker in trackers.values():
        tracker.instructor.assigned_courses.extend(tracker.assigned_courses)
        tracker.instructor.unique_courses.update(tracker.unique_courses)

    return instructors, courses, graphs


# %%
if __name__ == "__main__":
    # test cases -- overlapping preferences and classes

    import matplotlib.pyplot as plt
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
    final_instructors, final_courses, G = iterative_bipartite_matching_solver(instructor_list, course_list, instructor_weighted=False)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=False)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
    # %%

    def visualize_network(G):
        pos = nx.spring_layout(G, seed=42)  # Layout for positioning nodes

        # Extract the weights from the graph edges
        edge_labels = nx.get_edge_attributes(G, 'weight')

        # Draw the graph
        plt.figure(figsize=(12, 8))

        # Draw the nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')

        # Draw the edges with their weights
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

        # Draw the labels for nodes
        nx.draw_networkx_labels(G, pos, font_size=12, font_family="sans-serif")

        # Draw the edge labels (weights)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        plt.title("Bipartite Network Visualization with Weights")
        plt.show()

    # Visualize the network with Plotly
    visualize_network(G[-1])
