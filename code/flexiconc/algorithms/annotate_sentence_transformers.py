from sentence_transformers import SentenceTransformer
import pandas as pd
from pathlib import Path

def annotate_sentence_transformers(conc, **args) -> pd.Series:
    """
    Generate sentence-level embeddings for every concordance line (or the
    selected token window) using a Sentence Transformer model.

    Parameters
    ----------
    tokens_attribute : str, optional
        Positional-attribute column to read tokens from (default ``"word"``).
    window_start : int | None, optional
        Lower bound of the offset window (inclusive). ``None`` means
        unbounded to the left (default ``None``).
    window_end : int | None, optional
        Upper bound of the offset window (inclusive). ``None`` means
        unbounded to the right (default ``None``).
    model_name : str, optional
        Name of the pretrained Sentence Transformer model
        (default ``"all-MiniLM-L6-v2"``).

    Returns
    -------
    pandas.Series
        Series indexed by concordance line IDs; each element is a NumPy
        array representing the embedding for that line.

    Notes
    -----
    * Embeddings are cached in ``~/.cache/sentence_transformers`` by default.
    * If no window bounds are given, the entire line is encoded.
    """


    # Metadata for the algorithm
    annotate_sentence_transformers._algorithm_metadata = {
        "name": "Annotate with Sentence Transformers",
        "description": (
            "Generates embeddings for each concordance line (or part of it) using a Sentence Transformer model. "
            "Allows selection of tokens within a specified window and based on a specified token attribute."
        ),
        "algorithm_type": "annotation",
        "requires": ["sentence_transformers>=3.0.0"],
        "scope": "line",
        "args_schema": {
            "type": "object",
            "properties": {
                "tokens_attribute": {
                    "type": "string",
                    "description": "The positional attribute to extract tokens from (e.g., 'word').",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "window_start": {
                    "type": "integer",
                    "description": "The lower bound of the window (inclusive). If None, uses the entire line.",
                    "x-eval": "dict(minimum=min(conc.tokens['offset']))"
                },
                "window_end": {
                    "type": "integer",
                    "description": "The upper bound of the window (inclusive). If None, uses the entire line.",
                    "x-eval": "dict(maximum=max(conc.tokens['offset']))"
                },
                "model_name": {
                    "type": "string",
                    "description": "The name of the pretrained Sentence Transformer model.",
                    "default": "all-MiniLM-L6-v2"
                }
            },
            "required": []
        }
    }

    # Extract arguments
    tokens_attribute = args.get("tokens_attribute", "word")
    window_start = args.get("window_start", None)
    window_end = args.get("window_end", None)
    model_name = args.get("model_name", "all-MiniLM-L6-v2")

    # Use a default cache folder in the user's home directory.
    default_cache_folder = str(Path.home() / ".cache" / "sentence_transformers")
    model = SentenceTransformer(model_name, cache_folder=default_cache_folder)

    # Extract tokens within the specified window for each line
    def get_line_text(line_id):
        # Filter tokens for the specific line ID within the window range, or take the whole line if window_start/end is None
        if window_start is None and window_end is None:
            tokens = conc.tokens[conc.tokens["line_id"] == line_id][tokens_attribute].tolist()
        else:
            tokens = conc.tokens[
                (conc.tokens["line_id"] == line_id) &
                (conc.tokens["offset"] >= (window_start if window_start is not None else float('-inf'))) &
                (conc.tokens["offset"] <= (window_end if window_end is not None else float('inf')))
            ][tokens_attribute].tolist()

        # Join tokens into a single text string
        return " ".join(tokens)

    # Prepare a list of all concordance line IDs
    line_ids = conc.metadata.index.tolist()

    # Generate the sentences to encode from the concordance
    sentences = [get_line_text(line_id) for line_id in line_ids]

    # Calculate embeddings using the Sentence Transformer model
    embeddings = model.encode(sentences)

    # Convert embeddings to a Pandas Series indexed by line IDs
    embedding_series = pd.Series(data=list(embeddings), index=line_ids, name="embeddings_sentence_transformers")

    return embedding_series
