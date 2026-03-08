from collections import Counter
from typing import Dict, List, Tuple
from flexiconc.utils.line_operations import extract_words_at_offset


def cluster_context_tree(conc, **args):
    """
    Build a hierarchical clustering tree based on token continuations at specified offsets.
    
    The algorithm counts continuation tokens at position 1 to the right (or left) of the node
    in the given token-level attribute and clusters by them, with the biggest cluster coming first.
    This process continues recursively, expanding to further offsets (2nd, 3rd token, etc.) until 
    clusters of a certain size are reached. Cluster labels are sequences of tokens leading to each cluster.
    Single lines are treated as stray and sorted alphabetically.

    Parameters
    ----------
    tokens_attribute : str, optional
        The token-level attribute to use for clustering (default ``"word"``).
    offset : int, optional
        The offset position to check for continuations (default ``1`` for right context).
    direction : str, optional
        Direction of expansion: ``"right"`` or ``"left"`` (default ``"right"``).
    case_sensitive : bool, optional
        Whether to perform case-sensitive matching (default ``False``).
    min_cluster_size : int, optional
        Minimum cluster size to continue splitting (default ``2``).
    max_depth : int, optional
        Maximum depth of the clustering tree (default ``10``).

    Returns
    -------
    dict
        A dictionary with a single key ``"cluster"`` holding the root cluster
        object following this structure:
        ``{label: str, type: "cluster", children: [..., {type: "lines", line_ids: [...] }], illustrations: [], prototypicality: {line_id: score, ...}}``
    """

    # Metadata for the algorithm
    cluster_context_tree._algorithm_metadata = {
        "name": "Context Tree Clustering",
        "description": (
            "Creates a hierarchical clustering tree based on token continuations "
            "at specified offsets. Clusters are built by grouping lines that share "
            "the same continuation tokens, with the largest clusters appearing first."
        ),
        "algorithm_type": "clustering",
        "args_schema": {
            "type": "object",
            "properties": {
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token-level attribute to use for clustering.",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "offset": {
                    "type": "integer",
                    "description": "The offset position to check for continuations.",
                    "default": 1,
                    "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
                },
                "direction": {
                    "type": "string",
                    "description": "Direction of expansion: 'right' or 'left'.",
                    "default": "right",
                    "enum": ["right", "left"]
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether to perform case-sensitive matching.",
                    "default": False
                },
                "min_cluster_size": {
                    "type": "integer",
                    "description": "Minimum cluster size to continue splitting.",
                    "default": 2,
                    "minimum": 1
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth of the clustering tree.",
                    "default": 10,
                    "minimum": 1
                }
            },
            "required": []
        }
    }

    # Extract arguments
    tokens_attribute = args.get("tokens_attribute", "word")
    offset = args.get("offset", 1)
    direction = args.get("direction", "right")
    case_sensitive = args.get("case_sensitive", False)
    min_cluster_size = max(1, int(args.get("min_cluster_size", 2)))
    max_depth = max(1, int(args.get("max_depth", 10)))

    # Adjust offset based on direction
    if direction == "left":
        offset = -abs(offset)
    else:
        offset = abs(offset)

    # Get all line IDs
    line_ids = sorted(conc.tokens['line_id'].unique())
    
    # Counter for unique cluster IDs
    cluster_id_counter = 0

    def get_continuation_tokens(line_ids_subset: List[int], current_offset: int) -> List[str]:
        """Extract continuation tokens for the given line IDs at the specified offset."""
        # Filter tokens for the given line IDs and offset
        filtered_tokens = conc.tokens[
            (conc.tokens['line_id'].isin(line_ids_subset)) & 
            (conc.tokens['offset'] == current_offset)
        ]
        
        # Extract token values
        if len(filtered_tokens) == 0:
            return [''] * len(line_ids_subset)
        
        # Group by line_id and join multiple matches
        grouped = filtered_tokens.groupby('line_id')[tokens_attribute].apply(
            lambda x: ' '.join(str(val) for val in x)
        )
        
        # Apply case sensitivity
        if not case_sensitive:
            grouped = grouped.str.lower()
        
        # Return list in the same order as line_ids_subset
        result = []
        for line_id in line_ids_subset:
            token_value = grouped.get(line_id, '')
            result.append(token_value)
        
        return result

    def compute_prototypicality_scores(ids: List[int], current_offset: int) -> Dict[int, float]:
        """Compute prototypicality scores based on frequency of continuation tokens."""
        if len(ids) == 0:
            return {}
        
        continuation_tokens = get_continuation_tokens(ids, current_offset)
        token_counts = Counter(continuation_tokens)
        
        # Assign scores based on frequency (more frequent = more prototypical)
        max_count = max(token_counts.values()) if token_counts else 1
        scores = {}
        for line_id, token in zip(ids, continuation_tokens):
            if max_count > 0:
                scores[line_id] = token_counts[token] / max_count
            else:
                scores[line_id] = 1.0
        
        return scores

    def create_context_cluster(ids: List[int], level: int, label_prefix: str, context_sequence: List[str]) -> Dict:
        """Recursively create hierarchical clustering structure based on context continuations."""
        nonlocal cluster_id_counter
        cluster_id_counter += 1
        
        # Calculate current offset based on level and direction
        current_offset = offset + (level - 1) if direction == "right" else offset - (level - 1)
        
        # Base cluster object
        cluster = {
            "id": cluster_id_counter,
            "label": " ".join(context_sequence) if context_sequence else "root",
            "type": "cluster",
            "children": [],
            "illustrations": [],  # Always empty as requested
            "prototypicality": {},
        }

        # Compute prototypicality scores for current level
        cluster["prototypicality"] = compute_prototypicality_scores(ids, current_offset)

        # If depth exhausted or cluster too small, make terminal
        if level >= max_depth or len(ids) < min_cluster_size:
            # Sort lines alphabetically by their continuation token
            continuation_tokens = get_continuation_tokens(ids, current_offset)
            line_token_pairs = list(zip(ids, continuation_tokens))
            line_token_pairs.sort(key=lambda x: x[1])  # Sort by token alphabetically
            sorted_ids = [line_id for line_id, _ in line_token_pairs]
            
            cluster["children"].append({"type": "lines", "line_ids": sorted_ids})
            return cluster

        # Get continuation tokens for current level
        continuation_tokens = get_continuation_tokens(ids, current_offset)
        
        # Group line IDs by their continuation tokens
        token_groups = {}
        for line_id, token in zip(ids, continuation_tokens):
            if token not in token_groups:
                token_groups[token] = []
            token_groups[token].append(line_id)

        # Separate groups smaller than min_cluster_size (stray lines) from larger groups
        stray_lines = []
        multi_line_groups = {}
        
        for token, group_ids in token_groups.items():
            if len(group_ids) < min_cluster_size:
                stray_lines.extend(group_ids)
            else:
                multi_line_groups[token] = group_ids

        # Add stray lines as a single sorted group if any
        if stray_lines:
            # Sort stray lines alphabetically by their continuation token
            stray_tokens = get_continuation_tokens(stray_lines, current_offset)
            stray_line_token_pairs = list(zip(stray_lines, stray_tokens))
            stray_line_token_pairs.sort(key=lambda x: x[1])  # Sort by token alphabetically
            sorted_stray_ids = [line_id for line_id, _ in stray_line_token_pairs]
            
            cluster["children"].append({"type": "lines", "line_ids": sorted_stray_ids})

        # Process multi-line groups
        if multi_line_groups:
            # Sort groups by size (largest first), then by token value for stability
            sorted_groups = sorted(
                multi_line_groups.items(), 
                key=lambda x: (-len(x[1]), x[0])
            )

            # Create child clusters
            child_clusters_with_scores = []
            for i, (token, child_ids) in enumerate(sorted_groups):
                if child_ids:  # Only create child if it has lines
                    # Update context sequence
                    new_context = context_sequence + [token]
                    new_label = f"{label_prefix}.{i}"
                    
                    child_cluster = create_context_cluster(
                        child_ids, level + 1, new_label, new_context
                    )
                    
                    # Get the maximum prototypicality score for this child cluster
                    if child_cluster["prototypicality"]:
                        max_prototypicality = max(child_cluster["prototypicality"].values())
                    else:
                        max_prototypicality = 0
                    
                    child_clusters_with_scores.append((max_prototypicality, child_cluster))

            # Sort child clusters by their maximum prototypicality (descending)
            child_clusters_with_scores.sort(key=lambda x: x[0], reverse=True)
            
            # Add sorted child clusters to the parent
            for _, child_cluster in child_clusters_with_scores:
                cluster["children"].append(child_cluster)

        return cluster

    # Create the root cluster
    root = create_context_cluster(line_ids, level=1, label_prefix="C", context_sequence=[])
    return {"cluster": root}
