import hashlib


def sort_random(conc, **args):
    """
    Sorts lines pseudo-randomly while ensuring that given a specific seed,
    any pair of line_ids always appear in the same relative order regardless
    of what other line_ids are present.

    Args are dynamically validated and extracted from the schema.

    Parameters:
    - conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
    - **kwargs: Arguments defined dynamically in the schema.

    Returns:
    - dict: A dictionary containing:
        - "sort_keys": A mapping from line IDs to their stable pseudo-random ranks.
    """

    # Metadata for the algorithm
    sort_random._algorithm_metadata = {
        "name": "Random Sort",
        "description": "Sorts lines in a pseudo-random but stable manner. Given a seed, any pair of line_ids always appear in the same relative order, independent of the presence of other lines.",
        "algorithm_type": "sorting",
        "args_schema": {
            "type": "object",
            "properties": {
                "seed": {
                    "type": "integer",
                    "description": "An optional seed for generating the pseudo-random order.",
                    "default": 42
                }
            },
            "required": []
        }
    }

    # Extract arguments
    seed = args.get("seed", 42)

    # Extract line_ids
    line_ids = conc.metadata.index.tolist()

    def stable_random_key(line_id):
        # Create a stable hash from seed and line_id
        # Convert them into a string, encode, and hash with md5
        input_str = f"{seed}_{line_id}"
        hash_val = hashlib.md5(input_str.encode()).hexdigest()
        # Convert a portion of the hex hash to an integer, then to a float in [0,1)
        # For simplicity, just use the first 8 hex chars and convert to int
        int_val = int(hash_val[:8], 16)
        # Normalize to a float in [0,1) by dividing by 2^32
        # since 8 hex chars = 32 bits
        rand_float = int_val / (2**32)
        return rand_float

    # Default seed to 0 if not provided
    if seed is None:
        seed = 0

    # Sort line IDs based on the stable random key
    line_ids_sorted = sorted(line_ids, key=stable_random_key)

    # Map line IDs to their rank
    sort_keys = {line_id: rank for rank, line_id in enumerate(line_ids_sorted, start=1)}

    return {"sort_keys": sort_keys}
