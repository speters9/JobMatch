from pprint import pprint

import pandas as pd
# set wd
from pyprojroot.here import here

from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                 course_slots, instructor_max)
from jobmatch.global_functions import set_all_seeds
from jobmatch.JobMatch import JobMatch
from jobmatch.preprocessing import (build_courses, build_instructors,
                                    parse_preferences)

wd = here()

#%%
# load preferences df and order by instructor importance
pref_df = pd.read_excel(wd/ "data/raw/Teaching_Preferences_cao21Aug.xlsx")
pref_df = pref_df.set_index('Name')
pref_df = pref_df.reindex(instructor_max.keys()).reset_index()

course_df = pd.read_csv(wd / "data/raw/course_data.csv")
inst_df = pd.read_csv(wd / "data/raw/instructor_info.csv")

# get individual preferences from free response, add in core preferences last, if not included
individuals = {}
for item in pref_df.itertuples():
    name = item[1]
    core_class = core_dict.get(item[6], 'PS211')
    prefs = item[7]
    if not pd.isna(prefs):
        individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
    else:
        continue

instructor_list = build_instructors(inst_df,individuals)
course_list = build_courses(course_df)


set_all_seeds(94305)
#%%
# Create a solver factory
factory = JobMatch(instructor_list, course_list)

# Solve using the bipartite matching approach
print("Test on real preferences: Bipartite graph\n")
matches_bipartite = factory.solve(method='bipartite_matching', instructor_weighted=False)
# bipartite returns a tuple of (instructor:class, instructor:rank, nx.Graph)
factory.print_match_results(matches_bipartite[0])
print("")

# Solve using the stable marriage approach
print("Test on real preferences: stable marriage\n")
matches_stable = factory.solve(method='stable_marriage')
# stable marriage returns a tuple of (instructor:class, class:instructor)
factory.print_match_results(matches_stable[0])
print("")

# Solve using linear programming
print("Test on real preferences: linear programming\n")
matches_lp = factory.solve(method='linear_programming', lp_method='default')
factory.print_match_results(matches_lp[0])
print("")
