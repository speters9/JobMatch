from collections import Counter

import pandas as pd
from pyprojroot.here import here

wd = here()
pd.set_option('display.max_columns', None)


# %%
# df  = pd.read_excel(wd / "data/validate/revised_instructor_matches.xlsx")
# instr_matches = df['Assigned Courses'].str.split(", ", expand = True)

# instr_matches = df.join(instr_matches)

# instr_matches.to_excel(wd / "data/validate/revised_instructor_matches.xlsx", index= False)
# %%
course_df = pd.read_csv(wd / "data/validate/course_data.csv")
inst_df = pd.read_csv(wd / "data/validate/instructors_with_preferences.csv")


# load current working matches
df = pd.read_excel(wd / "data/validate/revised_instructor_matches.xlsx")

# create counter of current matches
assignments = pd.melt(df[['class_1', 'class_2', 'class_3']]).dropna(subset=['value'])
assignment_count = Counter(assignments['value'])

# validate that all course sections are covered
course_df['sections_assigned'] = course_df['course_name'].apply(lambda x: assignment_count.get(x, 0))
course_df['covered'] = course_df.apply(lambda row: row['sections_assigned'] == row['sections_available'], axis=1)
course_df = course_df.rename(columns = {'course_name': 'course',
                                        'sections_available': 'sections_required'})


cols_to_display = ['course', 'sections_required', 'sections_assigned', 'covered']
assert (~course_df['covered']).sum(
) == 0, f"Missing courses: {(~course_df['covered']).sum() - 1}\n{course_df[~course_df['covered']][cols_to_display]}"


print("All sections covered!")
if any(course_df['sections_assigned'] == 0):
    print(
        f"Note: Some courses have no assignment: \n{course_df[course_df['sections_assigned'] == 0][cols_to_display]}")


#%%

melted_df = df.melt(id_vars=['Name'], value_vars=['class_1', 'class_2', 'class_3'],
                    var_name='course_col', value_name='course')

course_instructors_df = melted_df.groupby('course')['Name'].apply(lambda x: ', '.join(sorted(x))).reset_index()
course_instructors_df.columns = ['course', 'instructors']


course_instructors_df = course_df.merge(course_instructors_df, on = 'course', how = "left")

col_order = ['course', 'course_id', 'course_description', 'students', 'sections_required',
             'sections_assigned', 'covered', 'instructors']
course_instructors_df = course_instructors_df[col_order]



df = df.drop(['Assigned Courses', 'Ranks'], axis =1)

#%%
course_instructors_df.to_excel(wd / "data/validate/revised_course_matches.xlsx", index= False)

df.to_excel(wd / "data/validate/working_instructor_matches.xlsx", index= False)
