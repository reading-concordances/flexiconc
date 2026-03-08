# Jupyter Notebook Utilities

This page documents the most important interactive utilities for working with the FlexiConc analysis tree and concordance objects in Jupyter notebooks.

---

## `add_node_ui(parent, *, execute=True)`

**Interactively add a subset or arrangement node to an analysis tree.**

* **Parameters:**

  * `parent` (`AnalysisTreeNode`):
    The node to which a new child node will be attached.
  * `execute` (`bool`, default `True`):
    If `True`, the node is created immediately.
    If `False`, the code snippet for creating the node is generated and inserted into a new cell for review or manual execution.

* **Returns:**
  A handle for `AnalysisTreeNode`.

  * After the **OK** button is pressed, the handle provides access to the created node object (if `execute=True`)
  * `.code` — the generated Python code for the operation

* **How it works:**
  Displays a user interface with:

  * Choice of node type: "subset" or "arrangement"
  * Configuration forms for algorithms and their parameters
  * **OK** button: runs or generates the code, shows output, errors, or the code snippet below the widget

**Example usage:**

```python
handle = add_node_ui(tree.root)
# → Interactively select node type and parameters, then press OK.
# handle references the newly created node (after creation)
# handle.code gives the generated code
```

---

## `add_annotation_ui(concordance)`

**Interactively add an annotation to a Concordance object.**

* **Parameters:**

  * `concordance` (`Concordance`):
    The concordance object to annotate.

* **Behavior:**

  * Shows a widget for selecting an annotation algorithm and specifying its arguments.
  * Lets you (optionally) specify column names for the annotation.
  * Press **Annotate** to run the annotation and see results or errors below.

* **Output:**

  * Applies the annotation and prints the code that was executed.

**Example usage:**

```python
add_annotation_ui(conc)
# → Use the form to select the annotation, set arguments, specify columns, and annotate interactively.
```

---

## `show_kwic(node, n=0, n_groups=None, token_attr='word', extra_token_attrs=None, metadata_columns=None, height=600)`

**Display a KWIC (Key Word in Context) table for a node in a scrollable notebook cell.**

* **Parameters:**

  * `node` (`AnalysisTreeNode`):
    The node (subset or arrangement) whose data you want to view.
  * `n` (`int`, default `0`):
    Maximum number of lines per group (or in total if not grouped). If `0`, all lines are shown.
  * `n_groups` (`int`, optional):
    Maximum number of groups to show (if partitioned).
  * `token_attr` (`str`, default `'word'`):
    Token attribute to display in the table.
  * `extra_token_attrs` (`list`, optional):
    Additional token attributes to display as subscripts.
  * `metadata_columns` (`list`, optional):
    Metadata columns to show per line.
  * `height` (`int`, default `600`):
    Height of the KWIC display area in pixels. Set to `0` for no scroll.

* **How it works:**
  Renders a scrollable HTML KWIC table using the node's data and chosen display settings.

**Example usage:**

```python
show_kwic(node, n=50, token_attr='lemma', metadata_columns=['genre'])
```

---

## `show_analysis_tree(concordance, suppress_line_info=True, mark=None, list_annotations=None)`

**Display the analysis tree structure for a Concordance object.**

* **Parameters:**

  * `concordance` (`Concordance`):
    The object whose analysis tree will be visualized.
  * `suppress_line_info` (`bool`, default `True`):
    If `True`, hides detailed line info in the display.
  * `mark` (optional):
    Optionally, specify the id of the node to highlight.
  * `list_annotations` (`bool`, optional):
    If `True`, lists annotations in the display.

* **How it works:**

  * Produces an HTML visualization of the analysis tree and displays it in the notebook.

**Example usage:**

```python
show_analysis_tree(conc)
```