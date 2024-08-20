from pprint import pprint

import pandas as pd
# set wd
from pyprojroot.here import here

from jobmatch.class_data import (course_id_map, course_map, course_slots,
                                 instructor_max)
from jobmatch.global_functions import set_all_seeds
from jobmatch.JobMatch import JobMatch
from jobmatch.preprocessing import parse_preferences

wd = here()

# %%
# load preferences df and order by instructor importance
pref_df = pd.read_excel(wd / "data/raw/Teaching_Preferences_cao18Aug.xlsx")
pref_df = pref_df.set_index('Name')
pref_df = pref_df.reindex(instructor_max.keys()).reset_index()


# %%
# convert class identifiers from form format to standard format
core_dict = {
    'PolSci 211': 'PS211',
    'SocSci 311': 'SocSci311',
}

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


pprint(individuals)


# %%
set_all_seeds(94305)
# Reinitialize factory with each iteration to ensure there is no data leakage

# Create a solver factory
factory = JobMatch(individuals, course_slots, instructor_max)
# Solve using the bipartite matching approach
print("Test on real preferences: Bipartite graph\n")
matches_bipartite = factory.solve(method='bipartite_matching', instructor_weighted=True)
rankings = factory.get_match_ranks(matches_bipartite[0])  # bipartite returns a tuple of (instructor:class, instructor:rank, nx.Graph)
factory.print_match_results(rankings)
print("")


# Solve using the stable marriage approach
print("Test on real preferences: stable marriage\n")
matches_stable = factory.solve(method='stable_marriage')
rankings = factory.get_match_ranks(matches_stable[0])  # stable marriage returns a tuple of (instructor:class, class:instructor)
factory.print_match_results(rankings)
print("")


# Solve using linear programming
print("Test on real preferences: linear programming\n")
matches_lp = factory.solve(method='linear_programming', lp_method='default')
rankings = factory.get_match_ranks(matches_lp[0])
factory.print_match_results(rankings)
print("")
