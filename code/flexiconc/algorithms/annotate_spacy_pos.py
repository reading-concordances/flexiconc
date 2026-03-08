import spacy
import pandas as pd


def annotate_spacy_pos(conc, **args):
    """
    Annotate each token with spaCy part-of-speech (POS) information or other
    token-level attributes.

    The function returns a ``pandas.DataFrame`` indexed by token IDs; every
    requested spaCy attribute is stored in its own column.  The annotation
    scope is **token**.

    Parameters
    ----------
    spacy_model : str, optional
        Name of the spaCy pipeline to run
        (default ``"en_core_web_sm"``).
    tokens_attribute : str, optional
        Concordance token-attribute column whose string values are tagged
        (default ``"word"``).
    spacy_attributes : list[str], optional
        List of spaCy ``Token`` attributes to extract.  Allowed values are
        ``"lemma_"``, ``"pos_"``, ``"tag_"``, ``"morph"``, ``"dep_"``,
        ``"ent_type_"`` (default ``["pos_"]``).

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by ``conc.tokens`` index with one column per
        requested attribute.

    Notes
    -----
    * ``spacy_attributes`` is always interpreted as a list; supply a single
      attribute as ``["attribute_name"]``.
    * If a token cannot be processed, an empty string is stored for every
      requested attribute.
    """

    # Metadata for the algorithm
    annotate_spacy_pos._algorithm_metadata = {
        "name": "Annotate with spaCy POS tags",
        "description": (
            "Annotates tokens with spaCy part-of-speech tags or related tag information using a specified spaCy model. "
            "The spacy_attributes parameter is always a list, so multiple annotations can be retrieved simultaneously."
        ),
        "algorithm_type": "annotation",
        "scope": "token",
        "requires": ["spacy>=3.8.4"],
        "args_schema": {
            "type": "object",
            "properties": {
                "spacy_model": {
                    "type": "string",
                    "description": "The spaCy model to use for POS tagging.",
                    "default": "en_core_web_sm"
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "The token attribute to use for POS tagging.",
                    "default": "word",
                    "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
                },
                "spacy_attributes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["lemma_", "pos_", "tag_", "morph", "dep_", "ent_type_"]
                    },
                    "description": "A list of spaCy token attributes to retrieve for annotation.",
                    "default": ["pos_"]
                }
            },
            "required": ["spacy_model", "spacy_attributes"]
        }
    }

    # Extract arguments
    spacy_model = args.get("spacy_model", "en_core_web_sm")
    tokens_attribute = args.get("tokens_attribute", "word")
    spacy_attributes = args.get("spacy_attributes", ["pos_"])
    # Ensure spacy_attributes is a list.
    if not isinstance(spacy_attributes, list):
        spacy_attributes = [spacy_attributes]

    # Load the spaCy model.
    nlp = spacy.load(spacy_model)

    # Get the token values as strings from the specified token attribute.
    tokens_series = conc.tokens[tokens_attribute].astype(str)

    # Process tokens in batches.
    docs = list(nlp.pipe(tokens_series, batch_size=100))

    # Build results for each requested attribute.
    results = {attr: [] for attr in spacy_attributes}
    for doc in docs:
        if doc:
            for attr in spacy_attributes:
                results[attr].append(getattr(doc[0], attr))
        else:
            for attr in spacy_attributes:
                results[attr].append("")

    return pd.DataFrame(results, index=tokens_series.index)
