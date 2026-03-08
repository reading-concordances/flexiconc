# FlexiConc algorithms

---

## **Selecting Algorithms**

### `Select by a Token-Level Attribute`
- **Description:** Selects lines based on the specified token-level attribute at a given offset, with optional case-sensitivity, regex, or negation.
- **Function:** `select_by_positional_attribute`
- **Arguments:**
  - **tokens_attribute** (str): The token-level attribute to check (e.g., "word"). Default is `"word"`.
  - **offset** (int): The offset from the current token to check the attribute. Default is `0`.
  - **value** (str): The value to match against. Default is an empty string.
  - **case_sensitive** (bool): If `True`, performs a case-sensitive match. Default is `False`.
  - **regex** (bool): If `True`, use regex matching instead of exact matching. Default is `False`.
  - **negative** (bool): If `True`, select lines where the match fails (negation). Default is `False`.
  
    >  Negative is one minus the result. Better call it `negation`, `complement`, `invert`, or so.

### `Select Span`
- **Description:** Selects the span to work with by choosing the corresponding offset column.
- **Function:** `select_span`
- **Arguments:**
  - **span_id** (int): The span identifier corresponding to the column `offset{span_id}`.

---

## **Sorting Algorithms**

### `Sort by Corpus Position`
- **Description:** Sorts the concordance lines by their `line_id`, corresponding to their position in the corpus.
- **Function:** `sort_by_corpus_position`
- **Arguments:** None.

### `Sort by Token-Level Attribute`
- **Description:** Sorts the concordance lines by the given token-level attribute at the specified offset, using locale-specific sorting. It can also handle case-sensitivity, reverse sorting, and string sorting from the end to the start.
- **Function:** `sort_by_token_attribute`
- **Arguments:**
  - **tokens_attribute** (str): The token-level attribute to sort by. Default is `"word"`.
  - **offset** (int): The offset from the token to apply the sort. Default is `0`.
  
    >  Better sort by span rather than single tokens? Could easily extend to complete left/right context if the lower/upper end of the span can be omitted.
  - **case_sensitive** (bool): If `True`, sorts in a case-sensitive manner. Default is `False`.
  - **reverse** (bool): If `True`, sorts in reverse order. Default is `False`.
  - **backwards** (bool): If `True`, sorts strings from the end to the start. Default is `False`.
  - **locale_str** (str): The locale to use for sorting. Default is `"en"`.

### `Random Sort`
- **Description:** Randomizes the order of the concordance lines by assigning unique random integers.
- **Function:** `sort_random`
- **Arguments:**
  
  - **seed** (Optional[int]): A random seed for reproducibility. Default is `None`.
  
    >  I don't think we should allow sorting without seed! Otherwise you've completely nuked reproducibility. Or at least auto-generate a seed that's made an explicity parameter in the analysis tree node.

---

## **Ranking Algorithms**

### `KWIC Grouper Ranker`
- **Description:** Ranks lines based on the count of a search term in a specified positional attribute within a window.
- **Function:** `rank_kwic_grouper`
- **Arguments:**
  - **tokens_attribute** (str): The token-level attribute to search within. Default is `"word"`.
  - **search_term** (str): The term to search for. Default is an empty string.
  
    > Single term doesn't make very much sense. Best would be to have a list of terms or a regex (or a list of regexes if you wish).
  - **regex** (bool): If `True`, uses regex matching. Default is `False`.
  - **case_sensitive** (bool): If `True`, performs a case-sensitive search. Default is `False`.
  - **include_node** (bool): If `True`, includes node-level tokens in the search. Default is `False`.
  - **window_start** (int): The start of the window range. Default is `0`.
  
    >  This can be difficult since window might be to left or right. Probably need a general solution for speciying offsets, perhaps by giving reference point (start / end of match) and numerical offsets.
  - **window_end** (int): The end of the window range. Default is `0`.

---

## **Partition Algorithms**

### `Partition by Metadata Attribute`
- **Description:** Partitions the concordance lines based on a specified metadata attribute and groups the data by the values of this attribute.
- **Function:** `partition_by_metadata_attribute`
- **Arguments:**
  - **metadata_attribute** (str): The metadata attribute to partition by. Default is `None`.
  - **sort_by_partition_size** (bool): If `True`, sorts partitions by size. Default is `True`.
  - **sorted_values** (Optional[List[Union[str, int]]]): A list of values to sort partitions by. Default is `None`.


----------------------------------------------------------
DO NOT READ BELOW THIS LINE! IT IS OLD, BUT SOME OF IT MIGHT BE USEFUL

# OLD
## Selecting Algorithms
{TODO: Copied from the description of the algorithms. Needs to be rewritten.}

- Select concordance lines based on metadata categories (e.g. certain text types) or a numerical range (e.g. date of publication). The algorithm may also allow analysts to formulate complex Boolean expressions involving multiple metadata variables. 

- KWIC filter selects or excludes concordance lines containing certain words, lemmas or POS tags (in a specified span around the node). 

- Selecting a random subset of lines to make close reading of the concordance a manageable task. It is essential that the operation is reproducible, which can be achieved by specifying a seed value for the random selection of lines. Alternatively, the selection could be based on hash values generated from the content of the concordance lines, making random subsets consistent when combined with other Selecting algorithms. 

- Manual selection of individual concordance lines or ranges of lines.

## Sorting Algorithms

