from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

def annotate_tf_idf(conc, **args) -> pd.Series:
    """
    Compute a TF-IDF vector for every concordance line (or for the selected
    token window around the node).

    Tokens whose ``offset`` lies in ``[window_start, window_end]`` are joined
    into a single text string per line; optional filters allow the exclusion of
    particular token values.  A corpus-wide vocabulary is built from these
    texts, and scikit-learn’s ``TfidfVectorizer`` returns one TF-IDF vector per
    line.

    Parameters
    ----------
    tokens_attribute : str, optional
        Token-attribute column used to build each line’s text
        (default ``"word"``).
    exclude_values_attribute : str | None, optional
        Token-attribute column whose values are checked against
        ``exclude_values_list`` to filter out unwanted tokens (default
        ``None`` – no filtering).
    exclude_values_list : list[str] | None, optional
        List of values to exclude when ``exclude_values_attribute`` is given
        (default ``None``).
    window_start : int, optional
        Lower bound of the offset window (inclusive, default ``-5``).
    window_end : int, optional
        Upper bound of the offset window (inclusive, default ``5``).
    include_node : bool, optional
        If *True*, include the node token (offset ``0``) in the window
        (default ``True``).

    Returns
    -------
    pandas.Series
        Series indexed by concordance line IDs; each element is a 1-D NumPy
        array containing the TF-IDF weights for that line.  The length of every
        array equals the size of the learned vocabulary.

    Notes
    -----
    * Vectors are stored in dense format.  For large concordances, consider
      keeping them in sparse form instead.
    * Offsets follow the FlexiConc convention where the node token has
      ``offset == 0``.
    """

    # Metadata for the algorithm
    annotate_tf_idf._algorithm_metadata = {
        "name": "Annotate with TF-IDF",
        "description": "Computes TF-IDF vectors for each line based on tokens in a specified window.",
        "algorithm_type": "annotation",
        "scope": "line",
        "requires": ["scikit_learn>=1.3.0"],
        "args_schema": {
            "type": "object",
            "properties": {
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token attribute to use for creating line texts.",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "exclude_values_attribute": {
                    "type": ["string"],
                    "description": "The attribute to filter out specific values."
                },
                "exclude_values_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The list of values to exclude."
                },
                "window_start": {
                    "type": "integer",
                    "description": "The lower bound of the token window (inclusive).",
                    "default": -5,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']))"
                },
                "window_end": {
                    "type": "integer",
                    "description": "The upper bound of the token window (inclusive).",
                    "default": 5,
                    "x-eval": "dict(maximum=max(conc.tokens['offset']))"
                },
                "include_node": {
                    "type": "boolean",
                    "description": "Whether to include the node token (offset 0).",
                    "default": True
                }
            },
            "required": []
        }
    }

    # Extract arguments
    tokens_attribute = args.get("tokens_attribute", "word")
    exclude_values_attribute = args.get("exclude_values_attribute", None)
    exclude_values_list = args.get("exclude_values_list", None)
    window_start = args.get("window_start", -5)
    window_end = args.get("window_end", 5)
    include_node = args.get("include_node", True)

    # Extract lines
    subset_tokens = conc.tokens[
        (conc.tokens['offset'] >= window_start) & (conc.tokens['offset'] <= window_end)
    ]
    if not include_node:
        subset_tokens = subset_tokens[subset_tokens['offset'] != 0]
    if exclude_values_attribute and exclude_values_list:
        subset_tokens = subset_tokens[~subset_tokens[exclude_values_attribute].isin(exclude_values_list)]

    # Group tokens by line_id
    lines = subset_tokens.groupby('line_id')[tokens_attribute].apply(lambda x: ' '.join(x))
    line_ids = lines.index.tolist()

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(lines)

    # Convert the sparse matrix to a list of dense vectors
    tf_idf_vectors = [X[i].toarray()[0] for i in range(X.shape[0])]

    # Create a Pandas Series indexed by line IDs
    tf_idf_series = pd.Series(data=tf_idf_vectors, index=line_ids, name="data")

    return tf_idf_series