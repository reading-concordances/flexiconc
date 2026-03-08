import hashlib
import random
from typing import Dict, List


def clustering_random(conc, **args):
    """
    Build a deterministic random hierarchical clustering over concordance lines.

    Parameters
    ----------
    seed : int, optional
        Seed for stable pseudo-randomization (default ``42``). The order is
        stable relative to line_id and seed, independent of what other lines
        are present.
    depth : int, optional
        Tree depth (number of cluster levels including root). ``1`` yields a
        single root cluster with no children. Default ``3``.
    min_split : int, optional
        Minimum number of subclusters to create at each split (default ``2``).
    max_split : int, optional
        Maximum number of subclusters to create at each split (default ``4``).
    min_stray_lines : int, optional
        Minimum number of stray lines to select at each level (default ``0``).
    max_stray_lines : int, optional
        Maximum number of stray lines to select at each level (default ``3``).

    Returns
    -------
    dict
        A dictionary with a single key ``"cluster"`` holding the root cluster
        object following this structure:
        ``{label: str, type: "cluster", children: [..., {type: "lines", line_ids: [...] }], illustrations: [...], prototypicality: {line_id: score, ...}}``
    """

    # Metadata for the algorithm
    clustering_random._algorithm_metadata = {
        "name": "Random Hierarchical Clustering",
        "description": (
            "Creates a deterministic random hierarchical clustering over lines "
            "based on a seed and desired depth."
        ),
        "algorithm_type": "clustering",
        "args_schema": {
            "type": "object",
            "properties": {
                "seed": {
                    "type": "integer",
                    "description": "Seed for stable pseudo-random ordering.",
                    "default": 42,
                },
                "depth": {
                    "type": "integer",
                    "description": "Depth of the clustering tree (>= 1).",
                    "default": 3,
                    "minimum": 1,
                    "x-eval": "dict(maximum=max(1, node.line_count))",
                },
                "min_split": {
                    "type": "integer",
                    "description": "Minimum number of subclusters to create at each split.",
                    "default": 2,
                    "minimum": 2,
                },
                "max_split": {
                    "type": "integer",
                    "description": "Maximum number of subclusters to create at each split.",
                    "default": 4,
                    "minimum": 2,
                },
                "min_stray_lines": {
                    "type": "integer",
                    "description": "Minimum number of stray lines to select at each level.",
                    "default": 0,
                    "minimum": 0,
                },
                "max_stray_lines": {
                    "type": "integer",
                    "description": "Maximum number of stray lines to select at each level.",
                    "default": 3,
                    "minimum": 0,
                },
            },
            "required": [],
        },
    }

    seed = args.get("seed", 42)
    depth = max(1, int(args.get("depth", 3)))
    min_split = max(2, int(args.get("min_split", 2)))
    max_split = max(min_split, int(args.get("max_split", 4)))
    min_stray_lines = max(0, int(args.get("min_stray_lines", 0)))
    max_stray_lines = max(min_stray_lines, int(args.get("max_stray_lines", 3)))
    
    # Set random seed for deterministic behavior
    random.seed(seed)

    line_ids: List[int] = conc.metadata.index.tolist()
    
    # Counter for unique cluster IDs
    cluster_id_counter = 0

    def stable_random_key(line_id: int) -> float:
        input_str = f"{seed}_{line_id}"
        hash_val = hashlib.md5(input_str.encode()).hexdigest()
        int_val = int(hash_val[:8], 16)
        return int_val / (2 ** 32)

    ordered_ids = sorted(line_ids, key=stable_random_key)

    def prototypicality_scores(ids: List[int]) -> Dict[int, float]:
        # Random prototypicality scores between 0 and 1
        if len(ids) == 0:
            return {}
        return {lid: random.random() for lid in ids}

    def make_cluster(ids: List[int], level: int, label_prefix: str) -> Dict:
        nonlocal cluster_id_counter
        cluster_id_counter += 1
        
        # Base cluster object
        cluster = {
            "id": cluster_id_counter,
            "label": f"{label_prefix}",
            "type": "cluster",
            "children": [],
            "illustrations": ids[: min(5, len(ids))],
            "prototypicality": prototypicality_scores(ids),
        }

        # If depth exhausted or trivial, attach all as lines and stop
        if level >= depth or len(ids) <= 1:
            cluster["children"].append({"type": "lines", "line_ids": ids})
            return cluster

        # Select stray lines first
        remaining_ids = ids.copy()
        stray_lines = []
        if len(remaining_ids) > 0:
            num_stray = random.randint(min_stray_lines, min(max_stray_lines, len(remaining_ids)))
            if num_stray > 0:
                stray_indices = random.sample(range(len(remaining_ids)), num_stray)
                stray_lines = [remaining_ids[i] for i in sorted(stray_indices, reverse=True)]
                for i in sorted(stray_indices, reverse=True):
                    remaining_ids.pop(i)

        # Add stray lines as a child if any
        if stray_lines:
            cluster["children"].append({"type": "lines", "line_ids": stray_lines})

        # If no remaining lines after stray selection, stop
        if not remaining_ids:
            return cluster

        # Randomly choose number of splits
        num_splits = random.randint(min_split, min(max_split, len(remaining_ids)))
        
        # Create random splits
        if num_splits == 1:
            # Single group - all remaining lines
            cluster["children"].append(
                make_cluster(remaining_ids, level + 1, f"{label_prefix}.0")
            )
        else:
            # Multiple groups - randomly distribute lines
            group_sizes = [0] * num_splits
            for _ in range(len(remaining_ids)):
                group_sizes[random.randint(0, num_splits - 1)] += 1
            
            # Shuffle remaining IDs and split according to group sizes
            random.shuffle(remaining_ids)
            start_idx = 0
            for i, size in enumerate(group_sizes):
                if size > 0:
                    group_ids = remaining_ids[start_idx:start_idx + size]
                    cluster["children"].append(
                        make_cluster(group_ids, level + 1, f"{label_prefix}.{i}")
                    )
                    start_idx += size

        return cluster

    root = make_cluster(ordered_ids, level=1, label_prefix="C")
    return {"cluster": root}


