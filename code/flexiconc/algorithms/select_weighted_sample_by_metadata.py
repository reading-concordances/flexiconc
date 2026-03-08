import numpy as np

def select_weighted_sample_by_metadata(conc, **args):
    """
    Selects a weighted sample of lines based on the distribution of a specified metadata attribute.

    Args are dynamically validated and extracted from the schema.

    Parameters:
    - conc (Concordance or ConcordanceSubset): The concordance data.
    - args (dict): Arguments include:
        - metadata_attribute (str): The metadata attribute to stratify by (e.g., 'genre', 'speaker').
        - sample_size (int): The total number of lines to sample.
        - seed (int, optional): Random seed for reproducibility. Default is None.

    Returns:
    - dict: A dictionary containing:
        - 'selected_lines': A list of line IDs that have been sampled.
        - 'line_count': The total number of lines sampled.
    """

    # Metadata for the algorithm
    select_weighted_sample_by_metadata._algorithm_metadata = {
        "name": "Select Weighted Sample by Metadata",
        "description": "Selects a weighted sample of lines based on the distribution of a specified metadata attribute.",
        "algorithm_type": "selecting",
        "conditions": {"x-eval": "has_metadata_attributes(conc)"},
        "args_schema": {
            "type": "object",
            "properties": {
                "metadata_attribute": {
                    "type": "string",
                    "description": "The metadata attribute to stratify by (e.g., 'text_id', 'speaker').",
                    "x-eval": "dict(enum=list(set(conc.metadata.columns) - {'line_id'}))"
                },
                "sample_size": {
                    "type": "integer",
                    "description": "The total number of lines to sample.",
                    "minimum": 1,
                    "x-eval": "dict(maximum=node.line_count)"
                },
                "seed": {
                    "type": ["integer"],
                    "description": "An optional seed for generating the pseudo-random order.",
                    "default": 42
                }
            },
            "required": ["metadata_attribute", "sample_size"]
        }
    }

    # Extract arguments
    metadata_attribute = args["metadata_attribute"]
    sample_size = args["sample_size"]
    seed = args.get("seed", None)

    # Validate input parameters
    if metadata_attribute not in conc.metadata.columns:
        raise ValueError(f"Metadata attribute '{metadata_attribute}' not found in the metadata DataFrame.")

    if seed is not None:
        np.random.seed(seed)

    # Get the counts of each category in the metadata attribute
    counts = conc.metadata[metadata_attribute].value_counts()

    # Compute the proportions of each category
    proportions = counts / counts.sum()

    # Compute the initial number of samples to take from each category
    samples_per_category = (proportions * sample_size).round().astype(int)

    # Adjust the total number of samples to match the desired sample_size
    total_allocated_samples = samples_per_category.sum()
    diff = sample_size - total_allocated_samples

    if diff != 0:
        # Adjust the counts to match the sample_size
        adjustment_order = samples_per_category.sort_values(ascending=False).index.tolist()
        for category in adjustment_order:
            if diff == 0:
                break
            samples_per_category[category] += np.sign(diff)
            diff -= np.sign(diff)

    # Collect sampled line IDs
    selected_lines = []

    for category, n_samples in samples_per_category.items():
        if n_samples <= 0:
            continue

        # Get line IDs for this category
        category_line_ids = conc.metadata[conc.metadata[metadata_attribute] == category].index.tolist()

        # If requested samples exceed available lines, adjust n_samples
        n_samples = min(n_samples, len(category_line_ids))

        # Sample without replacement
        sampled_ids = np.random.choice(category_line_ids, size=n_samples, replace=False)
        selected_lines.extend(sampled_ids)

    # Ensure the total number of sampled lines matches the desired sample_size
    if len(selected_lines) > sample_size:
        selected_lines = np.random.choice(selected_lines, size=sample_size, replace=False).tolist()
    elif len(selected_lines) < sample_size:
        remaining_line_ids = conc.metadata.index.difference(selected_lines)
        additional_samples = np.random.choice(remaining_line_ids, size=sample_size - len(selected_lines), replace=False)
        selected_lines.extend(additional_samples.tolist())

    result = {
        'selected_lines': sorted(selected_lines)
    }

    return result
