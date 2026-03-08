# File: select_rank_wrapper.py

## `select_by_rank`

Selects lines based on rank values obtained from a selected 'algo_*' key in the ordering_result["rank_keys"]
of the active_node, using a comparison operator and value.

Args are dynamically validated and extracted from the schema.

Parameters:
    conc (Union[Concordance, ConcordanceSubset]): The concordance or subset of data.
    args (dict): Arguments include:
        - active_node (object): The active node containing the ordering_result with rank_keys.
        - algo_key (str): The specific algorithm key from ordering_result["rank_keys"] to use.
                          Allowed values are those that start with "algo_". By default, the smallest key (lowest number) is used.
        - comparison_operator (str): The comparison operator ('==', '<=', '>=' ,'<', '>'). Default is "==".
        - value (number): The value to compare the rank keys against. Default is 0.

Returns:
    dict: A dictionary containing:
        - "selected_lines": A sorted list of selected line IDs.
        - "line_count": The total number of selected lines.

---

# File: select_random.py

## `select_random`

Selects a random sample of line IDs from the concordance metadata.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- **kwargs: Arguments defined dynamically in the schema.

Returns:
- dict: A dictionary containing:
    - "selected_lines": A list of randomly selected line IDs.
    - "line_count": The number of selected lines.

---

# File: sort_by_corpus_position.py

## `sort_by_corpus_position`

Sorts the concordance or subset of data by line_id, which corresponds to the corpus position.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - No additional arguments are required for this function.

Returns:
- dict: A dictionary containing:
    - "sort_keys": A mapping from line IDs to their sorted positions.

---

# File: annotate_spacy_pos.py

## `annotate_spacy_pos`

Annotates tokens with spaCy part-of-speech (POS) tags or related attributes.
This algorithm uses spaCy to determine the tag information for each token in the specified token attribute.
The spacy_attributes argument is always treated as a list: even if a single attribute is desired,
it should be provided as a one-element list. The algorithm returns a DataFrame with each column corresponding
to one of the requested attributes. The scope for this annotation is "token".

Parameters:
    conc (Concordance or ConcordanceSubset): The concordance data.
    args (dict): A dictionary of arguments with the following keys:
        - spacy_model (str): The spaCy model to use for POS tagging. Default is "en_core_web_sm".
        - tokens_attribute (str): The token attribute to use for POS tagging. Default is "word".
        - spacy_attributes (list of str): A list of spaCy token attributes to retrieve.
          Allowed values are "pos_", "tag_", "morph", "dep_", "ent_type_". Default is ["pos_"].

Returns:
    pd.DataFrame: A DataFrame indexed by token IDs with one column per requested attribute.

---

# File: annotate_tf_idf.py

## `annotate_tf_idf`

Annotates a concordance with TF-IDF vectors computed for each line based on tokens in a specified window.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - tokens_attribute (str): The token attribute to use for creating line texts. Default is 'word'.
    - exclude_values_attribute (str, optional): The attribute to filter out specific values.
    - exclude_values_list (list, optional): The list of values to exclude.
    - window_start (int): The lower bound of the token window (inclusive). Default is -5.
    - window_end (int): The upper bound of the token window (inclusive). Default is 5.
    - include_node (bool): Whether to include the node token (offset 0). Default is True.

Returns:
- pd.Series: A Pandas Series indexed by concordance line IDs, containing the TF-IDF vectors for each line.

---

# File: partition_openai_semantic.py

## `ClusteringResult`

*No docstring provided.*

---

## `partition_openai_semantic`

Sends a list of lines to OpenAI and requests clustering into `n_partitions` groups with labels,
using structured outputs for guaranteed JSON schema adherence.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - openai_api_key (str): The API key for OpenAI.
    - n_partitions (int): The number of partitions/clusters to create. Default is 5.
    - token_attr (str): The token attribute to use for creating line texts. Default is 'word'.
    - model (str): The OpenAI model to use. Default is 'gpt-4o-2024-11-20'.
    - introduction_line (str): Customizable prompt for the clustering task.

