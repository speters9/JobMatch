from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

# build and plot graph
import networkx as nx

from jobmatch.dataclasses import Course, Instructor
from jobmatch.global_functions import set_all_seeds

# %%

def build_network_with_factorized_instructors(instructors, courses, instructor_weighted=False):
    """
    Build a bipartite graph with factorized instructor sections and course sections.
    """
    G = nx.Graph()

    instructor_nodes = []
    course_nodes = [f"{course.name}_{i+1}" for course in courses for i in range(course.sections_available)]

    total_sections_available = sum(course.sections_available for course in courses)

    # Factorize instructors based on the number of sections they can teach
    # match on instructor-section and course-section
    for idx, instructor in enumerate(instructors):
        instructor_priority = 1 - (idx / len(instructors))  # Normalized instructor priority

        for i in range(instructor.max_classes):
            instructor_node = f"{instructor.name}_section_{i+1}"
            instructor_nodes.append(instructor_node)
            G.add_node(instructor_node, bipartite=0)

            # Add edges between each instructor section and course sections
            for course_name in course_nodes:
                course_base = course_name.split('_')[0]
                if instructor.preferences:
                    if course_base in instructor.preferences:
                        preference_rank = 1 - (instructor.preferences.index(course_base) / len(instructor.preferences))  # Normalized preference rank
                    else:
                        # Set a default rank based on the total sections available
                        preference_rank = 1 / total_sections_available

                    # Combine the preference rank with the instructor's priority
                    weight = preference_rank + (instructor_priority if instructor_weighted else 0)
                    G.add_edge(instructor_node, course_name, weight=weight)

    G.add_nodes_from(course_nodes, bipartite=1)

    return G, instructor_nodes

def bipartite_matching_solver(instructors, courses, instructor_weighted=False, verbose=False):
    """
    Solve the matching problem using bipartite matching with factorized instructors and tie-breaking by priority.
    """
    # Step 1: Build the graph
    G, instructor_nodes = build_network_with_factorized_instructors(instructors, courses, instructor_weighted)

    # Step 2: Perform the initial matching
    matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)

    if verbose:
        print(f"Matching: {matching}")

    # Step 3: Apply the matching to the instructors and courses
    for node1, node2 in matching:
        if node1 in instructor_nodes:
            instructor_section, course_section = node1, node2
        else:
            instructor_section, course_section = node2, node1

        instructor_name = instructor_section.split('_section_')[0]
        course_name = course_section.split('_')[0]

        instructor = next(inst for inst in instructors if inst.name == instructor_name)
        course = next(crs for crs in courses if crs.name == course_name)

        if instructor.can_teach(course.name):
            available_slots = min(1, course.sections_available)
            instructor.assign_course(course.name, available_slots)
            course.assigned_instructors.append(instructor.name)
            course.sections_available -= available_slots

    # Step 4: Post-processing to assign remaining unassigned courses
    unassigned_courses = [course for course in courses if course.sections_available > 0]
    unassigned_instructors = [instructor for instructor in instructors if len(instructor.assigned_courses) < instructor.max_classes]

    for course in unassigned_courses:
        for instructor in unassigned_instructors:
            if instructor.can_teach(course.name) and course.sections_available > 0:
                available_slots = min(1, course.sections_available)
                instructor.assign_course(course.name, available_slots)
                course.assigned_instructors.append(instructor.name)
                course.sections_available -= available_slots

            if course.sections_available == 0:
                break

    return instructors, courses, G


# %%
if __name__ == "__main__":
    # test cases -- overlapping preferences and classes

    #import matplotlib.pyplot as plt
    import pandas as pd
    from pyprojroot.here import here

    from gui.load_data import load_courses, load_instructors
    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     course_slots, instructor_max)
    from jobmatch.preprocessing import (build_courses, build_instructors,
                                        create_preference_tuples,
                                        parse_preferences,
                                        print_matching_results)
    wd = here()


    instructor_list = load_instructors(str(wd / "data/validate/instructors_with_preferences.csv"))
    course_list = load_courses(str(wd / "data/validate/course_data_with_course_directors.csv"))


    set_all_seeds(94305)
    # Solve using bipartite matching
    final_instructors, final_courses, G = bipartite_matching_solver(instructor_list, course_list,
                                                                              instructor_weighted=True)

    print("\nInstructor assignments")
    # Print instructor assignments and ranks
    for instructor in final_instructors:
        instructor.print_assignments(skip_none=False)

    print("\nCourse assignments")
    # Print course assignments
    for course in final_courses:
        course.print_assignments()
    # # %%

    # def visualize_network(G):
    #     pos = nx.spring_layout(G, seed=42)  # Layout for positioning nodes

    #     # Extract the weights from the graph edges
    #     edge_labels = nx.get_edge_attributes(G, 'weight')

    #     # Draw the graph
    #     plt.figure(figsize=(12, 8))

    #     # Draw the nodes
    #     nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')

    #     # Draw the edges with their weights
    #     nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

    #     # Draw the labels for nodes
    #     nx.draw_networkx_labels(G, pos, font_size=12, font_family="sans-serif")

    #     # Draw the edge labels (weights)
    #     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    #     plt.title("Bipartite Network Visualization with Weights")
    #     plt.show()

    # # Visualize the network with Plotly
    # visualize_network(G)
