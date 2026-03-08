# Flexiconc Vignette

## Installation
FlexiConc can currently be installed from the GitHub repository. To install FlexiConc, use the following command:
```
pip install git+https://github.com/menelik3/RC21.git
```
More user-friendly installation options, such as through`pypi`, will be available in the future.

## Usage
FlexiConc is a Python package that provides a flexible and accountable way to conduct concordance analysis.  For a detailed theoretical overview of the approach, the reader is referred to:

- Evert, Stephanie (et al.?). 2024. *Organising concordances with FlexiConc*. 

FlexiConc is most deeply integrated with [IMS Corpus Workbench (CWB)](https://cwb.sourceforge.io/); support for others tools will be added soon.

To work with CWB, you need a functioning installation of CWB as well as [`cwb-ccc`](https://pypi.org/project/cwb-ccc/) Python package.

To ensure that FlexiConc operates correctly, the CWB registry directory must be specified in the FlexiConc configuration file, which is located in the `flexiconc` folder within the system's default configuration directory, such as `~/.config/flexiconc`.

To load a concordance into FlexiConc, create a `Concordance` object and retrieve the concordance from the CWB. The following code snippet demonstrates this process:

```python
import flexiconc
c = flexiconc.Concordance()
c.retrieve_from_cwb(corpus_name="DNOV-CWB", query='[lemma="eye"]')
```

To apply concordance operations, use the `add_node` method:

```python
c.add_node(
    algorithms={
        "order": [
            {
                "algorithm_name": "KWIC Grouper Ranker",
                "args": {
                    "tokens_attribute": "word",
                    "search_term": "^(his|her|fixed)$",
                    "regex": True,
                    "window_start": -5,
                    "window_end": 5
                }
            }
        ]
    },
    active_node=0
)
```

In this example, the `active_node` argument specifies the index of the node to which the new node(s) should be attached. The `algorithms` argument is a dictionary that specifies the algorithms to be applied to the current subset of the concordance. The `algorithms` dictionary can include `"order"`, `"cluster"`, `"partition"`, and `"select"` keys corresponding to the types of algorithms to be applied. Permissible algorithm combinations are described in *Organising concordances with FlexiConc*.

Here is an example of applying a combination of algorithms to select 10 random lines from the concordance:

```python
c.add_node(
    {
        "order": [
            {
                "algorithm_name": "Random Sort",
                "args": {
                    "seed": 9101989
                }
            }
        ],
        "select": [
            {
                "algorithm_name": "Select by Sort Keys",
                "args": {
                    "comparison_operator": "<=",
                    "value": 10
                }
            }
        ]
    },
    active_node=0
)
```

The list of available algorithms and their parameters can be found in the `algorithms.json` file located in the `flexiconc` folder.

A concordance view can be exported to a CSV file:
    
```python
c.export_to_csv(node_id=5, "concordance.csv")
```

The resulting analysis tree can be exported to JSON for further reuse as a template:

```python
c.export_analysis_tree_to_json(output_path="analysis_tree.json")
```