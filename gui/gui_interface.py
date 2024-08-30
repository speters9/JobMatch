import csv
import os
import tkinter as tk
from tkinter import filedialog, ttk

import sv_ttk
from tkinterdnd2 import DND_FILES, TkinterDnD

from gui.load_data import load_courses, load_instructors
from jobmatch.global_functions import set_all_seeds
from jobmatch.JobMatch import JobMatch


class JobMatchApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Job Matching Tool")
        self.geometry("600x450")  # Increased window height for better layout

        self.instructor_file = None
        self.course_file = None
        self.instructors = None
        self.courses = None
        self.selected_method = tk.StringVar(value="bipartite_matching")  # Default method
        self.match_type = tk.StringVar(value="Instructor Matches")  # Default match type
        self.matching_results = None  # To store the results after the first run
        self.job_match_instance = None  # To store the instance of JobMatch
        self.set_seed = set_all_seeds

        self.create_widgets()

        # Set the default theme to light
        sv_ttk.set_theme("light")

    def create_widgets(self):
        # Use a grid layout manager
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Shaded drag-and-drop area for instructors file (covers two rows)
        self.instructor_label = ttk.Label(self, text="Drop Instructors File Here", width=30)
        self.instructor_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.instructor_label.config(font=("Helvetica", 12), relief="solid", padding=10)
        self.instructor_label.drop_target_register(DND_FILES)
        self.instructor_label.dnd_bind('<<Drop>>', self.load_instructor_file)

        # Shaded drag-and-drop area for courses file (covers two rows)
        self.course_label = ttk.Label(self, text="Drop Courses File Here", width=30)
        self.course_label.grid(row=2, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.course_label.config(font=("Helvetica", 12), relief="solid", padding=10)
        self.course_label.drop_target_register(DND_FILES)
        self.course_label.dnd_bind('<<Drop>>', self.load_course_file)

        # Button to run the matching algorithm (moved below drag-and-drop areas)
        self.run_button = ttk.Button(self, text="Run Matching", command=self.run_matching, width=20)
        self.run_button.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        # Button to view the selected match type (moved below drag-and-drop areas)
        self.view_button = ttk.Button(self, text="Print Results", command=self.view_matches, width=20)
        self.view_button.grid(row=5, column=0, padx=10, pady=5, sticky="w")

        # Dropdown for method selection with separate label row
        method_label = ttk.Label(self, text="Select Matching Method:")
        method_label.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")

        # Initialize the method dropdown with the options list
        method_options = ["bipartite_matching", "stable_marriage", "linear_programming"]
        self.method_menu = ttk.OptionMenu(self, self.selected_method, method_options[0], *method_options)
        self.method_menu.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="w")

        # Dropdown for match type selection with separate label row
        match_type_label = ttk.Label(self, text="Select Match Type to View:")
        match_type_label.grid(row=2, column=1, padx=10, pady=(10, 2), sticky="w")

        # Initialize the match type dropdown with the options list
        match_type_options = ["Instructor Matches", "Course Matches"]
        self.match_type_menu = ttk.OptionMenu(self, self.match_type, match_type_options[0], *match_type_options)
        self.match_type_menu.grid(row=3, column=1, padx=10, pady=(2, 10), sticky="w")

        # Button to export results to CSV (remains on the right side)
        self.export_button = ttk.Button(self, text="Export to CSV", command=self.export_results_to_csv, width=20)
        self.export_button.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Toggle Theme button (remains on the right side)
        self.toggle_theme_button = ttk.Button(self, text="Toggle Theme", command=self.toggle_theme, width=20)
        self.toggle_theme_button.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Apply initial theme settings
        self.apply_theme()


    def apply_theme(self):
        current_theme = sv_ttk.get_theme()
        if current_theme == "dark":
            self.instructor_label.config(background="#333333", foreground="white")
            self.course_label.config(background="#333333", foreground="white")
        else:
            self.instructor_label.config(background="#f0f0f0", foreground="black")
            self.course_label.config(background="#f0f0f0", foreground="black")

    def toggle_theme(self):
        # Toggle the theme and adjust the colors accordingly
        sv_ttk.toggle_theme()
        self.apply_theme()


    def load_instructor_file(self, event):
        file_path = event.data.strip('{}')
        if file_path and file_path != self.instructor_file:
            self.instructor_file = file_path
            try:
                self.instructors = load_instructors(self.instructor_file)
                if self.instructors:
                    tk.messagebox.showinfo("File Loaded", f"Instructor file loaded: {os.path.basename(self.instructor_file)}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to load instructor file: {str(e)}")

    def load_course_file(self, event):
        file_path = event.data.strip('{}')
        if file_path and file_path != self.course_file:
            self.course_file = file_path
            try:
                self.courses = load_courses(self.course_file)
                if self.courses:
                    tk.messagebox.showinfo("File Loaded", f"Course file loaded: {os.path.basename(self.course_file)}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to load course file: {str(e)}")

    def run_matching(self):
        if not self.instructor_file or not self.course_file:
            tk.messagebox.showerror("Error", "Please load both instructor and course files before running the matching.")
            return
        self.set_seed(94305)

        try:
            self.job_match_instance = JobMatch(self.instructors, self.courses)
            method = self.selected_method.get()  # Get the selected method from the dropdown
            self.matching_results = self.job_match_instance.solve(method=method)  # Store the results

            tk.messagebox.showinfo("Matching Results", "Matching completed successfully! \nUse the dropdown and 'Print Results' button to view results.")

        except Exception as e:
            tk.messagebox.showerror("Error", f"An error occurred during the matching process: {str(e)}")

    def view_matches(self):
        if not self.matching_results:
            tk.messagebox.showerror("Error", "No matching results to display. Please run the matching algorithm first.")
            return

        match_type = self.match_type.get()
        result_text = ""

        if match_type == "Instructor Matches":
            result_text = self.get_match_results_text(self.matching_results[0], query = 'instructor')
        elif match_type == "Course Matches":
            result_text = self.get_match_results_text(self.matching_results[1], query ='course')

        self.display_results_popup(result_text)

    def get_match_results_text(self, results, query):
        result_lines = []
        if query == "instructor":
            for instructor in results:
                courses = [course for course in instructor.assigned_courses]
                ranks = [
                    str(instructor.preferences.index(course) + 1) if course in instructor.preferences else "N/A"
                    for course in instructor.assigned_courses
                ]

                assignment_str = f"{instructor.name}: [{', '.join(courses)}] (Rank {', '.join(ranks)})"
                result_lines.append(assignment_str)

            return "\n".join(result_lines)
        elif query == "course":
            for course in results:
                instructors = [inst for inst in course.assigned_instructors]
                assignment_str = f"{course.name}: [{', '.join(instructors)}]"
                result_lines.append(assignment_str)

            return "\n".join(result_lines)

    def display_results_popup(self, text):
        result_popup = tk.Toplevel(self)
        result_popup.title("Matching Results")

        # Set the default size of the popup window
        result_popup.geometry("800x600")  # Adjust the width and height as needed

        text_area = tk.Text(result_popup, wrap=tk.WORD, width=80, height=25)  # Set default size for the text area
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, text)
        text_area.config(state=tk.DISABLED)  # Make the text area read-only

        # Add a scrollbar
        scrollbar = tk.Scrollbar(text_area)
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def export_results_to_csv(self):
        if not self.matching_results:
            tk.messagebox.showerror("Error", "No matching results to export. Please run the matching algorithm first.")
            return

        # Ask the user where to save the file
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return  # User cancelled the save dialog

        match_type = self.match_type.get()
        if match_type == "Instructor Matches":
            results = self.matching_results[0]
            query = 'instructor'
        elif match_type == "Course Matches":
            results = self.matching_results[1]
            query = 'course'

        method = self.selected_method.get()

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
                    writer.writerow([instructor.name] + courses + [', '.join([rank for rank in ranks if len(rank.strip())>0])])
            elif query == "course":
                writer.writerow(["Course", "Assigned Instructors"])  # Header row
                for course in results:
                    instructors = [inst for inst in course.assigned_instructors]
                    writer.writerow([course.name, ', '.join(sorted(instructors))])

        tk.messagebox.showinfo("Export Successful", f"Results have been exported to {file_path}")

if __name__ == "__main__":
    app = JobMatchApp()
    app.mainloop()
