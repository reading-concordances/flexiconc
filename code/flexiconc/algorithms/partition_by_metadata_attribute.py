def partition_by_metadata_attribute(conc, **args):
    """
    Partition concordance lines by the values of a chosen metadata column.

    Parameters
    ----------
    metadata_attribute : str
        Name of the concordance ``metadata`` column whose distinct values
        define the partitions.
    sort_by_partition_size : bool, optional
        If *True* (default), partitions are ordered by descending size.
        Ignored when *sorted_values* is supplied.
    sorted_values : list[str | int | float] | None, optional
        Explicit order of attribute values; only those present in the
        concordance are retained and listed in the given order.

    Returns
    -------
    dict
        ``{"partitions": [ {"id": int,
                             "label": str,
                             "line_ids": list[int]}, … ]}``

    Raises
    ------
    ValueError
        If *sorted_values* is not provided and *sort_by_partition_size* is
        set to *False*.

    Notes
    -----
    * ``label`` is the value of *metadata_attribute* shared by the lines in
      that partition.
    * ``line_ids`` are concordance line identifiers.
    """


    # Metadata for the algorithm
    partition_by_metadata_attribute._algorithm_metadata = {
        "name": "Partition by Metadata Attribute",
        "description": "Partitions the concordance lines based on a specified metadata attribute and groups the data by the values of this attribute.",
        "algorithm_type": "partitioning",
        "conditions": {"x-eval": "has_metadata_attributes(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "metadata_attribute": {
                    "type": "string",
                    "description": "The metadata attribute to partition by (e.g., 'text_id', 'speaker').",
                    "x-eval": "dict(enum=list(set(conc.metadata.columns) - {'line_id'}))"
                },
                "sort_by_partition_size": {
                    "type": "boolean",
                    "description": "If True, partitions will be sorted by size in descending order.",
                    "default": True
                },
                "sorted_values": {
                    "type": "array",
                    "items": {
                        "type": ["string", "number"]
                    },
                    "description": "If provided, partitions will be sorted by these specific values."
                }
            },
            "required": ["metadata_attribute"]
        }
    }

    # Extract arguments
    metadata_attribute = args["metadata_attribute"]
    sort_by_partition_size = args.get("sort_by_partition_size", True)
    sorted_values = args.get("sorted_values", None)

    # Group the data by the specified metadata attribute
    group_dict = conc.metadata.groupby(conc.metadata[metadata_attribute].astype(str)).apply(
        lambda df: df.index.tolist()).to_dict()

    # Sort the partitions by size or by the provided sorted_values
    if sort_by_partition_size:
        # Sort by partition size (number of lines in each group)
        sorted_group_dict = dict(sorted(group_dict.items(), key=lambda x: len(x[1]), reverse=True))
    elif sorted_values:
        # Sort by specific values provided in sorted_values
        sorted_group_dict = {value: group_dict.get(value, []) for value in sorted_values if value in group_dict}
    else:
        raise ValueError("Please provide a list of sorted values or choose to sort by partition size.")

    result = {
        "partitions": [
            {
                "id": idx,
                "label": label,
                "line_ids": line_ids
            }
            for idx, (label, line_ids) in enumerate(sorted_group_dict.items())
        ]
    }

    return result
