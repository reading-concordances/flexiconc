import re
import operator
import pandas as pd

def select_by_metadata_attribute(conc, **args):
    """
    Selects concordance lines based on a specified metadata attribute comparing it to a target value.

    When the target value is a list, only equality is used (the metadata value must equal one of the list items).
    When the target value is a single numeric value, a comparison operator (one of "==", "<", "<=", ">", ">=")
    can be provided. For string values, only equality is supported (with optional regex matching and case sensitivity).

    Parameters:
        conc (Concordance or ConcordanceSubset): The concordance object.
        args (dict): Arguments include:
            - metadata_attribute (str): The metadata attribute to filter on.
            - value (str, number, or list of str/number): The value (or list of values) to compare against.
            - operator (str, optional): Comparison operator for numeric comparisons. One of "==", "<", "<=", ">", ">=".
                                        Default is "==".
                                        This parameter is ignored if a list is provided or if the value is a string.
            - regex (bool, optional): If True, for string values use regex matching (only with equality). Default is False.
            - case_sensitive (bool, optional): If True, perform case-sensitive matching for strings. Default is False.
            - negative (bool, optional): If True, invert the selection. Default is False.

    Returns:
        dict: A dictionary containing:
            - "selected_lines": A sorted list of line IDs for which the metadata attribute meets the condition.
    """
    # Metadata for the algorithm
    select_by_metadata_attribute._algorithm_metadata = {
        "name": "Select by Metadata Attribute",
        "description": (
            "Selects lines based on whether a specified metadata attribute compares to a given target value. "
            "If a list is provided as the target value, membership is tested using equality. For a single numeric "
            "value, a comparison operator (==, <, <=, >, >=) can be specified. For strings, only equality (with "
            "optional regex matching and case sensitivity) is supported."
        ),
        "algorithm_type": "selecting",
        "conditions": {"x-eval": "has_metadata_attributes(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "metadata_attribute": {
                    "type": "string",
                    "description": "The metadata attribute to filter on.",
                    "x-eval": "dict(enum=list(set(conc.metadata.columns) - {'line_id'}))"
                },
                "value": {
                    "type": ["string", "number", "array"],
                    "description": (
                        "The value to compare against, or a list of acceptable values. When a list is provided, "
                        "only equality is used."
                    )
                },
                "operator": {
                    "type": "string",
                    "enum": ["==", "<", "<=", ">", ">="],
                    "description": (
                        "The comparison operator for numeric comparisons. Only allowed for single numeric values. "
                        "Default is '=='."
                    ),
                    "default": "=="
                },
                "regex": {
                    "type": "boolean",
                    "description": "If True, use regex matching for string comparisons (only with equality). Default is False.",
                    "default": False
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "If True, perform case-sensitive matching for strings. Default is False.",
                    "default": False
                },
                "negative": {
                    "type": "boolean",
                    "description": "If True, invert the selection. Default is False.",
                    "default": False
                }
            },
            "required": ["metadata_attribute", "value"]
        }
    }

    metadata_attribute = args["metadata_attribute"]
    target_value = args["value"]
    negative = args.get("negative", False)
    regex = args.get("regex", False)
    case_sensitive = args.get("case_sensitive", False)
    op_str = args.get("operator", "==")

    # Ensure the metadata attribute exists in the metadata DataFrame.
    if metadata_attribute not in conc.metadata.columns:
        raise ValueError(f"Metadata attribute '{metadata_attribute}' not found in metadata.")
    col_series = conc.metadata[metadata_attribute]

    # If target_value is a list, only equality (membership) is used.
    if isinstance(target_value, list):
        # Decide on numeric vs. string.
        if all(isinstance(val, (int, float)) for val in target_value):
            # Numeric membership: convert column to numeric.
            col_numeric = pd.to_numeric(col_series, errors="coerce")
            if col_numeric.isna().any():
                raise ValueError(f"Numeric conversion failed for '{metadata_attribute}'.")
            match_mask = col_numeric.apply(lambda x: x in target_value)
        else:
            # String membership.
            col_str = col_series.astype(str)
            if not case_sensitive:
                col_str = col_str.str.lower()
                target_value = [str(v).lower() for v in target_value]
            match_mask = col_str.apply(lambda x: x in target_value)
    else:
        # Single value: determine if numeric.
        if isinstance(target_value, (int, float)):
            # Numeric comparison using operator parameter.
            col_numeric = pd.to_numeric(col_series, errors="coerce")
            if col_numeric.isna().any():
                raise ValueError(f"Numeric conversion failed for '{metadata_attribute}'.")
            ops = {
                "==": operator.eq,
                "<": operator.lt,
                "<=": operator.le,
                ">": operator.gt,
                ">=": operator.ge
            }
            op_func = ops[op_str]
            match_mask = col_numeric.apply(lambda x: op_func(x, target_value))
        else:
            # String comparison.
            col_str = col_series.astype(str)
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                match_mask = col_str.apply(lambda x: bool(re.search(str(target_value), x, flags=flags)))
            else:
                if not case_sensitive:
                    col_str = col_str.str.lower()
                    target_value = str(target_value).lower()
                match_mask = col_str == target_value

    if negative:
        match_mask = ~match_mask

    selected_lines = sorted(conc.metadata.loc[match_mask, "line_id"].tolist())
    return {"selected_lines": selected_lines}
