# FlexiConc Python Library Documentation

The FlexiConc Python library is designed to facilitate accountable, reproducible, and transparent concordance analysis. It provides tools for working with concordances, utilizing existing and new algorithms implementing the fundamental strategies identified in the *Reading Concordances in the 21st Century* project.

For a more detailed theoretical overview of the approach, the reader is referred to:

Evert, Stephanie (et al.?). 2024. Organising concordances with FlexiConc. 

## Basic Design Principles

At the heart of the FlexiConc library is the `Concordance` class, which represents a concordance to be analysed with the help of FlexiConc algorithms. A `Concordance` object contains three Pandas DataFrames, `metadata`, `tokens`, and `matches`, which store metadata attributes (pertaining to concordance lines), token-level attributes, and the query matches (i.e. nodes of the concordance) as token spans, respectively. Additionally, it includes the **analysis tree** (`tree`), which tracks the history of operations applied to the concordance.

> Applying individual algorithms is no longer how we expect FlexiConc to work! I think it would be better to introduce “concordance views” and “subset operations” and explain directly that both are defined by combinations of suitable algorithms. Perhaps an itemization with 1) Concordance views and 2) Subset operations.

The `Concordance` class provides methods that allow users to apply various algorithms to the concordance, corresponding to one of five strategies: selecting, sorting, ranking, grouping, and clustering. Algorithms are implemented in separate Python modules, which are imported into the `Concordance` class once called. This modular approach enables users to apply algorithms flexibly and even create custom algorithms to extend the library's functionality.

Results from algorithmic operations are stored in the respective nodes of the analysis tree. Typically, FlexiConc users will be most interested in **concordance views**, which are visual representations of the concordance at the leaf nodes of the analysis tree. Since FlexiConc is not intended for use as a standalone application, but rather as a library integrated into a host app, FlexiConc concordance views are not direct visualizations, but pieces of information that are passed to the host app, which then takes care of actual concordance display.

## Requirements

{TODO: keep updated}

```
anytree>=2.12.1
cwb-ccc>=0.12.4
networkx>=3.1
numpy>=2.1.0
pandas>=2.2.2
PyICU>=2.11
```

## Installation

{TODO: complete}


## Mini-tutorial

> Would it make sense to start with a mini-tutorial here? Perhaps load concordance from CWB (explaining what the method does), then apply a few algorithms, obtain a concordance view, explain how it would be displayed, and navigate analysis tree.

## Working with Concordances

### `Concordance` Class

The `Concordance` class is the central part of FlexiConc, providing tools for storing, managing, and analyzing concordance data. A `Concordance` object contains the following core attributes:

#### Attributes:
- **metadata**: `pd.DataFrame`
  - Stores the values of metadata attributes (also known as structural attributes, or s-attributes) for concordance lines.
  
  - Each row corresponds to a concordance line, and columns represent attributes.
  
    >  what are restrictions on names and data types of the attributes?
  
  - `id` column stores unique identifiers for the concordance lines, which are sequential non-negative integers starting from 0 (referred to as line №s)
  
- **tokens**: `pd.DataFrame`
  
  - Stores token-level attributes (also known as positional attributes, or p-attributes in CWB terminology) for each word or token in the concordance.
  - Each row represents a token, and columns represent attributes such as word, lemma, part-of-speech tag, etc. Note that this is single data frame for all tokens from all concordance lines
  
  - `id`: unique identifiers for the tokens, which are sequential non-negative integers starting from 0.
  
    >  Do we need to enforce this? For a CWB corpus it might be convenient to reference tokens by their cpos. However, if concordance lines overlap these would no longer be unique, so perhaps best to assign internal IDs as you sugges
  - `line_id` column associates tokens with their respective concordance lines.
  - `id_in_line`: unique identifiers for the tokens within a line, which are sequential non-negative integers starting from 0.
  
    >  better `position` or so? but names are completely arbitrary, of course
  - `offset0`, `offset1`, `offset2`, `offset3`, etc. columns store the distance of the token from the closest token in the KWIC node depending on which query matching slot is activated (see below on query matching slots). In most cases, only `offset0` is used.
  
    >  I would still argue that these are undesirable and it's better to leave it to algorithms to compute offsets from `position` and the **matches** start/end positions
  
- **matches**: `pd.DataFrame`
  - Stores information about the tokens that match the query string. In the simplest case, each concordance line has only one KWIC node; however, FlexiConc also allows to work with more complex queries where a single concordance lines may contain several matching slots. For instance, when looking for expressions of desire, one might want to identify the subject of the desire, the desire itself, and the desired object or result. In this case, the concordance lines would look as follows:

