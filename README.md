# JobMatch

[![CCDS Project template](https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter)](https://cookiecutter-data-science.drivendata.org/)

## Overview

The JobMatch project provides a flexible and modular approach to solving individual and job assignment problems using various optimization strategies, including stable marriage, bipartite graph matching, linear programming, and genetic algorithms. It is designed to match instructors to courses based on their preferences, course capacities, and other constraints. By a process of iterative matching, each algorithm is structured to allow for matching to more than one assignment per instructor, while also allowing the designation of course directors.

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
├── notebooks          <- Jupyter notebooks with examples and base implementation.
│   ├── faces_in_spaces.py
│   ├── normalize_input_df.py
│   ├── validate_assignments.py
│   └── __init__.py
│
├── jobmatch           <- Source code for use in this project.
│   │
│   ├── JobMatch.py                   <- Factory implementation of the JobMatch class for calling various algorithms.
│   ├── bipartite_graph_match.py       <- Bipartite matching using factorized instructor and course sections.
│   ├── dataclasses.py                 <- Base dataclasses for managing input and processing data.
│   ├── genetic_algorithm.py           <- Genetic algorithm implementation for matching instructors to courses.
│   ├── linear_program_optimization.py <- Matching via linear programming optimization.
│   ├── preprocessing.py               <- Ingesting loaded data: preprocessing for passing to the algorithms.
│   ├── stable_marriage.py             <- Stable marriage algorithm implementation.
│   ├── global_functions.py            <- General utility functions.
│   └── archive                        <- Archive of old/unused implementations.
│       ├── iterative_bipartite_graph_match.py
│       ├── old_gui_interface.py
│       └── one_to_one_matching.py
│
└── gui                <- Directory for the GUI components and upload module.
     │
     ├── app_instructions.py  <- Instructions displayed in the JobMatch GUI.
     ├── gui_interface.py     <- Code for the drag-and-drop GUI interface.
     ├── jobmatch_app.py      <- Main entry point for running the JobMatch GUI application.
     ├── load_data.py         <- Preprocessing tasks for drag and drop data input, normalizing data and prepping for ingestion.
     └── resources_rc.py      <- Compiled resource files for the GUI.

```

--------
## Key Components

- **JobMatch Class**: The `JobMatch` class integrates the different solving methods (stable marriage, bipartite matching, linear programming, and genetic algorithm) and provides a unified interface for running the course assignment process.

### General Constraints Across All Algorithms:
All the matching algorithms ensure that:
- No instructor is assigned more than two unique courses.
- The total number of sections assigned does not exceed the maximum allowed for each instructor.
- Course directors are prioritized and automatically assigned to their respective courses where applicable.
- Factorized instructors and courses: In all algorithms but stable marriage, each instructor and course is broken down into available sections, enabling granular one-to-one matching.

### Unique Features of Each Algorithm:

- **Bipartite Graph Matching**:
    - Creates a graph of instructor sections and course sections, with edges weighted by instructor preference. This allows for a traditional one-to-one matching problem.
    - **Key Features**:
      - **Normalized Weights**: The edges between nodes are weighted according to instructor preferences and priority.
      - **Tie-breaking**: Instructor priority (based on order in the input list) is used to determine the final match.

- **Linear Programming Optimization**:
    - Uses linear programming to optimize the assignment of instructors to courses.
    - **Key Features**:
      - A mathematical optimization approach that ensures courses are filled according to their available sections, aiming to maximize overall satisfaction.

- **Modified Stable Marriage Algorithm**:
    - **Key Features**:
      - Allows for sequential matching, using a greedy method to assign additional sections if possible.
      - This version of stable marriage supports matching multiple sections of the same course to an instructor and prioritizes mutual preferences between instructors and courses.

- **Genetic Algorithm**:
    - Introduces an iterative evolutionary process to optimize the matching of instructors to courses.
    - **Key Features**:
      - Populations of potential matches are randomly initialized, and fitness functions evaluate solutions based on preferences, course director roles, and constraints.
      - The algorithm evolves through crossover and mutation across multiple generations to find the optimal assignments.
      - Course directors are automatically assigned to their designated courses upon initialization, ensuring that their assignments are prioritized from the start.

--------
## Usage
- **Install**:
  - Running `poetry install` or `pip install -e` with the pyproject.toml file should get you started.
- **Initialize**:
  - To use the JobMatch class, initialize it with:
    - A list of `Instructor` objects, each containing a list of preferences, maximum section load, and other relevant information.
    - A list of `Course` objects, each containing the course name, ID, description, and the number of sections available.
    - You can manually input these data structures or import them via a CSV using the drag-and-drop feature in the GUI.
    - You can then choose from one of the supported methods (`stable_marriage`, `bipartite_matching`, `linear_programming`, `genetic_algorithm`) to solve the assignment problem.
    - **Note**: The genetic algorithm is more computationally intensive and takes approximately 30 seconds to run due to its iterative nature.
  
--------
## New in v1.1:
- **Adds**:
    - The application now supports course director assignments.
      - When a course director is designated, each algorithm ensures that they are prioritized in the matching process for their respective courses.
    - Genetic algorithm matching has been added.
    - Rearranged user interface for more intuitive interactions.

--------
## Running the Application

The code has been packaged into a simple GUI for ease of use. Simply drag and drop your instructor preferences, course availability, and then choose your algorithm.

To run the JobMatch GUI application, you can execute the `run_jobmatch_app.py` script located in the `gui` directory:

```bash
poetry run python gui/run_jobmatch_app.py
```

If you're not using Poetry, ensure that all dependencies are installed (e.g., using pip), and then run the application with:

```bash
python gui/run_jobmatch_app.py
```
