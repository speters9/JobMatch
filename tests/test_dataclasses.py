import pytest

from jobmatch.dataclasses import Course, Instructor


@pytest.fixture
def sample_instructors():
    """Fixture to provide sample instructors."""
    return [
        Instructor(name='Alice', max_classes=3, degree='phd', preferences=['PS211', 'PS302', 'PS477']),
        Instructor(name='Bob', max_classes=2, degree='mas', preferences=['PS211', 'SocSci311'])
    ]

@pytest.fixture
def sample_courses():
    """Fixture to provide sample courses."""
    return [
        Course(name='PS211', course_id='211', course_description='Politics, American Government', sections_available=2),
        Course(name='PS302', course_id='302', course_description='American Foreign Policy', sections_available=1),
        Course(name='SocSci311', course_id='311', course_description='International Security Studies', sections_available=1)
    ]

def test_can_teach(sample_instructors, sample_courses):
    # Test PhD instructor
    phd_instructor = sample_instructors[0]
    assert phd_instructor.can_teach('PS211') is True
    assert phd_instructor.can_teach('PS302') is True

    # Assign two courses
    phd_instructor.assign_course('PS211', 1)
    phd_instructor.assign_course('PS302', 1)

    # Check if can assign another unique course
    assert phd_instructor.can_teach('PS477') is False

    # Assign another course
    phd_instructor.assign_course('PS211', 1)
    # Now should not be able to assign a fourth course
    assert phd_instructor.can_teach('PS211') is False

    # Test MAS instructor
    mas_instructor = sample_instructors[1]
    assert mas_instructor.can_teach('PS211') is True
    assert mas_instructor.can_teach('SocSci311') is True
    assert mas_instructor.can_teach('PS302') is True  # MAS instructor can teach any course

    # Assign courses and test limits
    mas_instructor.assign_course('PS211', mas_instructor.max_classes + 1)  # should only assign 2
    assert len(mas_instructor.assigned_courses) == mas_instructor.max_classes
    assert mas_instructor.can_teach('SocSci311') is False  # Should now be False since max_classes is reached

def test_assign_course(sample_instructors):
    # Test assigning courses
    instructor = sample_instructors[0]
    instructor.assign_course('PS211', 1)

    assert instructor.assigned_courses == ['PS211']
    assert instructor.unique_courses == {'PS211'}

    instructor.assign_course('PS211', 1)
    assert instructor.assigned_courses == ['PS211', 'PS211']

def test_max_unique_courses(sample_instructors):
    # Test max unique courses limit
    instructor = sample_instructors[0]
    instructor.assign_course('PS211', 1)
    instructor.assign_course('PS302', 1)
    instructor.assign_course('PS477', 1)

    # After assigning three unique courses, should not be able to assign another unique course
    assert instructor.can_teach('SocSci311') is False

def test_course_assignment(sample_courses):
    # Test the Course class for correct assignment tracking
    course = sample_courses[0]
    course.assigned_instructors.append('Alice')

    assert course.assigned_instructors == ['Alice']
    course.assigned_instructors.extend(['Bob', 'Charlie'])
    assert course.assigned_instructors == ['Alice', 'Bob', 'Charlie']

    # Ensure that the sections_available attribute can be tracked correctly
    course.sections_available -= 1
    assert course.sections_available == 1



if __name__ == "__main__":
    pytest.main([__file__])
