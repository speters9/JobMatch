import pytest

from jobmatch.genetic_algorithm import (crossover, fitness_function,
                                        genetic_algorithm,
                                        initialize_population, mutate)


# Mock classes for instructors and courses
class MockInstructor:
    def __init__(self, name, max_classes, degree, preferences=None):
        self.name = name
        self.max_classes = max_classes
        self.degree = degree
        self.preferences = preferences or []
        self.assigned_courses = []
        self.unique_courses = set()

    def assign_course(self, course_name, count):
        self.assigned_courses.append(course_name)
        self.unique_courses.add(course_name)

    def print_assignments(self):
        print(f"{self.name}: {self.assigned_courses}")


class MockCourse:
    def __init__(self, name, sections_available, course_director=None):
        self.name = name
        self.sections_available = sections_available
        self.course_director = course_director  # Course director is optional
        self.assigned_instructors = []

# Test cases


def test_initialize_population():
    instructors = [MockInstructor('Alice', 3, 'phd'), MockInstructor('Bob', 2, 'mas')]
    courses = [MockCourse('PS101', 2), MockCourse('PS102', 1)]
    population = initialize_population(10, instructors, courses)

    assert len(population) == 10  # Population size
    for chromosome in population:
        assert len(chromosome) == 3  # 2 sections of PS101 + 1 section of PS102


def test_initialize_population_with_course_directors():
    instructors = [
        MockInstructor('Alice', 3, 'phd'),
        MockInstructor('Bob', 2, 'mas'),
    ]
    courses = [
        MockCourse('PS101', 2, course_director='Alice'),  # Alice is the course director
        MockCourse('PS102', 1)
    ]

    population = initialize_population(10, instructors, courses)

    assert len(population) == 10  # Population size
    for chromosome in population:
        # Check that Alice is assigned as course director to PS101
        course_director_assignment = [(instructor, course)
                                      for instructor, course in chromosome if course.startswith('PS101_section') and instructor.startswith('Alice')]
        assert len(course_director_assignment) > 0, "Course director not assigned to their course"


def test_fitness_function_with_non_preferred_penalty():
    """Isolate preferences, holding core constant."""
    instructors = [
        MockInstructor('Alice', 3, 'mas', preferences=['PS211', 'PS302']),
        MockInstructor('Bob', 2, 'phd', preferences=['PS212'])
    ]
    # PS211 is a core course for master's degree holders like Alice
    courses = [
        MockCourse('PS211', 2),  # Preferred for Alice and core
        MockCourse('PS212', 1),  # Non-core
        MockCourse('PS302', 1)   # Non-core
    ]
    max_sections = {'Alice': 3, 'Bob': 2}
    max_unique_classes = 2
    non_preferred_penalty = 5
    chromosome = [
        ('Alice_section_1', 'PS211_section_1'),  # Core and preferred course
        ('Alice_section_2', 'PS212_section_1'),  # Core and non-preferred course for Alice
        ('Bob_section_1', 'PS302_section_1')     # Non-preferred course for Bob
    ]

    fitness = fitness_function(
        chromosome,
        instructors,
        courses,
        max_sections,
        max_unique_classes,
        non_preferred_penalty
    )

    # Expected fitness:
    # Alice: PS211 (core, preferred) + PS201 (core, non-preferred) (10-5)
    # Bob: PS102 (non-preferred) (-5)

    # Alice gets rewarded for PS101 (core and preferred) but penalized for PS201 (non-core and non-preferred).
    # Bob gets penalized for PS102 (non-preferred).
    # Alice: (10 - 0) [PS101] - non_preferred_penalty [PS201]
    # Bob: - non_preferred_penalty [PS102]
    # Fitness = (10 - 5 - 5) = 0
    assert fitness == 0


