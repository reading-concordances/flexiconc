import pandas as pd

def annotate_concordance_frequency_list(conc, **args) -> dict:
    """
    Build a token-level frequency list for a Concordance (or ConcordanceSubset).

    Counts tokens within an optional offset window around the node and returns a
    **FlexiConc frequency-list resource** without registering it.  The caller can
    inspect, store, or register the returned dictionary manually.

    Parameters
    ----------
    token_attribute : str, optional
        Token-attribute column to count types for (default ``"word"``).
    window_start : int | None, optional
        Lower bound of the counting window (inclusive). ``None`` means
        unbounded towards the left (default ``None``).
    window_end : int | None, optional
        Upper bound of the counting window (inclusive). ``None`` means
        unbounded towards the right (default ``None``).
    include_node : bool, optional
        If *True*, include the node token (offset 0) in the window
        (default ``False``).

    Returns
    -------
    dict
        Resource dictionary ::

            {
                "type": "frequency_list",   # literal string
                "df": pandas.DataFrame,     # columns: <token_attribute>, "f"
                "sample_size": int,         # total tokens counted
                "info": { ... }             # copy of input args
            }

    Notes
    -----
    * The resulting DataFrame is sorted by absolute frequency ``f`` descending.
    * ``sample_size`` equals ``df["f"].sum()``.
    * Offsets follow FlexiConc convention where the node token has offset 0.
    """


    # ------------------------------------------------------------------ metadata
    annotate_concordance_frequency_list._algorithm_metadata = {
        "name": "Token-level Frequency List",
        "description": "Aggregates token frequencies within an optional window "
                       "and returns a FlexiConc frequency-list resource.",
        "algorithm_type": "annotation",
        "scope": "type",
        "args_schema": {
            "type": "object",
            "properties": {
                "token_attribute": {
                    "type": "string",
                    "description": "Token attribute to count types for.",
                    "default": "word",
                    "x-eval": (
                        "dict(enum=list(set(conc.tokens.columns) "
                        "- {'id_in_line', 'line_id', 'offset'}))"
                    ),
                },
                "window_start": {
                    "type": ["integer", "null"],
                    "description": "Lower bound of token window (inclusive). "
                                   "Null means unbounded.",
                    "default": None,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']))",
                },
                "window_end": {
                    "type": ["integer", "null"],
                    "description": "Upper bound of token window (inclusive). "
                                   "Null means unbounded.",
                    "default": None,
                    "x-eval": "dict(maximum=max(conc.tokens['offset']))",
                },
                "include_node": {
                    "type": "boolean",
                    "description": "Include the node token (offset 0) in the "
                                   "counting window.",
                    "default": False,
                },
            },
            "required": ["token_attribute"],
        },
    }

    # ------------------------------------------------------------------ extract args
    token_attr   = args.get("token_attribute", "word")
    win_start    = args.get("window_start")   # may be None
    win_end      = args.get("window_end")     # may be None
    include_node = args.get("include_node", False)

    # ------------------------------------------------------------------ select tokens
    tok_df = conc.tokens

    if win_start is not None or win_end is not None or not include_node:
        lo = win_start if win_start is not None else -float("inf")
        hi = win_end   if win_end   is not None else  float("inf")
        mask = (tok_df["offset"] >= lo) & (tok_df["offset"] <= hi)
        if not include_node:
            mask &= tok_df["offset"] != 0
        tok_df = tok_df.loc[mask]

    freq_df = (
        tok_df.groupby(token_attr, as_index=False)
              .size()
              .rename(columns={"size": "f"})
    )
    sample_size = int(freq_df["f"].sum())

    # ------------------------------------------------------------------ resource dict
    resource_dict = {
        "type": "frequency_list",
        "df": freq_df.sort_values("f", ascending=False).reset_index(drop=True),
        "sample_size": sample_size,
        "info": args,
    }
    return resource_dict
