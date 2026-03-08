from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics.pairwise import pairwise_distances
import numpy as np

def partition_by_embeddings(conc, **args):
    """
    Partition concordance lines into clusters based on pre-computed
    line-embeddings stored in a metadata column.

    Parameters
    ----------
    embeddings_column : str
        Name of the concordance ``metadata`` column that holds an embedding
        vector for every line.
    n_partitions : int, optional
        Number of clusters to produce (default ``5``).
    method : {'agglomerative', 'kmeans'}, optional
        Clustering algorithm to use (default ``'agglomerative'``).
    metric : str, optional
        Distance metric for agglomerative clustering (default ``'cosine'``;
        ignored for k-means).
    linkage : str, optional
        Linkage criterion for agglomerative clustering (default ``'average'``).

    Returns
    -------
    dict
        ``{"partitions": [ {"id": int,
                             "label": str,
                             "line_ids": list[int]}, … ]}``

    Notes
    -----
    * The order of ``partitions`` follows the sorted unique cluster labels.
    * ``line_ids`` are concordance line identifiers.
    """


    # Metadata for the algorithm
    partition_by_embeddings._algorithm_metadata = {
        "name": "Flat Clustering by Embeddings",
        "description": (
            "Partitions lines based on embeddings stored in a concordance metadata column using clustering algorithms "
            "(Agglomerative Clustering or K-Means). Supports customizable distance metrics and linkage criteria."
        ),
        "algorithm_type": "partitioning",
        "requires": ["scikit_learn>=1.3.0"],
        "conditions": {"x-eval": "has_embeddings(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "embeddings_column": {
                    "type": "string",
                    "description": "The metadata column containing embeddings for each line.",
                    # Check if the column is iterable and contains only numbers
                    "x-eval": "dict(enum=[col for col in list(conc.metadata.columns) if (hasattr(conc.metadata[col].iloc[0], '__iter__') and not isinstance(conc.metadata[col].iloc[0], str) and all(isinstance(x, __import__('numbers').Number) for x in conc.metadata[col].iloc[0]))])"
                },
                "n_partitions": {
                    "type": "integer",
                    "description": "The number of partitions/clusters to create.",
                    "default": 5,
                    "x-eval": "dict(maximum=node.line_count)"
                },
                "metric": {
                    "type": "string",
                    "description": (
                        "The metric to compute distances between embeddings (used for Agglomerative Clustering only)."
                    ),
                    "default": "cosine"
                },
                "linkage": {
                    "type": "string",
                    "description": (
                        "The linkage criterion for Agglomerative Clustering (used only when method is 'agglomerative')."
                    ),
                    "default": "average"
                },
                "method": {
                    "type": "string",
                    "enum": ["agglomerative", "kmeans"],
                    "description": (
                        "The clustering method to use ('agglomerative' or 'kmeans'). Default is 'agglomerative'."
                    ),
                    "default": "kmeans"
                }
            },
            "required": ["embeddings_column"]
        }
    }

    # Extract arguments
    embeddings_column = args["embeddings_column"]
    n_partitions = args.get("n_partitions", 5)
    metric = args.get("metric", "cosine")
    linkage = args.get("linkage", "average")
    method = args.get("method", "agglomerative")

    # Retrieve embeddings from the concordance metadata
    if embeddings_column not in conc.metadata.columns:
        raise ValueError(f"The embeddings column '{embeddings_column}' is not present in the concordance metadata.")

    embeddings = np.vstack(conc.metadata[embeddings_column].to_numpy())
    line_ids = conc.metadata.index.tolist()

    # Perform clustering based on the selected method
    if method == "agglomerative":
        # Compute the distance matrix for Agglomerative Clustering
        if metric == "cosine":
            dist_matrix = pairwise_distances(embeddings, metric=metric)
        else:
            raise ValueError(f"Unsupported metric for Agglomerative Clustering: {metric}. Only 'cosine' is supported.")

        cluster_model = AgglomerativeClustering(
            n_clusters=n_partitions,
            metric=metric,
            linkage=linkage
        )
        labels = cluster_model.fit_predict(embeddings)

    elif method == "kmeans":
        # Perform K-Means Clustering
        cluster_model = KMeans(n_clusters=n_partitions, random_state=42, n_init=10)
        labels = cluster_model.fit_predict(embeddings)

    else:
        raise ValueError(f"Unsupported clustering method: {method}. Choose 'agglomerative' or 'kmeans'.")

    result = {
        "partitions": [
            {
                "id": idx,
                "label": f"Cluster_{lbl}",
                "line_ids": [line_ids[i] for i, l in enumerate(labels) if l == lbl]
            }
            for idx, lbl in enumerate(sorted(np.unique(labels)))
        ]
    }

    return result
