# Annotation Algorithms

## Annotate Association Scores

**Path:** `flexiconc/algorithms/annotate_association_scores.py`

**Description:**

Computes association scores from two frequency lists (concordance and whole corpus).

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| corpus_frequency_list | string | Name of the *corpus* frequency list registered in `conc.resources`. |
| concordance_frequency_list | string | Name of the *concordance* frequency list registered in `conc.resources`. |
| token_attribute | string | Token attribute column common to both lists. |
| ignore_case | boolean | Lowercase all string tokens before matching |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "corpus_frequency_list": {
      "type": "string",
      "description": "Name of the *corpus* frequency list registered in `conc.resources`.",
      "x-eval": "dict(enum=conc.resources.list('frequency_list'))"
    },
    "concordance_frequency_list": {
      "type": "string",
      "description": "Name of the *concordance* frequency list registered in `conc.resources`.",
      "x-eval": "dict(enum=conc.resources.list('frequency_list'))"
    },
    "token_attribute": {
      "type": "string",
      "description": "Token attribute column common to both lists."
    },
    "ignore_case": {
      "type": "boolean",
      "description": "Lowercase all string tokens before matching",
      "default": true
    }
  },
  "required": [
    "corpus_frequency_list",
    "concordance_frequency_list"
  ]
}
```

</details>

---

## Token-level Frequency List

**Path:** `flexiconc/algorithms/annotate_concordance_frequency_list.py`

**Description:**

Aggregates token frequencies within an optional window and returns a FlexiConc frequency-list resource.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| token_attribute | string | Token attribute to count types for. |
| window_start | ['integer', 'null'] | Lower bound of token window (inclusive). Null means unbounded. |
| window_end | ['integer', 'null'] | Upper bound of token window (inclusive). Null means unbounded. |
| include_node | boolean | Include the node token (offset 0) in the counting window. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "token_attribute": {
      "type": "string",
      "description": "Token attribute to count types for.",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "window_start": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Lower bound of token window (inclusive). Null means unbounded.",
      "default": null,
      "x-eval": "dict(minimum=min(conc.tokens['offset']))"
    },
    "window_end": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Upper bound of token window (inclusive). Null means unbounded.",
      "default": null,
      "x-eval": "dict(maximum=max(conc.tokens['offset']))"
    },
    "include_node": {
      "type": "boolean",
      "description": "Include the node token (offset 0) in the counting window.",
      "default": false
    }
  },
  "required": [
    "token_attribute"
  ]
}
```

</details>

---

## Annotate with Sentence Transformers

**Path:** `flexiconc/algorithms/annotate_sentence_transformers.py`

**Description:**

Generates embeddings for each concordance line (or part of it) using a Sentence Transformer model. Allows selection of tokens within a specified window and based on a specified token attribute.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| tokens_attribute | string | The positional attribute to extract tokens from (e.g., 'word'). |
| window_start | integer | The lower bound of the window (inclusive). If None, uses the entire line. |
| window_end | integer | The upper bound of the window (inclusive). If None, uses the entire line. |
| model_name | string | The name of the pretrained Sentence Transformer model. |


<details>
<summary>Show full JSON schema</summary>

```json
{
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
```

</details>

---

## Annotate with SpaCy Embeddings

**Path:** `flexiconc/algorithms/annotate_spacy_embeddings.py`

**Description:**

Generates averaged spaCy word embeddings for tokens within a specified window.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| spacy_model | string | The spaCy model to use. |
| tokens_attribute | string | The token attribute to use for creating line texts. |
| exclude_values_attribute | string | The attribute to filter out specific values. |
| exclude_values_list | array | The list of values to exclude. |
| window_start | integer | The lower bound of the token window (inclusive). |
| window_end | integer | The upper bound of the token window (inclusive). |
| include_node | boolean | Whether to include the node token (offset 0). |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "spacy_model": {
      "type": "string",
      "description": "The spaCy model to use.",
      "default": "en_core_web_md"
    },
    "tokens_attribute": {
      "type": "string",
      "description": "The token attribute to use for creating line texts.",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "exclude_values_attribute": {
      "type": "string",
      "description": "The attribute to filter out specific values."
    },
    "exclude_values_list": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "The list of values to exclude."
    },
    "window_start": {
      "type": "integer",
      "description": "The lower bound of the token window (inclusive).",
      "default": -5,
      "x-eval": "dict(minimum=min(conc.tokens['offset']))"
    },
    "window_end": {
      "type": "integer",
      "description": "The upper bound of the token window (inclusive).",
      "default": 5,
      "x-eval": "dict(maximum=max(conc.tokens['offset']))"
    },
    "include_node": {
      "type": "boolean",
      "description": "Whether to include the node token (offset 0).",
      "default": true
    }
  },
  "required": [
    "spacy_model"
  ]
}
```

</details>

---

## Annotate with spaCy POS tags

**Path:** `flexiconc/algorithms/annotate_spacy_pos.py`

**Description:**

Annotates tokens with spaCy part-of-speech tags or related tag information using a specified spaCy model. The spacy_attributes parameter is always a list, so multiple annotations can be retrieved simultaneously.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| spacy_model | string | The spaCy model to use for POS tagging. |
| tokens_attribute | string | The token attribute to use for POS tagging. |
| spacy_attributes | array | A list of spaCy token attributes to retrieve for annotation. |


<details>
<summary>Show full JSON schema</summary>

```json
{
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
        "enum": [
          "lemma_",
          "pos_",
          "tag_",
          "morph",
          "dep_",
          "ent_type_"
        ]
      },
      "description": "A list of spaCy token attributes to retrieve for annotation.",
      "default": [
        "pos_"
      ]
    }
  },
  "required": [
    "spacy_model",
    "spacy_attributes"
  ]
}
```

</details>

---

## Annotate with TF-IDF

**Path:** `flexiconc/algorithms/annotate_tf_idf.py`

**Description:**

Computes TF-IDF vectors for each line based on tokens in a specified window.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| tokens_attribute | string | The token attribute to use for creating line texts. |
| exclude_values_attribute | ['string'] | The attribute to filter out specific values. |
| exclude_values_list | array | The list of values to exclude. |
| window_start | integer | The lower bound of the token window (inclusive). |
| window_end | integer | The upper bound of the token window (inclusive). |
| include_node | boolean | Whether to include the node token (offset 0). |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "tokens_attribute": {
      "type": "string",
      "description": "The token attribute to use for creating line texts.",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "exclude_values_attribute": {
      "type": [
        "string"
      ],
      "description": "The attribute to filter out specific values."
    },
    "exclude_values_list": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "The list of values to exclude."
    },
    "window_start": {
      "type": "integer",
      "description": "The lower bound of the token window (inclusive).",
      "default": -5,
      "x-eval": "dict(minimum=min(conc.tokens['offset']))"
    },
    "window_end": {
      "type": "integer",
      "description": "The upper bound of the token window (inclusive).",
      "default": 5,
      "x-eval": "dict(maximum=max(conc.tokens['offset']))"
    },
    "include_node": {
      "type": "boolean",
      "description": "Whether to include the node token (offset 0).",
      "default": true
    }
  },
  "required": []
}
```

</details>

---

