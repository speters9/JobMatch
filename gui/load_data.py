import re

import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the column names of the DataFrame by converting them to lowercase,
    replacing spaces with underscores, and removing any leading/trailing whitespace.

    Args:
        df (pd.DataFrame): The DataFrame with raw column names.

    Returns:
        pd.DataFrame: The DataFrame with normalized column names.
    """
    df.columns = (
        df.columns.str.strip()  # Remove leading/trailing whitespace
        .str.lower()            # Convert to lowercase
        .str.replace(r'\s+', '_', regex=True)  # Replace spaces with underscores
        .str.replace(r'[^a-z0-9_]', '', regex=True)  # Remove non-alphanumeric characters
    )
    return df

def extract_preferences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and organize preference columns based on the numeric suffix, inferring their order.

    Args:
        df (pd.DataFrame): The DataFrame with normalized column names.

    Returns:
        pd.DataFrame: The original DataFrame with preference columns grouped and ordered.
    """
    preference_columns = [col for col in df.columns if re.search(r'_\d+$', col)]

    # Sort the preference columns by the numeric suffix
    preference_columns_sorted = sorted(preference_columns, key=lambda x: int(re.search(r'\d+$', x).group()))

    # Extract the relevant preference columns
    preferences_df = df[preference_columns_sorted]

    # Return DataFrame with the original data along with the sorted preferences
    non_preference_columns = [col for col in df.columns if col not in preference_columns]
    df_ordered = df[non_preference_columns].copy()
    df_ordered = pd.concat([df_ordered, preferences_df], axis=1)

    return df_ordered

def load_and_process_data(file_path: str) -> pd.DataFrame:
    """
    Load data from an Excel or CSV file, normalize the column names, and extract preferences.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        pd.DataFrame: The processed DataFrame with normalized column names and organized preferences.
    """
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

    # Normalize column names
    df = normalize_column_names(df)

    # Extract and organize preferences
    df = extract_preferences(df)

    return df


if __name__ == "__main__":
    # set wd
    from pyprojroot.here import here

    wd = here()

    # Example file path
    file_path = wd / 'data/processed/instructors_with_preferences.csv'

    # Load and process the data
    df = load_and_process_data(str(file_path))

    # Display the processed DataFrame
    print(df.head())
