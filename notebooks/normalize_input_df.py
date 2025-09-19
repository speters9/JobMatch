"""
Take in survey results and normalize to standard format
Output:
- instructors_with_preferences.csv (Overall preferences)
- instructors_with_course_preferences.csv (class preferences specifically)
- instructors_with_period_preferences.csv (teaching period preferences specifically)
"""


# %%
import re
import shutil

import pandas as pd
from pyprojroot.here import here

from jobmatch.class_data import instructor_max
from jobmatch.preprocessing import get_ordered_preferences

wd = here()

#%%


################## Load and Standardize Preferences Data ##################


#%%
# rename period columns to standard format period_1, period_2, etc.
def rename_period_columns(col):
    match = re.search(r'\[(\d+)[a-z]{2} period\]', col)
    if match:
        num = match.group(1)
        return f'period_{num}'
    return col


def clean_column_name(col):
    """Clean column names for consistency. Don't make all lowercase--classes need caps."""
    col = col.strip()
    # Rename core class selection
    if "core polsci classes" in col.lower():
        return "core_class"

    # Rename summer teaching interest
    if "summer" in col.lower():
        return "summer_interest"

    # Rename name and email fields
    if "enter your name" in col:
        return "name"
    if "enter your email" in col or "email address" in col.lower():
        return "email"

    # Rename timestamp
    if "timestamp" in col.lower():
        return "time"

    if "period" in col.lower():
        return rename_period_columns(col)

    # Rename additional information and excluded classes
    if "classroom preferences" in col.lower():
        return "classroom_preferences"
    if "additional" in col.lower():
        return "additional_info"
    if "do not want to teach" in col.lower():
        return "exclude"

    # Rename class preferences dynamically (e.g., "Class Preferences [PolSci 211: ...]" → "PS211")
    match = re.search(r'\[(PolSci|SocSci|FAS) (\d+[A-Z]*)', col)
    if match:
        prefix = "PS" if match.group(1) == "PolSci" else "SS" if match.group(1) == "SocSci" else "FAS"
        return f"{prefix}{match.group(2)}"

    # Rename teaching periods dynamically (e.g., "Preferred Teaching Periods [1st period]" → "period_1")
    match = re.search(r'Preferred Teaching Periods \[(\d+)[a-z]* period\]', col)
    if match:
        return f"period_{match.group(1)}"

    # Default: return the original column name
    return col


#%%

# load preferences df and order by instructor importance
pref_df = pd.read_excel(wd / "data/02_raw/course_time_preferences_raw_spring26.xlsx")

# rename columns
clean_column_names_dict = {col: clean_column_name(col) for col in pref_df.columns}
pref_df = pref_df.rename(columns=clean_column_names_dict)

# standardize names
pref_df['name'] = pref_df['name'].str.strip().str.title()
pref_df['core_class'] = pref_df['core_class'].replace({'PolSci ': 'PS',
                                                       'SocSci ': 'SS'}, regex=True)


# %%


################## Parse Preferences ##################


#%%

# get individual preferences from free response, add in core preferences last, if not included.
# **Courses will change by semester**
courses_available = [val for val in clean_column_names_dict.values() if "PS" in val or "SS" in val or "FAS" in val]

pref_df['ordered_classes'] = pref_df.apply(
    lambda row: get_ordered_preferences(row, courses=courses_available), axis=1)


individuals = {}
for person in pref_df.itertuples():
    name = person.name
    core_class = person.core_class if person.core_class else 'PS211'
    prefs = person.ordered_classes if person.ordered_classes else []
    if prefs:
        prefs.append(core_class) if not core_class in prefs else None
    else:
        prefs = [core_class]

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
inst_df = pd.read_csv(
    wd / "data/00_reference/instructor_info.csv", encoding='latin1')
inst_df['name'] = inst_df['name'].str.strip().str.title()


inst_df.columns = [col.lower() for col in inst_df.columns]
pref_df.columns = [col.lower() for col in pref_df.columns]

# merge preferences and additional instructor data (eg courses available to teach, degree)
# Outer join to keep both sets of data
intial_merge = pref_df.merge(inst_df, on='name', how='outer')
merged_df = intial_merge.merge(preferences_df, on='name', how='outer', )

merged_df['pref_1'] = merged_df[['lose_gain', 'time', 'pref_1']].apply(
    lambda x: 'PS211'
    if (x['lose_gain'] == "+" or pd.isna(x['time']))
    else x['pref_1'], axis=1)

# order by preceferred priority
name_order = inst_df['name'].tolist()
merged_df['name'] = pd.Categorical(merged_df['name'], categories=name_order, ordered=True)
merged_df = merged_df.sort_values('name').reset_index(drop=True)
# %%


################## Separate Course from Teaching Period Preferences ##################





#%%

# separate period prefernces from class preferences
replace_dict = {
    'Preferred': 1,
    'Neutral': 0,
    'Not Preferred': -1,
    'nan': 0,
}

period_cols = ['time', 'name', 'email', 'core_class',
               'period_1', 'period_2', 'period_3', 'period_4', 'period_5', 'period_6',
               'additional_info', 'exclude'
               ]
period_df = merged_df.copy()
for col in period_cols:
    if col.startswith('period'):
        period_df[col] = (
            period_df[col].astype(str)
            .str.strip()
            .replace(replace_dict)
            .infer_objects(copy=False)
            .replace(['', 'nan'], 0)
            .fillna(0)
        )
period_df = period_df[period_cols]


course_prefs_list = [f'pref_{i+1}' for i in range(max_prefs)]
class_cols = ['time', 'name', 'email', 'core_class', 'max_classes', 'degree',
               *course_prefs_list, 'additional_info', 'exclude', 'notes']
class_df = merged_df[class_cols]
class_df = class_df.loc[class_df['max_classes'] > 0].reset_index(drop=True)


# %%
merged_df.to_csv(
    wd / "data/03_processed/instructors_with_preferences_full.csv", index=False)

class_df.to_csv(
    wd / "data/03_processed/instructors_with_course_preferences.csv", index=False)

period_df.to_csv(
    wd / "data/03_processed/instructors_with_period_preferences.csv", index=False)

# ensure course data (if modified) is available for the next step
shutil.copy(wd / "data/00_reference/course_data.csv",
            wd / "data/03_processed/course_data_with_course_directors.csv")


# %%
