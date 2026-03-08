import operator
from flexiconc.utils.line_operations import extract_words_at_offset


def select_by_token_numeric_value(conc, **args):
    """
    Selects lines based on a token-level attribute using numeric comparison at a given offset.
    This algorithm supports both a single numeric value with various comparison operators and a list
    of numeric values (in which case only equality is used).

    Returns a dictionary containing:
      - "selected_lines": A list of line IDs where the numeric token at the given offset satisfies the comparison.
      - "token_spans": A DataFrame marking the span of the token(s) at the focus offset,
        including the attribute values from that token.
    """
    # Metadata for the algorithm
    select_by_token_numeric_value._algorithm_metadata = {
        "name": "Select by Token-Level Numeric Attribute",
        "description": (
            "Selects lines based on a token-level attribute using numeric comparison at a given offset. "
            "If a list is provided for 'value', only equality comparison is performed."
        ),
        "algorithm_type": "selecting",
        "conditions": {"x-eval": "has_numeric_token_attributes(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": ["number", "array"],
                    "items": {"type": "number"},
                    "description": (
                        "The numeric value(s) to compare against. "
                        "If a list is provided, only equality comparison is supported."
                    ),
                    "default": 0
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token-level attribute to check.",
                    "x-eval": "dict(enum=[col for col in list(conc.tokens.columns) if col not in {'id_in_line', 'line_id', 'offset'} and ('int' in str(conc.tokens[col].dtype) or 'float' in str(conc.tokens[col].dtype))])"
                },
                "offset": {
                    "type": "integer",
                    "description": "The token offset to check.",
                    "default": 0,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
                },
                "comparison_operator": {
                    "type": "string",
                    "enum": ["==", "<", ">", "<=", ">="],
                    "description": "The comparison operator to use for numeric values. Ignored if 'value' is a list.",
                    "default": "=="
                },
                "negative": {
                    "type": "boolean",
                    "description": "If True, inverts the selection.",
                    "default": False
                }
            },
            "required": ["value", "tokens_attribute"]
        }
    }

    tokens_attribute = args.get("tokens_attribute", "word")
    offset = args.get("offset", 0)
    value = args.get("value", 0)
    negative = args.get("negative", False)

    # Determine if value is a list; if so, only equality is supported.
    if isinstance(value, list):
        use_list = True
    else:
        use_list = False
        comp_op = args.get("comparison_operator", "==")

    # Extract token values at the given offset for each line.
    items = extract_words_at_offset(conc.tokens, p=tokens_attribute, offset=offset)
    all_line_ids = sorted(conc.tokens['line_id'].unique())

    selection = []
    if use_list:
        for item in items:
            try:
                token_num = float(item)
                # A token matches if it equals any of the provided values.
                match = any(token_num == v for v in value)
            except (ValueError, TypeError):
                match = False
            selection.append(1 if match else 0)
    else:
        ops = {
            "==": operator.eq,
            "<": operator.lt,
            ">": operator.gt,
            "<=": operator.le,
            ">=": operator.ge
        }
        comp_func = ops.get(comp_op)
        if comp_func is None:
            raise ValueError(f"Invalid comparison operator: {comp_op}")
        for item in items:
            try:
                token_num = float(item)
                match = comp_func(token_num, value)
            except (ValueError, TypeError):
                match = False
            selection.append(1 if match else 0)

    if negative:
        selection = [1 - x for x in selection]

    selected_lines = [all_line_ids[i] for i, flag in enumerate(selection) if flag == 1]

    # Build token_spans for the focus offset, following the same enrichment as in rank_kwic_grouper.
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