Returns:
- list: A list of dictionaries, where each dictionary contains:
    - "label": The label of the cluster.
    - "line_ids": A list of line IDs in the cluster.

---

# File: partition_by_metadata_attribute.py

## `partition_by_metadata_attribute`

Partitions the concordance data based on a specified metadata attribute and groups the lines accordingly.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - metadata_attribute (str): The metadata attribute to partition by (e.g., 'pos', 'speaker').
    - sort_by_partition_size (bool): If True, partitions will be sorted by size in descending order.
    - sorted_values (List[Union[str, int]], optional): If provided, partitions will be sorted by these specific values.

Returns:
- dict: A dictionary containing:
    - "partitions": A list of dictionaries, where each dictionary has:
        - "label": The value of the metadata attribute for this partition.
        - "line_ids": A list of line IDs that belong to this partition.

---

# File: select_sort_wrapper.py

## `select_by_sort`

Selects lines based on sort keys obtained from the active_node's ordering_result['sort_keys'],
using a comparison operator and a specified value.

Args are dynamically validated and extracted from the schema.

Parameters:
    conc (Union[Concordance, ConcordanceSubset]): The concordance or subset of data.
    args (dict): Arguments include:
        - comparison_operator (str): The comparison operator ('==', '<=', '>=', '<', '>'). Default is "==".
        - value (number): The value to compare the sort keys against. Default is 0.

Returns:
    dict: A dictionary containing:
        - "selected_lines": A sorted list of selected line IDs.
        - "line_count": The total number of selected lines.

---

# File: sort_random.py

## `sort_random`

Sorts lines pseudo-randomly while ensuring that given a specific seed,
any pair of line_ids always appear in the same relative order regardless
of what other line_ids are present.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- **kwargs: Arguments defined dynamically in the schema.

Returns:
- dict: A dictionary containing:
    - "sort_keys": A mapping from line IDs to their stable pseudo-random ranks.

---

# File: sort_by_token_attribute.py

## `sort_by_token_attribute`

Sorts the concordance lines by a specified token-level attribute.
It supports sorting by a single token at a given offset (sorting_scope="token"),
or by the whole left context (sorting_scope="left") or whole right context (sorting_scope="right").

For left context, tokens are joined from right to left (i.e. starting with offset -1, then -2, etc.).

Locale-specific sorting is attempted via pyicu; if unavailable, plain Unicode sorting is used.
Additionally, outputs token_spans for the tokens used for sorting.

Args are dynamically validated and extracted from the schema.

Parameters:
  - conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
  - args (dict): Arguments include:
      - tokens_attribute (str): The token attribute to sort by (e.g., "word", "lemma", "pos"). Default is "word".
      - sorting_scope (str): Specifies which context to use for sorting:
                           "token" for a single token at the given offset (default),
                           "left" for the entire left context (tokens with offset < 0 joined from right to left),
                           "right" for the entire right context (tokens with offset > 0 joined with a space).
      - offset (int): The offset value to filter tokens by when sorting_scope=="token". Default is 0.
      - case_sensitive (bool): If True, performs a case-sensitive sort. Default is False.
      - reverse (bool): If True, sort in descending order. Default is False.
      - backwards (bool): If True, reverses the string (e.g., for right-to-left sorting). Default is False.
      - locale_str (str): ICU locale string for language-specific sorting. Default is "en".

Returns:
  dict: A dictionary containing:
      - "sort_keys": A mapping from line IDs to their sorted ranks.
      - "token_spans": A DataFrame with columns:
            line_id, start_id_in_line, end_id_in_line, category, weight.
      The token_spans represent the span (min and max id_in_line) of the tokens used for sorting.

---

# File: partition_by_embeddings.py

## `partition_by_embeddings`

Partitions lines based on embeddings stored in a concordance metadata column using clustering algorithms.

