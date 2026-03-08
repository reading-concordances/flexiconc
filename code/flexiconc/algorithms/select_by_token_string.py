import re
from flexiconc.utils.line_operations import extract_words_at_offset


def select_by_token_string(conc, **args):
    """
    Selects lines based on a token-level attribute (string matching) at a given offset.
    The algorithm matches the token against any of the provided search terms.
    Supports regex matching and case sensitivity.

    Returns a dictionary containing:
      - "selected_lines": A list of line IDs where the token at the given offset matches any search term.
      - "token_spans": A DataFrame marking the span of the token(s) at the focus offset,
        including the attribute values from that token.
    """
    # Metadata for the algorithm
    select_by_token_string._algorithm_metadata = {
        "name": "Select by Token-Level String Attribute",
        "description": "Selects lines based on a token-level attribute (string matching) at a given offset. Supports regex and case sensitivity. The search_terms argument is a list of strings to match against.",
        "algorithm_type": "selecting",
        "args_schema": {
            "type": "object",
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The list of string values to match against.",
                    "default": []
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token attribute to check (e.g., 'word').",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "offset": {
                    "type": "integer",
                    "description": "The token offset to check.",
                    "default": 0,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "If True, performs a case-sensitive match.",
                    "default": False
                },
                "regex": {
                    "type": "boolean",
                    "description": "If True, uses regex matching.",
                    "default": False
                },
                "negative": {
                    "type": "boolean",
                    "description": "If True, inverts the selection.",
                    "default": False
                }
            },
            "required": ["search_terms"]
        }
    }

    # Get parameters; ensure search_terms is a list.
    search_terms = args.get("search_terms", [])
    if not isinstance(search_terms, list):
        search_terms = [search_terms]

    tokens_attribute = args.get("tokens_attribute", "word")
    offset = args.get("offset", 0)
    case_sensitive = args.get("case_sensitive", False)
    regex = args.get("regex", False)
    negative = args.get("negative", False)

    # Extract token values at the given offset for each line
    items = extract_words_at_offset(conc.tokens, p=tokens_attribute, offset=offset)
    all_line_ids = sorted(conc.tokens['line_id'].unique())

    selection = []
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        # Combine all search terms into a single regex pattern (assuming they are intended as patterns)
        pattern_str = "|".join(search_terms)
        pattern = re.compile(pattern_str, flags)
        for item in items:
            match = bool(pattern.search(item))
            selection.append(1 if match else 0)
    else:
        for item in items:
            if not case_sensitive:
                match = any(item.lower() == term.lower() for term in search_terms)
            else:
                match = any(item == term for term in search_terms)
            selection.append(1 if match else 0)

    if negative:
        selection = [1 - x for x in selection]

    selected_lines = [all_line_ids[i] for i, flag in enumerate(selection) if flag == 1]

    # Build token_spans for the focus offset
    span_tokens = conc.tokens[conc.tokens["offset"] == offset].copy()
    span_tokens = span_tokens.reset_index(drop=True)
    span_tokens["start_id_in_line"] = span_tokens["id_in_line"]
    span_tokens["end_id_in_line"] = span_tokens["id_in_line"]
    span_tokens["category"] = "A"
    span_tokens["weight"] = 1
    span_tokens = span_tokens[["line_id", "start_id_in_line", "end_id_in_line", "category", "weight"]]
    span_tokens["tokens_attribute"] = tokens_attribute
    span_tokens["values"] = span_tokens.apply(
        lambda row: conc.tokens[
            (conc.tokens["line_id"] == row["line_id"]) &
            (conc.tokens["id_in_line"] >= row["start_id_in_line"]) &
            (conc.tokens["id_in_line"] <= row["end_id_in_line"])
            ][tokens_attribute].tolist(),
        axis=1
    )

    return {"selected_lines": selected_lines, "token_spans": span_tokens}