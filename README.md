# JobMatch

[![CCDS Project template](https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter)](https://cookiecutter-data-science.drivendata.org/)

Putting faces in spaces

## Overview

The JobMatch project provides a flexible and modular approach to solving course assignment problems using various optimization strategies, including stable marriage, bipartite graph matching, and linear programming. It is designed to match instructors to courses based on their preferences, course capacities, and other potential constraints. By a process of iterative matching, each algorithm is structured to allow for matching to more than one assignment per instructor.


## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         jobmatch and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── jobmatch   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes jobmatch a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------
## Key Components

- **JobMatch Class**: The core class that integrates the different solving methods (stable marriage, bipartite matching, linear programming) and provides a unified interface for running the course assignment process.
- **Stable Marriage Solver**: Implements the stable marriage algorithm to ensure no instructor-course pair would prefer to be assigned to each other over their current assignment.
- **Bipartite Matching Solver**: Uses bipartite graph matching to optimally assign instructors to courses based on preferences, with optional weighting for instructor seniority.
- **Linear Programming Solver**: Applies linear programming techniques to solve the course assignment problem, offering different methods including default, perturbation, and multi-objective optimization.
- **Preprocessing**: Functions for standardizing and parsing input data, ensuring consistency across the various solving methods.

## Usage

To use the `JobMatch` class, initialize it with the list of instructors and their preferences, along with the course capacities. You can then choose from one of the supported methods (`stable_marriage`, `bipartite_matching`, `linear_programming`) to solve the assignment problem.
