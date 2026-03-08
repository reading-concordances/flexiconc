import operator

def select_by_rank(conc, **args):
    """
    Selects lines based on rank values obtained from a specific ranking key in the ordering_result["rank_keys"]
    of the current node. The ranking key corresponds to supplementary ranking information.
    """
    # Metadata for the algorithm
    select_by_rank._algorithm_metadata = {
        "name": "Select by Rank",
        "description": (
            "Selects lines based on rank values obtained from the ranking keys in the ordering_result['rank_keys'] "
            "of the current node, by default by the first ranking key. "
        ),
        "algorithm_type": "selecting",
        "status": "experimental",
        "conditions": {"x-eval": "has_rank_keys(node)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "ranking_column": {
                    "type": "string",
                    "description": "The ranking column to use for selection.",
                    "x-eval": (
                        "dict("
                        "enum=[f'{x}: {node.algorithms[\"ordering\"][x][\"algorithm_name\"]}' "
                        "for x in list(node.ordering_result['rank_keys'])], "
                        "default=[f'{x}: {node.algorithms[\"ordering\"][x][\"algorithm_name\"]}' "
                        "for x in list(node.ordering_result['rank_keys'])][0]"
                        ")"
                    )
                },
                "comparison_operator": {
                    "type": "string",
                    "enum": ["==", "<=", ">=", "<", ">"],
                    "description": "The comparison operator to use for the ranking scores.",
                    "default": "=="
                },
                "value": {
                    "type": "number",
                    "description": "The numeric value to compare the ranking scores against.",
                    "default": 0
                }
            },
            "required": []
        }
    }

    # Use the current active node.
    node = conc.active_node
    ranking_column = args.get("ranking_column", None)
    comparison_operator = args.get("comparison_operator", "==")
    value = args.get("value", 0)

    if not hasattr(node, "ordering_result") or "rank_keys" not in node.ordering_result:
        raise ValueError("The active node does not contain 'ordering_result' with 'rank_keys'.")

    rank_keys = node.ordering_result["rank_keys"]
    try:
        if ':' in ranking_column:
            algo_key = list(rank_keys)[int(ranking_column.split(":")[0])]
        else:
            algo_key = list(rank_keys)[int(ranking_column)]
    except:
        raise ValueError(f"Invalid ranking column '{ranking_column}'. Please provide a valid index or key.")

    ranks = rank_keys[algo_key]

    ops = {
        "==": operator.eq,
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt
    }
    comp_func = ops[comparison_operator]

    selected_lines = [line_id for line_id, rank in ranks.items() if comp_func(rank, value)]

    return {"selected_lines": sorted(selected_lines)}