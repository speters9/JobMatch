import csv
import os
from typing import List, Optional, Tuple, Union

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
                             QDialogButtonBox, QFileDialog, QHBoxLayout,
                             QLabel, QMainWindow, QMessageBox, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)

from gui.app_instructions import INSTRUCTIONS_TEXT
from gui.load_data import load_courses, load_instructors
from jobmatch.global_functions import set_all_seeds
from jobmatch.JobMatch import JobMatch


class DnDLabel(QLabel):
    """
    A QLabel subclass that supports drag and drop functionality.

    Attributes:
        app (JobMatchApp): Reference to the main application.
    """

    def __init__(self, text: str, app: "JobMatchApp", parent: Optional[QWidget] = None) -> None:
        """
        Initialize the DnDLabel with drag and drop capabilities.

        Args:
            text (str): The text to display on the label.
            app (JobMatchApp): Reference to the main application.
            parent (Optional[QWidget], optional): The parent widget. Defaults to None.
        """
        super().__init__(text, parent)
        self.app = app  # Reference to the main application
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid black; font-size: 20px;")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Handle the drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle the drop event."""
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.app.handle_file_drop(self, file_path)  # Call method on the main application


class CenteredComboBox(QComboBox):
    """
    A QComboBox subclass with centered text and theme support.

    Attributes:
        app (JobMatchApp): Reference to the main application for theme information.
    """

    def __init__(self, parent: Optional[QWidget] = None, app: Optional["JobMatchApp"] = None) -> None:
        """
        Initialize the CenteredComboBox with theme support.

        Args:
            parent (Optional[QWidget], optional): The parent widget. Defaults to None.
            app (Optional[JobMatchApp], optional): Reference to the main application. Defaults to None.
        """
        super().__init__(parent)
        self.app = app  # Reference to the main application for theme information

    def paintEvent(self, event):
        """Custom paint event to center the text and adjust colors based on the theme."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)

        # Draw the standard ComboBox
        self.style().drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter)

        # Determine the background color based on the current theme
        if self.app.is_light_theme:
            bg_color = QtGui.QColor(245, 245, 245)  # Light theme background color
            text_color = QtGui.QColor(0, 0, 0)  # Light theme text color
        else:
            bg_color = QtGui.QColor(77, 77, 77)  # Dark theme background color
            text_color = QtGui.QColor(255, 255, 255)  # Dark theme text color

        rect = opt.rect

        # Set the background color and draw the rectangle
        painter.fillRect(rect, bg_color)
        painter.drawRect(rect)

        # Set the text color and draw the centered text
        painter.setPen(text_color)
        text = opt.currentText
        painter.drawText(rect, QtCore.Qt.AlignCenter, text)


class JobMatchApp(QMainWindow):
    """
    The main application window for the Job Matching Tool.

    Attributes:
        is_light_theme (bool): Tracks the current theme.
        instructor_file (Optional[str]): Path to the instructor file.
        course_file (Optional[str]): Path to the course file.
        instructors (Optional[List]): List of instructors.
        courses (Optional[List]): List of courses.
        selected_method (str): Selected matching method.
        match_type (str): Selected match type.
        matching_results (Optional[List]): Store the results after the first run.
        job_match_instance (Optional[JobMatch]): Store the instance of JobMatch.
    """

    def __init__(self) -> None:
        """Initialize the JobMatchApp."""
        super().__init__()
        self.is_light_theme = True  # Track the current theme

        self.setWindowTitle("Job Matching Tool")
        self.setGeometry(100, 100, 800, 450)

        self.instructor_file = None
        self.course_file = None
        self.instructors = None
        self.courses = None
        self.selected_method = "bipartite_matching"  # Default method
        self.match_type = "Instructor Matches"  # Default match type
        self.matching_results = None  # To store the results after the first run
        self.job_match_instance = None  # To store the instance of JobMatch
        self.instructions_dialog = None
        self.set_seed = set_all_seeds

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and arrange the widgets in the main application window."""
        # Central widget setup
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)  # Vertical layout for the main structure


        # Add instructions button at the top
        self.instructions_button = QPushButton("Instructions", self)
        self.instructions_button.setStyleSheet("font-size: 16px;")
        self.instructions_button.setFixedWidth(200)  # Make the button a bit wider
        layout.addWidget(self.instructions_button, alignment=QtCore.Qt.AlignCenter)


        # Horizontal layout to contain the first row: top drag-and-drop box and dropdowns
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)

        # Horizontal layout to contain the second row: bottom drag-and-drop box and buttons
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)

        # Left layout for top drag-and-drop box
        left_layout_top = QVBoxLayout()
        top_layout.addLayout(left_layout_top)

        # Right layout for dropdowns
        right_layout_top = QVBoxLayout()
        right_layout_top.setSpacing(0)  # Reduce the spacing between the label and dropdown
        top_layout.addLayout(right_layout_top)

        # Left layout for bottom drag-and-drop box
        left_layout_bottom = QVBoxLayout()
        bottom_layout.addLayout(left_layout_bottom)

        # Right layout for buttons
        right_layout_bottom = QVBoxLayout()
        bottom_layout.addLayout(right_layout_bottom)

        # Instructor file drop area (top left)
        self.instructor_label = DnDLabel("Drop Instructors File Here", self, self)
        self.instructor_label.setMinimumHeight(200)
        left_layout_top.addWidget(self.instructor_label)

        # Course file drop area (bottom left)
        self.course_label = DnDLabel("Drop Courses File Here", self, self)
        self.course_label.setMinimumHeight(200)
        left_layout_bottom.addWidget(self.course_label)

        # Labels and Dropdowns (top right)
        method_label = QLabel("Select Matching Algorithm:", self)
        method_label.setStyleSheet("font-size: 16px; margin-bottom: 5px;")
        right_layout_top.addWidget(method_label)

        self.method_menu = CenteredComboBox(self, app=self)
        self.method_menu.addItems(["Bipartite Matching", "Stable Marriage", "Linear Programming"])
        self.method_menu.setStyleSheet("font-size: 16px; padding: 4px;")
        right_layout_top.addWidget(self.method_menu)

        match_type_label = QLabel("Select Print Option:", self)
        match_type_label.setStyleSheet("font-size: 16px; margin-bottom: 5px; margin-top: 15px;")
        right_layout_top.addWidget(match_type_label)

        self.match_type_menu = CenteredComboBox(self, app=self)
        self.match_type_menu.addItems(["Instructor Matches", "Course Matches"])
        self.match_type_menu.setStyleSheet("font-size: 16px; padding: 4px;")
        right_layout_top.addWidget(self.match_type_menu)

        # Buttons (bottom right)
        self.run_button = QPushButton("Run Matching", self)
        self.run_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout_bottom.addWidget(self.run_button)

        self.view_button = QPushButton("Print Results", self)
        self.view_button.setStyleSheet("font-size: 16px;")
        right_layout_bottom.addWidget(self.view_button)

        self.export_button = QPushButton("Export to CSV", self)
        self.export_button.setStyleSheet("font-size: 16px;")
        right_layout_bottom.addWidget(self.export_button)

        self.toggle_theme_button = QPushButton("Toggle Theme", self)
        self.toggle_theme_button.setStyleSheet("font-size: 16px;")
        right_layout_bottom.addWidget(self.toggle_theme_button)

        # Connect signals to slots
        self.run_button.clicked.connect(self.run_matching)
        self.view_button.clicked.connect(self.view_matches)
        self.export_button.clicked.connect(self.export_results_to_csv)
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.instructions_button.clicked.connect(self.show_instructions)

        # Set the default light theme
        self.apply_theme(light=True)

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        current_style = self.styleSheet()
        if "background-color: #333333;" in current_style:
            self.apply_theme(light=True)
        else:
            self.apply_theme(light=False)

    def apply_theme(self, light: bool = True) -> None:
        """
        Apply the selected theme to the application.

        Args:
            light (bool, optional): Whether to apply the light theme. Defaults to True.
        """
        self.is_light_theme = light  # Update the theme tracker
        if light:
            self.setStyleSheet("font-size: 16px; background-color: #f0f0f0; color: black;")
            self.instructor_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0; color: black;")
            self.course_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0; color: black;")
            self.method_menu.setStyleSheet("font-size: 16px; padding: 4px;")
            self.match_type_menu.setStyleSheet("font-size: 16px; padding: 4px;")
        else:
            self.is_light_theme = False
            self.setStyleSheet("font-size: 16px; background-color: #333333; color: white;")
            self.instructor_label.setStyleSheet("border: 1px solid white; background-color: #333333; color: white;")
            self.course_label.setStyleSheet("border: 1px solid white; background-color: #333333; color: white;")
            self.method_menu.setStyleSheet("font-size: 16px; padding: 4px;")
            self.match_type_menu.setStyleSheet("font-size: 16px; padding: 4px;")

    def show_instructions(self) -> None:
        if not self.instructions_dialog:
            self.instructions_dialog = QDialog(self)
            self.instructions_dialog.setWindowTitle("Instructions")
            self.instructions_dialog.setMinimumWidth(850)
            self.instructions_dialog.setMinimumHeight(850)

            layout = QVBoxLayout(self.instructions_dialog)

            text_edit = QTextEdit(self.instructions_dialog)
            text_edit.setReadOnly(True)
            text_edit.setHtml(INSTRUCTIONS_TEXT)
            layout.addWidget(text_edit)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(self.instructions_dialog.accept)
            layout.addWidget(button_box)

        self.instructions_dialog.show()  # show() instead of exec_()
        return self.instructions_dialog

    def handle_file_drop(self, label: QLabel, file_path: str) -> None:
        """
        Handle the file drop event.

        Args:
            label (QLabel): The label where the file was dropped.
            file_path (str): The path to the dropped file.
        """
        # print(f"File dropped: {file_path}")  # Debug statement
        if "Instructors" in label.text():
            self.load_instructor_file(file_path)
        elif "Courses" in label.text():
            self.load_course_file(file_path)

    def load_instructor_file(self, file_path: str) -> None:
        """
        Load the instructor file and display a message.

        Args:
            file_path (str): Path to the instructor file.
        """
        if file_path and file_path != self.instructor_file:
            self.instructor_file = file_path
            # print(f"Loading instructor file: {file_path}")  # Debug statement
            try:
                self.instructors = load_instructors(self.instructor_file)
                # print(f"Instructors loaded: {self.instructors}")  # Debug statement
                if self.instructors:
                    QMessageBox.information(self, "File Loaded", f"Instructor file loaded: {os.path.basename(self.instructor_file)}")
            except Exception as e:
                print(f"Failed to load instructor file: {str(e)}")  # Debug statement
                QMessageBox.critical(self, "Error", f"Failed to load instructor file: {str(e)}")
                # reset to allow for resubmit
                self.instructor_file = None

    def load_course_file(self, file_path: str) -> None:
        """
        Load the course file and display a message.

        Args:
            file_path (str): Path to the course file.
        """
        if file_path and file_path != self.course_file:
            self.course_file = file_path
            # print(f"Loading course file: {file_path}")  # Debug statement
            try:
                self.courses = load_courses(self.course_file)
                # print(f"Courses loaded: {self.courses}")  # Debug statement
                if self.courses:
                    QMessageBox.information(self, "File Loaded", f"Course file loaded: {os.path.basename(self.course_file)}")
            except Exception as e:
                print(f"Failed to load course file: {str(e)}")  # Debug statement
                QMessageBox.critical(self, "Error", f"Failed to load course file: {str(e)}")
                # reset to allow for resubmit
                self.course_file = None

    def run_matching(self) -> None:
        """Run the matching algorithm based on the selected method."""
        if not self.instructor_file or not self.course_file:
            QMessageBox.critical(self, "Error", "Please load both instructor and course files before running the matching.")
            return

        # Check if instructors and courses are actually loaded
        if not self.instructors or not self.courses:
            print("Instructors or Courses data not loaded!")  # Debug statement
            QMessageBox.critical(self, "Error", "Instructors or Courses data not loaded. Please check the files.")
            return

        method_dict = {"Bipartite Matching": "bipartite_matching",
                       "Stable Marriage": "stable_marriage",
                       "Linear Programming": "linear_programming"}

        self.set_seed(94305)

        try:
            self.job_match_instance = JobMatch(self.instructors, self.courses)
            selected_method = self.method_menu.currentText()  # Get the selected method from the dropdown
            method = method_dict.get(selected_method, "Matching Method Not Found")
            self.matching_results = self.job_match_instance.solve(method=method)  # Store the results

            QMessageBox.information(self, "Matching Results",
                                    "Matching completed successfully! \nUse the dropdown and 'Print Results' button to view results.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during the matching process: {str(e)}")

    def view_matches(self) -> None:
        """View the matching results based on the selected match type."""
        if not self.matching_results:
            QMessageBox.critical(self, "Error", "No matching results to display. Please run the matching algorithm first.")
            return

        match_type = self.match_type_menu.currentText()
        result_text = ""

        if match_type == "Instructor Matches":
            result_text = self.get_match_results_text(self.matching_results[0], query='instructor')
        elif match_type == "Course Matches":
            result_text = self.get_match_results_text(self.matching_results[1], query='course')

        self.display_results_popup(result_text)


    def get_match_results_text(self, results: List, query: str) -> str:
        """
        Generate formatted match results text.

        Args:
            results (List): List of results to format.
            query (str): The query type, either 'instructor' or 'course'.

        Returns:
            str: The formatted match results as an HTML table.
        """
        result_lines = []

        # Get the selected method and add it to the top of the results
        selected_method = self.method_menu.currentText()

        if query == "instructor":
            result_lines.append(f"<h3>Instructor Results: {selected_method}</h3><br>")
            for instructor in results:
                course_list = ', '.join(instructor.assigned_courses)
                ranks_list = ', '.join([
                    str(instructor.preferences.index(course) + 1) if course in instructor.preferences else "N/A"
                    for course in instructor.assigned_courses
                ])

                # Adjust the width percentages to expand the name and course fields
                assignment_str = (
                    f"<tr>"
                    f"<td style='width: 45%; padding-right: 30px;'>{instructor.name}</td>"
                    f"<td style='width: 45%; padding-right: 30px;'>{course_list}</td>"
                    f"<td style='width: 10%; padding-right: 30px;'>Rank {ranks_list}</td>"
                    f"</tr>"
                )
                result_lines.append(assignment_str)

            return f"<table style='width: 100%;'>{''.join(result_lines)}</table>"

        elif query == "course":
            result_lines.append(f"<h3>Course Results: {selected_method}</h3><br>")
            for course in results:
                instructors = ', '.join(course.assigned_instructors)
                assignment_str = (
                    f"<tr>"
                    f"<td style='width: 45%; padding-right: 30px;'>{course.name}</td>"
                    f"<td style='width: 45%; padding-right: 30px;'>{instructors}</td>"
                    f"</tr>"
                )
                result_lines.append(assignment_str)

            return f"<table style='width: 100%;'>{''.join(result_lines)}</table>"


    def display_results_popup(self, text: str) -> None:
        """
        Display the results in a popup.

        Args:
            text (str): The text to display in the popup.
        """
        result_popup = QMessageBox(self)
        result_popup.setWindowTitle("Matching Results")

        # Set the text area with a wider width
        text_area = QTextEdit(result_popup)
        text_area.setReadOnly(True)
        text_area.setText(text)
        text_area.setMinimumWidth(900)  # Adjust the width as needed
        text_area.setMinimumHeight(600)  # Adjust the height as needed

        result_popup.layout().addWidget(text_area)
        result_popup.setStandardButtons(QMessageBox.Ok)
        result_popup.exec_()

    def export_results_to_csv(self) -> None:
        """Export the matching results to a CSV file."""
        if not self.matching_results:
            QMessageBox.critical(self, "Error", "No matching results to export. Please run the matching algorithm first.")
            return

        # Ask the user where to save the file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV files (*.csv)")
        if not file_path:
            return  # User cancelled the save dialog

        match_type = self.match_type_menu.currentText()
        if match_type == "Instructor Matches":
            results = self.matching_results[0]
            query = 'instructor'
        elif match_type == "Course Matches":
            results = self.matching_results[1]
            query = 'course'

        method = self.method_menu.currentText()

        # Export the results to CSV
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([f"{match_type}: {method}"])
            if query == "instructor":
                # Determine the maximum number of courses assigned to any instructor
                max_courses = max(len(instructor.assigned_courses) for instructor in results)

                # Create header row with dynamic columns for each course assignment
                header = ["Name"] + [f"Course_{i+1}" for i in range(max_courses)] + ["Rankings"]
                writer.writerow(header)  # Write the header

                for instructor in results:
                    # Fill courses and ranks up to the max_courses length
                    courses = instructor.assigned_courses + [""] * (max_courses - len(instructor.assigned_courses))
                    ranks = [
                        str(instructor.preferences.index(course) + 1) if course in instructor.preferences else "N/A"
                        for course in instructor.assigned_courses
                    ] + [""] * (max_courses - len(instructor.assigned_courses))

                    # Write each instructor's name, courses, and ranks
                    writer.writerow([instructor.name] + courses + [', '.join([rank for rank in ranks if len(rank.strip()) > 0])])
            elif query == "course":
                writer.writerow(["Course", "Assigned Instructors"])  # Header row
                for course in results:
                    instructors = [inst for inst in course.assigned_instructors]
                    writer.writerow([course.name, ', '.join(sorted(instructors))])

        QMessageBox.information(self, "Export Successful", f"Results have been exported to {file_path}")


if __name__ == "__main__":
    app = QApplication([])
    window = JobMatchApp()
    window.show()
    app.exec_()
