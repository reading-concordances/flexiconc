# Loading Texts to Generate Concordances

This document explains how to load your own texts into FlexiConc for generating concordances. Currently, FlexiConc supports loading raw texts and Wmatrix corpora, using the `TextImport` interface.

---

## 1. Loading Plain Texts with `TextImport`

FlexiConc's `TextImport` class allows you to load and tokenize your own text files, build a searchable SQLite database, and run queries producing FlexiConc concordances.

### 1.1. Database Structure

A `TextImport` SQLite database contains:

* **tokens** table: One row per token, with at least:

  * `cpos` (corpus position, integer, unique)
  * `word` (surface form, string)
  * Optional: `lemma`, `pos`, etc.

* **spans\_\*** tables: Boundaries of token spans, such as sentences/files. Examples:

  * `spans_s`: Sentence spans, columns: `id`, `start`, `end`.
  * `spans_file`: File/document spans, columns: `id`, `start`, `end`.
 
Span tables can contain any optional columns, such as `filename` for `spans_file`.

You can add custom span types as needed.

### 1.2. Creating a Database from Raw Files

Use `TextImport.load_files` to tokenize plain text files (or directories), split into sentences, and build all necessary tables:

```python
from flexiconc import TextImport

ti = TextImport()  # Creates a temporary in-memory DB

ti.load_files(
    paths=["texts/file1.txt", "texts/file2.txt"],  # List of text files or folders
    db_name="mycorpus.sqlite",                     # Save DB to disk (optional)
    use_spacy=False,                               # Use regex tokenization rules (or set True for spaCy)
    spacy_model="en_core_web_sm",
    lemma=False,                                   # Add lemma using spaCy
    pos=False,                                     # Add part-of-speech using spaCy
    tag=False                                      # Add detailed POS tags using spaCy
)
```

#### Notes

* Accepts files or directories (recursively scans folders).
* Supports basic regex sentence splitting or spaCy-based segmentation and annotation.

### 1.3. Building Concordances from Queries

Once your corpus is loaded, you can search it and build concordances in a single step using `concordance_from_query`:

```python
# Run a search and build a FlexiConc-style concordance object in one call
conc = ti.concordance_from_query(
    query="climate change",           # Plain text or CQP-style search string
    context_size=(20, 20),              # (left, right) context window size
    limit_context_span="s",           # Limit context to a sentence (or use "file" for file/document); leave empty for no limiting by span
    span_types_for_metadata=['s', 'file']  # Which spans to include as metadata (optional)
)

---

## 2. Loading Wmatrix Corpora

For corpora hosted in Wmatrix, FlexiConc provides a streamlined import function. The **recommended entry point** is the `load` function.

```python
from flexiconc.utils import wmatrix

ti = wmatrix.load(
    corpus_name="LabourManifesto2005",   # Wmatrix corpus name (as in the web interface)
    username="your_username",
    password="your_password",
    db_filename="labour2005.db"           # Local file to store the database
)
```

If you have a Wmatrix corpus in a local SQLite database, you can load it directly:

```python
from flexiconc.utils import wmatrix

ti = wmatrix.load(
    db_filename="labour2005.db"           # Local file where the database is stored
)
```

### 2.2. Using the TextImport API

Once loaded, `ti` works just like for plain text:

```python

# Run a concordance query
conc = ti.concordance_from_query(
    query="antisocial behaviour",           # Plain text or CQP-style search string
    context_size=(20, 20),              # (left, right) context window size
    limit_context_span="s",           # Limit context to a sentence (or use "file" for file/document); leave empty for no limiting by span
    span_types_for_metadata=['s', 'file']  # Which spans to include as metadata (optional)
)
```