import random


def select_random(conc, **args):
    """
    Selects a random sample of line IDs from the concordance metadata.

    Args are dynamically validated and extracted from the schema.

    Parameters:
    - conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
    - **kwargs: Arguments defined dynamically in the schema.

    Returns:
    - dict: A dictionary containing:
        - "selected_lines": A list of randomly selected line IDs.
        - "line_count": The number of selected lines.
    """

    # Metadata for the algorithm
    select_random._algorithm_metadata = {
        "name": "Random Sample",
        "description": "Selects a random sample of lines from the concordance, optionally using a seed.",
        "algorithm_type": "selecting",
        "args_schema": {
            "type": "object",
            "properties": {
                "sample_size": {
                    "type": "integer",
                    "description": "The number of lines to sample.",
                    "minimum": 1,
                    "x-eval": "dict(maximum=node.line_count)"
                },
                "seed": {
                    "type": "integer",
                    "description": "The seed for random number generation.",
                    "default": 42
                }
            },
            "required": ["sample_size"]
        }
    }

    # Extract arguments
    sample_size = args["sample_size"]
    seed = args.get("seed", 42)

    # Prepare the line IDs from the concordance metadata
    line_ids = conc.metadata.index.tolist()

    # Set the random seed if provided
    if seed is not None:
        random.seed(seed)

    # Randomly sample line IDs and maintain original order by sorting the sampled indices
    sampled_indices = sorted(random.sample(range(len(line_ids)), min(sample_size, len(line_ids))))
    selected_lines = [line_ids[i] for i in sampled_indices]

    # Return the selected lines and their count
    return {
        "selected_lines": selected_lines
    }