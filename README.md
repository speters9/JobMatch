# JobMatch

[![CCDS Project template](https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter)](https://cookiecutter-data-science.drivendata.org/)

## Overview

The JobMatch project provides a flexible and modular approach to solving individual and job assignment problems using various optimization strategies, including stable marriage, bipartite graph matching, and linear programming. It is designed to match instructors to courses based on their preferences, course capacities, and other potential constraints. By a process of iterative matching, each algorithm is structured to allow for matching to more than one assignment per instructor.


## Project Organization

```
├── LICENSE            <- Open-source license
├── README.md          <- The top-level README for developers using this project.
|
├── data               <- Repository for raw matching preferences (not included here)
|
├── docs               <- Mkdocs for sphinx-generated documentation
│
├── models             <- Trained and serialized models, model predictions, or model summaries (None included yet)
│
├── notebooks          <- Includes base implementation.
│
└── jobmatch           <- Source code for use in this project.
    │
    ├── JobMatch.py             <- Factory implementation of JobMatch class, a factory for calling the various algorithms.
    │
    ├── bipartite_graph_match.py               <- Code for bipartite matching
    │
    ├── linear_program_optimization.py         <- Code for matching via linear program optimization
    │
    ├── stable_marriage.py      <- Code for matching using stable marriage
    │
    ├── preprocessing.py        <- Code for parsing input preferences and preprocessing for passing to the matching algorithms
    |
    └── global_functions.py     <- Code with general utility functions

```

--------
## Key Components

- **JobMatch Class**: The core class that integrates the different solving methods (stable marriage, bipartite matching, linear programming) and provides a unified interface for running the course assignment process.

- **Iterative Bipartite Matching & Iterative Linear Programming:**
    - These algorithms optimize for instructor preferences while iteratively matching instructors with courses.
    - Greedy matching is employed, where if an instructor is matched with a section, the algorithm will attempt to assign additional sections of the same course until the instructor's maximum sections or course capacity is reached.
    - No instructor is assigned more than two unique courses.
    - The algorithms iterate through all instructors and courses until no more matches can be made, leading to convergence.
  
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

## Usage

To use the `JobMatch` class, initialize it with a user-provided:
     - Dict of instructors and their list of preferences, 
     - A dict of instructors and their maximum section load, and 
     - A dict of courses and their respective number of sections available.
         - A full pipeline includes importing a csv of raw text preferences, and then converting to the above `Dict[str, list]` (in the `preprocessing` module); but those can be manually input to bypass a step.

You can then choose from one of the supported methods (`stable_marriage`, `bipartite_matching`, `linear_programming`) to solve the assignment problem. 

Dependencies are managed by poetry, so `poetry install` with `pyproject.toml` file should get you going.
