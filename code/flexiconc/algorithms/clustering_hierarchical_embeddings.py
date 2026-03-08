from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import pairwise_distances
import numpy as np
from typing import Dict, List


def clustering_hierarchical_embeddings(conc, **args):
    """
    Build a hierarchical clustering over concordance lines based on embeddings using DBSCAN.

    Parameters
    ----------
    embeddings_column : str
        Name of the concordance ``metadata`` column that holds an embedding
        vector for every line.
    depth : int, optional
        Tree depth (number of cluster levels including root). ``1`` yields a
        single root cluster with no children. Default ``3``.
    eps : float, optional
        Maximum distance between two samples for one to be considered in the 
        neighborhood of the other (default ``0.5``).
    min_samples : int, optional
        Minimum number of samples in a neighborhood for a point to be considered
        a core point (default ``2``).
    metric : str, optional
        Distance metric for clustering (default ``'cosine'``).

    Returns
    -------
    dict
        A dictionary with a single key ``"cluster"`` holding the root cluster
        object following this structure:
        ``{label: str, type: "cluster", children: [..., {type: "lines", line_ids: [...] }], illustrations: [...], prototypicality: {line_id: score, ...}}``
    """

    # Metadata for the algorithm
    clustering_hierarchical_embeddings._algorithm_metadata = {
        "name": "Hierarchical Clustering by Embeddings",
        "description": (
            "Creates a hierarchical clustering over lines based on embeddings "
            "stored in a concordance metadata column using DBSCAN clustering."
        ),
        "algorithm_type": "clustering",
        "requires": ["scikit_learn>=1.3.0"],
        "conditions": {"x-eval": "has_embeddings(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "embeddings_column": {
                    "type": "string",
                    "description": "The metadata column containing embeddings for each line.",
                    "x-eval": "dict(enum=[col for col in list(conc.metadata.columns) if (hasattr(conc.metadata[col].iloc[0], '__iter__') and not isinstance(conc.metadata[col].iloc[0], str) and all(isinstance(x, __import__('numbers').Number) for x in conc.metadata[col].iloc[0]))])"
                },
                "depth": {
                    "type": "integer",
                    "description": "Depth of the clustering tree (>= 1).",
                    "default": 3,
                    "minimum": 1,
                    "x-eval": "dict(maximum=max(1, node.line_count))",
                },
                "eps": {
                    "type": "number",
                    "description": "Maximum distance between two samples for one to be considered in the neighborhood of the other.",
                    "default": 0.5,
                    "minimum": 0.0
                },
                "min_samples": {
                    "type": "integer",
                    "description": "Minimum number of samples in a neighborhood for a point to be considered a core point.",
                    "default": 2,
                    "minimum": 1
                },
                "metric": {
                    "type": "string",
                    "description": "The metric to compute distances between embeddings.",
                    "default": "cosine"
                }
            },
            "required": ["embeddings_column"]
        },
    }

    # Extract arguments
    embeddings_column = args["embeddings_column"]
    depth = max(1, int(args.get("depth", 3)))
    eps = float(args.get("eps", 0.5))
    min_samples = max(1, int(args.get("min_samples", 2)))
    metric = args.get("metric", "cosine")

    # Retrieve embeddings from the concordance metadata
    if embeddings_column not in conc.metadata.columns:
        raise ValueError(f"The embeddings column '{embeddings_column}' is not present in the concordance metadata.")

    embeddings = np.vstack(conc.metadata[embeddings_column].to_numpy())
    line_ids = conc.metadata.index.tolist()
    
    # Counter for unique cluster IDs
    cluster_id_counter = 0

    def compute_prototypicality_scores(ids: List[int], embeddings_subset: np.ndarray) -> Dict[int, float]:
        """Compute prototypicality scores based on distance to cluster centroid."""
        if len(ids) == 0:
            return {}
        
        # Compute centroid
        centroid = np.mean(embeddings_subset, axis=0)
        
        # Compute distances to centroid
        distances = np.linalg.norm(embeddings_subset - centroid, axis=1)
        
        # Convert distances to prototypicality scores (closer to centroid = higher score)
        max_distance = np.max(distances) if len(distances) > 0 else 1.0
        if max_distance > 0:
            prototypicality = 1.0 - (distances / max_distance)
        else:
            prototypicality = np.ones(len(distances))
        
        return {line_id: float(score) for line_id, score in zip(ids, prototypicality)}

    def create_hierarchical_clustering(ids: List[int], level: int, label_prefix: str) -> Dict:
        """Recursively create hierarchical clustering structure using DBSCAN."""
        nonlocal cluster_id_counter
        cluster_id_counter += 1
        
        # Base cluster object
        cluster = {
            "id": cluster_id_counter,
            "label": f"{label_prefix}",
            "type": "cluster",
            "children": [],
            "illustrations": [],
            "prototypicality": {},
        }

        # Get embeddings for current subset and compute prototypicality
        indices = [line_ids.index(line_id) for line_id in ids]
        embeddings_subset = embeddings[indices]
        cluster["prototypicality"] = compute_prototypicality_scores(ids, embeddings_subset)
        
        # Set illustrations to the 2 most prototypical lines
        if cluster["prototypicality"]:
            sorted_by_prototypicality = sorted(
                cluster["prototypicality"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            cluster["illustrations"] = [line_id for line_id, _ in sorted_by_prototypicality[:2]]

        # If depth exhausted or trivial, attach all as lines and stop
        if level >= depth or len(ids) <= 1:
            # Order lines by prototypicality descending
            if cluster["prototypicality"]:
                sorted_ids = sorted(
                    ids, 
                    key=lambda x: cluster["prototypicality"].get(x, 0), 
                    reverse=True
                )
            else:
                sorted_ids = ids
            cluster["children"].append({"type": "lines", "line_ids": sorted_ids})
            return cluster

        # Adjust eps for hierarchical clustering - make it more restrictive at deeper levels
        current_eps = eps * (0.8 ** (level - 1))  # Decrease eps as we go deeper
        current_min_samples = max(min_samples, min(len(ids) // 4, 3))  # Adaptive min_samples
        
        if len(ids) < current_min_samples:
            # Not enough data to cluster, make terminal
            cluster["children"].append({"type": "lines", "line_ids": ids})
            return cluster

        # Perform DBSCAN clustering
        try:
            if metric == "cosine":
                # For cosine distance, we need to use precomputed distances
                dist_matrix = pairwise_distances(embeddings_subset, metric=metric)
                cluster_model = DBSCAN(
                    eps=current_eps,
                    min_samples=current_min_samples,
                    metric="precomputed"
                )
                labels = cluster_model.fit_predict(dist_matrix)
            else:
                cluster_model = DBSCAN(
                    eps=current_eps,
                    min_samples=current_min_samples,
                    metric=metric
                )
                labels = cluster_model.fit_predict(embeddings_subset)
        except Exception as e:
            # If clustering fails, make terminal
            cluster["children"].append({"type": "lines", "line_ids": ids})
            return cluster

        # Group line IDs by cluster labels (-1 is noise)
        cluster_groups = {}
        noise_ids = []
        
        for i, label in enumerate(labels):
            if label == -1:  # Noise points
                noise_ids.append(ids[i])
            else:
                if label not in cluster_groups:
                    cluster_groups[label] = []
                cluster_groups[label].append(ids[i])

        # If no clusters found or only noise, make terminal
        if not cluster_groups:
            cluster["children"].append({"type": "lines", "line_ids": ids})
            return cluster

        # Add noise points as a separate group if any
        if noise_ids:
            cluster_groups["noise"] = noise_ids

        # Create child clusters
        # Sort by label type first (integers before strings), then by value
        sorted_items = sorted(cluster_groups.items(), key=lambda x: (isinstance(x[0], str), x[0]))
        
        # Create child clusters and collect them with their max prototypicality
        child_clusters_with_scores = []
        for i, (label, child_ids) in enumerate(sorted_items):
            if child_ids:  # Only create child if it has lines
                child_cluster = create_hierarchical_clustering(
                    child_ids, level + 1, f"{label_prefix}.{i}"
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
    root = create_hierarchical_clustering(line_ids, level=1, label_prefix="C")
    return {"cluster": root}
