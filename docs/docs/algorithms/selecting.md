# Selecting Algorithms

## Select by Metadata Attribute

**Path:** `flexiconc/algorithms/select_by_metadata_attribute.py`

**Description:**

Selects lines based on whether a specified metadata attribute compares to a given target value. If a list is provided as the target value, membership is tested using equality. For a single numeric value, a comparison operator (==, <, <=, >, >=) can be specified. For strings, only equality (with optional regex matching and case sensitivity) is supported.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| metadata_attribute | string | The metadata attribute to filter on. |
| value | ['string', 'number', 'array'] | The value to compare against, or a list of acceptable values. When a list is provided, only equality is used. |
| operator | string | The comparison operator for numeric comparisons. Only allowed for single numeric values. Default is '=='. |
| regex | boolean | If True, use regex matching for string comparisons (only with equality). Default is False. |
| case_sensitive | boolean | If True, perform case-sensitive matching for strings. Default is False. |
| negative | boolean | If True, invert the selection. Default is False. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "metadata_attribute": {
      "type": "string",
      "description": "The metadata attribute to filter on.",
      "x-eval": "dict(enum=list(set(conc.metadata.columns) - {'line_id'}))"
    },
    "value": {
      "type": [
        "string",
        "number",
        "array"
      ],
      "description": "The value to compare against, or a list of acceptable values. When a list is provided, only equality is used."
    },
    "operator": {
      "type": "string",
      "enum": [
        "==",
        "<",
        "<=",
        ">",
        ">="
      ],
      "description": "The comparison operator for numeric comparisons. Only allowed for single numeric values. Default is '=='.",
      "default": "=="
    },
    "regex": {
      "type": "boolean",
      "description": "If True, use regex matching for string comparisons (only with equality). Default is False.",
      "default": false
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "If True, perform case-sensitive matching for strings. Default is False.",
      "default": false
    },
    "negative": {
      "type": "boolean",
      "description": "If True, invert the selection. Default is False.",
      "default": false
    }
  },
  "required": [
    "metadata_attribute",
    "value"
  ]
}
```

</details>

---

## Select by Rank

**Path:** `flexiconc/algorithms/select_rank_wrapper.py`

**Description:**

Selects lines based on rank values obtained from the ranking keys in the ordering_result['rank_keys'] of the current node, by default by the first ranking key. 

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| ranking_column | string | The ranking column to use for selection. |
| comparison_operator | string | The comparison operator to use for the ranking scores. |
| value | number | The numeric value to compare the ranking scores against. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "ranking_column": {
      "type": "string",
      "description": "The ranking column to use for selection.",
      "x-eval": "dict(enum=[f'{x}: {node.algorithms[\"ordering\"][x][\"algorithm_name\"]}' for x in list(node.ordering_result['rank_keys'])], default=[f'{x}: {node.algorithms[\"ordering\"][x][\"algorithm_name\"]}' for x in list(node.ordering_result['rank_keys'])][0])"
    },
    "comparison_operator": {
      "type": "string",
      "enum": [
        "==",
        "<=",
        ">=",
        "<",
        ">"
      ],
      "description": "The comparison operator to use for the ranking scores.",
      "default": "=="
    },
    "value": {
      "type": "number",
      "description": "The numeric value to compare the ranking scores against.",
      "default": 0
    }
  },
  "required": []
}
```

</details>

---

## Select by Token-Level Numeric Attribute

**Path:** `flexiconc/algorithms/select_by_token_numeric_value.py`

**Description:**

