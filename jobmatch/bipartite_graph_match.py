from pathlib import Path
from typing import Dict, List, Tuple

# build and plot graph
import networkx as nx

# %%

def build_network(individuals: Dict[str, List[str]], courses: Dict[str, int], instructor_weighted: bool = False) -> nx.Graph:
    """Build a bipartite graph with adjusted weights for instructor rank and course preferences.

    Args:
        individuals (Dict[str, List[str]]): A dictionary of instructors and their course preferences.
        courses (Dict[str, int]): A dictionary of courses and their respective capacities.
        weighted (bool): Whether to incorporate instructor rank into the edge weights. Defaults to False.

    Returns:
        nx.Graph: A bipartite graph with instructors and course options as nodes, and preferences as edges.
    """
    # Create a bipartite graph
    G = nx.Graph()

    # Add nodes with the bipartite attribute
    instructors = list(individuals.keys())
    courses_list = []

    # Expand courses_list to account for multiple availabilities
    for course, availability in courses.items():
        courses_list.extend([f"{course}_{i+1}" for i in range(availability)])

    # Add instructor nodes
    G.add_nodes_from(instructors, bipartite=0)

    # Add course nodes (with expanded availability)
    G.add_nodes_from(courses_list, bipartite=1)

    # Define the penalty rank for courses not listed in preferences
    unlisted_rank = 1/(len(courses_list) + 1)

    # Determine instructor rank: assume earlier in list is more important
    instructor_ranks = {instructor: i + 1 for i, instructor in enumerate(instructors)}

    # Add edges with weights corresponding to preference rankings
    for instructor, preferences in individuals.items():
        # pull instructor ranking
        instructor_rank = instructor_ranks[instructor]
        for course in courses_list:
            course_base = course.split('_')[0]  # Extract the base course name
            if course_base in preferences:
                preference_rank = 1/(preferences.index(course_base) + 1)
            else:
                preference_rank = unlisted_rank  # Assign constant but low rank for unlisted courses

            if instructor_weighted:
                # Combine preference rank and instructor rank into a single weight
                rank = preference_rank + 0.1*(1 / instructor_rank)  # Preference dominates, but instructor rank breaks ties
            else:
                # Basic preference rank without instructor weight
                rank = preference_rank
            # Lower rank means higher preference, so weight is inverse of rank
            G.add_edge(instructor, course, weight=rank)

    return G


# def bipartite_matching_solver(individuals: Dict[str, List[str]],
#                               courses: Dict[str, int],
#                               instructor_weighted: bool = False) -> Tuple[Dict[str, str], Dict[str, int], nx.Graph]:
#     """Perform maximum weight matching on the bipartite graph and return matches with their ranks.

#     Args:
#         individuals (Dict[str, List[str]]): A dictionary of instructors and their course preferences.
#         courses (Dict[str, int]): A dictionary of courses and their respective capacities.
#         weighted (bool): Whether to incorporate instructor rank into the edge weights. Defaults to False.

#     Returns:
#         Tuple[Dict[str, Optional[str]], Dict[str, List[str]], nx.Graph]:
#             A tuple containing three items:
#             - The first dictionary maps each instructor to their assigned course (or None if not assigned).
#             - The second dictionary maps each course to a list of assigned instructors.
#             - The third is the resulting graph object
#     """
#     # Build the network
#     G = build_network(individuals, courses, instructor_weighted)

#     # Perform maximum weight matching
#     matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)

#     instructor_assignments = {}
#     course_assignments = {course: [] for course in courses}

#     for instructor, course in matching:
#         if instructor in individuals:
#             assigned_course = course
#         else:
#             instructor, assigned_course = course, instructor

#         instructor_assignments[instructor] = assigned_course.split('_')[0]
#         course_assignments[assigned_course.split('_')[0]].append(instructor)

