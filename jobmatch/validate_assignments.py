from pprint import pprint

import pandas as pd
from pyprojroot.here import here

from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                 course_slots, instructor_max)
from jobmatch.preprocessing import (build_courses, build_instructors,
                                    create_preference_tuples,
                                    parse_preferences, print_matching_results)

wd = here()


#%%
course_df = pd.read_csv(wd / "data/validate/course_data.csv")
inst_df = pd.read_csv(wd / "data/validate/instructors_with_preferences.csv")




#%%
# df  = pd.read_excel(wd / "data/validate/revised_instructor_matches.xlsx")
# instr_matches = df['Assigned Courses'].str.split(", ", expand = True)

# instr_matches = df.join(instr_matches)

# instr_matches.to_excel(wd / "data/validate/revised_instructor_matches.xlsx", index= False)
#%%


df  = pd.read_excel(wd / "data/validate/revised_instructor_matches.xlsx")



#%%

# load preferences df and order by instructor importance
pref_df = pd.read_excel(wd / "data/raw/Teaching_Preferences_cao21Aug.xlsx")
pref_df = pref_df.set_index('Name')
pref_df = pref_df.reindex(instructor_max.keys()).reset_index()



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

instructor_list = build_instructors(inst_df, individuals)
course_list = build_courses(course_df)
