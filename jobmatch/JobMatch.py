import copy
import logging
from typing import Callable, Dict, List, Optional, Tuple

import networkx as nx

from gui.load_data import load_courses, load_instructors
from jobmatch.bipartite_graph_match import bipartite_matching_solver
from jobmatch.dataclasses import Course, Instructor
from jobmatch.linear_program_optimization import \
    iterative_linear_programming_solver
from jobmatch.preprocessing import create_preference_tuples, parse_preferences
from jobmatch.stable_marriage import stable_marriage_solver

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),
                        logging.StreamHandler()  # This will print to the console
                    ])

# %%


class JobMatch:
    def __init__(self, instructors: List[Instructor], courses: List[Course]):
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
        self.raw_instructors = instructors
        self.raw_courses = courses
        self.instructors, self.courses = self.match_course_directors(self.raw_instructors, self.raw_courses)

    def match_course_directors(self, instructors,courses):
        updated_courses = []
        updated_instructors = [inst for inst in instructors]  # Shallow copy of instructors

        for course in courses:
            if course.course_director:
                director = next((inst for inst in updated_instructors if inst.name == course.course_director), None)
                if director:
                    # Greedily assign as many sections as possible to the director
                    available_sections = min(director.max_classes - len(director.assigned_courses), course.sections_available)

                    if available_sections > 0:
                        # Assign the director to the course for the available sections
                        course.assigned_instructors.extend([director.name] * available_sections)
                        course.sections_available -= available_sections
                        director.assign_course(course.name, available_sections)
                        logging.info(f"{director.name} assigned as course director for {course.name}")

            updated_courses.append(course)

        return updated_instructors, updated_courses

    def rank_order_preferences(self):
        """Generate preference tuples for instructors."""
        self.preferences_with_ranks = {
            instructor.name: create_preference_tuples([instructor], self.courses)[instructor.name]
            for instructor in self.instructors
        }

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
            return self.bipartite_matching_solver
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
        instructors = copy.deepcopy(self.instructors)
        courses = copy.deepcopy(self.courses)
        # Call the stable marriage solution logic
        return stable_marriage_solver(instructors, courses)

    def bipartite_matching_solver(self, instructor_weighted: bool = True) -> Tuple[Dict[str, str], Dict[str, int], nx.Graph]:
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
        instructors = copy.deepcopy(self.instructors)
        courses = copy.deepcopy(self.courses)

        # Call the stable marriage solution logic
        return bipartite_matching_solver(instructors, courses, instructor_weighted=instructor_weighted)

    def iterative_linear_programming_solver(self) -> Tuple[Dict[str, str], Dict[str, int]]:
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
        instructors = copy.deepcopy(self.instructors)
        courses = copy.deepcopy(self.courses)

        # Call the linear programming solution logic
        return iterative_linear_programming_solver(instructors, courses)

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
        # self.match_ranks = self.print_match_results(result[0])

        return result

    def print_match_results(self, results):
        """Print the matching results using the Instructor's print method."""
        for instructor in results:
            instructor.print_assignments()


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


    instructor_list = load_instructors(str(wd / "data/validate/instructors_with_preferences.csv"))
    course_list = load_courses(str(wd / "data/validate/course_data_with_course_directors.csv"))

    # Create a solver factory
    factory = JobMatch(instructor_list, course_list)

    # Solve using the bipartite matching approach
    print("Test on real preferences: Bipartite graph\n")
    matches_bipartite = factory.solve(method='bipartite_matching', instructor_weighted=False)
    # bipartite returns a tuple of (instructor:class, instructor:rank, nx.Graph)
    factory.print_match_results(matches_bipartite[0])
    factory.print_match_results(matches_bipartite[1])
    print("")

    # Solve using the stable marriage approach
    print("Test on real preferences: stable marriage\n")
    matches_stable = factory.solve(method='stable_marriage')
    # stable marriage returns a tuple of (instructor:class, class:instructor)
    factory.print_match_results(matches_stable[0])
    factory.print_match_results(matches_stable[1])
    print("")

    # Solve using linear programming
    print("Test on real preferences: linear programming\n")
    matches_lp = factory.solve(method='linear_programming')
    factory.print_match_results(matches_lp[0])
    factory.print_match_results(matches_lp[1])
    print("")
