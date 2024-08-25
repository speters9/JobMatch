# JobMatch

[![CCDS Project template](https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter)](https://cookiecutter-data-science.drivendata.org/)

## Overview

The JobMatch project provides a flexible and modular approach to solving individual and job assignment problems using various optimization strategies, including stable marriage, bipartite graph matching, and linear programming. It is designed to match instructors to courses based on their preferences, course capacities, and other potential constraints. By a process of iterative matching, each algorithm is structured to allow for matching to more than one assignment per instructor.


## Project Organization

```
├── LICENSE            <- Open-source license
├── README.md          <- The top-level README for developers using this project.
│
├── data               <- Repository for raw matching preferences (not included here)
│
├── docs               <- Mkdocs for sphinx-generated documentation
│
├── models             <- Trained and serialized models, model predictions, or model summaries (None included yet)
│
├── notebooks          <- Includes base implementation.
│
└── jobmatch           <- Source code for use in this project.
|    │
|    ├── JobMatch.py                   <- Factory implementation of JobMatch class, a factory for calling the various algorithms.
|    │
|    ├── bipartite_graph_match.py       <- Code for bipartite matching using factorized instructor and course sections.
|    │
|    ├── linear_program_optimization.py <- Code for matching via linear program optimization.
|    │
|    ├── stable_marriage.py             <- Code for matching using stable marriage algorithm.
|    │
|    ├── preprocessing.py               <- Code for parsing input preferences and preprocessing for passing to the matching algorithms.
|    |
|    └── global_functions.py            <- Code with general utility functions.
│
└── gui                     <- Directory for the upload module and GUI components.
     │
     ├── load_data.py        <- Preprocessing tasks for drag and drop data input, normalizing data and prepping for ingestion.
     │
     ├── data_ingestion.py   <- Code for handling normalized input and converting to Instructor and Course objects for the algorithms to use.
     │
     ├── gui_interface.py    <- Code for the drag-and-drop GUI interface.
     │
     └── run_jobmatch_app.py <- Main entry point for running the JobMatch GUI application.
```

--------
## Key Components

- **JobMatch Class**: The JobMatch class integrates the different solving methods (stable marriage, bipartite matching, linear programming) and provides a unified interface for running the course assignment process.

- **Bipartite Matching with Factorization**
     - This algorithm factorizes both instructors and courses into individual sections, allowing for a traditional one-to-one matching problem.
     - This approach optimizes for instructor preferences by creating a bipartite graph where each node represents a section of an instructor or a section of a given course.
     - The edges between nodes are weighted according to the instructor's preference for the course and the priority of the instructor.

       **Key Features:**
          - Factorization: Each instructor and course is broken down into sections, enabling a granular one-to-one matching.
          - Normalized Weights: The weights assigned to the edges are normalized to account for the varying numbers of sections each instructor can teach, ensuring a fair and balanced matching process.
          - Tie-breaking: In case of ties, instructor priority (based on the order in the input list) is used to determine the final match.

- **Linear Programming Optimization**
     - This approach uses linear programming to optimize the matching of instructors to courses. The algorithm iterates through potential matches, ensuring that:
          - No instructor is assigned more than two unique courses.
          - The total number of sections taught does not exceed the maximum allowed for each instructor.
          - Courses are filled according to their available sections.
     - The algorithm supports different solving strategies, such as multi-objective optimization methods, to achieve the best possible assignment based on the given constraints. Default seems to work the best
  
- **Modified Stable Marriage Algorithm:**
    - This version of the stable marriage algorithm sequentially matches instructors to courses based on their preferences.
    - The algorithm ensures that:
        - No instructor is assigned more than two unique courses.
        - Instructors are greedily assigned to additional sections of a course they are already teaching, as long as their maximum sections or course capacity is not exceeded.
        - The process iterates until no more matches can be made, either because all instructors have been fully assigned or all course capacities are exhausted.
    - Unlike traditional stable marriage, this version supports sequential and greedy matching, allowing for multiple sections of the same course to be assigned to an instructor.
        - Instructors propose to their preferred courses sequentially, and courses can "reject" instructors if they have reached capacity or if another instructor with a higher preference has already been assigned.
        - The process continues iteratively until all instructors are assigned within the constraints.
  
- **Preprocessing**: Functions for standardizing and parsing input data, ensuring consistency across the various solving methods.

--------
- ## Usage
     - To use the JobMatch class, initialize it with:
          - A list of Instructor objects, each containing a list of preferences, maximum section load, and other relevant information.
          - A list of Course objects, each containing the course name, ID, description, and the number of sections available.
          - A full pipeline includes importing a CSV of raw text preferences and course information, and then converting them to the necessary data structures using the preprocessing module. Provided the input csvs use the standard naming convention, it's as easy as drag and drop. However, you can manually input these data structures to bypass the preprocessing step.
     - You can then choose from one of the supported methods (`stable_marriage`, `bipartite_matching`, `linear_programming`) to solve the assignment problem.

     - Dependencies are managed by Poetry, so running `poetry install` with the pyproject.toml file should get you started.

     - See notebooks/faces_in_spaces for an example code implementation.

--------
## Running the Application

The code has also been packaged into a simple GUI for ease of use. Simply drag and drop your instructor preferences, course availability, and then choose your algorithm.

To run the JobMatch GUI application, you can execute the `run_jobmatch_app.py` script located in the gui directory. This script launches the drag-and-drop interface, allowing you to input instructor and course data, select a matching algorithm, and view the results interactively.

```
poetry run python gui/run_jobmatch_app.py
```
