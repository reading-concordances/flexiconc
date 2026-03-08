import spacy
import numpy as np
import pandas as pd

def annotate_spacy_embeddings(conc, **args) -> pd.Series:
    """
    Generate averaged spaCy embeddings for every concordance line (or for the
    selected token window around the node).

    For each line, all tokens whose ``offset`` lies in the interval
    ``[window_start, window_end]`` are collected (optionally excluding the node
    and/or specific token values), their spaCy vectors are averaged, and the
    resulting embedding is returned in a Series indexed by ``line_id``.

    Parameters
    ----------
    spacy_model : str, optional
        Name of the spaCy pipeline that contains word vectors
        (default ``"en_core_web_md"``).
    tokens_attribute : str, optional
        Token-attribute column used to build the text of each line
        (default ``"word"``).
    exclude_values_attribute : str | None, optional
        Token-attribute column that will be checked against
        ``exclude_values_list`` to filter out unwanted tokens
        (default ``None`` – no filtering).
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
        Series indexed by concordance line IDs; each element is a NumPy array
        representing the mean spaCy vector for that line.
    """


    # Metadata for the algorithm
    annotate_spacy_embeddings._algorithm_metadata = {
        "name": "Annotate with SpaCy Embeddings",
        "description": "Generates averaged spaCy word embeddings for tokens within a specified window.",
        "algorithm_type": "annotation",
        "scope": "line",
        "requires": ["spacy>=3.8.4"],
        "args_schema": {
            "type": "object",
            "properties": {
                "spacy_model": {
                    "type": "string",
                    "description": "The spaCy model to use.",
                    "default": "en_core_web_md"
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token attribute to use for creating line texts.",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "exclude_values_attribute": {
                    "type": "string",
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
            "required": ["spacy_model"]
        }
    }

    # Extract arguments
    spacy_model = args.get("spacy_model", "en_core_web_md")
    tokens_attribute = args.get("tokens_attribute", "word")
    exclude_values_attribute = args.get("exclude_values_attribute", None)
    exclude_values_list = args.get("exclude_values_list", None)
    window_start = args.get("window_start", -5)
    window_end = args.get("window_end", 5)
    include_node = args.get("include_node", True)

    # Load the spaCy model
    nlp = spacy.load(spacy_model)

    # Filter tokens
    subset_tokens = conc.tokens[
        (conc.tokens['offset'] >= window_start) & (conc.tokens['offset'] <= window_end)
    ]
    if not include_node:
        subset_tokens = subset_tokens[subset_tokens['offset'] != 0]
    if exclude_values_attribute and exclude_values_list:
        subset_tokens = subset_tokens[~subset_tokens[exclude_values_attribute].isin(exclude_values_list)]

    # Group tokens by line_id and create text representations
    lines = subset_tokens.groupby('line_id')[tokens_attribute].apply(lambda x: ' '.join(x))
    line_ids = lines.index.tolist()

    # Compute embeddings by averaging token vectors
    embeddings = []
    for text in lines:
        doc = nlp(text)
        if len(doc) > 0:
            vec = doc.vector
        else:
            vec = np.zeros(nlp.meta['vectors']['width'], dtype=np.float32)
        embeddings.append(vec)

    # Convert embeddings to a Pandas Series indexed by line IDs
    embeddings_series = pd.Series(data=list(embeddings), index=line_ids, name="embeddings_spacy")

    return embeddings_series
