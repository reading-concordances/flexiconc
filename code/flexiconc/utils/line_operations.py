import pandas as pd


def extract_words_at_offset(tokens_df, p='word', offset=0):
    """
    Extracts words from a DataFrame of tokens at a specified offset for each line_id.
    If a line_id has no match, an empty string is returned.
    If there are multiple matches for a line_id, they are joined by a space.

    Parameters:
    ----------
    tokens_df : pandas.DataFrame
        DataFrame containing token information with columns 'line_id', 'offset0', and the specified attribute 'p'.
    p : str, optional (default='word')
        Column name in tokens_df from which to extract values.
    offset : int, optional (default=0)
        Offset value to filter tokens_df.

    Returns:
    -------
    list
        List of extracted values from the 'p' column at the specified 'offset', with missing matches filled with ''.
    """
    # Filter the DataFrame for rows where 'offset0' equals the given offset
    filtered_df = tokens_df[tokens_df['offset'] == offset][['line_id', p]]

    # Group by line_id and join multiple matches by a space
    grouped = filtered_df.groupby('line_id')[p].apply(lambda x: ' '.join(x))

    # Get all unique line_ids in ascending order
    all_line_ids = sorted(tokens_df['line_id'].unique())

    # Return a list where each entry corresponds to a line_id
    # If a line_id is missing, return an empty string
    result = [grouped.get(line_id, '') for line_id in all_line_ids]

    return result



def isalpha_extended(s, extensions='-'):
    return all(c.isalpha() or c in extensions for c in s)
