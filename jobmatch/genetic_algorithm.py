import random
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from tqdm import tqdm

from jobmatch.dataclasses import Course, Instructor
from jobmatch.global_functions import set_all_seeds

# %%


def initialize_population(num_individuals: int, instructors: List[Instructor], courses: List[Course]) -> List[List[Tuple[str, str]]]:
    """
    Randomly initialize the population for the genetic algorithm.

    Args:
        num_individuals (int): Number of individuals in the population.
        instructors (List[Instructor]): List of Instructor objects.
        courses (List[Course]): List of Course objects.

    Returns:
        List[List[Tuple[str, str]]]: A list of chromosomes where each chromosome is a list of (instructor_section, course_section) tuples.
        The maximum length of the chromosome list is sum(instructor.max_classes) for all instructors.
    """
    population = []
    instructor_sections = [
        f"{instructor.name}_section_{i+1}" for instructor in instructors for i in range(instructor.max_classes)
    ]
    instructor_lookup = {inst.name: inst for inst in instructors}

    for _ in range(num_individuals):
        chromosome = []
        for course in courses:
            # If there's a course director, assign them to their sections first
            if course.course_director:
                director = instructor_lookup.get(course.course_director, None)
                if director:
                    for section in range(min(course.sections_available, director.max_classes)):
                        chromosome.append((f"{director.name}_section_{section+1}", f"{course.name}_section_{section+1}"))

            # Randomly assign other instructors to remaining sections
            for section in range(course.sections_available - len([pair for pair in chromosome if pair[1].startswith(f"{course.name}_section")])):
                instructor_section = random.choice(instructor_sections)
                chromosome.append((instructor_section, f"{course.name}_section_{section+1}"))

        population.append(chromosome)

    return population


# def fitness_function(chromosome: List[Tuple[str, str]], instructors: List[Instructor],
#                      courses: List[Course], max_sections: Dict[str, int],
#                      max_unique_classes: int, non_preferred_penalty: int = 0,
#                      course_director_penalty: int = 30) -> int:
#     """
#     Calculate the fitness of a chromosome based on the instructor preferences, constraints, and course director roles.

#     Args:
#         chromosome (List[Tuple[str, str]]): The chromosome representing a potential solution.
#         instructors (List[Instructor]): List of Instructor objects.
#         courses (List[Course]): List of Course objects.
#         max_sections (Dict[str, int]): Maximum number of sections per instructor.
#         max_unique_classes (int): Maximum number of unique classes an instructor can teach.
#         non_preferred_penalty (int, optional): Penalty applied for each course assigned to an instructor
#                                                that is not in their preference list. Defaults to 0.
#         course_director_penalty (int, optional): Penalty for not assigning a course director the max sections for
#                                                  their designated course. Defaults to 30.

#     Returns:
#         int: The fitness score of the chromosome.
#     """
#     fitness = 0
#     instructor_sections = {instructor.name: [] for instructor in instructors}
#     core_courses = ['PS211', 'PS211FR', 'SocSci311', 'SocSci212']

#     # Step 1: Populate instructor_sections with the courses from the chromosome
#     for instructor_section, course_section in chromosome:
#         instructor_name = instructor_section.split('_section_')[0]
#         course_name = course_section.split('_section_')[0]
#         instructor_sections[instructor_name].append(course_name)

#     # Step 2: Evaluate fitness for each instructor
#     for instructor_name, assigned_courses in instructor_sections.items():
#         unique_courses = set(assigned_courses)

#         # Penalty for exceeding max unique courses or max sections
#         if len(unique_courses) > max_unique_classes:
#             fitness -= 25 * (len(unique_courses) - max_unique_classes)
#         if len(assigned_courses) > max_sections[instructor_name]:
#             fitness -= 25 * (len(assigned_courses) - max_sections[instructor_name])

#         # Get the instructor object
#         instructor = next(inst for inst in instructors if inst.name == instructor_name)

