def label_sequential_letters(conc, **args):
    """
    Assign sequential letter labels (A, B, C, etc.) to partitions or clusters.
    
    Parameters
    ----------
    partitions : list, optional
        List of partition dictionaries from a grouping algorithm result.
        Each partition should have a 'line_ids' key.
        If not provided, will use partitions from the grouping_result.
    cluster : dict, optional
        Cluster dictionary from a hierarchical clustering algorithm.
        If not provided, will use cluster from the grouping_result.
    start_letter : str, optional
        Starting letter for labels (default 'A').
    
    Returns
    -------
    dict
        Dictionary with 'labels' key containing a mapping from partition/cluster
        identifiers to letter labels.
    """
    
    # Metadata for the algorithm
    label_sequential_letters._algorithm_metadata = {
        "name": "Sequential Letter Labels",
        "description": (
            "Assigns sequential letter labels (A, B, C, etc.) to partitions or clusters "
            "in a grouping result."
        ),
        "algorithm_type": "labelling",
        "args_schema": {
            "type": "object",
            "properties": {
                "start_letter": {
                    "type": "string",
                    "description": "Starting letter for labels (default 'A').",
                    "default": "A",
                },
            },
            "required": [],
        },
    }
    
    start_letter = args.get("start_letter", "A")
    start_ord = ord(start_letter.upper())
    
    # Get partitions or clusters from the grouping result
    # This will be passed by the arrangement node
    partitions = args.get("partitions", [])
    cluster = args.get("cluster", None)
    
    labels = {}
    
    if partitions:
        # Label partitions sequentially
        for idx, partition in enumerate(partitions):
            label = chr(start_ord + idx)
            # Use partition index or existing label as key
            partition_key = partition.get("label", f"partition_{idx}")
            labels[partition_key] = label
            # Also store in partition dict for easy access
            partition["label"] = label
    elif cluster:
        # Label clusters recursively
        def label_cluster_recursive(cluster_dict, current_ord):
            if cluster_dict.get("type") == "cluster":
                label = chr(current_ord[0])
                cluster_id = cluster_dict.get("id")
                if cluster_id:
                    labels[cluster_id] = label
                # Store label in cluster dict
                cluster_dict["label"] = label
                current_ord[0] += 1
                
                # Recursively label children
                if "children" in cluster_dict:
                    for child in cluster_dict["children"]:
                        if child.get("type") == "cluster":
                            label_cluster_recursive(child, current_ord)
        
        current_ord = [start_ord]
        label_cluster_recursive(cluster, current_ord)
    
    return {"labels": labels}