#     return instructor_assignments, course_assignments, G
def iterative_bipartite_matching_solver(individuals: Dict[str, List[str]],
                                        courses: Dict[str, int],
                                        instructor_max_full: Dict[str, int],
                                        instructor_weighted: bool = False) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[nx.Graph]]:
    """
    Perform greedy bipartite matching to assign instructors to multiple courses,
    ensuring no instructor teaches more than two different courses.

    Args:
        individuals (Dict[str, List[str]]): A dictionary of instructors and their course preferences.
        courses (Dict[str, int]): A dictionary of courses and their respective capacities.
        instructor_max_full (Dict[str, int]): A dictionary mapping full instructor names to their maximum allowed classes.
        instructor_weighted (bool): Whether to incorporate instructor rank into the edge weights. Defaults to False.

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, List[str]], List[nx.Graph]]:
            A tuple containing three items:
            - The first dictionary maps each instructor to their list of assigned courses.
            - The second dictionary maps each course to a list of assigned instructors.
            - The third is a list of graphs generated during the matching iterations.
    """
    # Step 1: Initialize assignment tracking
    instructor_assignments = {instructor: [] for instructor in individuals.keys()}
    course_assignments = {course: [] for course in courses}
    instructor_course_counts = {instructor: 0 for instructor in individuals.keys()}
    instructor_unique_courses = {instructor: set() for instructor in individuals.keys()}
    graphs = []
    iter_count = 0

    # Step 2: Iterate until no more assignments can be made
    while True:
        iter_count += 1
        # Build the network
        G = build_network(individuals, courses, instructor_weighted)
        graphs.append(G)  # Store the current graph

        # Perform maximum weight matching
        matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)

        # Track if we made any assignments in this iteration
        assignments_made = False

        # Process the matching to assign courses
        for instructor, course in matching:
            if instructor in individuals:
                assigned_course = course
            else:
                instructor, assigned_course = course, instructor

            course_base = assigned_course.split('_')[0]

            # Calculate how many sections can be assigned to the instructor
            available_slots = min(instructor_max_full[instructor] - instructor_course_counts[instructor], courses[course_base])

            # Check if the instructor can still be assigned more courses and if they already teach fewer than 2 different courses
            if available_slots > 0 and len(instructor_unique_courses[instructor]) < 2:
                # Assign as many sections of the course as possible to the instructor
                instructor_assignments[instructor].extend([course_base] * available_slots)
                course_assignments[course_base].extend([instructor] * available_slots)
                instructor_course_counts[instructor] += available_slots
                instructor_unique_courses[instructor].add(course_base)
                courses[course_base] -= available_slots  # Reduce the number of available slots for this course
                assignments_made = True

        # Break the loop if no assignments were made in this iteration
        if not assignments_made:
            print(f"Convergence after {iter_count} iterations")
            break

        # Remove fully assigned instructors and empty courses
        individuals = {inst: prefs for inst, prefs in individuals.items() if instructor_course_counts[inst] < instructor_max_full[inst]}
        courses = {course: capacity for course, capacity in courses.items() if capacity > 0}

        # If there are no more instructors or courses to assign, end the loop
        if not individuals or not courses:
            print(f"Convergence after {iter_count} iterations")
            break

    return instructor_assignments, course_assignments, graphs


# %%
if __name__ == "__main__":
    # test cases -- overlapping preferences and classes

    import matplotlib.pyplot as plt
    import pandas as pd
    from pyprojroot.here import here

    from jobmatch.class_data import (course_id_map, course_map, course_slots,
                                     instructor_max)
    from jobmatch.preprocessing import (create_preference_tuples,
                                        parse_preferences,
                                        print_matching_results)
    wd = here()

    # load preferences df and order by instructor importance
    pref_df = pd.read_excel(wd / "data/raw/Teaching_Preferences_cao18Aug.xlsx")
    pref_df = pref_df.set_index('Name')
    pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

    # convert class identifiers from form format to standard format
    core_dict = {
        'PolSci 211': 'PS211',
        'SocSci 311': 'SocSci311',
    }

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

    # Example usage
    print("Test on real preferences:\n")
    instructor_assignments, course_assignments, G = iterative_bipartite_matching_solver(
        individuals, course_slots, instructor_max, instructor_weighted=True)

    match_ranks = print_matching_results(instructor_assignments, individuals)

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