#         # Step 3: Loop through assigned courses and calculate fitness based on preferences, course director status, and degree
#         for course in assigned_courses:
#             course_obj = next(crs for crs in courses if crs.name == course)

#             # Reward based on preferences
#             if course in instructor.preferences:
#                 rank = instructor.preferences.index(course)  # Rank starts at 0
#                 fitness += (10 - rank)  # Higher rank -> higher reward
#             else:
#                 fitness -= non_preferred_penalty  # Penalty for non-preferred courses

#             # Nudge master's degree holders toward core courses
#             if instructor.degree == 'mas':
#                 if course in core_courses:
#                     # Reward for assigning master's degree holders to core courses
#                     fitness += non_preferred_penalty  # Reward for core courses
#                 else:
#                     # Penalize if master's degree holders are assigned non-core courses
#                     fitness -= non_preferred_penalty  # Penalty for non-core courses

#             # Step 4: Apply course director penalty if the instructor is a course director
#             for course in assigned_courses:
#                 course_obj = next(crs for crs in courses if crs.name == course)

#                 if course_obj.course_director == instructor.name:
#                     course_count = assigned_courses.count(course_obj.name)
#                     if course_count < min(max_sections[instructor_name], course_obj.sections_available):
#                         missing_sections = max_sections[instructor_name] - course_count
#                         fitness -= course_director_penalty * missing_sections
#     return fitness


def fitness_function(chromosome: List[Tuple[str, str]], instructors: List[Instructor],
                     courses: List[Course], max_sections: Dict[str, int],
                     max_unique_classes: int, non_preferred_penalty: int = 0,
                     course_director_penalty: int = 30) -> int:
    """
    Calculate the fitness of a chromosome based on the instructor preferences, constraints, and course director roles.

    Args:
        chromosome (List[Tuple[str, str]]): The chromosome representing a potential solution.
        instructors (List[Instructor]): List of Instructor objects.
        courses (List[Course]): List of Course objects.
        max_sections (Dict[str, int]): Maximum number of sections per instructor.
        max_unique_classes (int): Maximum number of unique classes an instructor can teach.
        non_preferred_penalty (int, optional): Penalty applied for each course assigned to an instructor
                                               that is not in their preference list. Defaults to 0.
        course_director_penalty (int, optional): Penalty for not assigning a course director the max sections for
                                                 their designated course. Defaults to 30.

    Returns:
        int: The fitness score of the chromosome.
    """
    fitness = 0
    instructor_sections = {instructor.name: [] for instructor in instructors}
    core_courses = ['PS211', 'PS211FR', 'SocSci311', 'SocSci212']

    # Create lookup dictionaries for faster access to instructors and courses
    course_lookup = {crs.name: crs for crs in courses}
    instructor_lookup = {inst.name: inst for inst in instructors}

    # Step 1: Populate instructor_sections with the courses from the chromosome
    for instructor_section, course_section in chromosome:
        instructor_name = instructor_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]
        instructor_sections[instructor_name].append(course_name)

    # Step 2: Evaluate fitness for each instructor
    for instructor_name, assigned_courses in instructor_sections.items():
        unique_courses = set(assigned_courses)

        # Penalty for exceeding max unique courses or max sections
        if len(unique_courses) > max_unique_classes:
            fitness -= 25 * (len(unique_courses) - max_unique_classes)
        if len(assigned_courses) > max_sections[instructor_name]:
            fitness -= 25 * (len(assigned_courses) - max_sections[instructor_name])

        # Get the instructor object using the lookup
        instructor = instructor_lookup[instructor_name]

        # Step 3: Loop through assigned courses and calculate fitness based on preferences, course director status, and degree
        for course in assigned_courses:
            # Get the course object using the lookup
            course_obj = course_lookup[course]

            # Reward based on preferences
            if course in instructor.preferences:
                rank = instructor.preferences.index(course)  # Rank starts at 0
                fitness += (10 - rank)  # Higher rank -> higher reward
            else:
                fitness -= non_preferred_penalty  # Penalty for non-preferred courses

            # Nudge master's degree holders toward core courses
            if instructor.degree == 'mas':
                if course in core_courses:
                    # Reward for assigning master's degree holders to core courses
                    fitness += non_preferred_penalty  # Reward for core courses
                else:
                    # Penalize if master's degree holders are assigned non-core courses
                    fitness -= non_preferred_penalty  # Penalty for non-core courses

            # Step 4: Apply course director penalty if the instructor is a course director
            if course_obj.course_director == instructor.name:
                course_count = assigned_courses.count(course_obj.name)
                if course_count < min(max_sections[instructor_name], course_obj.sections_available):
                    missing_sections = max_sections[instructor_name] - course_count
                    fitness -= course_director_penalty * missing_sections

    return fitness

