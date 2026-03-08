# Concordance Views

The `view()` method of an `AnalysisTreeNode` returns a dictionary representing a concordance view. This view is a structured, JSON-serializable summary of the concordance data at a given node in the analysis tree. The output is organized into several keys, each providing specific information about the concordance lines and any additional processing (ordering, grouping, ranking, token spans) that has been applied.

Below is the exact specification of the output:

---

## 1. `selected_lines`

- **Type:** `List[int]`
- **Description:**  
  A list of line numbers (indices from the original concordance metadata) that are visible in the view.
    - **If the node defines its own `selected_lines`:** That list is used.
    - **Otherwise:** The view inherits `selected_lines` from the nearest ancestor that has them.
    - **Fallback:** If no such ancestor exists, it defaults to all line numbers in the concordance metadata.

---

## 2. `ordering`

- **Type:** `List[int]`
- **Description:**  
  An ordered list of the visible line numbers. This ordering is determined by:
    - The node’s own `ordering_result["sort_keys"]`, if present.
    - Or, inherited from the nearest ancestor that has an ordering result.
  - **Filtering:** Only line numbers present in the current node’s `selected_lines` are included.
  - **Default:** If no ordering is defined, it falls back to the natural order (using the line number as the sort key).

---

## 3. `grouping` (Optional)

- **Type:** `dict`
- **Description:** Included only when a grouping / clustering algorithm has been applied to the node. The object bundles **column metadata** and the **actual list / tree of groups**.

```jsonc
"grouping": {
  "column_info": [          
    {"name": "Quality", "type": "float", "description": "Silhouette score", ...},
    {"name": "Size",    "type": "int",   "description": "Number of lines",   ...}
  ],
  "partitions": [           // or "clusters" for hierarchical output
    {
      "id": 0,
      "label": "Cluster_0",
      "line_ids": [ ... ],    // ordered according to the global ordering
      "prototypes": [ ... ],  // optional
      "info": {               // keys correspond to column_info
        "Quality": 0.72,
        "Size": 37
      }
    },
    {
      "id": 1,
      "label": "Cluster_1",
      "line_ids": [ ... ],
      "info": {
        "Quality": 0.65,
        "Size": 22
      }
    }
  ]
}
```

* **`grouping`** *(object)*  
  * **`column_info`** – `List[dict]` describing each supplementary group‑level metric.  
  * **`partitions`** or **`clusters`** – `List[Group]`; flat for partitions or hierarchical when using clusters.

* **`Group`** *(object)*  
  * **`id`** – `int`, required.  
  * **`label`** – `str`, optional display name.  
  * **`line_ids`** – `List[int]`, required for leaf groups (ordered by the view’s `ordering`).  
  * **`prototypes`** – `List[int]`, optional representative lines.  
  * **`info`** – `Dict[str, Any]` keyed by the entries in `column_info`.  
  * **`children`** – `List[Group]`, only present for hierarchical clusterings.

### 3.1 `column_info` `column_info`
Lists group‑level columns (e.g. cluster quality, within‑variance, size).

### 3.2 `partitions` / `clusters`
A flat list (for partitions) or a recursive list (for clusters). Each dict can contain:

| Key | Type | Always? | Meaning |
|-----|------|---------|---------|
| `id` | `int` | ✔︎ | Numeric identifier. |
| `label` | `str` | ✖︎ | Human‑readable name to be shown in UI. |
| `line_ids` | `List[int]` | ✔︎ for partitions / leaf clusters | Lines that belong to this group. Ordered according to the view’s `ordering`. |
| `prototypes` | `List[int]` | ✖︎ | Representative line‑ids. |
| `info` | `Dict[str,Any]` | ✔︎ (may be empty) | Values keyed by `column_info[i]["name"]`. |
| `children` | `List[dict]` | ✖︎ | Present only for hierarchical clustering; same structure recursively. |

---

## 4. `global_info` (Optional)

- **Type:** `Dict[str, Any]`
- **Description:**  
  A dictionary containing overall information about the view. For example:
    - Differentiation information from the ordering algorithm (e.g., counts of adjacent line pairs that were differentiated by each ordering algorithm).
      - Any additional information stored in the node (from `self.info`).

---

## 5. `line_info`  (Optional)
This part of a concordance view typically includes ranking scores.

```jsonc
"line_info": {
  "column_info": [ /* array of column metadata */ ],
  "data": {
	...,
    12: {               // line_id
      "Ranking: KWIC Grouper Ranker": 1,
      "Ranking: GDEX": 0.485
    },
    13: {               // line_id
      "Ranking: KWIC Grouper Ranker": 0,
      "Ranking: GDEX": 0.871
    },
	...
  }
}
```

### 5.1 `column_info`
Each object fully describes one column.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | The human‑readable column name. Convention: `"Ranking: <Algorithm name>"`. |
| `algorithm` | `str` | The exact name of the algorithm used for ranking. |
| `algorithm_index_withing_ordering` | `int` | The position of the algorithm within the list of ordering algorithms used at current node (0-based). |
| `type` | `str` | `"ranking"` for ranking algorithms. |
| `description` | `str` | One‑line tooltip explaining the column. |

### 5.2 `data`
*Keys* → `line_id`.
*Values* → dict mapping **column key** → line information, most typically ranking value (`int` or `float`).
Only lines listed in `selected_lines` are included.

---

## 6. `token_spans` (Optional)

- **Type:** `List[dict]`
- **Description:**  
  A list of token span objects used to mark tokens in a KWIC (Key Word In Context) display. Each token span dictionary includes:
    - **`line_id`**: The line number in which the span occurs.
    - **`start_id_in_line`**: The starting token id (inclusive) relative to the line. 
    - **`end_id_in_line`**: The ending token id (inclusive) relative to the line.
    - **`category`**: A string indicating the mark (e.g., `"A"`).
    - **`weight`**: A numerical weight, typically in the range `[0, 1]`.

---

## 7. `node_type`

- **Type:** `str`
- **Description:**  
  A string indicating the type of the node (e.g., `"subset"`, `"arrangement"`).

---

## Additional Notes

- **Serialization:**  
  The entire view is designed to be JSON-serializable.
  
- **Mandatory vs. Optional:**  
    - The keys `selected_lines` and `ordering` are always present.
    - The keys `grouping`, `global_info`, `line_info`, and `token_spans` are optional and are included only if relevant algorithms (grouping, ranking, etc.) have been applied to the node.
  
- **Ordering Details:**  
  The ordering list sorts the lines based on the sort keys computed by ordering algorithms. Ties are handled in a stable manner to maintain consistency.
  
- **Token Spans:**  
  When present, token spans provide precise information for marking specific segments of tokens within each line, enhancing the KWIC display for further visualization.

---

This specification outlines the complete structure and content of a Concordance View as generated by FlexiConc. Use it as a reference for understanding the output and for integrating or visualizing concordance data in your applications.