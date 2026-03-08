def partition_ngrams(conc, **args):
    """
    Partition concordance lines by the n-gram tuples of tokens at the specified offsets. Compare Anthony's (2018) KWIC Patterns and subsequent work.

    Parameters
    ----------
    positions : list[int]
        Offsets (relative token positions) that form the pattern.
    tokens_attribute : str, optional
        Token-attribute column used to fetch the tokens
        (default ``"word"``).
    case_sensitive : bool, optional
        Preserve original casing if *True*; otherwise tokens are converted
        to lowercase (default ``False``).

    Returns
    -------
    dict
        ``{"partitions": [ {"id": int,
                             "label": str,
                             "line_ids": list[int]}, … ]}``

    Notes
    -----
    * The ``label`` of each partition is the stringified tuple of tokens
      extracted at *positions*.
    * Partitions are ordered by descending size and, for equal sizes,
      alphabetically by their label.
    """


    # Metadata for the algorithm
    partition_ngrams._algorithm_metadata = {
        "name": "Partition by Ngrams",
        "description": "Extracts ngram patterns from specified positions and partitions the concordance according to their frequency in the concordance lines. Compare Anthony's (2018) KWIC Patterns and subsequent work.",
        "algorithm_type": "partitioning",
        "args_schema": {
            "type": "object",
            "properties": {
                "positions": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "The list of positions (offsets) to extract for the ngram pattern."
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "The positional attribute to search within (e.g., 'word').",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "If True, the search is case-sensitive.",
                    "default": False
                }
            },
            "required": ["positions"]
        }
    }

    # Extract arguments
    positions = args["positions"]
    tokens_attribute = args.get("tokens_attribute", "word")
    case_sensitive = args.get("case_sensitive", False)

    # Step 1: Filter tokens based on the specified positions
    filtered_tokens = conc.tokens[conc.tokens["offset"].isin(positions)].copy()

    # Step 2: Apply case sensitivity
    if not case_sensitive:
        filtered_tokens[tokens_attribute] = filtered_tokens[tokens_attribute].str.lower()

    # Step 3: Aggregate ngrams by line_id as tuples of tokens at the specified positions
    ngram_dict = filtered_tokens.groupby("line_id")[tokens_attribute].apply(
        lambda x: tuple(x.tolist())
    ).to_dict()

    # Step 4: Group line IDs by unique ngram patterns
    group_dict = {}
    for line_id, ngram in ngram_dict.items():
        group_dict.setdefault(ngram, []).append(line_id)

    # Step 5: Sort ngram patterns: first by descending size, then alphabetically by their string representation.
    sorted_group_dict = {
        str(ngram): line_ids
        for ngram, line_ids in sorted(
            group_dict.items(),
            key=lambda item: (-len(item[1]), str(item[0]))
        )
    }

    # Step 6: Format the output as a list of dictionaries with an "id" for each group.
    result = {"partitions": [
        {
            "id": idx,
            "label": label,
            "line_ids": line_ids
        }
        for idx, (label, line_ids) in enumerate(sorted_group_dict.items())
    ]}

    return result
