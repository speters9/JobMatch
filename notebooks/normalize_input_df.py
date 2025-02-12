"""
Take in survey results and normalize to standard format
Output:
- instructors_with_preferences.csv (Overall preferences)
- instructors_with_course_preferences.csv (class preferences specifically)
- instructors_with_period_preferences.csv (teaching period preferences specifically)
"""


# %%
import re

import pandas as pd
from pyprojroot.here import here

from jobmatch.class_data import instructor_max
from jobmatch.preprocessing import get_ordered_preferences

wd = here()

#%%


################## Load and Standardize Preferences Data ##################


#%%

def clean_column_name(col):
    """Clean column names for consistency."""
    # Rename core class selection
    if "core PolSci classes" in col:
        return "core_class"

    # Rename summer teaching interest
    if "summer" in col:
        return "summer_interest"

    # Rename name and email fields
    if "enter your name" in col:
        return "name"
    if "enter your email" in col:
        return "email"

    # Rename timestamp
    if "Timestamp" in col:
        return "time"

    # Rename additional information and excluded classes
    if "additional" in col:
        return "additional_info"
    if "do NOT want to teach" in col:
        return "exclude"

    # Rename class preferences dynamically (e.g., "Class Preferences [PolSci 211: ...]" → "PS211")
    match = re.search(r'\[(PolSci|SocSci) (\d+[A-Z]*)', col)
    if match:
        prefix = "PS" if match.group(1) == "PolSci" else "SS"
        return f"{prefix}{match.group(2)}"

    # Rename teaching periods dynamically (e.g., "Preferred Teaching Periods [1st period]" → "period_1")
    match = re.search(r'Preferred Teaching Periods \[(\d+)[a-z]* period\]', col)
    if match:
        return f"period_{match.group(1)}"

    # Default: return the original column name
    return col


#%%

# load preferences df and order by instructor importance
pref_df = pd.read_csv(wd / "data/02_raw/course_time_preferences_raw.csv")

# rename columns
clean_column_names_dict = {col: clean_column_name(col) for col in pref_df.columns}
pref_df = pref_df.rename(columns=clean_column_names_dict)

# standardize class names
pref_df['core_class'] = pref_df['core_class'].replace({'PolSci ': 'PS',
                                                       'SocSci ': 'SS'}, regex=True)


# add all known instructors to the preference df
pref_df = pref_df.set_index('name')
pref_df = pref_df.reindex(instructor_max.keys()).reset_index()


# %%


################## Parse Preferences ##################


#%%

# get individual preferences from free response, add in core preferences last, if not included.
# **Courses will change by semester**
courses_available = [val for val in clean_column_names_dict.values() if "PS" in val or "SS" in val]

pref_df['ordered_classes'] = pref_df.apply(
    lambda row: get_ordered_preferences(row, courses=courses_available), axis=1)


individuals = {}
for person in pref_df.itertuples():
    name = person.name
    core_class = person.core_class if person.core_class else 'PS211'
    prefs = person.ordered_classes if person.ordered_classes else []
    if prefs:
        prefs.append(core_class) if not core_class in prefs else None

    individuals[name] = {
        'name': name,
        'core_class': core_class,
        'preferences': prefs
    }


# %%

# Convert the dictionary into a DataFrame with preferences as columns
# Find the maximum number of preferences
max_prefs = max(len(ind.get('preferences')) for ind in individuals.values())
preferences_df = pd.DataFrame.from_dict(
        # pad missing preferences with None
        {name: ind["preferences"] + [None] * \
        (max_prefs - len(ind["preferences"])) for name, ind in individuals.items()},
        orient='index',
        # add preference columns
        columns=[f'pref_{i+1}' for i in range(max_prefs)]
    ).reset_index().rename(columns={'index': 'name'})

# %%


############## Merge preferences with instructor data ##################



#%%
# load additional instructor data
inst_df = pd.read_csv(wd / "data/00_reference/instructor_info.csv")

inst_df.columns = [col.lower() for col in inst_df.columns]
pref_df.columns = [col.lower() for col in pref_df.columns]

# merge preferences and additional instructor data (eg courses available to teach, degree)
intial_merge = pref_df.merge(inst_df, on = 'name', how = 'left')
merged_df = intial_merge.merge(preferences_df, on = 'name', how = 'left')

merged_df['pref_1'] = merged_df[['lose_gain', 'pref_1']].apply(
    lambda x: 'PS211' if x['lose_gain'] == "+" else x['pref_1'], axis=1)


# %%


################## Separate Course from Teaching Period Preferences ##################



#%%


# separate period prefernces from class preferences
replace_dict = {
    'Preferred': 1,
    'Neutral': 0,
    'Not Preferred': -1
}

period_cols = ['time', 'name', 'email', 'core_class', 'summer_interest',
               'period_1', 'period_2', 'period_3', 'period_4', 'period_5', 'period_6',
               'additional_info', 'exclude'
               ]

for col in period_cols:
    if col.startswith('period'):
        merged_df[col] = merged_df[col].str.strip().replace(replace_dict)
period_df = merged_df[period_cols]


course_prefs_list = [f'pref_{i+1}' for i in range(max_prefs)]
class_cols = ['time', 'name', 'email', 'core_class', 'max_classes', 'degree',
              'summer_interest', *course_prefs_list, 'additional_info', 'exclude']
class_df = merged_df[class_cols]


# %%
merged_df.to_csv(
    wd / "data/03_processed/instructors_with_preferences.csv", index=False)

class_df.to_csv(
    wd / "data/03_processed/instructors_with_course_preferences.csv", index=False)

period_df.to_csv(
    wd / "data/03_processed/instructors_with_period_preferences.csv", index=False)

# %%
