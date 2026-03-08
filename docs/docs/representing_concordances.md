# Representing Concordances

FlexiConc is designed to standardize the way concordance data is stored and processed. Internally, a **Concordance** object always contains three Pandas DataFrames—**metadata**, **tokens**, and **matches**—which together form its internal structure.

---

## 1. Internal Structure of the Concordance Object

The Concordance object maintains three DataFrames that hold different aspects of the concordance data:

### A. Metadata DataFrame

The `metadata` DataFrame stores information about each concordance line. It must include a unique identifier, **line_id**, for each row. Additional columns may include details such as the source text identifier, chapter, paragraph, and sentence.

For example, the metadata table might be structured as follows:

| line_id | text_id | chapter | paragraph | sentence |
|---------|---------|---------|-----------|----------|
| 0       | ED      | 10      | 35        | 63       |
| 1       | ED      | 10      | 36        | 71       |
| 2       | ED      | 14      | 115       | 262      |
| 3       | ED      | 23      | 7         | 78       |
| 4       | LD      | 45      | 85        | 192      |


---

### B. Tokens DataFrame

The tokens DataFrame holds token-level details for each concordance line. It must include **line_id** to link tokens to their corresponding metadata entry. In addition, the tokens DataFrame typically contains:

- **offset:** Indicates the token’s relative position to the matched (node) token(s):

    - Negative values represent tokens in the left context.
    - Zero marks the matched (node) token(s).
    - Positive values represent tokens in the right context.
  
- **id_in_line:** (Optional) The token’s sequential index within the line. If omitted, FlexiConc will reconstruct it.
- **word:** The token text.
- Other attributes such as part-of-speech, lemma, etc., may also be provided.

A tokens table might look like this:

| cpos   | offset | word         | pos | lemma       | line_id | id_in_line |
|--------|--------|--------------|-----|-------------|---------|------------|
| 445643 | -20    | to           | IN  | to          | 0       | 0          |
| 445644 | -19    | the          | DT  | the         | 0       | 1          |
| 445645 | -18    | toll-keeper  | JJ  | toll-keeper | 0       | 2          |
| 445646 | -17    | keeper       | NN  | keeper      | 0       | 3          |
| 445647 | -16    | .            | .   | .           | 0       | 4          |
| 445648 | -15    | then         | RB  | then        | 0       | 5          |
| 445649 | -14    | he           | PRP | he          | 0       | 6          |


*Notes:*
- The **cpos** column (optional) represents the corpus position in the original corpus when available.

---

### C. Matches DataFrame

The `matches` DataFrame specifies the match location within each of the concordance lines. In simple cases, it contains the same information as the **offset** column in `tokens`. It must include:

- **line_id:** To associate the match with its corresponding metadata row.
- **match_start** and **match_end:** Indicate the token indices that mark the beginning and end of the match.
- **slot:** An integer that allows for multiple matches per line.

An example `matches` table might look like this:

| line_id | match_start | match_end | slot |
|---------|-------------|-----------|------|
| 0       | 20          | 20        | 0    |
| 1       | 61          | 61        | 0    |
| 2       | 102         | 102       | 0    |
| 3       | 143         | 143       | 0    |

The `matches` DataFrame is essential when there are multiple matching slots per line:

| line_id | match_start | match_end | slot |
|---------|-------------|-----------|------|
| 0       | 20          | 20        | 0    |
| 0       | 22          | 22        | 1    |
| 1       | 61          | 61        | 0    |
| 1       | 62          | 62        | 1    |

The `slot` column allows FlexiConc to focus on different matches within the same line, enabling more complex analyses.