<table>
  <tr><th colspan="5"><strong>Slot 0: The complete match</strong></th></tr>
  <tr><th>Slot 1: Subject</th><th></th><th>Slot 2: Desire</th><th>Slot 3: Desired object/result</th></tr>
  <tr><td>The child</td><td></td><td>wants</td><td>an ice cream</td><td>.</td></tr>
  <tr><td>Donald Trump</td><td>desperately</td><td>wishes</td><td>to become president of the U.S.</td><td>.</td></tr>
</table>

  - columns of the **matches** data frame


    - `line_id` links query matches to their respective concordance lines.
    - `match_start` indicates the number of the first token of the match.
    - `match_end` indicates the number of the last token of the match.
    - `slot` (optional) indicates the number of the slot in the query that the match corresponds to, slots being numbered with positive integers starting with 1. Slot 0 corresponds to the whole query.
    
      >  `slot` shouldn't be optional but instead start with 0, so slot 0 is always the default view (and usually the only one). Leave it to host app to decide whether slot 0 is entire match or something else. Constructor could automatically add `slot` column with all zeroes if missing.
      >
      >  How do you deal with a situation where some slots are not defined for all concordance lines? Do you run a validity check up front?


`metadata`, `tokens`, and `matches` DataFrames are never modified after the concordance has been received from the host app. Instead, the analysis tree is used to keep track of the operations applied to the concordance.

<!-- 

- **subsets**: `Dict[str, ConcordanceSubset]`
    - A collection of subsets, which are portions of the concordance data produced by certain operations. 


-->

- **tree**: A list of AnyTree nodes representing the analysis tree. The nodes are numbered with sequential non-negative integers starting from 0. A node corresponds to a concordance operation which may involve creating a concordance or applying of one or several algorithms to it and has the following attributes:

  >  Shouldn't this be just an AnyTree object (i.e. the root node of the tree) rather than a list of all nodes?

  - `id`: The unique identifier of the node.

  - `type`: The type of operation performed, which can be one of the following: `query`, `load`, `order` (corresponding to Sorting and Ranking operations), `partition`, `cluster`.

  - `function`: The function that was applied to the concordance to generate the node.

  - `args`: The arguments passed to the function.

  - `offset_column`: The number of the offset column relevant for the node and its children (unless overridden by the value of this attribute in a child node).

  - `bookmarked`: A boolean value indicating whether the node is bookmarked. Default is `False`.

  - `label`: A string label for the node. Default is an empty string.

  - Additional attributes specific to the operation type, which are used to produce a concordance view, such as:
    - For `select` nodes:
      - `selected_lines` list containing the line IDs of the selected concordance lines;
    - For `order` nodes:
      - `sort_keys` corresponding to *surrogate* sort keys generated by the operation;
      - `rank_keys` with subdictionaries for any algorithms in the operation containing the *natural* ranking keys;
      - `differentiation_info` a dictionary showing how many pairs of adjacent lines are differentiated by the first, second, third, etc. ordering algorithm applied; the higher this number, the more important is the role of the algorithm in a concordance view corresponding to this node;
    - For `partition` nodes:
      - `partitions` dict, where keys correspond to the number of the partition in the sorted display started with 0, and values are dictionaries containing:
        - `label` of the partition;
        - sorted `line_ids` in the partition;
        - (optional) `best_example` line ID representing the most prototypical line of the partition.
    - For `cluster` nodes: {TODO}

  - >  This tree still has a separate node for every algorithm applied, so it's not consistent with our mathematical model!

- **active_node**: The ID of the currently active node within the analysis tree. Since concordance reading is perceived as an interactive process, it is useful to keep track of the current position in the analysis tree. New nodes can be added only as children or siblings of the active node. In order to add a node elsewhere, the user has to navigate the tree to the desired location by changing the active node.

  >  Developers seem to be firmly opposed to such stateful APIs. Methods should rather pass the tree node they want to access explicitly.

- **info**: `Dict[str, Any]`
  - Metadata about the concordance, such as the `query` used to generate it and the `language` of the corpus.


The methods of the `Concordance` class allow users to apply various algorithms to the concordance, which will be detailed in the following sections.

### Getting Information about the Concordance and FlexiConc itself

#### `metadata_attributes(self)`