def crossover(parent1: List[Tuple[str, str]], parent2: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    Perform crossover between two parent chromosomes to produce offspring.

    Args:
        parent1 (List[Tuple[str, str]]): First parent chromosome.
        parent2 (List[Tuple[str, str]]): Second parent chromosome.

    Returns:
        Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]: Two offspring chromosomes.
    """
    point = random.randint(0, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2


def mutate(chromosome: List[Tuple[str, str]], instructors: List[Instructor]) -> List[Tuple[str, str]]:
    """
    Perform mutation on a chromosome by changing one gene.

    Args:
        chromosome (List[Tuple[str, str]]): The chromosome to mutate.
        instructors (List[Instructor]): List of Instructor objects.

    Returns:
        List[Tuple[str, str]]: The mutated chromosome.
    """
    gene_index = random.randint(0, len(chromosome) - 1)
    instructor = random.choice(instructors)
    new_section = f"{instructor.name}_section_{random.randint(1, instructor.max_classes)}"
    chromosome[gene_index] = (new_section, chromosome[gene_index][1])
    return chromosome


def genetic_algorithm(instructors: List[Instructor], courses: List[Course], max_sections: Dict[str, int],
                      max_unique_classes: int, num_generations: int = 500, population_size: int = 500,
                      non_preferred_penalty: int = 3, seed: int = 42, progress_callback: Optional[Callable[[int], None]] = None,
                      early_stopping_window: int = 250, min_fitness_change: float = 1e-4) -> Tuple[List['Instructor'], List['Course'], List[int]]:
    """
    Run the genetic algorithm to optimize the assignment of instructors to courses with early stopping.

    Args:
        instructors (List[Instructor]): List of Instructor objects.
        courses (List[Course]): List of Course objects.
        max_sections (Dict[str, int]): Maximum number of sections per instructor.
        max_unique_classes (int): Maximum number of unique classes an instructor can teach.
        num_generations (int, optional): Number of generations for the algorithm. Defaults to 500.
        population_size (int, optional): Size of the population. Defaults to 500.
        non_preferred_penalty (int, optional): Penalty for non-preferred courses. Defaults to 3.
        seed (int, optional): Seed for reproducibility. Defaults to 42.
        progress_callback (Optional[Callable[[int], None]], optional): Callback for progress updates.
        early_stopping_window (int, optional): Number of generations to consider for early stopping.
        min_fitness_change (float, optional): Minimum fitness change between generations to continue running.

    Returns:
        Tuple[List[Instructor], List[Course], List[int]]: The best instructors, courses, and fitness scores over time.
    """
    # Set all seeds for reproducibility
    set_all_seeds(seed)

    population = initialize_population(population_size, instructors, courses)
    fitness_over_time = []

    for generation in tqdm(range(num_generations)):
        fitness_scores = [fitness_function(chromosome, instructors, courses,
                                            max_sections, max_unique_classes,
                                            non_preferred_penalty) for chromosome in population]

        fitness_scores = np.array(fitness_scores)
        max_fitness = np.max(fitness_scores)
        fitness_over_time.append(max_fitness)

        # Emit progress update
        if progress_callback:
            progress_callback(int((generation / num_generations) * 100))

        # Early Stopping based on mean change in fitness
        if generation >= early_stopping_window:
            # Get the last `early_stopping_window` fitness scores
            recent_fitness = fitness_over_time[-early_stopping_window:]
            mean_fitness_change = np.mean(np.diff(recent_fitness))

            if abs(mean_fitness_change) < min_fitness_change:
                print(f"Early stopping at generation {generation}: Mean fitness change < {min_fitness_change}")
                break

        sorted_population = [chromosome for _, chromosome in sorted(zip(fitness_scores, population), reverse=True)]
        top_individuals = sorted_population[:population_size // 2]

        new_population = []
        while len(new_population) < population_size:
            parent1 = random.choice(top_individuals)
            parent2 = random.choice(top_individuals)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, instructors)
            child2 = mutate(child2, instructors)
            new_population.extend([child1, child2])

        population = new_population

    final_fitness_scores = [fitness_function(chromosome, instructors, courses,
                                             max_sections, max_unique_classes) for chromosome in population]
    best_solution = population[np.argmax(final_fitness_scores)]

    # Create lookup dictionaries for faster access to instructors and courses
    course_lookup = {crs.name: crs for crs in courses}
    instructor_lookup = {inst.name: inst for inst in instructors}

    for instructor in instructors:
        instructor.assigned_courses = []
        instructor.unique_courses = set()

    for instructor_section, course_section in best_solution:
        # split sections and instructors to append to each's assignment
        instructor_name = instructor_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]

        # find course and instructor
        course = course_lookup[course_name]
        instructor = instructor_lookup[instructor_name]

        # assign course to instructor and vice versa
        if len(instructor.assigned_courses) < instructor.max_classes:
            instructor.assign_course(course_name, 1)
            course.assigned_instructors.append(instructor.name)

    return instructors, courses, fitness_over_time


# Example usage:
def print_ga_assignments(instructors: List, courses: List) -> None:
    """
    Print the assignments of instructors to courses.

    Args:
        instructors (List): List of Instructor objects.
    """
    print("\nInstructor assignments")
    for instructor in instructors:
        instructor.print_assignments()

    print("\nCourse assignments")
    for course in courses:
        course.print_assignments()

# %%


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import pandas as pd
    from pyprojroot.here import here

    from gui.load_data import load_courses, load_instructors
    from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                     instructor_max)
    from jobmatch.preprocessing import (build_courses, build_instructors,
                                        create_preference_tuples,
                                        parse_preferences)

    wd = here()

#    instructor_list_raw = load_instructors(str(wd / "data/validate/instructors_with_preferences.csv"))
#    course_list = load_courses(str(wd / "data/validate/course_data_with_course_directors.csv"))

    instructor_list_raw = load_instructors(str(wd / "releases/v1.1/example_instructors.xlsx"))
    course_list = load_courses(str(wd / "releases/v1.1/example_courses.xlsx"))

    instructor_list = [inst for inst in instructor_list_raw if inst.max_classes > 0]

    best_instructors, best_courses, fitness_over_time = genetic_algorithm(
        instructors=instructor_list,
        courses=course_list,
        max_sections={inst.name: inst.max_classes for inst in instructor_list},
        max_unique_classes=2,
        num_generations=500,
        population_size=500,
        non_preferred_penalty=5,
        seed=8675309
    )

    # Inspect the best solution
    print_ga_assignments(best_instructors, best_courses)

    # Plotting function
    def plot_fitness_over_time(fitness_over_time: List[int]) -> None:
        """
        Plot the max fitness score over generations.

        Args:
            fitness_over_time (List[int]): List of fitness scores over generations.
        """
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(fitness_over_time)), fitness_over_time, marker='o')
        plt.title('Max Fitness Score Over Generations')
        plt.xlabel('Generation')
        plt.ylabel('Max Fitness Score')
        plt.grid(True)
        plt.show()

    # Plot the fitness over time
    plot_fitness_over_time(fitness_over_time)
