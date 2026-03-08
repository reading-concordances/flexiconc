# Loading Concordances

## 1. Utility Functions for Loading Data from External Systems

FlexiConc provides a set of utility functions to retrieve concordance data from external corpus systems. These functions automatically build and populate the internal DataFrames (**metadata**, **tokens**, and **matches**) by processing raw query results. The following sections describe each retrieval function in detail, including the required arguments and example calls.

---

### 1.1 Retrieving from CWB

The function to retrieve data from IMS Open Corpus Workbench (CWB) requires the following arguments:

- **registry_dir** (str):  
  The path to the CWB registry directory.
- **corpus_name** (str):  
  The name of the corpus to be queried.
- **query** (str):  
  The search query string.
- **tokens_attrs** (list of str):  
  A list of token-level attribute names to retrieve (e.g., `["word", "lemma", "pos"]`).
- **metadata_attrs** (list of str):  
  A list of metadata attribute names to retrieve (e.g., `["speaker", "chapter", "paragraph"]`).
- **context** (int):  
  The number of tokens to include as context on each side of the matched token.

**Example:**

```python
concordance.retrieve_from_cwb(
    registry_dir="/path/to/cwb/registry",
    corpus_name="my_corpus",
    query="search_term",
    tokens_attrs=["word", "lemma", "pos"],
    metadata_attrs=["speaker", "chapter", "paragraph"],
    context=20
)
```

Internally, this function performs the following steps:
1. Instantiates a CWB Corpus object using the specified registry directory and corpus name.
2. Executes the query with the provided context.
3. Converts the raw output into DataFrames for metadata, tokens, and, if necessary, matches by unnesting token-level data and computing token positions.
4. Populates the Concordance object with these DataFrames.

---

### 1.2 Retrieving from CLiC

The retrieval function for CLiC is designed for corpora accessible via the CLiC API. It accepts the following arguments:

- **query** (list of str):  
  A list containing one or more query strings.
- **corpora** (str):  
  The identifier(s) for the corpus or corpora to search.
- **subset** (str):  
  A string specifying which subset of the corpus to search (e.g., `"all"`, `"quote"`, or `"nonquote"`).
- **contextsize** (int):  
  The number of tokens of context to include on each side of the match.

**Example:**

```python
concordance.retrieve_from_clic(
    query=["search term"],
    corpora="my_corpora",
    subset="all",
    contextsize=20
)
```

This function works as follows:
1. Sends HTTP GET requests to the CLiC API with the specified parameters.
2. Parses the JSON response to extract both metadata and token-level details.
3. Aggregates tokens from nested JSON structures and assigns proper `line_id` values.
4. Constructs the internal DataFrames and assigns them to the Concordance object.

---

### 1.3 Retrieving from SketchEngine

The SketchEngine retrieval function is used to retrieve concordance data via the SketchEngine API. It requires these arguments:

- **query** (str):  
  The search query string.
- **corpus** (str):  
  The identifier for the target corpus (e.g., `"bnc2"`).
- **api_username** (str):  
  Your SketchEngine username.
- **api_key** (str):  
  Your SketchEngine API key.

**Example:**

```python
concordance.retrieve_from_sketchengine(
    query="search_term",
    corpus="bnc2",
    api_username="your_username",
    api_key="your_api_key"
)
```

This function operates as follows:
1. Constructs an authenticated HTTP request using your API credentials.
2. Retrieves the JSON response containing both token-level and structural data.
3. Unnests the token data and maps structural details to create the **metadata**, **tokens**, and **matches** DataFrames.
4. Computes additional columns such as `id_in_line` if they are not provided.
5. Assigns these DataFrames to the Concordance object.

---

Add this after the section on “Utility Functions for External Systems”:

---

### 1.4 Loading from CQPweb Export

FlexiConc provides a convenient function for loading concordance data exported from **CQPweb**. This function automatically parses standard CQPweb concordance TSV files (with or without POS tags) and constructs the required internal DataFrames (**metadata**, **tokens**, **matches**) for analysis.

**Function:**
`Concordance.load_from_cqpweb_export(filepath)`

