import copy
from typing import Callable, Dict, List, Optional, Tuple

import networkx as nx

from jobmatch.bipartite_graph_match import iterative_bipartite_matching_solver
from jobmatch.linear_program_optimization import \
    iterative_linear_programming_solver
from jobmatch.preprocessing import create_preference_tuples, parse_preferences
from jobmatch.stable_marriage import stable_marriage_solver

# %%


class JobMatch:
    def __init__(self, individuals: Dict[str, List[str]], course_slots: Dict[str, int], instructor_max: Dict[str, int]):
        """Initialize the JobMatch class with individuals, course slots, and instructor maximum sections.

        Args:
            individuals (Dict[str, List[str]]): A dictionary where keys are instructor names
                and values are lists of course preferences.
            course_slots (Dict[str, int]): A dictionary where keys are course names and values are
                the number of available slots for each course.
            instructor_max (Dict[str, int]): A dictionary where keys are instructor names and values are
                the maximum number of sections each instructor is available to teach.

        Each algorithm optimizes for instructor preference, subject to three constraints:
            1) No instructor can teach more than two unique classes.
            2) No instructor can teach more than three sections total.
            3) Total sections taught within one class cannot exceed the total sections available for that class.

        **Matching Algorithms:**

        - **Iterative Bipartite Matching & Iterative Linear Programming:**
            These algorithms optimize for instructor preferences while iteratively matching instructors with courses.
            Greedy matching is employed, where if an instructor is matched with a section,
                the algorithm will attempt to assign additional sections of the same course until the instructor's maximum sections
                or course capacity is reached.
            The algorithms iterate through all instructors and courses until no more matches can be made, leading to convergence.

        - **Modified Stable Marriage Algorithm:**
            This version of the stable marriage algorithm sequentially matches instructors to courses based on their preferences.
            The algorithm ensures that:
                1) No instructor is assigned more than two unique courses.
                2) Instructors are greedily assigned to additional sections of a course they are already teaching,
                    as long as their maximum sections or course capacity is not exceeded.
                3) The process iterates until no more matches can be made, either because all instructors have been fully assigned
                    or all course capacities are exhausted.
            Unlike traditional stable marriage, this version supports sequential and greedy matching,
                allowing for multiple sections of the same course to be assigned to an instructor.
                Instructors propose to their preferred courses sequentially,
                    and courses can "reject" instructors if they have reached capacity or if another instructor
                    with a higher preference has already been assigned.
                The process continues iteratively until all instructors are assigned within the constraints.

        The order of instructors in the `individuals` dictionary impacts their priority in course selection,
            with those listed earlier being given higher priority.
        """
        self.individuals = individuals
        self.course_slots = course_slots
        self.instructor_max = instructor_max

    def rank_order_preferences(self):
        """Standard method to parse preferences, expand courses, etc."""
        # Example parsing steps (add more as needed)
        self.preferences_with_ranks = create_preference_tuples(self.individuals, list(self.course_slots.keys()))

    def select_solver(self, method: str) -> Callable:
        """Select the appropriate solver method based on the specified strategy.

        Args:
            method (str): The solving strategy to use ('stable_marriage', 'bipartite_matching',
                or 'linear_programming').
        Returns:
            Callable: The selected solver method.
        """
        if method == 'stable_marriage':
            return self.stable_marriage_solver
        elif method == 'bipartite_matching':
            return self.iterative_bipartite_matching_solver
        elif method == 'linear_programming':
            return self.iterative_linear_programming_solver
        else:
            raise ValueError(f"Unknown method: {method}")

    def stable_marriage_solver(self) -> Tuple[Dict[str, Optional[str]], Dict[str, int]]:
        """Solve the matching problem using the stable marriage algorithm.

        Returns:
            Tuple[Dict[str, Optional[str]], Dict[str, List[str]]]:
                A tuple containing two dictionaries:
                - The first dictionary maps each instructor to their assigned course (or None if not assigned).
                - The second dictionary maps each course to a list of assigned instructors.
        """
        # copy class attributes to avoid leakage if values are modified
        prefs = copy.deepcopy(self.preferences_with_ranks)
        slots = copy.deepcopy(self.course_slots)
        inst_max = copy.deepcopy(self.instructor_max)
        # Call the stable marriage solution logic
        return stable_marriage_solver(prefs, slots, inst_max)

    def iterative_bipartite_matching_solver(self, instructor_weighted: bool = False) -> Tuple[Dict[str, str], Dict[str, int], nx.Graph]:
        """Solve the matching problem using the bipartite matching algorithm.

        Args:
            instructor_weighted (bool, optional): Whether to weight the bipartite graph by instructor
                seniority. Defaults to False.

        Returns:
            Tuple[Dict[str, Optional[str]], Dict[str, List[str]]]:
                A tuple containing two dictionaries:
                - The first dictionary maps each instructor to their assigned course (or None if not assigned).
                - The second dictionary maps each course to a list of assigned instructors.
                - The bipartite graph used in the matching.
        """
        # copy class attributes to avoid leakage if values are modified
        inds = copy.deepcopy(self.individuals)
        slots = copy.deepcopy(self.course_slots)
        inst_max = copy.deepcopy(self.instructor_max)
        # Call the bipartite matching solution logic
        return iterative_bipartite_matching_solver(inds, slots, inst_max, instructor_weighted=instructor_weighted)

    def iterative_linear_programming_solver(self, lp_method: str = 'default') -> Tuple[Dict[str, str], Dict[str, int]]:
        """Solve the matching problem using linear programming.

        Args:
            lp_method (str, optional): The method for solving the linear programming problem
                ('default', 'perturb', 'multi_objective'). Defaults to 'default'.

        Returns:
            Tuple[Dict[str, Optional[str]], Dict[str, List[str]]]:
                A tuple containing two dictionaries:
                - The first dictionary maps each instructor to their assigned course (or None if not assigned).
                - The second dictionary maps each course to a list of assigned instructors.
        """
        # copy class attributes to avoid leakage if values are modified
        prefs = copy.deepcopy(self.preferences_with_ranks)
        slots = copy.deepcopy(self.course_slots)
        inst_max = copy.deepcopy(self.instructor_max)
        # Call the linear programming solution logic
        return iterative_linear_programming_solver(prefs, slots, inst_max, method=lp_method)

    def solve(self, method: str, **kwargs) -> Tuple:
        """Main entry point for solving the matching problem with the selected method.

        Args:
            method (str): The solving strategy to use ('stable_marriage', 'bipartite_matching',
                or 'linear_programming').
            **kwargs: Additional keyword arguments passed to the selected solver.

        Returns:
            Tuple: The result from the selected solver, typically including matches and class assignments.
        """
        # Step 1: Parse preferences and prepare data
        self.rank_order_preferences()

        # Step 2: Select the solver
        solver = self.select_solver(method)

        # Step 3: Solve the problem using the selected solver
        result = solver(**kwargs)

        # Calculate and store match ranks
        self.match_ranks = self.get_match_ranks(result[0])

        return result

    def get_match_ranks(self, matches: Dict[str, List[str]]) -> Dict[str, Tuple[List[str], List[int]]]:
        """Calculate and return the matched courses and their ranks for each instructor.

        Args:
            matches (Dict[str, List[str]]): A dictionary mapping instructors to their assigned courses.

        Returns:
            Dict[str, Tuple[List[str], List[int]]]: A dictionary mapping instructors to a tuple,
                where the first element is a list of courses and the second is a list of corresponding ranks.
        """
        match_ranks = {}

        for instructor, courses in sorted(matches.items()):
            ranked_courses = []
            ranks = []

            for course in courses:
                # Get the rank of the matched course according to the instructor's preferences
                if self.preferences_with_ranks and instructor in self.preferences_with_ranks:
                    pref_dict = {pref.course: pref.rank for pref in self.preferences_with_ranks[instructor]}
                    rank = pref_dict.get(course, len(self.course_slots))
                else:
                    rank = len(self.course_slots)  # Default to a low rank if not found

                ranked_courses.append(course)
                ranks.append(rank)

            match_ranks[instructor] = (ranked_courses, ranks)

        return match_ranks

    # def get_match_ranks(self, matches: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, int]]]:
    #     """Calculate and return the matched courses and their ranks for each instructor.

    #     Args:
    #         matches (Dict[str, List[str]]): A dictionary mapping instructors to their assigned courses.

    #     Returns:
    #         Dict[str, List[Tuple[str, int]]]: A dictionary mapping instructors to a list of tuples,
    #             each containing a course and its rank.
    #     """
    #     match_ranks = {}
    #     for instructor, courses in sorted(matches.items()):
    #         ranked_courses = []
    #         for course in courses:
    #             # Get the rank of the matched course according to the instructor's preferences
    #             if self.preferences_with_ranks and instructor in self.preferences_with_ranks:
    #                 pref_dict = {pref.course: pref.rank for pref in self.preferences_with_ranks[instructor]}
    #                 rank = pref_dict.get(course, len(self.course_slots))
    #             else:
    #                 rank = len(self.course_slots)  # Default to a low rank if not found
    #             ranked_courses.append((course, rank))
    #         match_ranks[instructor] = ranked_courses
    #     return match_ranks

    def print_match_results(self, match_ranks: Dict[str, Tuple[List[str], List[int]]]):
        """Print the matching results in the desired format."""
        for instructor, (courses, ranks) in sorted(match_ranks.items()):
            print(f"{instructor}: {courses} (Ranks: {ranks})")


