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
        List[List[Tuple[str, str]]]: A list of chromosomes where each chromosome is a list of
        (instructor_section, course_section) tuples.
    """
    population = []
    instructor_lookup = {inst.name: inst for inst in instructors}

    for _ in range(num_individuals):
        chromosome = []
        # Create a fresh copy of available instructor sections for each chromosome
        available_instructor_sections = [
            f"{instructor.name}_section_{i+1}"
            for instructor in instructors
            for i in range(instructor.max_classes)
        ]

        # Process each course
        for course in courses:
            remaining_sections = course.sections_available

            # Handle course director assignments first
            if course.course_director:
                director = instructor_lookup.get(course.course_director)
                if director:
                    # Find all available sections for this director
                    director_sections = [
                        sect for sect in available_instructor_sections
                        if sect.startswith(f"{director.name}_section_")
                    ]

                    # Calculate how many sections to assign
                    sections_to_assign = min(len(director_sections), remaining_sections)

                    # Assign sections
                    for i in range(sections_to_assign):
                        if director_sections:  # Double check we have sections left
                            section = director_sections[i]
                            if section in available_instructor_sections:  # Verify section is still available
                                available_instructor_sections.remove(section)
                                chromosome.append((section, f"{course.name}_section_{i+1}"))
                                remaining_sections -= 1

            # Assign remaining sections randomly
            while remaining_sections > 0 and available_instructor_sections:
                instructor_section = random.choice(available_instructor_sections)
                available_instructor_sections.remove(instructor_section)
                section_num = course.sections_available - remaining_sections + 1
                chromosome.append((instructor_section, f"{course.name}_section_{section_num}"))
                remaining_sections -= 1

        population.append(chromosome)

    return population

def fitness_function(chromosome: List[Tuple[str, str]], instructors: List[Instructor],
                     courses: List[Course], max_sections: Dict[str, int],
                     max_unique_classes: int, non_preferred_penalty: int = 3,
                     course_director_penalty: int = 30, unfilled_penalty: int = 25) -> int:
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
    core_courses = ['PS211', 'PS211FR', 'SS311', 'SS212']

    # Create lookup dictionaries for faster access to instructors and courses
    course_lookup = {crs.name: crs for crs in courses}
    instructor_lookup = {inst.name: inst for inst in instructors}

    # Track filled sections for each course
    filled_sections = {crs.name: 0 for crs in courses}

    # Step 1: Populate instructor_sections with the courses from the chromosome
    for instructor_section, course_section in chromosome:
        instructor_name = instructor_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]
        instructor_sections[instructor_name].append(course_name)
        filled_sections[course_name] += 1  # Count filled sections

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
            original_fitness = fitness
            # Get the course object using the lookup
            course_obj = course_lookup[course]

            # Reward based on preferences
            if course in instructor.preferences:
                rank = instructor.preferences.index(course)  # Rank starts at 0
                # Higher rank -> higher reward
                fitness += (30 - rank*non_preferred_penalty)
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

    # Penalty for unfilled Courses
    for course_name, filled in filled_sections.items():
        total_sections = course_lookup[course_name].sections_available
        unfilled = total_sections - filled
        if unfilled > 0:
            fitness -= unfilled_penalty * unfilled  # Penalize unfilled sections

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
    max_mutations = max(1, len(chromosome) // 10) # Max mutation of 10% to scale with problem size
    num_mutations = random.randint(1, max_mutations)
    for _ in range(num_mutations):
        gene_index = random.randint(0, len(chromosome) - 1)
        instructor = random.choice(instructors)
        new_section = f"{instructor.name}_section_{random.randint(1, instructor.max_classes)}"
        chromosome[gene_index] = (new_section, chromosome[gene_index][1])
    return chromosome

def repair_chromosome(chromosome: List[Tuple[str, str]],
                              instructors: List[Instructor],
                              courses: List[Course],
                              max_sections: Dict[str, int],
                              max_unique_classes: int) -> List[Tuple[str, str]]:
    """
    Partially repair a chromosome by fixing only the assignments that are in violation.

    This function checks each assignment and if it violates a constraint,
    it attempts to replace it with a valid alternative. If no replacement is found,
    that assignment is removed.

    Args:
        chromosome: List of (instructor_section, course_section) assignments.
        instructors: List of Instructor objects.
        courses: List of Course objects.
        max_sections: Dictionary mapping instructor names to their maximum sections.
        max_unique_classes: Maximum unique courses an instructor can teach.

    Returns:
        A partially repaired chromosome.
    """
    # Build assignment counts.
    instructor_assignments = {inst.name: [] for inst in instructors}
    course_assignments = {course.name: [] for course in courses}

    for inst_section, course_section in chromosome:
        inst_name = inst_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]
        instructor_assignments[inst_name].append(course_name)
        course_assignments[course_name].append(inst_name)

    repaired = list(chromosome)  # Work on a copy

    for i, (inst_section, course_section) in enumerate(repaired):
        inst_name = inst_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]
        course_obj = next((c for c in courses if c.name == course_name), None)

        # Check instructor capacity.
        if len(instructor_assignments[inst_name]) > max_sections[inst_name]:
            # Try to find a replacement instructor with available capacity.
            replacement = None
            for inst in instructors:
                # Check capacity
                if len(instructor_assignments[inst.name]) < max_sections[inst.name]:
                    # Allow if this instructor already teaches the course
                    # or if they haven't reached their unique course limit.
                    if (course_name in instructor_assignments[inst.name] or
                        len(set(instructor_assignments[inst.name])) < max_unique_classes):
                        replacement = inst.name
                        break
            if replacement:
                # Create a new assignment for the replacement.
                new_inst_section = f"{replacement}_section_{len(instructor_assignments[replacement]) + 1}"
                new_assignment = (new_inst_section, course_section)
                # Update counts: remove from original, add to replacement.
                instructor_assignments[inst_name].remove(course_name)
                instructor_assignments[replacement].append(course_name)
                # Update the chromosome.
                repaired[i] = new_assignment
            else:
                # If no replacement is found, remove the assignment.
                repaired[i] = None
                instructor_assignments[inst_name].remove(course_name)
                course_assignments[course_name].remove(inst_name)

        # Check course section limits.
        if course_obj and len(course_assignments[course_name]) > course_obj.sections_available:
            # Remove the extra assignment.
            repaired[i] = None
            course_assignments[course_name].remove(inst_name)
            if course_name in instructor_assignments[inst_name]:
                instructor_assignments[inst_name].remove(course_name)

    # Filter out any removed assignments.
    repaired = [assignment for assignment in repaired if assignment is not None]

    return repaired

def is_valid_solution(chromosome: List[Tuple[str, str]], instructors: List[Instructor],
                     courses: List[Course], max_sections: Dict[str, int],
                     max_unique_classes: int) -> bool:
    """
    Check if a chromosome satisfies all constraints.
    """
    instructor_counts = {}
    instructor_courses = {}
    course_sections = {}

    for inst_section, course_section in chromosome:
        inst_name = inst_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]

        # Count instructor assignments
        instructor_counts[inst_name] = instructor_counts.get(inst_name, 0) + 1
        if instructor_counts[inst_name] > max_sections[inst_name]:
            return False

        # Track unique courses per instructor
        if inst_name not in instructor_courses:
            instructor_courses[inst_name] = set()
        instructor_courses[inst_name].add(course_name)
        if len(instructor_courses[inst_name]) > max_unique_classes:
            return False

        # Track course sections
        course_sections[course_name] = course_sections.get(course_name, 0) + 1
        course = next(c for c in courses if c.name == course_name)
        if course_sections[course_name] > course.sections_available:
            return False

        # Check course director constraint
        if course.course_director and course.course_director != inst_name:
            if course_sections[course_name] == 1:  # First section must be taught by director
                return False

    return True


def genetic_algorithm(instructors: List[Instructor], courses: List[Course], max_sections: Dict[str, int],
                      max_unique_classes: int, num_generations: int = 500, population_size: int = 1000,
                      non_preferred_penalty: int = 5, seed: int = 42,
                      progress_callback: Optional[Callable[[int], None]] = None,
                      early_stopping_window: int = 400, min_fitness_change: float = 1e-6,
                      unfilled_penalty: int = 50) -> Tuple[List['Instructor'], List['Course'], List[int]]:
    """
    Run the genetic algorithm with proper section tracking.
    """
    set_all_seeds(seed)

    # Store original sections count
    original_sections = {course.name: course.sections_available for course in courses}

    population = initialize_population(population_size, instructors, courses)
    fitness_over_time = []

    # Track the best solution found so far
    best_solution = None
    best_fitness = float('-inf')

    for generation in tqdm(range(num_generations)):
        fitness_scores = [
            fitness_function(chromosome, instructors, courses,
                           max_sections, max_unique_classes,
                           non_preferred_penalty=non_preferred_penalty,
                           unfilled_penalty=unfilled_penalty)
            for chromosome in population
        ]

        # Update best solution if we found a better one
        current_best_idx = np.argmax(fitness_scores)
        if fitness_scores[current_best_idx] > best_fitness:
            best_fitness = fitness_scores[current_best_idx]
            best_solution = population[current_best_idx]

        fitness_over_time.append(max(fitness_scores))

        if progress_callback:
            progress_callback(int((generation / num_generations) * 100))

        # Early stopping check
        if generation >= early_stopping_window:
            recent_fitness = fitness_over_time[-early_stopping_window:]
            if abs(np.mean(np.diff(recent_fitness))) < min_fitness_change:
                print(f"Early stopping at generation {generation}")
                break

        # Selection and creation of new population
        sorted_indices = np.argsort(fitness_scores)[::-1]
        top_individuals = [population[i] for i in sorted_indices[:population_size // 2]]

        new_population = []
        while len(new_population) < population_size:
            parent1 = random.choice(top_individuals)
            parent2 = random.choice(top_individuals)
            # child1, child2 = crossover(parent1, parent2)
            # child1 = mutate(child1, instructors)
            # child2 = mutate(child2, instructors)

            # crossover and mutate
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, instructors)
            child2 = mutate(child2, instructors)

            # # periodic repairs
            # if generation % 50 == 0:
            #     child1 = repair_chromosome(child1, instructors, courses, max_sections, max_unique_classes)
            #     child2 = repair_chromosome(child2, instructors, courses, max_sections, max_unique_classes)
            new_population.extend([child1, child2])

        population = new_population

    # Use the best solution found throughout all generations
    if best_solution is None:
        best_solution = population[np.argmax([
            fitness_function(chrom, instructors, courses, max_sections,
                           max_unique_classes, non_preferred_penalty, unfilled_penalty)
            for chrom in population
        ])]

    # Reset assignments
    for instructor in instructors:
        instructor.assigned_courses = []
        instructor.unique_courses = set()

    for course in courses:
        course.assigned_instructors = []
        course.sections_available = original_sections[course.name]  # Reset to original value

    # Apply the best solution
    assignments = {}
    for instructor_section, course_section in best_solution:
        instructor_name = instructor_section.split('_section_')[0]
        course_name = course_section.split('_section_')[0]

        if course_name not in assignments:
            assignments[course_name] = []
        assignments[course_name].append(instructor_name)

        instructor = next(i for i in instructors if i.name == instructor_name)
        course = next(c for c in courses if c.name == course_name)

        if len(instructor.assigned_courses) < instructor.max_classes and course.sections_available > 0:
            instructor.assign_course(course_name, 1)
            if instructor_name not in course.assigned_instructors:
                course.assigned_instructors.append(instructor_name)
            course.sections_available -= 1

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