**Description:**
This method reads a CQPweb concordance export (TSV format), handling both plain and POS-tagged exports. Tagged columns (such as “Tagged context before”) are detected automatically. POS information is separated into a distinct column if present. The method also collects metadata fields from all non-token columns.

**Example:**

```python
concordance.load_from_cqpweb_export("path/to/cqpweb_export.tsv")
```

* **filepath**: Path to the CQPweb concordance TSV file (exported from the CQPweb interface).


Each of these retrieval functions converts external data formats into FlexiConc’s standard internal structure, allowing you to analyze and visualize your corpus data immediately after loading.

## 2. Loading Data From External FlexiConc-Compatible Files

FlexiConc’s `Concordance.load()` method is used to populate the three internal DataFrames—**metadata**, **tokens**, and **matches**—from external data files. The method is designed to accept TSV (Tab-Separated Values) files based on the MTSV format proposed by Anthony & Evert (2019).

### Concordance.load() Method

The `load()` method accepts file paths for:
- **metadata**: A TSV file containing structural information about each line.
- **tokens**: A TSV file containing token-level data.
- **matches** (optional): A TSV file containing match location details if your tokens file does not provide an `offset` column.
- **info** (optional): A JSON file or dictionary with additional information.

The method reads these files using Pandas and assigns the resulting DataFrames to the Concordance object’s attributes. It automatically checks for the presence of required columns such as `line_id` in the metadata file. In the tokens file, if the `id_in_line` column is missing, the method reconstructs it based on the token order. Similarly, if the tokens file includes an `offset` column, the matches table is optional; otherwise, you must provide a matches table to specify the match location.

### Example

Assuming you have TSV files with headers, you can load them as follows:

```python
from flexiconc.concordance import Concordance

# Create the Concordance object
concordance = Concordance()

# Option A: Tokens file includes 'offset'
concordance.load(
    metadata="path/to/metadata.tsv",  # must contain 'line_id' and other structural columns
    tokens="path/to/tokens.tsv",      # must contain 'line_id' and 'offset' (id_in_line is optional)
    info="path/to/info.json"          # optional additional information
)

# Option B: Tokens file does NOT include 'offset'; matches provided separately
concordance.load(
    metadata="path/to/metadata.tsv",   # must contain 'line_id'
    tokens="path/to/tokens.tsv",       # must contain 'line_id' (other token attributes as needed)
    matches="path/to/matches.tsv",     # must contain 'line_id', 'match_start', 'match_end', and 'slot'
    info="path/to/info.json"           # optional additional information
)
```

### Technical Details and Options

- **TSV Files with Headers:**  
  The load method assumes that each TSV file has a header row. This header is used to name the columns of the DataFrame. For example, the metadata TSV should include a header line like:
  
  ```
  line_id   text_id   chapter   paragraph   sentence
  ```
  
  Similarly, the tokens TSV must have headers for columns such as `line_id`, `offset`, and optionally `id_in_line`, along with token attributes like `word`, `pos`, etc.

- **Providing Offsets vs. Matches Table:**
    - **With Offsets:**  
      If your tokens file includes an `offset` column, the load method uses it to determine the token’s relative position (negative for left context, zero for the matched token, positive for right context). In this configuration, you do not need to supply a matches table.  
    - **Without Offsets:**  
      If the tokens file lacks an `offset` column, you must provide a matches table. The matches file should include:
        - `line_id`: To link the match to the correct metadata entry.
        - `match_start` and `match_end`: Token indices that mark the beginning and end of the match.
    
        It can also include:
  
           - `slot`: An integer value that is used to determine the focus of concordance operations if a line contains multiple matches.
  
  - **Omission of `id_in_line`:**  
  The tokens file may or may not include an `id_in_line` column. If it is omitted, FlexiConc will reconstruct it by ordering the tokens within each line based on their original position.

  - **Internal Consistency:**  
  Regardless of which option you choose, the `load()` method guarantees that the Concordance object will have all three internal DataFrames:
    - **metadata**: Contains structural data.
    - **tokens**: Contains token-level data.
    - **matches**: Contains match location data (either directly provided or inferred from the tokens).

By providing the data in these formats, FlexiConc ensures that all subsequent analyses—such as building an analysis tree or applying algorithms—work on a consistent and standardized dataset.
