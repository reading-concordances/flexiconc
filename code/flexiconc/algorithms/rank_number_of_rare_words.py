import pandas as pd
from typing import Dict, List, Optional


def rank_number_of_rare_words(conc, **args) -> dict:
    """
    Rank lines by the number of *rare* words they contain.

    • A word is considered *rare* when
        – it is missing from the frequency list, **or**
        – its frequency  <  threshold, **or**
        – its rank       >  rank_threshold
    • Tokens with attribute values listed in *ignore_attrs* are skipped.
    • By default the resulting score is **negative** (− rare-count) so that
      lines with *fewer* rare words sort to the top.  Set *positive=True*
      to get the raw rare-counts instead.

    Returns
    -------
    dict with keys
        "rank_keys"   : {line_id: score}
        "token_spans" : DataFrame highlighting every rare token
    """

    rank_number_of_rare_words._algorithm_metadata = {
        "name": "Rank by Number of Rare Words",
        "description": "Ranks lines by their count of rare words.",
        "algorithm_type": "ranking",
        "requires_resources": ["frequency_list"],
        "conditions": {"x-eval": "has_frequency_lists(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "p_attr": {
                    "type": "string",
                    "description": "Token attribute to look up in the frequency list",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - "
                              "{'id_in_line','line_id','offset'}))"
                },
                "freq_list": {
                    "type": "string",
                    "description": "Name of a registered frequency list",
                    "x-eval": "dict(enum=conc.resources.list('frequency_list'))"
                },
                "frequency_type": {
                    "type": "string",
                    "description": "Type of frequency to use: raw frequency ('f'), relative frequency ('rel_f'), or instances per million words ('pmw').",
                    "enum": ["f", "rel_f", "pmw"],
                    "default": "pmw"
                },
                "threshold": {
                    "type": "number",
                    "description": "Frequency threshold below which tokens count as rare"
                },
                "rank_threshold": {
                    "type": "integer",
                    "description": "Rank threshold above which tokens count as rare"
                },
                "window_start": {
                    "type": "integer",
                    "description": "Lower bound of the token-offset window (inclusive)"
                },
                "window_end": {
                    "type": "integer",
                    "description": "Upper bound of the token-offset window (inclusive)"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Match tokens against the frequency list case-sensitively",
                    "default": False
                },
                "positive": {
                    "type": "boolean",
                    "description": (
                        "If True, the score is the raw count of rare tokens "
                        "(more-rare → higher score). "
                        "If False (default), score is the *negative* count "
                        "so lines with fewer rare words rank higher."
                    ),
                    "default": False
                },
                "ignore_attrs": {
                    "type": "object",
                    "description": "Mapping of token attrs → list of values to ignore",
                    "default": {},
                    "x-eval": (
                        "dict(propertyNames={'enum': list(set(conc.tokens.columns) - "
                        "{'id_in_line','line_id','offset'})})"
                    ),
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": ["string", "number", "boolean"]}
                    }
                }
            },
            "required": ["p_attr", "freq_list"]
        }
    }

    # ------------------------------------------------------------------ #
    #  unpack arguments
    # ------------------------------------------------------------------ #
    p_attr: str                   = args.get("p_attr")
    freq_list_name: str           = args.get("freq_list")
    frequency_type: str           = args.get("frequency_type")
    threshold: Optional[int]      = args.get("threshold")
    rank_threshold: Optional[int] = args.get("rank_threshold")
    window_start: Optional[int] = args.get("window_start")
    window_end: Optional[int] = args.get("window_end")
    case_sensitive: bool          = args.get("case_sensitive", False)
    positive: bool                = args.get("positive", False)
    ignore_attrs: Dict[str, List] = args.get("ignore_attrs", {}) or {}

    #  load & normalise frequency list
    df_freq = conc.root.concordance().resources.get_frequency_list(name=freq_list_name, frequency_columns=[frequency_type], token_attribute_columns=[p_attr])
    if p_attr not in df_freq.columns or frequency_type not in df_freq.columns:
        raise ValueError("Frequency list must have columns "
                         f"'{p_attr}' and '{frequency_type}'.")

    key_freq = df_freq[p_attr].astype(str)
    if not case_sensitive:
        key_freq = key_freq.str.lower()

    df_freq = (
        df_freq.assign(_key=key_freq)
               .groupby("_key", as_index=False)
               .agg({frequency_type: "sum"})
               .sort_values(frequency_type, ascending=False)
               .reset_index(drop=True)
    )
    df_freq["rank"] = df_freq.index + 1
    freq_map = dict(zip(df_freq["_key"], df_freq[frequency_type]))
    rank_map = dict(zip(df_freq["_key"], df_freq["rank"]))

    #  concordance tokens, filters & matching
    tokens = conc.tokens.copy()

    if window_start is not None:
        tokens = tokens[tokens["offset"] >= window_start]
    if window_end is not None:
        tokens = tokens[tokens["offset"] <= window_end]

    # skip tokens whose target attribute is empty/blank
    tokens = tokens[tokens[p_attr].astype(str).str.strip() != ""]

    for attr, vals in ignore_attrs.items():
        tokens = tokens[~tokens[attr].isin(vals)]

    key_tok = tokens[p_attr].astype(str)
    if not case_sensitive:
        key_tok = key_tok.str.lower()

    tokens["_key"] = key_tok
    tokens[frequency_type]    = tokens["_key"].map(freq_map)
    tokens["rank"] = tokens["_key"].map(rank_map)

    mask = tokens[frequency_type].isna()

    if threshold is not None:
        freq_mask = tokens[frequency_type] < threshold
        mask |= freq_mask

    if rank_threshold is not None:
        rank_mask = tokens["rank"] > rank_threshold
        mask |= rank_mask

    rare = tokens[mask].copy()

    #  token spans (one-token spans)
    rare["start_id_in_line"] = rare["id_in_line"]
    rare["end_id_in_line"]   = rare["id_in_line"]
    rare["category"]         = "rare"
    rare["weight"]           = 1
    rare["tokens_attribute"] = p_attr
    rare["values"]           = rare[p_attr].apply(lambda x: [x])

    token_spans = rare[
        ["line_id", "start_id_in_line", "end_id_in_line",
         "category", "weight", "tokens_attribute", "values"]
    ]

    #  score per line
    counts = rare.groupby("line_id").size()
    counts = counts.reindex(conc.metadata.index, fill_value=0)

    # positive → raw count; negative (default) → −count
    scores = counts if positive else -counts

    return {
        "rank_keys":  scores.to_dict(),
        "token_spans": token_spans
    }