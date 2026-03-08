# Sorting Algorithms

## Sort by Corpus Position

**Path:** `flexiconc/algorithms/sort_by_corpus_position.py`

**Description:**

Sorts the concordance lines by their line_id, which corresponds to their position in the corpus.

**Arguments:**

_No arguments defined._

<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

</details>

---

## Sort by Token-Level Attribute

**Path:** `flexiconc/algorithms/sort_by_token_attribute.py`

**Description:**

Sorts the concordance lines by the given token-level attribute using locale-specific sorting (default 'en'). Supports sorting by a single token at a given offset, or by whole left/right context by joining tokens. When sorting by left context, tokens are joined from right to left. Optionally reverses strings for right-to-left sorting.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| tokens_attribute | string | The token attribute to sort by. |
| sorting_scope | string | Specifies which context to use for sorting: 'token' for a single token at the given offset, 'left' for the entire left context (joined from right to left), or 'right' for the entire right context. |
| offset | integer | The offset value to filter tokens by when sorting_scope is 'token'. |
| case_sensitive | boolean | If True, performs a case-sensitive sort. |
| reverse | boolean | If True, sort in descending order. |
| backwards | boolean | If True, reverses the string (e.g., for right-to-left sorting). |
| locale_str | string | ICU locale string for language-specific sorting. |


<details>
<summary>Show full JSON schema</summary>

```json
{
  "type": "object",
  "properties": {
    "tokens_attribute": {
      "type": "string",
      "description": "The token attribute to sort by.",
      "default": "word",
      "x-eval": "dict(enum=list(set(conc.tokens.columns) - {'id_in_line', 'line_id', 'offset'}))"
    },
    "sorting_scope": {
      "type": "string",
      "description": "Specifies which context to use for sorting: 'token' for a single token at the given offset, 'left' for the entire left context (joined from right to left), or 'right' for the entire right context.",
      "default": "token",
      "enum": [
        "token",
        "left",
        "right"
      ]
    },
    "offset": {
      "type": "integer",
      "description": "The offset value to filter tokens by when sorting_scope is 'token'.",
      "default": 0,
      "x-eval": "dict(minimum=min(conc.tokens['offset']), maximum=max(conc.tokens['offset']))"
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "If True, performs a case-sensitive sort.",
      "default": false
    },
    "reverse": {
      "type": "boolean",
      "description": "If True, sort in descending order.",
      "default": false
    },
    "backwards": {
      "type": "boolean",
      "description": "If True, reverses the string (e.g., for right-to-left sorting).",
      "default": false
    },
    "locale_str": {
      "type": "string",
      "description": "ICU locale string for language-specific sorting.",
      "default": "en"
    }
  },
  "required": []
}
```

</details>

---

## Random Sort

**Path:** `flexiconc/algorithms/sort_random.py`

**Description:**

Sorts lines in a pseudo-random but stable manner. Given a seed, any pair of line_ids always appear in the same relative order, independent of the presence of other lines.

**Arguments:**

| Name | Type | Description |
| --- | --- | --- |
| seed | integer | An optional seed for generating the pseudo-random order. |


<details>
<summary>Show full JSON schema</summary>

```json
{
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
```

</details>

---

