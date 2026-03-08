import pandas as pd

def rank_by_collocations(conc, **args):
    """
    Rank concordance lines by the prominence of their collocates, measured with
    an association-score list.

    Collocate tokens whose association score is positive and—optionally—among
    the *top N* highest-scoring types are selected within a user-defined window.
    For every line, either the **sum** of these scores or the **count** of
    qualifying tokens is used as the ranking key.

    Parameters
    ----------
    scores_list : str
        Name of the *scores* resource registered in ``conc.resources``.
    token_attribute : str, optional
        Token-attribute column common to both the scores table and the
        concordance tokens (default ``"word"``).
    score_column : str, optional
        Numeric column in the scores table that holds the association measure
        (default ``"log_local_MI"``).
    top_n : int | None, optional
        If given, restrict collocates to the *top N* by *score_column*
        (default ``None`` – no restriction).
    method : {'sum', 'count'}, optional
        How to compute the ranking key: add up scores (**sum**) or simply count
        qualifying tokens (**count**) (default ``"sum"``).
    window_start : int | None, optional
        Lower bound of the token window (inclusive).  ``None`` means
        unbounded to the left (default ``None``).
    window_end : int | None, optional
        Upper bound of the token window (inclusive).  ``None`` means
        unbounded to the right (default ``None``).
    include_node : bool, optional
        If *True*, include the node token (offset 0) in the window
        (default ``False``).
    positive_filter : dict[str, list[str]], optional
        Include only tokens that match *any* of the attribute–value lists
        provided here (default ``{}`` – no filter).
    negative_filter : dict[str, list[str]], optional
        Exclude tokens that match *any* of the attribute–value lists provided
        here (default ``{}`` – no filter).

    Returns
    -------
    dict
        A dictionary compatible with FlexiConc’s ranking interface ::

            {
                "rank_keys": {line_id: float, ...},
                "token_spans": pandas.DataFrame[
                    "line_id",
                    "start_id_in_line",
                    "end_id_in_line",
                    "category",
                    "weight"
                ]
            }

    Notes
    -----
    * ``rank_keys`` maps every concordance line to its ranking value; lines
      with no qualifying collocates receive ``0``.
    * ``token_spans`` marks each selected collocate as a single-token span
      (``category == "COL"``) and stores its association score in the
      ``weight`` column.
    * Offsets follow the FlexiConc convention where the node token has
      ``offset == 0``.
    """


    rank_by_collocations._algorithm_metadata = {
        "name": "Collocation Ranker",
        "description": (
            "Ranks lines by the sum (or count) of association-measure "
            "scores within a window."
        ),
        "algorithm_type": "ranking",
        "conditions": {"x-eval": "has_scores(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "scores_list": {
                    "type": "string",
                    "description": "Name of a *scores* resource registered in "
                                   "`conc.resources`.",
                    "x-eval": "dict(enum=conc.resources.list('scores'))",
                },
                "token_attribute": {
                    "type": "string",
                    "description": "Token attribute shared by the scores table "
                                   "and the concordance tokens.",
                    "default": "word",
                    "x-eval": (
                        "dict(enum=list(set(conc.tokens.columns) "
                        "- {'id_in_line', 'line_id', 'offset'}))"
                    ),
                },
                "score_column": {
                    "type": "string",
                    "description": "Numeric column in the scores table to use.",
                    "default": "log_local_MI",
                },
                "top_n": {
                    "type": ["integer", "null"],
                    "description": "Number of top collocates to take into account.",
                    "default": None
                },
                "method": {
                    "type": "string",
                    "enum": ["sum", "count"],
                    "description": "'sum' = add up scores, 'count' = count "
                                   "top-N collocates.",
                    "default": "sum",
                },
                "window_start": {
                    "type": ["integer", "null"],
                    "description": "Lower bound of token window (inclusive).",
                    "default": None,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']))",
                },
                "window_end": {
                    "type": ["integer", "null"],
                    "description": "Upper bound of token window (inclusive).",
                    "default": None,
                    "x-eval": "dict(maximum=max(conc.tokens['offset']))",
                },
                "positive_filter": {
                    "type": "object",
                    "description": "Only include tokens matching these {attribute: [values]} pairs.",
                },
                "negative_filter": {
                    "type": "object",
                    "description": "Exclude tokens matching these {attribute: [values]} pairs.",
                },
                "include_node": {
                    "type": "boolean",
                    "description": "Include the node token (offset 0) in the window.",
                    "default": False,
                }
            },
            "required": ["scores_list"],
        },
    }

    # ------------------------------------------------------------------ args
    scores_name     = args["scores_list"]
    token_attr      = args.get("token_attribute", "word")
    score_col       = args.get("score_column", "log_local_MI")
    top_n           = args.get("top_n", None)
    method          = args.get("method", "sum")
    win_start       = args.get("window_start")
    win_end         = args.get("window_end")
    include_node    = args.get("include_node", False)
    positive_filter = args.get("positive_filter", {})
    negative_filter = args.get("negative_filter", {})

    # fetch + trim scores
    scores_df = conc.resources.get_scores(
        scores_name,
        columns={
            "attribute_columns": [token_attr],
            "score_columns": [score_col],
        },
    )
    scores_df = scores_df[scores_df[score_col] > 0]
    if top_n is not None:
        top_df    = scores_df.nlargest(top_n, score_col)
    else:
        top_df    = scores_df
    top_scores = dict(zip(top_df[token_attr], top_df[score_col]))

    if not top_scores:                                       # safety
        raise ValueError("No positive scores found in the top-N selection.")

    tok = conc.tokens
    if conc.resources.get_scores_info(scores_name).get("ignore_case", False):
        for col in tok.columns:
            if tok[col].dtype == object:
                tok[col] = tok[col].str.lower()

        positive_filter = {
            k: [v.lower() for v in vals]
            for k, vals in positive_filter.items()
        }
        negative_filter = {
            k: [v.lower() for v in vals]
            for k, vals in negative_filter.items()
        }

    lo  = win_start if win_start is not None else -float("inf")
    hi  = win_end   if win_end   is not None else  float("inf")
    mask = (tok["offset"] >= lo) & (tok["offset"] <= hi)
    if not include_node:
        mask &= tok["offset"] != 0
    tok = tok.loc[mask]

    if positive_filter:
        keep_mask = pd.Series(False, index=tok.index)
        for attr, allowed in positive_filter.items():
            keep_mask |= tok[attr].isin(allowed)
        tok = tok[keep_mask]

    for attr, blocked in negative_filter.items():
        tok = tok[~tok[attr].isin(blocked)]

    tok = tok[tok[token_attr].isin(top_scores)]
    if tok.empty:
        # nothing matched – all ranks = 0, spans empty
        zero_ranks = {lid: 0 for lid in conc.metadata.index}
        return {"rank_keys": zero_ranks,
                "token_spans": pd.DataFrame(columns=[
                    "line_id", "start_id_in_line",
                    "end_id_in_line", "category", "weight"
                ])}

    tok["weight"] = tok[token_attr].map(top_scores)

    # build spans (single-token)
    spans = tok[["line_id", "id_in_line", "weight"]].copy()
    spans["start_id_in_line"] = spans["id_in_line"]
    spans["end_id_in_line"]   = spans["id_in_line"]
    spans["category"]         = "COL"
    spans = spans[[
        "line_id", "start_id_in_line", "end_id_in_line", "category", "weight"
    ]].reset_index(drop=True)

    # ranking keys
    if method == "sum":
        ranks = tok.groupby("line_id")["weight"].sum()
    else:                               # "count"
        ranks = tok.groupby("line_id").size()

    # include all concordance lines, fill with 0
    rank_keys = ranks.reindex(conc.metadata.index, fill_value=0).to_dict()

    return {"rank_keys": rank_keys, "token_spans": spans}
