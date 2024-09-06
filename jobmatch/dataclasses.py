from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Instructor:
    name: str
    max_classes: int
    degree: str  # 'mas' or 'phd'
    preferences: List[str] = field(default_factory=list)
    assigned_courses: List[str] = field(default_factory=list, compare=False)
    unique_courses: Set[str] = field(default_factory=set, compare=False)

    def can_teach(self, course: str) -> bool:
        """Check if the instructor can be assigned another section of the given course."""
        if len(self.assigned_courses) >= self.max_classes:
            return False

        elif len(self.unique_courses) >= 2 and course not in self.unique_courses:
            return False

        elif self.degree and self.degree == 'mas':
            return True  # Adjust this based on specific courses master's degree holders can teach
            # Return True only if the course is in the specified allowed list for master's degree instructors
            # return course in ['PS211', 'PS211S', 'PS211FR', 'SocSci311', 'SocSci311S', 'SocSci212']
        else:
            return True  # PhD instructors can teach any course

    def assign_course(self, course: str, slots: int):
        """Assign the course to the instructor, ensuring it does not exceed max_classes."""
        # Calculate the number of slots that can actually be assigned
        available_slots = min(slots, self.max_classes - len(self.assigned_courses))

        if available_slots > 0:
            self.assigned_courses.extend([course] * available_slots)
            self.unique_courses.add(course)

        # Log if no slots could be assigned (optional)
        if available_slots < slots:
            print(f"{available_slots} out of {slots} requested slots were assigned to {self.name} due to max course load")

    def print_assignments(self, skip_none=False):
        """Print the assigned courses and their ranks."""
        max_name_length = 23  # Adjust this based on your longest instructor name
        max_courses_length = 20  # Adjust this based on your longest list of courses

        if self.assigned_courses:
            courses_str = ", ".join(self.assigned_courses)
            if self.preferences:
                ranks_str = ", ".join(
                    str(self.preferences.index(course) + 1 if course in self.preferences else len(self.preferences) + 1)
                    for course in self.assigned_courses
                )
                # Format the output with aligned columns
                print(f"{self.name:<{max_name_length}} [{courses_str:<{max_courses_length}}] Ranks: ({ranks_str})")
        else:
            if not skip_none:
                print(f"{self.name:<{max_name_length}} No courses assigned.")


@dataclass
class Course:
    name: str
    course_id: str
    course_description: str
    sections_available: int
    assigned_instructors: List[str] = field(default_factory=list, compare=False)
    course_director: str = None

    def print_assignments(self, skip_none=False):
        """Print the assigned instructors for the course."""
        max_course_name_length = 10  # Adjust based on your longest course name
        max_instructors_length = 15  # Adjust based on your longest list of instructors

        if self.assigned_instructors:
            instructors_str = ", ".join(self.assigned_instructors)
            # Format the output with aligned columns
            print(f"{self.name:<{max_course_name_length}} Instructors: [{instructors_str:<{max_instructors_length}}]")
        else:
            if not skip_none:
                print(f"{self.name:<{max_course_name_length}} No instructors assigned.")
