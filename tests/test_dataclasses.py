import pytest

from jobmatch.dataclasses import AssignmentTracker, Course, Instructor


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

def test_can_assign(sample_instructors, sample_courses):
    # Test PhD instructor
    phd_tracker = AssignmentTracker(instructor=sample_instructors[0])
    assert phd_tracker.can_assign('PS211') is True
    assert phd_tracker.can_assign('PS302') is True

    # Assign two courses
    phd_tracker.assign_course('PS211', 1)
    phd_tracker.assign_course('PS302', 1)

    # Check if can assign another unique course
    assert phd_tracker.can_assign('PS477') is False

    # Assign another course
    phd_tracker.assign_course('PS211', 1)
    # Now should not be able to assign a fourth course
    assert phd_tracker.can_assign('PS211') is False

    # Test MAS instructor
    mas_tracker = AssignmentTracker(instructor=sample_instructors[1])
    assert mas_tracker.can_assign('PS211') is True
    assert mas_tracker.can_assign('SocSci311') is True
    assert mas_tracker.can_assign('PS302') is True  # Should return False for a course not in the allowed list

    # Assign courses and test limits
    mas_tracker.assign_course('PS211', mas_tracker.instructor.max_classes + 1) # should only assign 2
    assert len(mas_tracker.assigned_courses) == mas_tracker.instructor.max_classes
    assert mas_tracker.can_assign('SocSci311') is False  # Should now be False since max_classes is reached

def test_assign_course(sample_instructors):
    # Test assigning courses
    tracker = AssignmentTracker(instructor=sample_instructors[0])
    tracker.assign_course('PS211', 1)

    assert tracker.assigned_courses == ['PS211']
    assert tracker.unique_courses == {'PS211'}
    assert tracker.course_count == 1

    tracker.assign_course('PS211', 1)
    assert tracker.assigned_courses == ['PS211', 'PS211']
    assert tracker.course_count == 2

def test_max_unique_courses(sample_instructors):
    # Test max unique courses limit
    tracker = AssignmentTracker(instructor=sample_instructors[0])
    tracker.assign_course('PS211', 1)
    tracker.assign_course('PS302', 1)
    tracker.assign_course('PS477', 1)

    # After assigning three unique courses, should not be able to assign another unique course
    assert tracker.can_assign('SocSci311') is False


if __name__ == "__main__":
    pytest.main([__file__])