# %%
if __name__ == "__main__":

    from pprint import pprint

    import pandas as pd
    from pyprojroot.here import here

    from jobmatch.class_data import (course_id_map, course_map, course_slots,
                                     instructor_max)
    from jobmatch.global_functions import set_all_seeds
    wd = here()

    set_all_seeds(80920)

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
        core_class = core_dict.get(item[6], 'SocSci211')
        prefs = item[7]
        if not pd.isna(prefs):
            individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
        else:
            continue

    # Create a solver factory
    factory = JobMatch(individuals, course_slots, instructor_max)

    # Solve using the bipartite matching approach
    print("Test on real preferences: Bipartite graph\n")
    matches_bipartite = factory.solve(method='bipartite_matching', instructor_weighted=True)
    rankings = factory.get_match_ranks(matches_bipartite[0])  # bipartite returns a tuple of (instructor:class, instructor:rank, nx.Graph)
    factory.print_match_results(rankings)
    print("")

    # Solve using the stable marriage approach
    print("Test on real preferences: stable marriage\n")
    matches_stable = factory.solve(method='stable_marriage')
    rankings = factory.get_match_ranks(matches_stable[0])  # stable marriage returns a tuple of (instructor:class, class:instructor)
    factory.print_match_results(rankings)
    print("")

    # Solve using linear programming
    print("Test on real preferences: linear programming\n")
    matches_lp = factory.solve(method='linear_programming', lp_method='default')
    rankings = factory.get_match_ranks(matches_lp[0])
    factory.print_match_results(rankings)
    print("")
