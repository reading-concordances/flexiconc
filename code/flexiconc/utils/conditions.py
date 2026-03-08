def has_metadata_attributes(conc):
    """
    Check if the concordance object has metadata columns other than 'line_id'.

    :param conc: The concordance object.
    :return: True if there are metadata columns other than 'line_id', False otherwise.
    """
    return len(set(conc.metadata.columns) - {'line_id'}) > 0

def has_multiple_slots(conc):
    """
    Check if the concordance object has multiple slots.

    :param conc: The concordance object.
    :return: True if there are multiple slots, False otherwise.
    """
    return conc.matches['slot'].nunique() > 1 if 'slot' in conc.matches else False

def has_rank_keys(node):
    """
    Check if the node has rank keys.

    :param node: The node object.
    :return: True if the node has rank keys, False otherwise.
    """
    return hasattr(node, 'ordering_result') and 'rank_keys' in node.ordering_result and len(node.ordering_result['rank_keys']) > 0

def has_numeric_token_attributes(conc):
    """
    Check if the concordance object has numeric token attributes.

    :param conc: The concordance object.
    :return: True if there are numeric token attributes, False otherwise.
    """
    numeric_cols = conc.tokens.select_dtypes(include=['number']).columns
    excluded = {'id_in_line', 'line_id', 'offset'}
    return any(col not in excluded for col in numeric_cols)

def has_frequency_lists(conc):
    """
    Check if the concordance object has registered frequency lists.

    :param conc: The concordance object.
    :return: True if there are registered frequency lists, False otherwise.
    """
    return len(conc.resources.list('frequency_list')) > 0

def has_scores(conc):
    """
    Check if the concordance object has scores.

    :param conc: The concordance object.
    :return: True if there are scores, False otherwise.
    """
    return len(conc.resources.list('scores')) > 0

def has_embeddings(conc):
    """
    Check if the concordance object has embeddings.

    :param conc: The concordance object.
    :return: True if there is a column with embeddings, False otherwise.
    """

    import numbers

    for col in conc.metadata.columns:
        first_value = conc.metadata[col].dropna().iloc[0]  # skip NaNs/None
        if (
                hasattr(first_value, "__iter__")  # ① iterable
                and not isinstance(first_value, str)  # ② not str
                and all(isinstance(x, numbers.Number) for x in first_value)  # ③ numeric
        ):
            return True
    return False