def test_fitness_function_with_core_course_penalty():
    """Test punishment for core violations."""
    instructors = [
        MockInstructor('Alice', 3, 'mas', preferences=['PS101', 'PS102']),
        MockInstructor('Bob', 2, 'phd', preferences=['PS101'])
    ]
    courses = [MockCourse('PS101', 2), MockCourse('PS102', 1), MockCourse('PS211', 1)]  # PS211 is a core course
    max_sections = {'Alice': 3, 'Bob': 2}
    max_unique_classes = 2
    non_preferred_penalty = 0  # No penalty for non-preferred in this case

    chromosome = [
        ('Alice_section_1', 'PS101_section_1'),  # Preferred course, not core (10 - 0)
        ('Alice_section_2', 'PS211_section_1'),  # Core course, but not preferred (0 - 0)
        ('Bob_section_1', 'PS102_section_1')     # Non-preferred course for Bob (0)
    ]

    fitness = fitness_function(
        chromosome,
        instructors,
        courses,
        max_sections,
        max_unique_classes,
        non_preferred_penalty
    )

    # Expected fitness:
    # Alice: PS101 (preferred) + PS211 (core but not preferred) -> reward for PS101, neutral for PS211
    # Bob: PS102 (non-preferred) -> penalty for non-preferred

    # Alice: (10 - 0) [PS101] + (neutral) [PS211]
    # Bob: (0) [PS102]
    # Fitness = 10 - 0 = 10
    assert fitness == 10


def test_fitness_function_with_course_director_penalty():
    instructors = [
        MockInstructor('Alice', 3, 'mas', preferences=['PS101']),
        MockInstructor('Bob', 2, 'phd', preferences=['PS101'])
    ]
    courses = [
        MockCourse('PS101', 3, course_director='Alice'),  # Alice is course director for PS101
        MockCourse('PS102', 1)
    ]
    max_sections = {'Alice': 3, 'Bob': 2}
    max_unique_classes = 2
    course_director_penalty = 30
    chromosome = [
        ('Alice_section_1', 'PS101_section_1'),  # Alice assigned to 1 PS101 section, but needs more
        ('Bob_section_1', 'PS102_section_1')
    ]

    fitness = fitness_function(
        chromosome,
        instructors,
        courses,
        max_sections,
        max_unique_classes,
        non_preferred_penalty=0,
        course_director_penalty=course_director_penalty
    )

    # Alice should be penalized for not teaching all 3 sections of PS101 as the course director
    assert fitness < 0  # Fitness should be negative due to the penalty for course director


def test_crossover():
    parent1 = [('Alice_section_1', 'PS101_section_1'), ('Bob_section_1', 'PS102_section_1')]
    parent2 = [('Alice_section_1', 'PS102_section_1'), ('Bob_section_1', 'PS101_section_1')]

    child1, child2 = crossover(parent1, parent2)
    assert len(child1) == len(parent1)
    assert len(child2) == len(parent2)
    assert child1 != parent1 and child2 != parent2  # Ensure crossover produces different offspring


def test_mutate():
    instructors = [MockInstructor('Alice', 3, 'mas'), MockInstructor('Bob', 2, 'phd')]
    chromosome = [('Alice_section_1', 'PS101_section_1'), ('Bob_section_1', 'PS102_section_1')]

    # Make sure to fix the initial value of the chromosome
    chromosome_to_mutate = chromosome.copy()
    mutated = mutate(chromosome_to_mutate, instructors)
    assert len(mutated) == len(chromosome)  # Ensure chromosome length remains the same
    assert mutated != chromosome  # Mutation should change the chromosome


def test_genetic_algorithm():
    instructors = [MockInstructor('Alice', 3, 'mas', preferences=['PS101', 'PS102']),
                   MockInstructor('Bob', 2, 'phd', preferences=['PS101'])]
    courses = [MockCourse('PS101', 2), MockCourse('PS102', 1)]
    max_sections = {'Alice': 3, 'Bob': 2}
    max_unique_classes = 2
    non_preferred_penalty = 5

    final_instructors, final_courses, fitness_over_time = genetic_algorithm(
        instructors, courses, max_sections, max_unique_classes, non_preferred_penalty=non_preferred_penalty
    )

    assert len(fitness_over_time) > 0  # Ensure fitness evolves over time
    assert final_instructors[0].assigned_courses  # Ensure instructors are assigned courses
    assert final_instructors[1].assigned_courses


if __name__ == "__main__":
    pytest.main([__file__])
