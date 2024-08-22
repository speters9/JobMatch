from dataclasses import dataclass, field
from typing import List, Set


@dataclass(frozen=True)
class Instructor:
    name: str
    max_classes: int
    degree: str  # 'mas' or 'phd'
    preferences: List[str] = field(default_factory=list)
    assigned_courses: List[str] = field(default_factory=list, compare=False)
    unique_courses: Set[str] = field(default_factory=set, compare=False)

    def can_teach(self, course: str) -> bool:
        """Check if the instructor can teach the specified course."""
        if self.degree == 'mas':
            return True
            #return course in ['PS211', 'PS211S', 'PS211FR', 'SocSci311', 'SocSci311S', 'SocSci212']  # Adjust courses as needed
        return True  # 'phd' can teach any course

    def print_assignments(self, skip_none=False):
        """Print the assigned courses and their ranks."""
        max_name_length = 23  # Adjust this based on your longest instructor name
        max_courses_length = 20  # Adjust this based on your longest list of courses

        if self.assigned_courses:
            courses_str = ", ".join(self.assigned_courses)
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


@dataclass
class AssignmentTracker:
    instructor: Instructor
    assigned_courses: List[str] = field(default_factory=list)
    unique_courses: Set[str] = field(default_factory=set)
    course_count: int = 0

    def can_assign(self, course: str) -> bool:
        """Check if the instructor can be assigned another section of the given course."""
        if self.course_count >= self.instructor.max_classes:
            return False

        if len(self.unique_courses) >= 2 and course not in self.unique_courses:
            return False

        if self.instructor.degree == 'mas':
            return True
            # Return True only if the course is in the specified allowed list for master's degree instructors
            #return course in ['PS211', 'PS211S', 'PS211FR', 'SocSci311', 'SocSci311S', 'SocSci212']
        return True  # PhD instructors can teach any course

    def assign_course(self, course: str, slots: int):
        """Assign the course to the instructor, ensuring it does not exceed max_classes."""
        # Calculate the number of slots that can actually be assigned
        available_slots = min(slots, self.instructor.max_classes - self.course_count)

        if available_slots > 0:
            self.assigned_courses.extend([course] * available_slots)
            self.unique_courses.add(course)
            self.course_count += available_slots

        # Log if no slots could be assigned (optional)
        if available_slots < slots:
            print(f"{available_slots} out of {slots} requested slots were assigned to {self.instructor.name} due to max course load")