Supports Agglomerative Clustering and K-Means.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - embeddings_column (str): The metadata column containing embeddings for each line.
    - n_partitions (int): The number of partitions/clusters to create. Default is 5.
    - metric (str): The metric to compute distances between embeddings (only for Agglomerative). Default is "cosine".
    - linkage (str): The linkage criterion for Agglomerative Clustering. Default is "average".
    - method (str): The clustering method ("agglomerative" or "kmeans"). Default is "agglomerative".

Returns:
- list: A list of dictionaries, where each dictionary contains:
    - "label": The label of the cluster.
    - "line_ids": A list of line IDs in the cluster.

---

# File: annotate_sentence_transformers.py

## `annotate_sentence_transformers`

Annotates a concordance with embeddings generated by a Sentence Transformer model.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Concordance or ConcordanceSubset): The concordance data.
- args (dict): Arguments include:
    - tokens_attribute (str): The positional attribute to extract tokens from (e.g., "word"). Default is "word".
    - window_start (int, optional): The lower bound of the window (inclusive). Default is None (entire line).
    - window_end (int, optional): The upper bound of the window (inclusive). Default is None (entire line).
    - model_name (str): The name of the pretrained Sentence Transformer model. Default is "all-MiniLM-L6-v2".

Returns:
- pd.Series: A Pandas Series indexed by concordance line IDs, containing the embeddings for each line.

---

# File: annotate_spacy_embeddings.py

## `annotate_spacy_embeddings`

Annotates a concordance with embeddings generated by averaging spaCy word embeddings
for tokens within a specified window.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - spacy_model (str): The spaCy model to use. Default is "en_core_web_md".
    - tokens_attribute (str): The token attribute to use for creating line texts. Default is "word".
    - exclude_values_attribute (str, optional): The attribute to filter out specific values.
    - exclude_values_list (list, optional): The list of values to exclude.
    - window_start (int): The lower bound of the token window (inclusive). Default is -5.
    - window_end (int): The upper bound of the token window (inclusive). Default is 5.
    - include_node (bool): Whether to include the node token (offset 0). Default is True.

Returns:
- pd.Series: A Pandas Series indexed by concordance line IDs, containing the averaged embeddings for each line.

---

# File: select_by_metadata_attribute.py

## `select_by_metadata_attribute`

Selects concordance lines based on a specified metadata attribute comparing it to a target value.

When the target value is a list, only equality is used (the metadata value must equal one of the list items).
When the target value is a single numeric value, a comparison operator (one of "==", "<", "<=", ">", ">=")
can be provided. For string values, only equality is supported (with optional regex matching and case sensitivity).

Parameters:
    conc (Concordance or ConcordanceSubset): The concordance object.
    args (dict): Arguments include:
        - metadata_attribute (str): The metadata attribute to filter on.
        - value (str, number, or list of str/number): The value (or list of values) to compare against.
        - operator (str, optional): Comparison operator for numeric comparisons. One of "==", "<", "<=", ">", ">=".
                                    Default is "==".
                                    This parameter is ignored if a list is provided or if the value is a string.
        - regex (bool, optional): If True, for string values use regex matching (only with equality). Default is False.
        - case_sensitive (bool, optional): If True, perform case-sensitive matching for strings. Default is False.
        - negative (bool, optional): If True, invert the selection. Default is False.

Returns:
    dict: A dictionary containing:
        - "selected_lines": A sorted list of line IDs for which the metadata attribute meets the condition.

---

# File: select_slot.py

## `select_slot`

Selects the appropriate offset column based on the slot_id.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The concordance or subset of data.
- args (dict): Arguments include:
    - slot_id (int): The slot identifier used to generate the offset column name.

Returns:
- dict: A dictionary containing:
    - "slot_to_use": The slot ID being selected.
    - "selected_lines": A list of all line IDs in the concordance.
    - "line_count": The total number of lines.

---

# File: select_by_token_attribute.py

