try:
    import icu
    def get_sort_key(x, locale_str):
        collator = icu.Collator.createInstance(icu.Locale(locale_str))
        return collator.getSortKey(str(x))
except ImportError:
    def get_sort_key(x, locale_str):
        return str(x)

from flexiconc.utils.line_operations import *
import pandas as pd


def sort_by_token_attribute(conc, **args):
    """
    Sorts the concordance lines by a specified token-level attribute.
    It supports sorting by a single token at a given offset (sorting_scope="token"),
    or by the whole left context (sorting_scope="left") or whole right context (sorting_scope="right").

    For left context, tokens are joined from right to left (i.e. starting with offset -1, then -2, etc.).

    Locale-specific sorting is attempted via pyicu; if unavailable, plain Unicode sorting is used.
    Additionally, outputs token_spans for the tokens used for sorting.

    Args are dynamically validated and extracted from the schema.

    Parameters:
      - conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
      - args (dict): Arguments include:
          - tokens_attribute (str): The token attribute to sort by (e.g., "word", "lemma", "pos"). Default is "word".
          - sorting_scope (str): Specifies which context to use for sorting:
                               "token" for a single token at the given offset (default),
                               "left" for the entire left context (tokens with offset < 0 joined from right to left),
                               "right" for the entire right context (tokens with offset > 0 joined with a space).
          - offset (int): The offset value to filter tokens by when sorting_scope=="token". Default is 0.
          - case_sensitive (bool): If True, performs a case-sensitive sort. Default is False.
          - reverse (bool): If True, sort in descending order. Default is False.
          - backwards (bool): If True, reverses the string (e.g., for right-to-left sorting). Default is False.
          - locale_str (str): ICU locale string for language-specific sorting. Default is "en".

    Returns:
      dict: A dictionary containing:
          - "sort_keys": A mapping from line IDs to their sorted ranks.
          - "token_spans": A DataFrame with columns:
                line_id, start_id_in_line, end_id_in_line, category, weight.
          The token_spans represent the span (min and max id_in_line) of the tokens used for sorting.
    """
    # Metadata for the algorithm
    sort_by_token_attribute._algorithm_metadata = {
        "name": "Sort by Token-Level Attribute",
        "description": (
            "Sorts the concordance lines by the given token-level attribute using locale-specific sorting "
            "(default 'en'). Supports sorting by a single token at a given offset, or by whole left/right context "
            "by joining tokens. When sorting by left context, tokens are joined from right to left. "
            "Optionally reverses strings for right-to-left sorting."
        ),
        "algorithm_type": "sorting",
        "requires": ["pyicu"],
        "args_schema": {
            "type": "object",
            "properties": {
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token attribute to sort by.",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "sorting_scope": {
                    "type": "string",
                    "description": (
                        "Specifies which context to use for sorting: 'token' for a single token at the given offset, "
                        "'left' for the entire left context (joined from right to left), or 'right' for the entire right context."
                    ),
                    "default": "token",
                    "enum": ["token", "left", "right"]
                },
                "offset": {
                    "type": "integer",
                    "description": "The offset value to filter tokens by when sorting_scope is 'token'.",
                    "default": 0,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "If True, performs a case-sensitive sort.",
                    "default": False
                },
                "reverse": {
                    "type": "boolean",
                    "description": "If True, sort in descending order.",
                    "default": False
                },
                "backwards": {
                    "type": "boolean",
                    "description": "If True, reverses the string (e.g., for right-to-left sorting).",
                    "default": False
                },
                "locale_str": {
                    "type": "string",
                    "description": "ICU locale string for language-specific sorting.",
                    "default": "en"
                }
            },
            "required": []
        }
    }

    # Extract arguments
    tokens_attribute = args.get("tokens_attribute", "word")
    sorting_scope = args.get("sorting_scope", "token")
    offset = args.get("offset", 0)
    case_sensitive = args.get("case_sensitive", False)
    reverse = args.get("reverse", False)
    backwards = args.get("backwards", False)
    locale_str = args.get("locale_str", "en")

    # Determine the string to sort for each line based on sorting_scope.
    if sorting_scope == "token":
        # Use a single token at the specified offset.
        items = list(extract_words_at_offset(conc.tokens, p=tokens_attribute, offset=offset))
    elif sorting_scope == "left":
        # For left context, join tokens with offset < 0 in descending order (i.e. from -1, -2, ...).
        left_tokens = conc.tokens[conc.tokens["offset"] < 0]
        grouped = left_tokens.sort_values("offset", ascending=False).groupby("line_id")[tokens_attribute].apply(
            lambda x: " ".join(x.astype(str))
        )
        items = [grouped.get(line_id, "") for line_id in conc.metadata.index]
    elif sorting_scope == "right":
        # Join all tokens with offset > 0 in ascending order.
        right_tokens = conc.tokens[conc.tokens["offset"] > 0]
        grouped = right_tokens.groupby("line_id")[tokens_attribute].apply(
            lambda x: " ".join(x.astype(str))
        )
        items = [grouped.get(line_id, "") for line_id in conc.metadata.index]
    else:
        raise ValueError("Invalid sorting_scope value. Must be 'token', 'left', or 'right'.")

    # Apply case sensitivity if required.
    if not case_sensitive:
        items = [item.lower() if isinstance(item, str) else item for item in items]
    # Apply backwards transformation if required.
    if backwards:
        items = [item[::-1] if isinstance(item, str) else item for item in items]

    # Retrieve the line IDs corresponding to the active subset.
    line_ids = conc.metadata.index.tolist()

    # Build DataFrame for sorting.
    df = pd.DataFrame({"line_id": line_ids, tokens_attribute: items})

    # Sort using locale-specific sort key if possible, else fallback to plain sorting.
    try:
        sorted_df = df.sort_values(
            by=tokens_attribute,
            key=lambda col: col.apply(lambda x: get_sort_key(x, locale_str)),
            ascending=not reverse
        )
    except Exception:
        sorted_df = df.sort_values(by=tokens_attribute, ascending=not reverse)

    # Compute sort keys with tie handling.
    sort_keys = {}
    current_rank = 0
    tie_count = 0
    for i in range(len(sorted_df)):
        current_val = sorted_df.iloc[i][tokens_attribute]
        if i > 0 and current_val == sorted_df.iloc[i - 1][tokens_attribute]:
            sort_keys[sorted_df.iloc[i]['line_id']] = current_rank
            tie_count += 1
        else:
            current_rank += tie_count + 1
            sort_keys[sorted_df.iloc[i]['line_id']] = current_rank
            tie_count = 0

    # Build token_spans DataFrame based on the sorting_scope used.
    if sorting_scope == "token":
        span_tokens = conc.tokens[conc.tokens["offset"] == offset].copy()
    elif sorting_scope == "left":
        span_tokens = conc.tokens[conc.tokens["offset"] < 0].copy()
    elif sorting_scope == "right":
        span_tokens = conc.tokens[conc.tokens["offset"] > 0].copy()
    span_tokens = span_tokens.reset_index(drop=True)
    aggregated = span_tokens.groupby("line_id", as_index=False).agg({
        "id_in_line": ["min", "max"]
    })
    aggregated.columns = ["line_id", "start_id_in_line", "end_id_in_line"]
    token_spans = aggregated.copy()
    token_spans["category"] = "A"
    token_spans["weight"] = 1
    # Add the tokens_attribute and the list of token values over the span.
    token_spans["tokens_attribute"] = tokens_attribute
    token_spans["values"] = token_spans.apply(
        lambda row: conc.tokens[
            (conc.tokens["line_id"] == row["line_id"]) &
            (conc.tokens["id_in_line"] >= row["start_id_in_line"]) &
            (conc.tokens["id_in_line"] <= row["end_id_in_line"])
        ][tokens_attribute].tolist(),
        axis=1
    )
    token_spans = token_spans[["line_id", "start_id_in_line", "end_id_in_line", "category", "weight", "tokens_attribute", "values"]]

    return {"sort_keys": sort_keys, "token_spans": token_spans}