#### `sort_random(seed=0)`

The `sort_random` method randomizes the order of concordance data.

**Parameters:**

- **seed** (int, optional): The seed value for the random number generator. Setting a specific seed ensures that the randomization is reproducible. By default, it is set to `0`, which will use the specified seed. If `None` is provided, the method will use the current system time, leading to a different random order each time.

**Returns:**

- **list**: A list of line IDs representing the randomized order of the concordance lines.

**Other sorting algortihms:** {TODO: Copied from the description of the algorithms. Needs to be rewritten.}

- Sort alphabetically by left or right context. 

- Sort by POS tag of the token immediately before the node (L1). The corresponding POS tags might be returned by the algorithm in the dictionary of supplementary information. 

- Sort by lemma or word form of the three tokens to the right of the node (R1, R2, R3). This is equivalent to applying a sequence of three Sorting algorithms: by R1, then by R2 and by R3 as tie-breakers. Both approaches will produce exactly the same result, but being able to sort on multiple tokens directly is more convenient for analysts. 

- The “KWIC patterns” functionality of AntConc is very similar, but sorts lines based on descending frequency of the trigram (R1, R2, R3), then alphabetically. To match the AntConc visualisation, the respective tokens would be highlighted in different colours (as single-token spans assigned to different categories). It might also be useful to return trigram frequency in the dictionary of supplementary information so that users have an indication how many further lines of the same pattern they need to scroll through. 
- Sort concordance lines by a numerical value, such as date of publication or timestamp of a posting (e.g. on Twitter). 

- Sort concordance lines according to a categorical metadata variable (genre, author, year/decade, etc.). The analyst may be allowed to specify multiple metadata variables for breaking ties, which is equivalent to – but more convenient than – applying a sequence of multiple Sorting algorithms (one for each metadata variable). 

- Sort concordance lines in their original order, i.e. by line №. This algorithm is always used implicitly as a final tie-breaker and need not be specified by the analyst.

## Ranking Algorithms
{TODO: Copied from the description of the algorithms. Needs to be rewritten.}

- Sketch Engine’s GDEX algorithm, which computes a score indicating how useful each concordance line is as a dictionary example. This Ranking algorithm will typically prefer short sentences without many rare words, which can be understood without referring to a larger context. As most Ranking algorithms, GDEX should return its scores in the dictionary of supplementary information.
- Ranking lines based on the number of significant collocates found in the context. Parameters selected by the analyst include the association measure used to determine collocates, the corresponding significance threshold, and the context span in which collocates are counted. In addition, a frequency list has to be provided as marginal frequencies for the association measures. Collocate counts might be weighted by the distance between node and collocate or by its association score. Occurrences of the collocates in the concordance lines may be highlighted as token spans, using relevance weights to indicate association scores.
- Ranking lines based on how well they fit a user-specified CEFR level. Preference scores are the classification probabilities of a machine-learning CEFR classifier. With a wordlist-based classifier, token spans might be used to highlight words belonging to the different CEFR levels in different colours.
- KWICgrouper (Brook O'Donnell 2008) as implemented in the CLiC concordancer, i.e. rank lines based on the number of manually selected keywords occurring close to the node (and possibly weighted by distance). The keywords are chosen by the analyst as a parameter of the algorithm and might allow regular expression notation for greater flexibility. Occurrences of the keywords will be highlighted as token spans. 

## Partitioning Algorithms
{TODO: Copied from the description of the algorithms. Needs to be rewritten.}
- Partition by POS tag of the token at some offset from the concordance node, e.g. by the first token before the node (L1). Sets will normally be ordered by decreasing size, but analysts may have the option to switch to alphabetical ordering. Partition labels are the corresponding POS tags. 

- Partition by lemma or word form of the three tokens to the right of the node, creating frequency counts for the trigram (R1, R2, R3). Partition labels are the respective trigrams. 

- Partition concordance lines according to a categorical metadata variable (genre, author, year/decade, etc.), whose values form the display labels of the sets. This algorithm will also allow users to select multiple metadata variables in order to carry out a cross-classification. Partition labels are the respective metadata values (or concatenated combinations of values for a cross-classification). 

- Partition concordance lines by CEFR level, based on a machine-learning CEFR classifier.

- A Partitioning wrapper could take any Sorting algorithm (with its parameters) and group concordance lines based on its surrogate keys. 

- Another Partitioning wrapper could take multiple Partitioning algorithms (with their parameters) and carry out the cross-classification of all partitionings. In this case, display labels are easily constructed from the display labels assigned by the individual Partitioning algorithms. 

## Clustering Algorithms
{TODO: Copied from the description of the algorithms. Needs to be rewritten.}
- Cluster concordance lines according to their lexical similarity (i.e. the number of shared words in the left and right context).
- Cluster concordance lines according to their syntactic similarity (e.g. the number of shared POS n-grams in the left and right context, or a tree kernel determining the similarity of phrase structure trees or dependency graphs).
- Cluster concordance lines according to their semantic similarity (e.g. based on word embeddings and maximum weight matching, on context-sensitive word embeddings of the node, or on LLM span embeddings for the entire concordance line). 
- Cluster concordance lines based on multiple metadata variables: the more metadata values two lines share, the more similar they are assumed to be. 
- A word tree (or POS tree) visualisation of the left or right context (Wattenberg & Viégas 2008) can also be understood as a Clustering algorithm.