## `select_by_token_attribute`

Selects lines based on a positional attribute at a given offset.

Args are dynamically validated and extracted from the schema.

Parameters:
  - conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
  - **kwargs: Arguments defined dynamically in the schema.

Returns:
  - dict: A dictionary containing:
      - "selected_lines": A list of line IDs where the condition is met.

---

# File: select_manual.py

## `select_manual`

Manually selects lines into a subset by providing a list of line IDs or by specifying groups
(by labels or numbers) from the active node's grouping result. Groups may be partitions or clusters.
In case of clusters (which may be nested), the entire grouping structure is traversed recursively
to collect all groups that match the given identifiers.

Additionally, this algorithm ensures that only lines that are present in the current node's
selected_lines (or its closest ancestor that has this attribute) are allowed.

Args:
    conc (Union[Concordance, ConcordanceSubset]): The concordance or its subset.
    args (dict): Arguments include:
        - line_ids (list, optional): A list of specific line IDs to include in the subset.
        - groups (list, optional): A list of group identifiers (either integers or strings) that
          refer to groups (partitions or clusters) in the grouping_result.

Returns:
    dict: A dictionary containing:
        - "selected_lines": A sorted list of unique selected line IDs.
        - "line_count": The total number of selected lines.

---

# File: select_set_operation.py

## `select_set_operation`

Performs a set operation (union, intersection, difference, disjunctive union, complement)
on the sets of lines from specified nodes in the analysis tree.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The concordance or subset of data.
- args (dict): Arguments include:
    - operation_type (str): Type of set operation ('union', 'intersection', 'difference',
                            'disjunctive union', 'complement').
    - nodes (list): A list of nodes to retrieve selected lines from.

Returns:
- dict: A dictionary containing:
    - "selected_lines": A sorted list of line IDs resulting from the set operation.
    - "line_count": The total number of selected lines.

---

# File: select_weighted_sample_by_metadata.py

## `select_weighted_sample_by_metadata`

Selects a weighted sample of lines based on the distribution of a specified metadata attribute.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Concordance or ConcordanceSubset): The concordance data.
- args (dict): Arguments include:
    - metadata_attribute (str): The metadata attribute to stratify by (e.g., 'genre', 'speaker').
    - sample_size (int): The total number of lines to sample.
    - seed (int, optional): Random seed for reproducibility. Default is None.

Returns:
- dict: A dictionary containing:
    - 'selected_lines': A list of line IDs that have been sampled.
    - 'line_count': The total number of lines sampled.

---

# File: partition_ngrams.py

## `partition_ngrams`

Extracts ngram patterns from specified positions within each line and partitions the concordance
according to the frequency of these patterns.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- args (dict): Arguments include:
    - positions (List[int]): The list of positions (offsets) to extract for the ngram pattern.
    - tokens_attribute (str): The positional attribute to search within (e.g., 'word'). Default is 'word'.
    - case_sensitive (bool): If True, the search is case-sensitive. Default is False.

Returns:
- list: A list of dictionaries, where each dictionary has:
    - "label": The ngram pattern (as a string).
    - "line_ids": A list of line IDs associated with the pattern.

---

# File: rank_kwic_grouper.py

## `rank_kwic_grouper`

Ranks lines based on the count of a search term within a specific positional attribute column
within a given window (KWIC). Additionally, returns token spans for matching tokens.

Args are dynamically validated and extracted from the schema.

Parameters:
- conc (Union[Concordance, ConcordanceSubset]): The full concordance or a subset of it.
- **kwargs: Arguments defined dynamically in the schema.

Returns:
- dict: A dictionary containing:
    - "rank_keys": A mapping from line IDs to their ranking values based on the count of the search term.
    - "token_spans": A DataFrame with columns:
          id, line_id, start_id_in_line, end_id_in_line, category, weight.
      Here, category is "A", weight is 1, and since each span is one token long,
      start_id_in_line equals end_id_in_line (an inclusive index).

---
