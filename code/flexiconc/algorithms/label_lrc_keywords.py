from collections import Counter
from scipy.stats import beta
import math


def label_lrc_keywords(conc, **args):
    """
    Assign labels to partitions or clusters based on LRC (Log Ratio Coefficient) keywords.
    
    Parameters
    ----------
    partitions : list, optional
        List of partition dictionaries from a grouping algorithm result.
        Each partition should have a 'line_ids' key.
        If not provided, will use partitions from the grouping_result.
    cluster : dict, optional
        Cluster dictionary from a hierarchical clustering algorithm.
        If not provided, will use cluster from the grouping_result.
    max_keywords : int, optional
        Maximum number of keywords to include in the label (default 5).
    lrc_cutoff : float, optional
        Minimum absolute LRC value to consider a keyword (default 0.0).
    include_negative : bool, optional
        Whether to include negative keywords (LRC < 0) listed separately at the end (default False).
    whitelist : dict, optional
        Dictionary with token-level attribute names as keys and lists of allowed values.
        Example: {"pos": ["NN", "JJ"]} - only consider nouns and adjectives.
    blacklist : dict, optional
        Dictionary with token-level attribute names as keys and lists of excluded values.
        Example: {"pos": ["PUN"]} - exclude punctuation.
    window_start : int, optional
        Lower bound of token window for context analysis (default -5).
    window_end : int, optional
        Upper bound of token window for context analysis (default 5).
    tokens_attribute : str, optional
        Token attribute to use for keyword analysis (default 'word').
    alpha : float, optional
        Significance level for LRC computation (default 0.05).
    
    Returns
    -------
    dict
        Dictionary with 'labels' key containing a mapping from partition/cluster
        identifiers to human-readable label strings.
    """
    
    # Metadata for the algorithm
    label_lrc_keywords._algorithm_metadata = {
        "name": "LRC Keyword Labels",
        "description": (
            "Assigns labels to partitions or clusters based on Log Ratio Coefficient (LRC) keywords. "
            "Labels are human-readable strings containing the top keywords that distinguish each partition/cluster."
        ),
        "algorithm_type": "labelling",
        "args_schema": {
            "type": "object",
            "properties": {
                "max_keywords": {
                    "type": "integer",
                    "description": "Maximum number of keywords to include in the label.",
                    "default": 5,
                    "minimum": 1,
                },
                "lrc_cutoff": {
                    "type": "number",
                    "description": "Minimum absolute LRC value to consider a keyword.",
                    "default": 0.0,
                    "minimum": 0.0,
                },
                "include_negative": {
                    "type": "boolean",
                    "description": "Whether to include negative keywords (LRC < 0) listed separately at the end.",
                    "default": False,
                },
                "whitelist": {
                    "type": "object",
                    "description": "Dictionary with token-level attribute names as keys and lists of allowed values.",
                    "default": {},
                },
                "blacklist": {
                    "type": "object",
                    "description": "Dictionary with token-level attribute names as keys and lists of excluded values.",
                    "default": {},
                },
                "window_start": {
                    "type": "integer",
                    "description": "Lower bound of token window for context analysis.",
                    "default": -5,
                },
                "window_end": {
                    "type": "integer",
                    "description": "Upper bound of token window for context analysis.",
                    "default": 5,
                },
                "tokens_attribute": {
                    "type": "string",
                    "description": "Token attribute to use for keyword analysis.",
                    "default": "word",
                },
                "alpha": {
                    "type": "number",
                    "description": "Significance level for LRC computation.",
                    "default": 0.05,
                },
            },
            "required": [],
        },
    }
    
    def compute_lrc(f1, f2, n1, n2, alpha=0.05):
        """Compute Log Ratio Coefficient with Pearson-Clopper binomial confidence intervals."""
        if f1 == 0 and f2 == 0:
            return 0.0
        
        m = f1 + f2
        alpha_adj = alpha / m
        
        if m == 0:
            return 0.0
        
        if f1 == 0:
            pi_lower = 0.0
        else:
            pi_lower = beta.ppf(alpha_adj / 2, f1, f2 + 1)
        
        if f2 == 0:
            pi_upper = 1.0
        else:
            pi_upper = beta.ppf(1 - alpha_adj / 2, f1 + 1, f2)
        
        if pi_lower > 0 and pi_lower < 1 and n1 > 0 and n2 > 0:
            lrc_lower = math.log2((n2 * pi_lower) / (n1 * (1 - pi_lower)))
        elif pi_lower == 0:
            lrc_lower = float('-inf')
        else:
            lrc_lower = float('inf')
        
        if pi_upper > 0 and pi_upper < 1 and n1 > 0 and n2 > 0:
            lrc_upper = math.log2((n2 * pi_upper) / (n1 * (1 - pi_upper)))
        elif pi_upper == 1:
            lrc_upper = float('inf')
        else:
            lrc_upper = float('-inf')
        
        if lrc_lower <= 0 <= lrc_upper:
            return 0.0
        
        p1 = f1 / n1 if n1 > 0 else 0.0
        p2 = f2 / n2 if n2 > 0 else 0.0
        
        if p1 > p2:
            return lrc_lower
        else:
            return lrc_upper
    
    # Extract parameters
    max_keywords = args.get("max_keywords", 5)
    lrc_cutoff = args.get("lrc_cutoff", 0.0)
    include_negative = args.get("include_negative", False)
    whitelist = args.get("whitelist", {})
    blacklist = args.get("blacklist", {})
    window_start = args.get("window_start", -5)
    window_end = args.get("window_end", 5)
    tokens_attribute = args.get("tokens_attribute", "word")
    alpha = args.get("alpha", 0.05)
    
    # Get partitions or clusters from the grouping result
    partitions = args.get("partitions", [])
    cluster = args.get("cluster", None)
    
    labels = {}
    
    if partitions:
        # Collect all line IDs from all partitions for reference corpus
        all_partition_line_ids = set()
        for partition in partitions:
            all_partition_line_ids.update(partition.get('line_ids', []))
        
        # Process each partition
        for partition in partitions:
            line_ids = partition.get('line_ids', [])
            if len(line_ids) == 0:
                continue
            
            # Get tokens for this partition (target corpus)
            partition_tokens = conc.tokens[conc.tokens['line_id'].isin(line_ids)].copy()
            partition_tokens = partition_tokens[
                (partition_tokens['offset'].between(window_start, window_end)) & 
                (partition_tokens['offset'] != 0)
            ]
            
            # Apply whitelist/blacklist filters
            if whitelist:
                for attr, allowed_values in whitelist.items():
                    if attr in partition_tokens.columns:
                        partition_tokens = partition_tokens[partition_tokens[attr].isin(allowed_values)]
            
            if blacklist:
                for attr, excluded_values in blacklist.items():
                    if attr in partition_tokens.columns:
                        partition_tokens = partition_tokens[~partition_tokens[attr].isin(excluded_values)]
            
            # Get tokens for reference corpus (all other partitions)
            ref_line_ids = all_partition_line_ids - set(line_ids)
            ref_tokens = conc.tokens[conc.tokens['line_id'].isin(ref_line_ids)].copy()
            ref_tokens = ref_tokens[
                (ref_tokens['offset'].between(window_start, window_end)) & 
                (ref_tokens['offset'] != 0)
            ]
            
            # Apply whitelist/blacklist filters to reference corpus
            if whitelist:
                for attr, allowed_values in whitelist.items():
                    if attr in ref_tokens.columns:
                        ref_tokens = ref_tokens[ref_tokens[attr].isin(allowed_values)]
            
            if blacklist:
                for attr, excluded_values in blacklist.items():
                    if attr in ref_tokens.columns:
                        ref_tokens = ref_tokens[~ref_tokens[attr].isin(excluded_values)]
            
            # Convert to lowercase for case-insensitive analysis
            partition_tokens['word_lower'] = partition_tokens[tokens_attribute].str.lower()
            ref_tokens['word_lower'] = ref_tokens[tokens_attribute].str.lower()
            
            # Count frequencies
            target_freqs = Counter(partition_tokens['word_lower'])
            ref_freqs = Counter(ref_tokens['word_lower'])
            
            # Corpus sizes
            n1 = len(partition_tokens)
            n2 = len(ref_tokens)
            
            # Get all candidate words
            all_words = set(target_freqs.keys()) | set(ref_freqs.keys())
            
            # Compute LRC for each word
            lrc_scores = {}
            for word in all_words:
                f1 = target_freqs.get(word, 0)
                f2 = ref_freqs.get(word, 0)
                lrc = compute_lrc(f1, f2, n1, n2, alpha)
                lrc_scores[word] = lrc
            
            # Filter by cutoff and separate positive/negative
            positive_keywords = [(w, lrc) for w, lrc in lrc_scores.items() 
                                if lrc > 0 and abs(lrc) >= lrc_cutoff]
            negative_keywords = [(w, lrc) for w, lrc in lrc_scores.items() 
                               if lrc < 0 and abs(lrc) >= lrc_cutoff]
            
            # Sort by absolute LRC descending, then by LRC descending
            positive_keywords.sort(key=lambda x: (abs(x[1]), x[1]), reverse=True)
            negative_keywords.sort(key=lambda x: (abs(x[1]), x[1]), reverse=True)
            
            # Take top keywords
            top_positive = positive_keywords[:max_keywords]
            top_negative = negative_keywords[:max_keywords] if include_negative else []
            
            # Build human-readable label (space-separated keywords)
            keyword_list = []
            if top_positive:
                keyword_list.extend([w for w, _ in top_positive])
            
            if include_negative and top_negative:
                neg_words = [w for w, _ in top_negative]
                keyword_list.append("(not: " + " ".join(neg_words) + ")")
            
            keywords_str = " ".join(keyword_list) if keyword_list else "no keywords"
            
            # Store label - preserve original cluster number
            # Use existing label if present, otherwise create one based on index
            original_label = partition.get("label", f"Cluster_{partitions.index(partition)}")
            partition_key = original_label
            
            # Extract cluster number from label (e.g., "Cluster_0" -> "0", "partition_1" -> "1")
            import re
            match = re.search(r'(\d+)$', original_label)
            cluster_num = match.group(1) if match else str(partitions.index(partition))
            
            # Create new label: "1 (keyword1, keyword2, keyword3)"
            new_label = f"{cluster_num} ({keywords_str})"
            labels[partition_key] = new_label
            partition["label"] = new_label
    
    elif cluster:
        # For hierarchical clusters, process recursively
        def process_cluster_recursive(cluster_dict, all_cluster_line_ids):
            if cluster_dict.get("type") == "cluster":
                line_ids = []
                # Collect line_ids from this cluster and its children
                def collect_line_ids(c):
                    if "line_ids" in c:
                        line_ids.extend(c["line_ids"])
                    if "children" in c:
                        for child in c["children"]:
                            if child.get("type") == "lines":
                                line_ids.extend(child.get("line_ids", []))
                            elif child.get("type") == "cluster":
                                collect_line_ids(child)
                
                collect_line_ids(cluster_dict)
                
                if len(line_ids) == 0:
                    return
                
                # Get tokens for this cluster (target corpus)
                cluster_tokens = conc.tokens[conc.tokens['line_id'].isin(line_ids)].copy()
                cluster_tokens = cluster_tokens[
                    (cluster_tokens['offset'].between(window_start, window_end)) & 
                    (cluster_tokens['offset'] != 0)
                ]
                
                # Apply filters
                if whitelist:
                    for attr, allowed_values in whitelist.items():
                        if attr in cluster_tokens.columns:
                            cluster_tokens = cluster_tokens[cluster_tokens[attr].isin(allowed_values)]
                
                if blacklist:
                    for attr, excluded_values in blacklist.items():
                        if attr in cluster_tokens.columns:
                            cluster_tokens = cluster_tokens[~cluster_tokens[attr].isin(excluded_values)]
                
                # Get tokens for reference corpus (all other clusters)
                ref_line_ids = all_cluster_line_ids - set(line_ids)
                ref_tokens = conc.tokens[conc.tokens['line_id'].isin(ref_line_ids)].copy()
                ref_tokens = ref_tokens[
                    (ref_tokens['offset'].between(window_start, window_end)) & 
                    (ref_tokens['offset'] != 0)
                ]
                
                # Apply filters to reference
                if whitelist:
                    for attr, allowed_values in whitelist.items():
                        if attr in ref_tokens.columns:
                            ref_tokens = ref_tokens[ref_tokens[attr].isin(allowed_values)]
                
                if blacklist:
                    for attr, excluded_values in blacklist.items():
                        if attr in ref_tokens.columns:
                            ref_tokens = ref_tokens[~ref_tokens[attr].isin(excluded_values)]
                
                cluster_tokens['word_lower'] = cluster_tokens[tokens_attribute].str.lower()
                ref_tokens['word_lower'] = ref_tokens[tokens_attribute].str.lower()
                
                target_freqs = Counter(cluster_tokens['word_lower'])
                ref_freqs = Counter(ref_tokens['word_lower'])
                
                n1 = len(cluster_tokens)
                n2 = len(ref_tokens)
                
                all_words = set(target_freqs.keys()) | set(ref_freqs.keys())
                
                lrc_scores = {}
                for word in all_words:
                    f1 = target_freqs.get(word, 0)
                    f2 = ref_freqs.get(word, 0)
                    lrc = compute_lrc(f1, f2, n1, n2, alpha)
                    lrc_scores[word] = lrc
                
                positive_keywords = [(w, lrc) for w, lrc in lrc_scores.items() 
                                    if lrc > 0 and abs(lrc) >= lrc_cutoff]
                negative_keywords = [(w, lrc) for w, lrc in lrc_scores.items() 
                                   if lrc < 0 and abs(lrc) >= lrc_cutoff]
                
                positive_keywords.sort(key=lambda x: (abs(x[1]), x[1]), reverse=True)
                negative_keywords.sort(key=lambda x: (abs(x[1]), x[1]), reverse=True)
                
                top_positive = positive_keywords[:max_keywords]
                top_negative = negative_keywords[:max_keywords] if include_negative else []
                
                # Build human-readable label (space-separated keywords)
                keyword_list = []
                if top_positive:
                    keyword_list.extend([w for w, _ in top_positive])
                
                if include_negative and top_negative:
                    neg_words = [w for w, _ in top_negative]
                    keyword_list.append("(not: " + " ".join(neg_words) + ")")
                
                keywords_str = " ".join(keyword_list) if keyword_list else "no keywords"
                
                # Preserve original cluster label/number
                original_label = cluster_dict.get("label", f"Cluster_{cluster_dict.get('id', 'unknown')}")
                cluster_id = cluster_dict.get("id")
                
                # Extract cluster number from label
                import re
                match = re.search(r'(\d+)$', original_label)
                cluster_num = match.group(1) if match else str(cluster_id) if cluster_id else "unknown"
                
                # Create new label: "1 (keyword1, keyword2, keyword3)"
                new_label = f"{cluster_num} ({keywords_str})"
                
                if cluster_id:
                    labels[cluster_id] = new_label
                cluster_dict["label"] = new_label
                
                # Process children recursively
                if "children" in cluster_dict:
                    for child in cluster_dict["children"]:
                        if child.get("type") == "cluster":
                            process_cluster_recursive(child, all_cluster_line_ids)
        
        # Collect all line IDs from the cluster tree
        def collect_all_line_ids(c):
            line_ids = []
            if "line_ids" in c:
                line_ids.extend(c["line_ids"])
            if "children" in c:
                for child in c["children"]:
                    if child.get("type") == "lines":
                        line_ids.extend(child.get("line_ids", []))
                    elif child.get("type") == "cluster":
                        line_ids.extend(collect_all_line_ids(child))
            return line_ids
        
        all_cluster_line_ids = set(collect_all_line_ids(cluster))
        process_cluster_recursive(cluster, all_cluster_line_ids)
    
    return {"labels": labels}