Returns a list of metadata attributes contained in the concordance, i.e. the column names of the `metadata` DataFrame except for `id`.

**Returns:**

- **list**: A list of metadata attributes.

#### `tokens_attributes(self)`

Returns a list of token-level attributes contained in the concordance, i.e. the column names of the `tokens` DataFrame except for `id`, `line_id`, `id_in_line`, and `offset0`, `offset1`, etc.

**Returns:**

- **list**: A list of token-level attributes.

#### `list_algorithms(update: bool = False) -> list[dict]`

Lists all available algorithms in the FlexiConc installation. If the `update` parameter is set to `True`, the method will update the list of algorithms by scanning the `algorithms` folder and save it to `algorithms.json`. Otherwise, it will load the list from this file.

**Returns:**

- **`list[dict]`**: A list of dictionaries, each containing the following keys:
  - **`name`**: `str` — The name of the algorithm.
  - **`description`**: `str` — A brief description of the algorithm.
  - **`module`**: `str` — The name of the Python module containing the algorithm.
  - **`function`**: `str` — The name of the function implementing the algorithm.
  - **`args`**: `list[dict]` — A list of dictionaries, each containing the following keys:
    - **`name`**: `str` — The name of the argument.
    - **`type`**: `str` — The type of the argument (possible values follow the conventions used in the [**typing**](https://docs.python.org/3/library/typing.html) module).
    - **`default`**: `Any` — The default value of the argument.

#### `compute_nodes(node_ids : Optional[List[int]] = None)` {TODO}

If a concordance is supplied with an analysis tree template, the results of the application of concordance operations are not computed immediately, which results in attributes like `selected_lines`, `order_keys` or `partitions` being absent from analysis tree nodes. This method actually applies the declared algorithms to the listed nodes of the analysis tree.

> Could this rather happen automatically when a node of the analysis tree is accessed? If the respective subset / concordance view has already been computerd, it is directly returned. Otherwise the computation is carried out and the result cached in memory.

**Parameters:**

- **node_ids** (list of int, optional): A list of node IDs to compute. If not provided, the method computes all nodes that lack a result of the computation.

**Updates:**

- The `Concordance` object that the method is called on. The `tree` attribute is updated with the computed results.

**Returns:**

- **bool**: `True` if the operation was successful, `False` otherwise.

## Loading Concordances

Concordances can be supplied as a collection of Python objects, retrieved from external programs, or loaded from a set of files. These files typically include metadata (structural attributes) and tokens in TSV format, and optionally, a JSON file containing the analysis tree.

### Methods for Loading Concordances

##### `retrieve_from_cwb(self, registry_dir=None, corpus_name="DNOV-CWB", query="", tokens_attrs=None, metadata_attrs=None)`

This method retrieves a concordance from the CWB (Corpus Workbench).

**Parameters:**

- **registry_dir** (str, optional): The path to the CWB registry directory. If `None`, it uses the default configuration.
- **corpus_name** (str, default="DNOV-CWB"): The name of the corpus in CWB.

  >  Having a default corpus name (especially this one) is rather weird.
- **query** (str, optional): The query string used to retrieve concordance lines.
- **tokens_attrs** (list, optional): A list of positional attributes (p-attributes) to include as token-level annotation in the concordance. Defaults to all p-attributes in the corpus.
- **metadata_attrs** (list, optional): A list of structural attributes (s-attributes) to include as concordance line metadata in the concordance. Defaults to all s-attributes with values in the corpus.

**Updates:**

- Populates the `Concordance` object with the retrieved data in the `metadata`, `tokens`, and `matches` attributes.
- Updates the analysis tree with a root node and the query results.
- Automatically applies a default sorting algorithm (`Sort by Corpus Position`).

##### `load(self, metadata, tokens, matches, tree=None, info=None)`

This method loads a concordance from a set of files or from provided data structures.

**Parameters:**

- **metadata** (str or pd.DataFrame): The path to the TSV file containing the structural attributes of concordance lines, or a Pandas DataFrame with the same data.
- **tokens** (str or pd.DataFrame): The path to the TSV file containing the tokens of concordance lines, or a Pandas DataFrame with the same data.
- **matches** (str or pd.DataFrame): The path to the TSV file containing the query matches of concordance lines, or a Pandas DataFrame with the same data.
- **tree** (str or list, optional): The path to the JSON file containing the analysis tree, or a list representing the analysis tree structure. The tree can either include the results of algorithm application or serve as a template. If omitted, a new analysis tree is created with a root node.

  >  format of the JSON file needs to be defined! Is it just an AnyTree serialisation format?
- **info** (str or dict, optional): The path to a JSON file or a dictionary containing additional info about the concordance.

**Updates:**

- The `Concordance` object is populated with the provided `metadata`, `tokens`, `matches`, and optionally, the analysis `tree` and `info`. If no tree is provided, a root node is created for the tree.
- Sets the `active_node` to the last node in the tree or to the root node if no tree is supplied.

  >  Why do we only get a root node for the analysis tree here, but `retrieve_from_cwb` also creates a default concordance view as a leaf node?


## Concordance Operations

All algorithms that can be applied to the concordances are stored in the `algorithms` folder of the `flexiconc` package. This folder contains separate Python modules, each of them implementing one or more concordance operations. These Python modules are imported dynamically once called.

The names of the operations are preferably to be written in_snake_case, where the part before the first underscore is the name of the substrategy (`select`, `sort`, `rank`, `partition`, `cluster`; e.g., `select_by_structural_attribute`, `sort_random`). All algorithms available in a FlexiConc installation can be listed by calling the `flexiconc.list_algorithms()`.

> Can the the algorithms be organised in submodules? Wouldn't it be better then to have the qualified names rather than long snake case in a flat namespace? e.g. `select.by_medatada.structural_attribute`
>
> How can host apps add their own algorithms? Do they have to be mixed in with the FlexiConc source code, or can you have other libraries using the same structure (esp. with `algorithms.select`, `algorithms.sort`, ... submodules)?
>
> And would it make more sense to organise algorithms by their self-chosen names rather than the symbols the functions happen to be assigned to? Some kind of `register_algorithm(name, type, code)` method that keeps everything organised in an internal data structure? I don't know Python well enough to know what the most idiomatic way of doing this is.

### Applying Concordance Operations

> Applying single algorithms doesn't fit  our mathematical model and the analysis tree! My preference would be to create an object for a single algorithm with its parameters, and then pass multiple such objects to `make_concordance_view` and `make_subset` methods. That seems more robust than passing a single data structure where the host app has to provide dictionaries that happen to have the right keys. The parameter objects could also easily be stored in the analysis tree and retrieved later.

To apply an algorithm to the concordance, use the following syntax:

#### `apply_algorithm(self, algorithm_name, args = {})`

Applies an algorithm to the subset of the concordance data at the active node and updates the analysis tree. The algorithm is specified by its name, and the arguments are passed as a dictionary.

**Parameters:**

- **algorithm_name** (str): The name of the algorithm to apply.
- **args** (dict): A dictionary of arguments to pass to the algorithm. If no arguments are provided, defaults are used.

**Returns:**

- The dict with result of algorithm application (e.g., sorted order, selected lines, partitions).

#### Example:

```python
# Apply sorting and selecting algorithms
sort_result = concordance.apply_algorithm("Sort by Token-Level Attribute", {"tokens_attribute": "word", "offset": 2})
select_result = concordance.apply_algorithm("Select by a Token-Level Attribute", {"tokens_attribute": "lemma", "value": "run"})
```

However, FlexiConc users will mostly be interested not in merely applying algorithms, but in updating the analysis tree. This is achieved by adding new nodes to represent each operation applied to the concordance. 

> `apply_algorithm` above says that it updates the analysis tree, too!

The `add_node` method is designed to handle the application of one or more algorithms, combining them when necessary and updating the tree to reflect the analysis process. This allows users to track and manage the history of operations, facilitating reproducible and transparent concordance analysis.

#### `add_node(self, algorithms: List[Dict[str, Any]], auto_create_leaf_for_select: bool = True) -> bool`

This method adds a new node to the analysis tree based on a list of algorithms. It supports combining multiple algorithms of different types (e.g., `sort`, `select`, `partition`) and ensures that the resulting data is updated in the tree.

> I'd find it clearer to have separate arguments for the single Grouping algorithm, a list of Ordering algorithms, and the single Selecting algorithm (where None easily indicated the respective algos are not applied). I feel separate methods for creating inner nodes and leaf nodes would also be clearer.

**Parameters:**

- **algorithms** (List[Dict[str, Any]]): A list of dictionaries, where each dictionary specifies an algorithm to apply. Each dictionary contains:
  - **algorithm_name** (str): The name of the algorithm to apply.
  - **args** (Dict[str, Any]): Arguments to pass to the algorithm.
  
  Algorithms are executed in the order they are provided, and results from one algorithm (e.g., ordering results) may be passed to subsequent algorithms (e.g., selection or partitioning).

- **auto_create_leaf_for_select** (bool, optional): If `True`, and the last algorithm is of type "select", a child node is automatically created with an ordered view.

**Functionality:**

- **Combining algorithms:**
- If the provided list of algorithms contains only one algorithm, this algorithm is executed.
- If the provided list of algorithms contains multiple algorithms, the method first checks whether their combination is permissible depending on their types ("order", "select", "partition", and "cluster"). The following constraints exist:
  - The list may not contain the algorithms of more than two types.
  - The algorithms of the same type must be adjacent in the list.
  - An algorithm of type "cluster" may occur only once in the list and may not co-occur with an algorithm of type "partition".
- If the list contains only one type of algorithms, they are combined in the following way:
  - If all algorithms are of type **"order"**, they are executed in the order they are provided. Differentiation information is calculated showing the contribution of each ordering algorithm to the differentiation of adjacent lines.
  - If all algorithms are of type **"partition"**, a new partitioning based on the cross-classification of all partitionings is created. Note that this might result in a large number of small partitions.
  - If all algorithms are of type **"select"**, an intersection of subsets created by individual select operations is created.
- If the list contains algorithms of two different types, the following rules apply:
  - **"order"** algorithms are executed first, and their results are passed to the subsequent algorithms, which may use them for ordering concordance lines within partitions/clusters or for selecting concordance lines.
  - **"partition"** and **"cluster"** algorithms are executed next; their results may be used for selecting concordance lines.
  - **"select"** algorithms are executed last.

- **Tree updates:** After applying the algorithms, a new node is added to the analysis tree. This node represents the combined result of the algorithms, storing the full list of algorithms applied and their results (e.g., `sort_keys`, `selected_lines`, `partitions`). The node is added as a child or sibling of the active node in the tree, allowing users to track the flow of operations.

- **Leaf nodes for ordering:** If the last algorithm is a selection algorithm, the method can automatically create a child node to display the ordered subset. This child node applies any existing ordering algorithms from the current arguments or from the last sibling node, ensuring the selected data is ordered appropriately for display.

**Returns:**

- **bool**: `True` if the algorithms were successfully executed and a node was added to the tree, `False` otherwise.

  >  Perhaps it should return a reference to the resulting concordance view? (Or the new inner node in case you don't automatically create a view for it. I think always having a view might be better, and the subset can be obtained from the view's parent with a suitable method.)

#### Example:

```python
# Add a new node combining sorting and partitioning algorithms
concordance.add_node([
    {"algorithm_name": "Sort by Token-Level Attribute", "args":{"tokens_attribute": "lemma", "offset": -1}},
    {"algorithm_name": "Partition by Metadata Attribute", "args":{"metadata_attribute": "text_id"}}
])

# This will sort the concordance by the first token to the left of the node and then partition the results by text_id.
```


### FlexiConc Algorithms
See [FlexiConc Algorithms](algorithms.md) for a list of algorithms implemented in the FlexiConc library.

## Concordance Views

A concordance view is produced by applying one or more algorithms to the concordance data.

> The data structures don't match the specification in the algorithms document. Should we have another discussion about the details?

A concordance view is a dictionary with the following keys:

- **type**: "flat", "partitions", or "hierarchical".
- **line_ids**: If `type` == "flat", a list of line IDs corresponding to the concordance lines selected and ordered as required by the concordance view.
- **groups**: If `type` == "partitions" or `type` == "hierarchical", a list of dictionaries containing:
  - **label**: partition label
  - **line_ids**: list of line IDs corresponding to the concordance lines in the partition.
  - **best_example** (optional): line IDs that represents the most prototypical line of the partition to be shown when it is collapsed.
  - **children** (optional): a list of dictionaries containing the same keys as the parent dictionary, representing the subpartitions (for `type` == "hierarchical" only).
- **focus_spans** (optional): A dataframe with focus spans that should be highlighted for visualization. {TODO: think about exactly what this should be}
- **tree** (optional): The analysis tree.

#### `view(self, node_id=None, include_tree=False)`

Returns a concordance view based on the specified node in the analysis tree.

**Parameters:**

- **node_id** (int, optional): The ID of the node in the analysis tree. If not provided, the active node is used.
- **include_tree** (bool, optional): Whether to include the analysis tree in the concordance view. Default is False.

**Returns:**

- dict: A concordance view.
