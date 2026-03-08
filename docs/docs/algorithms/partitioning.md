# Partitioning Algorithms

## Flat Clustering by Embeddings

**Path:** `flexiconc/algorithms/partition_by_embeddings.py`

**Description:**

Partitions lines based on embeddings stored in a concordance metadata column using clustering algorithms (Agglomerative Clustering or K-Means). Supports customizable distance metrics and linkage criteria.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| embeddings_column | string | The metadata column containing embeddings for each line. |
| n_partitions | integer | The number of partitions/clusters to create. |
| metric | string | The metric to compute distances between embeddings (used for Agglomerative Clustering only). |
| linkage | string | The linkage criterion for Agglomerative Clustering (used only when method is 'agglomerative'). |
| method | string | The clustering method to use ('agglomerative' or 'kmeans'). Default is 'agglomerative'. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "embeddings_column": {
      "type": "string",
      "description": "The metadata column containing embeddings for each line.",
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
      "description": "The metric to compute distances between embeddings (used for Agglomerative Clustering only).",
      "default": "cosine"
    },
    "linkage": {
      "type": "string",
      "description": "The linkage criterion for Agglomerative Clustering (used only when method is 'agglomerative').",
      "default": "average"
    },
    "method": {
      "type": "string",
      "enum": [
        "agglomerative",
        "kmeans"
      ],
      "description": "The clustering method to use ('agglomerative' or 'kmeans'). Default is 'agglomerative'.",
      "default": "kmeans"
    }
  },
  "required": [
    "embeddings_column"
  ]
}
```

</details>

---

## Partition by Metadata Attribute

**Path:** `flexiconc/algorithms/partition_by_metadata_attribute.py`

**Description:**

Partitions the concordance lines based on a specified metadata attribute and groups the data by the values of this attribute.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| metadata_attribute | string | The metadata attribute to partition by (e.g., 'text_id', 'speaker'). |
| sort_by_partition_size | boolean | If True, partitions will be sorted by size in descending order. |
| sorted_values | array | If provided, partitions will be sorted by these specific values. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "metadata_attribute": {
      "type": "string",
      "description": "The metadata attribute to partition by (e.g., 'text_id', 'speaker').",
      "x-eval": "dict(enum=list(set(conc.metadata.columns) - {'line_id'}))"
    },
    "sort_by_partition_size": {
      "type": "boolean",
      "description": "If True, partitions will be sorted by size in descending order.",
      "default": true
    },
    "sorted_values": {
      "type": "array",
      "items": {
        "type": [
          "string",
          "number"
        ]
      },
      "description": "If provided, partitions will be sorted by these specific values."
    }
  },
  "required": [
    "metadata_attribute"
  ]
}
```

</details>

---

## Partition by Ngrams

**Path:** `flexiconc/algorithms/partition_ngrams.py`

**Description:**

Extracts ngram patterns from specified positions and partitions the concordance according to their frequency in the concordance lines. Compare Anthony's (2018) KWIC Patterns and subsequent work.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| positions | array | The list of positions (offsets) to extract for the ngram pattern. |
| tokens_attribute | string | The positional attribute to search within (e.g., 'word'). |
| case_sensitive | boolean | If True, the search is case-sensitive. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "positions": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "description": "The list of positions (offsets) to extract for the ngram pattern."
    },
    "tokens_attribute": {
      "type": "string",
      "description": "The positional attribute to search within (e.g., 'word').",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "If True, the search is case-sensitive.",
      "default": false
    }
  },
  "required": [
    "positions"
  ]
}
```

</details>

---

