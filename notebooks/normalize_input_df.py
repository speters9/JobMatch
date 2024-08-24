
import pandas as pd
# set wd
from pyprojroot.here import here

from jobmatch.class_data import (core_dict, course_id_map, course_map,
                                 instructor_max)
from jobmatch.preprocessing import parse_preferences

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
    core_class = core_dict.get(item[6], 'PS211' if not item[0]==0 else item[7])
    prefs = item[7]
    if not pd.isna(prefs):
        individuals[name] = parse_preferences(prefs, course_id_map, course_map, core_class)
    else:
        continue


# Convert the dictionary into a DataFrame with preferences as columns
max_prefs = max(len(prefs) for prefs in individuals.values())  # Find the maximum number of preferences
preferences_df = (pd.DataFrame.from_dict(
            individuals, orient='index', columns=[f'pref_{i+1}' for i in range(max_prefs)]
            )
            .reset_index()
            .rename(columns = {'index': 'name'}))


inst_df.columns = [col.lower() for col in inst_df.columns]
pref_df.columns = [col.lower() for col in pref_df.columns]
intial_merge = pref_df.merge(inst_df, on = 'name', how = 'left')
merged_df = intial_merge.merge(preferences_df, on = 'name', how = 'left')
merged_df.to_csv(wd / "data/processed/instructors_with_preferences.csv", index=False)