Selects lines based on a token-level attribute using numeric comparison at a given offset. If a list is provided for 'value', only equality comparison is performed.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| value | ['number', 'array'] | The numeric value(s) to compare against. If a list is provided, only equality comparison is supported. |
| tokens_attribute | string | The token-level attribute to check. |
| offset | integer | The token offset to check. |
| comparison_operator | string | The comparison operator to use for numeric values. Ignored if 'value' is a list. |
| negative | boolean | If True, inverts the selection. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "value": {
      "type": [
        "number",
        "array"
      ],
      "items": {
        "type": "number"
      },
      "description": "The numeric value(s) to compare against. If a list is provided, only equality comparison is supported.",
      "default": 0
    },
    "tokens_attribute": {
      "type": "string",
      "description": "The token-level attribute to check.",
      "x-eval": "dict(enum=[col for col in list(conc.tokens.columns) if col not in {'id_in_line', 'line_id', 'offset'} and ('int' in str(conc.tokens[col].dtype) or 'float' in str(conc.tokens[col].dtype))])"
    },
    "offset": {
      "type": "integer",
      "description": "The token offset to check.",
      "default": 0,
      "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
    },
    "comparison_operator": {
      "type": "string",
      "enum": [
        "==",
        "<",
        ">",
        "<=",
        ">="
      ],
      "description": "The comparison operator to use for numeric values. Ignored if 'value' is a list.",
      "default": "=="
    },
    "negative": {
      "type": "boolean",
      "description": "If True, inverts the selection.",
      "default": false
    }
  },
  "required": [
    "value",
    "tokens_attribute"
  ]
}
```

</details>

---

## Select by Token-Level String Attribute

**Path:** `flexiconc/algorithms/select_by_token_string.py`

**Description:**

Selects lines based on a token-level attribute (string matching) at a given offset. Supports regex and case sensitivity. The search_terms argument is a list of strings to match against.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| search_terms | array | The list of string values to match against. |
| tokens_attribute | string | The token attribute to check (e.g., 'word'). |
| offset | integer | The token offset to check. |
| case_sensitive | boolean | If True, performs a case-sensitive match. |
| regex | boolean | If True, uses regex matching. |
| negative | boolean | If True, inverts the selection. |


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
      "description": "The list of string values to match against.",
      "default": []
    },
    "tokens_attribute": {
      "type": "string",
      "description": "The token attribute to check (e.g., 'word').",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "offset": {
      "type": "integer",
      "description": "The token offset to check.",
      "default": 0,
      "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "If True, performs a case-sensitive match.",
      "default": false
    },
    "regex": {
      "type": "boolean",
      "description": "If True, uses regex matching.",
      "default": false
    },
    "negative": {
      "type": "boolean",
      "description": "If True, inverts the selection.",
      "default": false
    }
  },
  "required": [
    "search_terms"
  ]
}
```

</details>

---

## Manual Line Selection

**Path:** `flexiconc/algorithms/select_manual.py`

**Description:**

Manually selects lines into a subset by specifying line IDs or groups (partitions or clusters) from the active node's grouping result. Additionally, ensures selection is restricted to allowed lines.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| line_ids | array | A list of specific line IDs to include in the subset. |
| groups | array | A list of group identifiers (by label or number) to include lines from. For clusters, groups may be nested, and all matching groups in the hierarchy will be used. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "line_ids": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "description": "A list of specific line IDs to include in the subset."
    },
    "groups": {
      "type": "array",
      "items": {
        "type": [
          "string",
          "integer"
        ]
      },
      "description": "A list of group identifiers (by label or number) to include lines from. For clusters, groups may be nested, and all matching groups in the hierarchy will be used."
    }
  },
  "required": []
}
```

</details>

---

## Random Sample

**Path:** `flexiconc/algorithms/select_random.py`

**Description:**

Selects a random sample of lines from the concordance, optionally using a seed.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| sample_size | integer | The number of lines to sample. |
| seed | integer | The seed for random number generation. |


<details>
<summary>Show full JSON schema</summary>

```json
{
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
  "required": [
    "sample_size"
  ]
}
```

</details>

---

## Select Slot

**Path:** `flexiconc/algorithms/select_slot.py`

**Description:**

Selects the slot to work with.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| slot_id | integer | The slot identifier to select. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "slot_id": {
      "type": "integer",
      "description": "The slot identifier to select.",
      "x-eval": "dict(enum=list(set(conc.matches['slot'])))"
    }
  },
  "required": [
    "slot_id"
  ]
}
```

</details>

---

## Select Weighted Sample by Metadata

**Path:** `flexiconc/algorithms/select_weighted_sample_by_metadata.py`

**Description:**

Selects a weighted sample of lines based on the distribution of a specified metadata attribute.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| metadata_attribute | string | The metadata attribute to stratify by (e.g., 'text_id', 'speaker'). |
| sample_size | integer | The total number of lines to sample. |
| seed | ['integer'] | An optional seed for generating the pseudo-random order. |


<details>
<summary>Show full JSON schema</summary>

```json
{
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
      "type": [
        "integer"
      ],
      "description": "An optional seed for generating the pseudo-random order.",
      "default": 42
    }
  },
  "required": [
    "metadata_attribute",
    "sample_size"
  ]
}
```

</details>

---

