# Ranking Algorithms

## Collocation Ranker

**Path:** `flexiconc/algorithms/rank_by_collocations.py`

**Description:**

Ranks lines by the sum (or count) of association-measure scores within a window.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| scores_list | string | Name of a *scores* resource registered in `conc.resources`. |
| token_attribute | string | Token attribute shared by the scores table and the concordance tokens. |
| score_column | string | Numeric column in the scores table to use. |
| top_n | ['integer', 'null'] | Number of top collocates to take into account. |
| method | string | 'sum' = add up scores, 'count' = count top-N collocates. |
| window_start | ['integer', 'null'] | Lower bound of token window (inclusive). |
| window_end | ['integer', 'null'] | Upper bound of token window (inclusive). |
| positive_filter | object | Only include tokens matching these {attribute: [values]} pairs. |
| negative_filter | object | Exclude tokens matching these {attribute: [values]} pairs. |
| include_node | boolean | Include the node token (offset 0) in the window. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "scores_list": {
      "type": "string",
      "description": "Name of a *scores* resource registered in `conc.resources`.",
      "x-eval": "dict(enum=conc.resources.list('scores'))"
    },
    "token_attribute": {
      "type": "string",
      "description": "Token attribute shared by the scores table and the concordance tokens.",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "score_column": {
      "type": "string",
      "description": "Numeric column in the scores table to use.",
      "default": "log_local_MI"
    },
    "top_n": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Number of top collocates to take into account.",
      "default": null
    },
    "method": {
      "type": "string",
      "enum": [
        "sum",
        "count"
      ],
      "description": "'sum' = add up scores, 'count' = count top-N collocates.",
      "default": "sum"
    },
    "window_start": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Lower bound of token window (inclusive).",
      "default": null,
      "x-eval": "dict(minimum=min(conc.tokens['offset']))"
    },
    "window_end": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Upper bound of token window (inclusive).",
      "default": null,
      "x-eval": "dict(maximum=max(conc.tokens['offset']))"
    },
    "positive_filter": {
      "type": "object",
      "description": "Only include tokens matching these {attribute: [values]} pairs."
    },
    "negative_filter": {
      "type": "object",
      "description": "Exclude tokens matching these {attribute: [values]} pairs."
    },
    "include_node": {
      "type": "boolean",
      "description": "Include the node token (offset 0) in the window.",
      "default": false
    }
  },
  "required": [
    "scores_list"
  ]
}
```

</details>

---

## KWIC Grouper Ranker

**Path:** `flexiconc/algorithms/rank_kwic_grouper.py`

**Description:**

Ranks lines based on the count of search terms in a specified token attribute within a window.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| search_terms | array | A list of terms to search for within the tokens. |
| tokens_attribute | string | The token attribute to search within (e.g., 'word'). |
| mode | string | Matching strategy for search_terms |
| case_sensitive | boolean | If True, the search is case-sensitive. |
| include_node | boolean | If True, include node-level tokens in the search. |
| window_start | integer | The lower bound of the window (offset range). |
| window_end | integer | The upper bound of the window (offset range). |
| count_types | boolean | If True, count unique types within each line; otherwise, count all matches. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "search_terms": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "A list of terms to search for within the tokens."
    },
    "tokens_attribute": {
      "type": "string",
      "description": "The token attribute to search within (e.g., 'word').",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "mode": {
      "type": "string",
      "enum": [
        "literal",
        "regex",
        "cqp"
      ],
      "description": "Matching strategy for search_terms",
      "default": "literal"
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "If True, the search is case-sensitive.",
      "default": false
    },
    "include_node": {
      "type": "boolean",
      "description": "If True, include node-level tokens in the search.",
      "default": false
    },
    "window_start": {
      "type": "integer",
      "description": "The lower bound of the window (offset range).",
      "x-eval": "dict(minimum=min(conc.tokens['offset']))"
    },
    "window_end": {
      "type": "integer",
      "description": "The upper bound of the window (offset range).",
      "x-eval": "dict(maximum=max(conc.tokens['offset']))"
    },
    "count_types": {
      "type": "boolean",
      "description": "If True, count unique types within each line; otherwise, count all matches.",
      "default": true
    }
  },
  "required": [
    "search_terms"
  ]
}
```

</details>

---

## Rank by Number of Rare Words

**Path:** `flexiconc/algorithms/rank_number_of_rare_words.py`

**Description:**

Ranks lines by their count of rare words.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| p_attr | string | Token attribute to look up in the frequency list |
| freq_list | string | Name of a registered frequency list |
| frequency_type | string | Type of frequency to use: raw frequency ('f'), relative frequency ('rel_f'), or instances per million words ('pmw'). |
| threshold | number | Frequency threshold below which tokens count as rare |
| rank_threshold | integer | Rank threshold above which tokens count as rare |
| window_start | integer | Lower bound of the token-offset window (inclusive) |
| window_end | integer | Upper bound of the token-offset window (inclusive) |
| case_sensitive | boolean | Match tokens against the frequency list case-sensitively |
| positive | boolean | If True, the score is the raw count of rare tokens (more-rare → higher score). If False (default), score is the *negative* count so lines with fewer rare words rank higher. |
| ignore_attrs | object | Mapping of token attrs → list of values to ignore |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "p_attr": {
      "type": "string",
      "description": "Token attribute to look up in the frequency list",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line','line_id','offset'}))"
    },
    "freq_list": {
      "type": "string",
      "description": "Name of a registered frequency list",
      "x-eval": "dict(enum=conc.resources.list('frequency_list'))"
    },
    "frequency_type": {
      "type": "string",
      "description": "Type of frequency to use: raw frequency ('f'), relative frequency ('rel_f'), or instances per million words ('pmw').",
      "enum": [
        "f",
        "rel_f",
        "pmw"
      ],
      "default": "pmw"
    },
    "threshold": {
      "type": "number",
      "description": "Frequency threshold below which tokens count as rare"
    },
    "rank_threshold": {
      "type": "integer",
      "description": "Rank threshold above which tokens count as rare"
    },
    "window_start": {
      "type": "integer",
      "description": "Lower bound of the token-offset window (inclusive)"
    },
    "window_end": {
      "type": "integer",
      "description": "Upper bound of the token-offset window (inclusive)"
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "Match tokens against the frequency list case-sensitively",
      "default": false
    },
    "positive": {
      "type": "boolean",
      "description": "If True, the score is the raw count of rare tokens (more-rare \u2192 higher score). If False (default), score is the *negative* count so lines with fewer rare words rank higher.",
      "default": false
    },
    "ignore_attrs": {
      "type": "object",
      "description": "Mapping of token attrs \u2192 list of values to ignore",
      "default": {},
      "x-eval": "dict(propertyNames={'enum': list(set(conc.tokens.columns) - {'id_in_line','line_id','offset'})})",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": [
            "string",
            "number",
            "boolean"
          ]
        }
      }
    }
  },
  "required": [
    "p_attr",
    "freq_list"
  ]
}
```

</details>

---

