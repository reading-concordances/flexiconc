import html
import pandas as pd
import time
from collections import defaultdict

def format_concordance_line(line_df, left_node_right=False, html=False, table=False, p=["word"], style={},
                            l=-float('Inf'), u=float('Inf')):

    """
    Formats the given concordance line as a string.

    Parameters:
    - line_df (DataFrame): The dataframe representing the line.
    - left_node_right: A boolean flag. If set to True, it will return a dictionary structure
      dividing the line into left, node, and right sections. If set to False, it will just
      format the line as a single string.

    Returns:
    - A formatted string or a dictionary structure with the 'left', 'node', and 'right'
      parts of the line, depending on the `left_node_right` parameter.
    """

    # If just formatting the entire line as a single string
    if not left_node_right:
        output = ''
        right_punctuation = ['.', '?', '!', ',', '…', ';', ':', '"', "'", "n't"]
        left_punctuation = ['(', '`', '``']
        words = list(line_df.word.astype(str))
        offsets = list(line_df.offset)

        # Check if there are spaces provided in the concordance, else default to None
        spaces = list(line_df.space.astype(str)) if 'space' in line_df else None

        for i, word in enumerate(words):
            if offsets[i] < l or offsets[i] > u:
                continue
            if 'offset' in style and offsets[i] in style['offset']:
                output += style['offset'][offsets[i]].format(word)
            else:
                output += word

            # If explicit spaces are provided, use them
            if spaces is not None:
                output += spaces[i]
            else:
                # Check conditions to decide whether to add space or not
                if word in left_punctuation:
                    continue
                elif i < len(words) - 1 and (words[i + 1] in right_punctuation or words[i + 1][0] == "'"):
                    continue
                else:
                    output += ' '

        return output

    # If splitting the line into left, node, and right sections
    else:
        return {
            'left': format_concordance_line(line_df[line_df["offset"] < 0], html=html, table=table, p=p, style=style),
            'node': format_concordance_line(line_df[line_df["offset"] == 0], html=html, table=table, p=p, style=style),
            'right': format_concordance_line(line_df[line_df["offset"] > 0], html=html, table=table, p=p, style=style)
        }


def find_optimal_prototypicality_rounding(cluster_structure):
    """
    Find the optimal number of decimal places for displaying prototypicality scores
    such that no non-identical values appear identical after rounding.
    
    Args:
        cluster_structure: The clustering structure (dict) containing prototypicality scores
        
    Returns:
        int: The optimal number of decimal places for rounding
    """
    def collect_all_scores(cluster_obj):
        """Recursively collect all prototypicality scores from the cluster structure."""
        scores = []
        
        # Get scores from current cluster
        if "prototypicality" in cluster_obj:
            scores.extend(cluster_obj["prototypicality"].values())
        
        # Recursively collect from children
        for child in cluster_obj.get("children", []):
            if child.get("type") == "cluster":
                scores.extend(collect_all_scores(child))
        
        return scores
    
    # Collect all prototypicality scores
    all_scores = collect_all_scores(cluster_structure)
    
    if not all_scores:
        return 3  # Default to 3 decimal places if no scores found
    
    # Remove duplicates and sort
    unique_scores = sorted(set(all_scores))
    
    if len(unique_scores) <= 1:
        return 3  # If only one unique score, default to 3 decimal places
    
    # Test different decimal places
    for decimal_places in range(1, 10):  # Test 1 to 9 decimal places
        rounded_scores = [round(score, decimal_places) for score in unique_scores]
        if len(set(rounded_scores)) == len(unique_scores):
            # All unique scores remain unique after rounding
            return decimal_places
    
    # If we can't find a rounding that preserves uniqueness, return 6 decimal places
    return 6


def generate_concordance_html(concordance, node, n=None, n_groups=None, token_attr='word', extra_token_attrs=None,
                              metadata_columns=None, lines_to_display=None, show_clusters=False, cluster_max_depth=None, 
                              enable_timing=False, timing_report=None):
    """
    Generates HTML for concordance lines from the tokens in the subset at the given node,
    with optional custom metadata columns inserted between the line ID and the KWIC display.

    Parameters:
        concordance: The Concordance object.
        node: The analysis tree node whose subset is to be displayed.
        n (int, optional): The number of lines to display per partition or overall.
        n_groups (int, optional): If concordance view is partitioned, show only first `n_groups` groups. Default None shows all groups.
        token_attr (str, optional): The token attribute to display (e.g., 'word', 'lemma'). Default is 'word'.
        metadata_columns (list of str, optional): A list of metadata column names to display for each line.
            These columns will be shown between the "Line ID" column and the KWIC display columns.
        lines_to_display (list or range, optional): Specific line IDs to display. If provided, only these lines
            will be shown regardless of other filtering. Can be a list of line IDs or a range object.
        show_clusters (bool, optional): Whether to show cluster visualization if clustering results are available. Default False.
        cluster_max_depth (int, optional): Maximum depth to show in cluster tree. Default None shows all levels.
        enable_timing (bool, optional): Whether to enable detailed timing instrumentation. Default False.
        timing_report (dict, optional): Dictionary to store timing results. If None, timing results are printed.

    Returns:
        str: An HTML string representing the concordance lines.
    """
    # Initialize timing
    if enable_timing:
        if timing_report is None:
            timing_report = defaultdict(list)
        start_time = time.time()
        timing_report['total_start'] = start_time

    if extra_token_attrs is None:
        extra_token_attrs = []

    # Get the subset at the specified node.
    if enable_timing:
        subset_start = time.time()
    subset = concordance.subset_at_node(node)
    tokens = subset.tokens
    metadata = subset.metadata
    if enable_timing:
        timing_report['subset_retrieval'].append(time.time() - subset_start)

    # ── gather ranking columns from node.view() ────────────────────────────
    if enable_timing:
        ranking_start = time.time()
    ranking_cols = []  # list of (key, short_label)
    ranking_values = {}  # {line_id: {key: value …}}

    v = node.view()
    if "line_info" in v:
        col_info = v["line_info"]["column_info"]
        ranking_values = v["line_info"]["data"]

        for info in col_info:
            key = info["key"]  # full human-readable key
            # make a short label (R0, R1, …) instead of the long key
            short = f"R{info.get('algorithm_index_withing_ordering', 0)}"
            ranking_cols.append((key, short))
    if enable_timing:
        timing_report['ranking_columns'].append(time.time() - ranking_start)
    
    # Precompute data structures
    if enable_timing:
        precompute_start = time.time()
    
    tokens_by_line = tokens.sort_values(['line_id', 'offset', 'id_in_line']).groupby('line_id')
    
    metadata_by_line = {}
    if not metadata.empty:
        metadata_by_line = metadata.set_index('line_id').to_dict('index')
    
    span_lookup = {}
    span_dict_cache = {}
    if "token_spans" in v and v["token_spans"]:
        spans = v["token_spans"]
        if isinstance(spans, pd.DataFrame):
            for _, row in spans.iterrows():
                line_id = int(row["line_id"])
                start_id = int(row["start_id_in_line"])
                end_id = int(row["end_id_in_line"])
                category = row["category"] if "category" in row else "A"
                
                span_lookup.setdefault(line_id, []).append((start_id, end_id, category))
                
                if line_id not in span_dict_cache:
                    span_dict_cache[line_id] = {}
                for tok_id in range(start_id, end_id + 1):
                    span_dict_cache[line_id][tok_id] = f"mark-{category}"
        else:
            for span in spans:
                line_id = span["line_id"]
                start_id = span["start_id_in_line"]
                end_id = span["end_id_in_line"]
                category = span.get("category", "A")
                
                span_lookup.setdefault(line_id, []).append((start_id, end_id, category))
                
                if line_id not in span_dict_cache:
                    span_dict_cache[line_id] = {}
                for tok_id in range(start_id, end_id + 1):
                    span_dict_cache[line_id][tok_id] = f"mark-{category}"
    
    if enable_timing:
        timing_report['precompute_structures'].append(time.time() - precompute_start)

    # Start building the HTML.
    if enable_timing:
        html_build_start = time.time()

    CAT_COLOURS = {
        "A": "#ffe08a",  # warm yellow-orange
        "B": "#9ddfff",  # light blue-cyan
        "C": "#ffb3c9",  # soft pink
        "D": "#80B1D3",  # sky-blue
        "E": "#FDB462",  # vivid orange
        "F": "#B3DE69",  # light green
        "G": "#BC80BD",  # medium purple
        "H": "#FB8072",  # salmon red
        "I": "#CCEBC5",  # mint green
        "J": "#D9D9D9",  # mid-grey
    }

    html_output = """
    <script>
    function togglePartition(className) {
        const rows = document.querySelectorAll('.' + className);
        for (const row of rows) {
            row.style.display = (row.style.display === 'none') ? '' : 'none';
        }
    }

    // Track mouse events to distinguish between drag and click
    let mouseDownTime = 0;
    let mouseDownX = 0;
    let mouseDownY = 0;
    let isDragging = false;

    function handleMouseDown(event) {
        mouseDownTime = Date.now();
        mouseDownX = event.clientX;
        mouseDownY = event.clientY;
        isDragging = false;
    }

    function handleMouseMove(event) {
        if (mouseDownTime > 0) {
            const deltaX = Math.abs(event.clientX - mouseDownX);
            const deltaY = Math.abs(event.clientY - mouseDownY);
            if (deltaX > 5 || deltaY > 5) {
                isDragging = true;
            }
        }
    }

    function handleMouseUp(event) {
        mouseDownTime = 0;
    }

    function handleRowClick(event, row) {
        // Only show KWIC if it's not a drag operation
        if (!isDragging) {
            showKWIC(row);
        }
        isDragging = false;
    }

    function showKWIC(row){
        const left = row.querySelector('td.left-context div.left-context').innerHTML;
        const node = row.querySelector('td.node').innerHTML;
        const right= row.querySelector('td.right-context div.right-context').innerHTML;
        const ov = document.createElement('div');
        ov.className='kwic-overlay';
        ov.innerHTML = `<div class=\"kwic-modal\"><span class=\"kwic-close\" onclick=\"this.closest('.kwic-overlay').remove()\">×</span><div class=\"kwic-line\"><span class=\"left-context\">${left}</span> <span class=\"node\">${node}</span> <span class=\"right-context\">${right}</span></div></div>`;
        ov.addEventListener('click',e=>{if(e.target===ov)ov.remove()});
        document.body.appendChild(ov);
    }

    // Add global mouse event listeners
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    </script>

    <style>
        table.concordance {
            border-collapse: collapse;
            width: 100%;
            table-layout: auto;
        }
        table.concordance th, table.concordance td {
            border: 1px solid #dddddd;
            padding: 4px;
            vertical-align: top;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        table.concordance th {
            background-color: #f2f2f2;
            text-align: center;
        }
        table.concordance th.line-id, table.concordance td.line-id {
            text-align: center;
       ·     white-space: nowrap;
        }
        table.concordance th.metadata, table.concordance td.metadata {
            text-align: center;
            white-space: nowrap;
        }
        table.concordance th.left-context, table.concordance td.left-context {
            text-align: right;
            overflow: hidden;
            white-space: nowrap;
            width: 40%;
            max-width: 0px;
        }
        table.concordance th.node, table.concordance td.node {
            text-align: center;
            font-weight: bold;
            white-space: nowrap;
        }
        table.concordance th.right-context, table.concordance td.right-context {
            text-align: left;
            overflow: hidden;
            white-space: nowrap;
            width: 40%;
            max-width: 0px;
        }
        table.concordance div.left-context {
            float: right;
            white-space: nowrap;
        }
        table.concordance div.right-context {
            float: left;
            white-space: nowrap;
        }
        .kwic-overlay {position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:1000}
        .kwic-modal {background:#fff;padding:20px 28px;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.3);max-width:92%;overflow:auto}
        .kwic-close {float:right;font-size:140%;cursor:pointer;margin-left:8px}
        .kwic-line {white-space:pre-wrap}
    """
    for cat, col in CAT_COLOURS.items():
        html_output += f"        .mark-{cat} {{ background-color: {col}; }}\n"
    html_output += """
    </style>
    """
    
    # Only generate main table if not showing clusters or if no clusters exist
    if enable_timing:
        timing_report['html_structure_build'].append(time.time() - html_build_start)
        table_build_start = time.time()
    has_clusters = v.get("grouping", {}).get("cluster") is not None
    if not (show_clusters and has_clusters):
        html_output += """    <table class="concordance">
        <colgroup>
            <col>
    """
        # If metadata_columns are provided, add one <col> per column.
        if metadata_columns:
            for _ in metadata_columns:
                html_output += "            <col>\n"
        html_output += """            <col>
            <col>
            <col>
        </colgroup>
        <tr>
            <th class="line-id">Line ID</th>
    """
        # Add header cells for custom metadata columns.
        # metadata columns first …
        if metadata_columns:
            for col in metadata_columns:
                html_output += f'            <th class="metadata">{col}</th>\n'
        # … then any ranking columns
        for _k, short in ranking_cols:
            html_output += f'            <th class="metadata">{short}</th>\n'

        html_output += """            <th class="left-context">Left Context</th>
            <th class="node">Node</th>
            <th class="right-context">Right Context</th>
        </tr>
    """

    def _generate_lines_html(subset, line_ids, token_attr, metadata_columns=None, row_class="", hidden=False, ranking_values=None, ranking_cols=None, tokens_by_line=None, metadata_by_line=None, span_lookup=None, enable_timing=False, timing_report=None):
        if enable_timing:
            lines_start = time.time()

        tokens = subset.tokens
        metadata = subset.metadata
        html_rows = ""

        # Use passed parameters or fall back to global variables
        if ranking_values is None:
            ranking_values = globals().get('ranking_values', {})
        if ranking_cols is None:
            ranking_cols = globals().get('ranking_cols', [])

        # ---------- use precomputed span_lookup or build fallback ------------
        if span_lookup is None:
            span_lookup = {}
        spans_from_view = node.view().get("token_spans", None)
        if spans_from_view is not None:
            spans = spans_from_view
            if isinstance(spans, pd.DataFrame):
                for _, row in spans.iterrows():
                    span_lookup.setdefault(int(row["line_id"]), []).append(
                        (int(row["start_id_in_line"]),
                         int(row["end_id_in_line"]),
                         row["category"] if "category" in row else "A")
                    )
            else:  # list / iterable of dicts
                for span in spans:
                    span_lookup.setdefault(span["line_id"], []).append(
                        (span["start_id_in_line"],
                         span["end_id_in_line"],
                         span.get("category", "A"))
                    )

        # punctuation heuristics for spacing
        LEFT_PUNCT = {'(', '[', '{', '"'}
        RIGHT_PUNCT = {'.', ',', '!', '?', ';', ':', '"', ')', ']', '}', "...",
                       "'s", "'m", "'d", "'ve", "'re", "'ll", "'t", "n't"}

        def tokens_to_html(tok_df, line_id):
            """Convert tokens to HTML with span highlighting."""
            if tok_df.empty:
                return ""
            
            span_dict = span_dict_cache.get(line_id, {})
            LEFT_PUNCT_SET = frozenset(LEFT_PUNCT)
            RIGHT_PUNCT_SET = frozenset(RIGHT_PUNCT)
            
            parts = []
            parts_append = parts.append
            prev_tok = ''
            
            for row in tok_df.itertuples():
                tok_id = int(row.id_in_line)
                tok_text = str(getattr(row, token_attr))
                
                subscript = ""
                if extra_token_attrs:
                    extras = []
                    for attr in extra_token_attrs:
                        if hasattr(row, attr):
                            extras.append(str(getattr(row, attr)))
                    if extras:
                        sub_val = " / ".join(extras)
                        if sub_val.strip():
                            subscript = f"<sub style='margin-left:0.1em;font-size:80%;color:#999'>{html.escape(sub_val)}</sub>"
                
                mark_cls = span_dict.get(tok_id, None)
                
                if mark_cls:
                    span_html = f'<span data-id="{tok_id}" class="{mark_cls}">{html.escape(tok_text)}{subscript}</span>'
                else:
                    span_html = f'<span data-id="{tok_id}">{html.escape(tok_text)}{subscript}</span>'
                
                if parts and tok_text not in RIGHT_PUNCT_SET and prev_tok not in LEFT_PUNCT_SET:
                    parts_append(' ')
                parts_append(span_html)
                prev_tok = tok_text
            
            return ''.join(parts)
        
        

        # ---------- use precomputed data structures --------------------------
        # Use precomputed tokens_by_line if provided, otherwise build fallback
        if tokens_by_line is None:
            if line_ids:
                tokens_filtered = tokens[tokens['line_id'].isin(line_ids)].sort_values(
                    by=['line_id', 'offset', 'id_in_line']
                )
                tokens_by_line = tokens_filtered.groupby('line_id')
            else:
                tokens_by_line = {}

        # Use precomputed metadata_by_line if provided, otherwise build fallback
        if metadata_by_line is None:
            metadata_dict = {}
            if metadata_columns and not metadata.empty:
                for _, row in metadata.iterrows():
                    line_id = row['line_id']
                    metadata_dict[line_id] = {col: str(row.get(col, "")) for col in metadata_columns}
        else:
            # Use precomputed metadata_by_line
            metadata_dict = {}
            if metadata_columns:
                for line_id in line_ids:
                    if line_id in metadata_by_line:
                        metadata_dict[line_id] = {col: str(metadata_by_line[line_id].get(col, "")) for col in metadata_columns}

        # Pre-process ranking values (this is still needed per batch for prototypicality)
        ranking_dict = {}
        for line_id in line_ids:
            rv = ranking_values.get(line_id, {})
            ranking_dict[line_id] = {key: str(rv.get(key, "")) for key, _short in ranking_cols}

        html_rows_list = []
        
        if enable_timing:
            processing_start = time.time()
        
        display_style = "display: none;" if hidden else ""
        
        for line_id in line_ids:
            if line_id in tokens_by_line.groups:
                line_tok = tokens_by_line.get_group(line_id)
                left_tokens = line_tok[line_tok['offset'] < 0]
                node_tokens = line_tok[line_tok['offset'] == 0]
                right_tokens = line_tok[line_tok['offset'] > 0]
            else:
                left_tokens = node_tokens = right_tokens = pd.DataFrame()

            left_html = tokens_to_html(left_tokens, line_id)
            node_html = tokens_to_html(node_tokens, line_id)
            right_html = tokens_to_html(right_tokens, line_id)

            meta_cells = ""
            if metadata_columns:
                row_meta = metadata_dict.get(line_id, {})
                meta_cells = ''.join(f'<td class="metadata">{html.escape(row_meta.get(col, ""))}</td>\n' 
                                   for col in metadata_columns)

            rank_cells = ""
            if ranking_cols:
                rv = ranking_dict.get(line_id, {})
                rank_cells = ''.join(f'<td class="metadata">{html.escape(rv.get(key, ""))}</td>\n' 
                                   for key, _short in ranking_cols)

            row_html = f"""            <tr class="{row_class}" style="{display_style}" onclick="handleRowClick(event, this)">
                <td class="line-id">{line_id}</td>
                {meta_cells}{rank_cells}
                <td class="left-context"><div class="left-context">{left_html}</div></td>
                <td class="node">{node_html}</td>
                <td class="right-context"><div class="right-context">{right_html}</div></td>
            </tr>
            """
            html_rows_list.append(row_html)
        
        result = ''.join(html_rows_list)
        if enable_timing:
            timing_report['lines_html_generation'].append(time.time() - lines_start)
        return result


    def _generate_cluster_section_html(concordance, node, clusters, subset, token_attr, metadata_columns, ranking_cols, n, max_depth, tokens_by_line=None, metadata_by_line=None, span_lookup=None, enable_timing=False, timing_report=None):
        """Generate HTML for cluster visualization section."""
        if enable_timing:
            cluster_section_start = time.time()
        
        # Generate a unique tree ID to avoid conflicts with multiple trees on same page
        import time
        import random
        tree_id = f"tree_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # Find optimal rounding for prototypicality scores
        optimal_rounding = find_optimal_prototypicality_rounding(clusters)
        
        # Cache for cluster traversal results to avoid repeated computation
        cluster_cache = {}
        
        # Line data generation removed - using direct rendering approach
        
        # Add cluster-specific CSS
        cluster_css = """
        <style>
        .cluster-section {
            margin: 20px 0;
            font-family: Arial, sans-serif;
        }
        .cluster-header {
            background-color: #e8f4fd;
            border: 1px solid #b3d9ff;
            border-radius: 4px;
            padding: 12px 16px;
            margin: 8px 0;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .cluster-header:hover {
            background-color: #d1ecf1;
        }
        .cluster-header-small {
            cursor: default; /* No click for small clusters */
        }
        .cluster-header-small:hover {
            background-color: #e8f4fd; /* No hover effect for small clusters */
        }
        .cluster-toggle {
            margin-right: 10px;
            font-family: monospace;
            font-size: 14px;
        }
        .cluster-illustrations {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
            font-style: italic;
            color: #856404;
        }
        .cluster-illustrations .illustration-label {
            font-weight: bold;
            margin-bottom: 8px;
            color: #6c5ce7;
            font-size: 12px;
            text-transform: uppercase;
        }
        .cluster-content {
            margin-left: 20px;
            border-left: 3px solid #e9ecef;
            padding-left: 15px;
            margin-top: 10px;
        }
        .cluster-children {
            margin-top: 10px;
        }
        .cluster-lines {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
        }
        .cluster-lines .lines-label {
            font-weight: bold;
            margin-bottom: 8px;
            color: #495057;
            font-size: 12px;
            text-transform: uppercase;
        }
        /* Cluster tables use same styles as main concordance table */
        .cluster-concordance-table {
            border-collapse: collapse;
            width: 100%;
            table-layout: auto;
        }
        .cluster-concordance-table th, .cluster-concordance-table td {
            border: 1px solid #dddddd;
            padding: 4px;
            vertical-align: top;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .cluster-concordance-table th {
            background-color: #f2f2f2;
            text-align: center;
        }
        .cluster-concordance-table th.line-id, .cluster-concordance-table td.line-id {
            text-align: center;
            white-space: nowrap;
        }
        .cluster-concordance-table th.metadata, .cluster-concordance-table td.metadata {
            text-align: center;
            white-space: nowrap;
        }
        .cluster-concordance-table th.left-context, .cluster-concordance-table td.left-context {
            text-align: right;
            overflow: hidden;
            white-space: nowrap;
            width: 40%;
            max-width: 0px;
            text-overflow: ellipsis;
            direction: rtl;
            unicode-bidi: plaintext;
        }
        .cluster-concordance-table th.node, .cluster-concordance-table td.node {
            text-align: center;
            font-weight: bold;
            white-space: nowrap;
        }
        .cluster-concordance-table th.right-context, .cluster-concordance-table td.right-context {
            text-align: left;
            overflow: hidden;
            white-space: nowrap;
            width: 40%;
            max-width: 0px;
        }
        .cluster-concordance-table div.left-context {
            float: right;
            white-space: nowrap;
        }
        .cluster-concordance-table div.right-context {
            float: left;
            white-space: nowrap;
        }
        /* Ensure consistent column alignment across all tables */
        .cluster-section table {
            table-layout: fixed;
        }
        .cluster-section .line-id {
            width: 80px;
        }
        .cluster-section .metadata {
            width: 100px;
        }
        .cluster-section .left-context {
            width: 100%;
            text-align: right;
        }
        .cluster-section .node {
            width: 10%;
        }
        .cluster-section .right-context {
            width: 100%;
            text-align: left;
        }
        .cluster-mode-toggle {
            margin-left: 10px;
            font-size: 11px;
            display: none; /* Hidden by default, shown when expanded */
        }
        .cluster-mode-toggle select {
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: white;
            font-size: 11px;
            cursor: pointer;
        }
        .cluster-mode-toggle select:hover {
            background: #f8f9fa;
            border-color: #999;
        }
        .cluster-mode-toggle select:focus {
            outline: none;
            border-color: #2196F3;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
        }
        .prototypicality-score {
            font-size: 10px;
            color: #666;
            margin-left: 5px;
        }
        </style>
        """
        
        html_output = cluster_css
        html_output += '<div class="cluster-section">\n'
        
        def count_lines_in_cluster(cluster_obj):
            """Helper function to count lines in a cluster with caching."""
            cluster_id = cluster_obj.get("id")
            if cluster_id in cluster_cache:
                return cluster_cache[cluster_id]["line_count"]
            
            count = 0
            for child in cluster_obj.get("children", []):
                if child.get("type") == "lines":
                    count += len(child.get("line_ids", []))
                else:
                    count += count_lines_in_cluster(child)
            
            # Cache the result
            if cluster_id not in cluster_cache:
                cluster_cache[cluster_id] = {}
            cluster_cache[cluster_id]["line_count"] = count
            return count
        
        def get_illustration_lines(cluster):
            """Get illustration lines for a cluster."""
            illustrations = cluster.get("illustrations", [])
            if not illustrations:
                return []
            
            # Limit illustrations if n is specified
            if n is not None and n > 0:
                illustrations = illustrations[:n]
            
            return illustrations
        
        def get_all_lines_in_cluster(cluster):
            """Get all lines in a cluster (including from children) with prototypicality scores and caching."""
            cluster_id = cluster.get("id")
            if cluster_id in cluster_cache and "all_lines" in cluster_cache[cluster_id]:
                return cluster_cache[cluster_id]["all_lines"]
            
            all_lines = []
            prototypicality = cluster.get("prototypicality", {})
            
            def collect_lines(cluster_obj):
                for child in cluster_obj.get("children", []):
                    if child.get("type") == "lines":
                        line_ids = child.get("line_ids", [])
                        for line_id in line_ids:
                            score = prototypicality.get(line_id, 0.0)
                            all_lines.append((line_id, score))
                    else:
                        collect_lines(child)
            
            collect_lines(cluster)
            
            # Sort by prototypicality (descending)
            all_lines.sort(key=lambda x: x[1], reverse=True)
            
            # Cache the result
            if cluster_id not in cluster_cache:
                cluster_cache[cluster_id] = {}
            cluster_cache[cluster_id]["all_lines"] = all_lines
            
            # Limit if n is specified
            if n is not None and n > 0:
                all_lines = all_lines[:n]
            
            return all_lines
        
        def has_child_clusters(cluster):
            """Check if cluster has child clusters (not just lines)."""
            for child in cluster.get("children", []):
                if child.get("type") != "lines":
                    return True
            return False
        
        def render_cluster_table_header():
            """Generate the table header structure matching the main concordance table."""
            # Create a combined ranking_cols that includes prototypicality for cluster tables
            cluster_ranking_cols = list(ranking_cols)
            if ('prototypicality', 'Prototypicality') not in cluster_ranking_cols:
                cluster_ranking_cols.append(('prototypicality', 'Prototypicality'))
            
            header_html = """
        <colgroup>
            <col>
    """
            # If metadata_columns are provided, add one <col> per column.
            if metadata_columns:
                for _ in metadata_columns:
                    header_html += "            <col>\n"
            header_html += """            <col>
            <col>
            <col>
        </colgroup>
        <tr>
            <th class="line-id">Line ID</th>
    """
            # Add header cells for custom metadata columns.
            if metadata_columns:
                for col in metadata_columns:
                    header_html += f'            <th class="metadata">{col}</th>\n'
            # Add ranking columns including prototypicality
            for _k, short in cluster_ranking_cols:
                header_html += f'            <th class="metadata">{short}</th>\n'

            header_html += """            <th class="left-context">Left Context</th>
            <th class="node">Node</th>
            <th class="right-context">Right Context</th>
        </tr>
    """
            return header_html

        def render_concordance_lines_batch(line_ids_with_scores, token_attr):
            """Render multiple concordance lines efficiently for cluster display."""
            if not line_ids_with_scores:
                return ""
            
            # Extract line IDs and create ranking values efficiently
            line_ids = [line_id for line_id, _ in line_ids_with_scores]
            
            # Create local ranking values without full copy - only for lines we need
            local_ranking_values = {}
            for line_id, score in line_ids_with_scores:
                # Start with existing ranking values for this line
                local_ranking_values[line_id] = ranking_values.get(line_id, {}).copy()
                if score is not None:
                    rounded_score = round(score, optimal_rounding)
                    local_ranking_values[line_id]['prototypicality'] = rounded_score
            
            # Create ranking columns that includes prototypicality
            local_ranking_cols = list(ranking_cols)
            if ('prototypicality', 'Prototypicality') not in local_ranking_cols:
                local_ranking_cols.append(('prototypicality', 'Prototypicality'))
            
            # Generate HTML for all lines at once
            return _generate_lines_html(subset, line_ids, token_attr, metadata_columns, row_class="", hidden=False, 
                                     ranking_values=local_ranking_values, ranking_cols=local_ranking_cols,
                                     tokens_by_line=tokens_by_line, metadata_by_line=metadata_by_line, span_lookup=span_lookup)
        
        def render_concordance_line(line_id, token_attr, prototypicality_score=None):
            """Render a single concordance line for cluster display (legacy function for compatibility)."""
            return render_concordance_lines_batch([(line_id, prototypicality_score)], token_attr)
        
        def render_cluster_header(cluster, depth=0):
            """Render only the cluster header with illustrations (collapsed state)."""
            if max_depth is not None and depth >= max_depth:
                return ""
            
            cluster_id = f"{tree_id}_cluster_{cluster['id']}"
            has_children = cluster.get("children") and len(cluster["children"]) > 0
            has_child_clusters_flag = has_child_clusters(cluster)
            
            line_count = count_lines_in_cluster(cluster)
            cluster_label = cluster.get('label', f'Cluster {cluster["id"]}')
            
            # Get illustration lines for this cluster
            illustration_lines = get_illustration_lines(cluster)
            
            # Check if this is a small cluster (illustrations = cluster size)
            is_small_cluster = len(illustration_lines) == line_count and line_count > 0
            
            # Build cluster header
            if is_small_cluster:
                # Small cluster: no toggle, no illustrations, always expanded
                cluster_html = f"""
                <div class="cluster-header cluster-header-small">
                    <div>
                        <strong>{cluster_label}</strong> ({line_count} lines)
                    </div>
                """
                
                # Add mode toggle if cluster has child clusters
                if has_child_clusters_flag:
                    cluster_html += f"""
                    <span class="cluster-mode-toggle" id="toggle_switch_{cluster_id}" onclick="event.stopPropagation();">
                        <select id="mode_{cluster_id}" onchange="changeClusterMode_{tree_id}('{cluster_id}')">
                            <option value="tree">Tree</option>
                            <option value="flat">Flat</option>
                        </select>
                    </span>
                    """
                
                cluster_html += """
                </div>
                """
            else:
                # Regular cluster: with toggle and illustrations
                should_auto_expand = len(illustration_lines) == line_count and line_count > 0
                
                cluster_html = f"""
                <div class="cluster-header" onclick="toggleCluster_{tree_id}('{cluster_id}')">
                    <div>
                        <span class="cluster-toggle" id="toggle_{cluster_id}">{"▼" if should_auto_expand else "▶"}</span>
                        <strong>{cluster_label}</strong> ({line_count} lines)
                    </div>
                """
                
                # Add mode toggle if cluster has child clusters (only visible when expanded)
                if has_child_clusters_flag:
                    cluster_html += f"""
                    <span class="cluster-mode-toggle" id="toggle_switch_{cluster_id}" onclick="event.stopPropagation();">
                        <select id="mode_{cluster_id}" onchange="changeClusterMode_{tree_id}('{cluster_id}')">
                            <option value="tree">Tree</option>
                            <option value="flat">Flat</option>
                        </select>
                    </span>
                    """
                
                cluster_html += """
                </div>
                """
            
            # Add illustrations in collapsed state (only for regular clusters, not small ones)
            if illustration_lines and not is_small_cluster:
                cluster_html += f"""
                <div class="cluster-illustrations">
                """
                
                # Show illustration lines in a table format
                cluster_html += '<table class="cluster-concordance-table">'
                cluster_html += render_cluster_table_header()
                
                # Render illustrations in batch
                if illustration_lines:
                    illustration_data = [(line_id, cluster.get("prototypicality", {}).get(line_id, None)) 
                                       for line_id in illustration_lines]
                    cluster_html += render_concordance_lines_batch(illustration_data, token_attr)
                
                cluster_html += '</table>\n'
                cluster_html += "</div>\n"
            
            return cluster_html
        
        def render_cluster_content(cluster, depth=0):
            """Render the expanded content of a cluster (children and lines)."""
            if max_depth is not None and depth >= max_depth:
                return ""
            
            cluster_id = f"{tree_id}_cluster_{cluster['id']}"
            has_children = cluster.get("children") and len(cluster["children"]) > 0
            
            if not has_children:
                return ""
            
            # Check if this is a small cluster (illustrations = cluster size)
            illustration_lines = get_illustration_lines(cluster)
            line_count = count_lines_in_cluster(cluster)
            is_small_cluster = len(illustration_lines) == line_count and line_count > 0
            
            # Small clusters are always visible, regular clusters start hidden
            cluster_html = f'<div class="cluster-content" id="content_{cluster_id}" style="display: {"block" if is_small_cluster else "none"};">'
            
            # Tree mode content (default)
            cluster_html += f'<div id="tree_content_{cluster_id}">'
            
            # Separate child clusters from stray lines
            child_clusters = []
            stray_lines = []
            
            for child in cluster["children"]:
                if child.get("type") == "lines":
                    stray_lines.append(child)
                else:
                    child_clusters.append(child)
            
            # First render child clusters
            for child in child_clusters:
                cluster_html += render_cluster_header(child, depth + 1)
                cluster_html += render_cluster_content(child, depth + 1)
            
            # Then render stray lines last, ordered by prototypicality
            for child in stray_lines:
                line_ids = child.get("line_ids", [])
                
                # Sort lines by prototypicality (descending order - highest first)
                if line_ids:
                    prototypicality_scores = cluster.get("prototypicality", {})
                    line_ids_with_scores = []
                    for line_id in line_ids:
                        score = prototypicality_scores.get(line_id, 0.0)
                        line_ids_with_scores.append((line_id, score))
                    
                    # Sort by prototypicality score (descending)
                    line_ids_with_scores.sort(key=lambda x: x[1], reverse=True)
                    sorted_line_ids = [line_id for line_id, score in line_ids_with_scores]
                    
                    if n is not None and n > 0:
                        sorted_line_ids = sorted_line_ids[:n]
                    
                    cluster_html += f'<div class="cluster-lines">'
                    cluster_html += f'<div class="lines-label">Lines ({len(sorted_line_ids)})</div>'
                    cluster_html += '<table class="cluster-concordance-table">'
                    cluster_html += render_cluster_table_header()
                    
                    # Render lines in batch
                    if sorted_line_ids:
                        lines_data = [(line_id, cluster.get("prototypicality", {}).get(line_id, None)) 
                                    for line_id in sorted_line_ids]
                        cluster_html += render_concordance_lines_batch(lines_data, token_attr)
                    
                    cluster_html += '</table>\n</div>\n'
            
            cluster_html += '</div>'
            
            # Flat mode content (initially hidden)
            cluster_html += f'<div id="flat_content_{cluster_id}" style="display: none;">'
            
            # Get all lines in cluster ordered by prototypicality
            all_lines = get_all_lines_in_cluster(cluster)
            
            if all_lines:
                cluster_html += f'<div class="cluster-lines">'
                cluster_html += f'<div class="lines-label">All Lines ({len(all_lines)}) - Ordered by Prototypicality</div>'
                cluster_html += '<table class="cluster-concordance-table">'
                cluster_html += render_cluster_table_header()
                
                # Render all lines in batch
                cluster_html += render_concordance_lines_batch(all_lines, token_attr)
                
                cluster_html += '</table>\n</div>\n'
            
            cluster_html += '</div>\n'
            cluster_html += '</div>\n'
            
            return cluster_html
        
        def render_cluster(cluster, depth=0):
            """Render a complete cluster (header + content)."""
            if max_depth is not None and depth >= max_depth:
                return ""
            
            # Render the header (always visible, shows label and illustrations)
            cluster_html = render_cluster_header(cluster, depth)
            
            # Render the content (initially hidden, shows children)
            cluster_html += render_cluster_content(cluster, depth)
            
            return cluster_html
        
        # Add JavaScript for cluster toggling and mode switching
        cluster_js = """
        <script>
        // Ensure functions are available globally for Jupyter notebooks
        window.toggleCluster = function(clusterId) {
            const content = document.getElementById('content_' + clusterId);
            const toggle = document.getElementById('toggle_' + clusterId);
            const header = toggle ? toggle.closest('.cluster-header') : null;
            const illustrations = header ? header.nextElementSibling : null;
            const toggleSwitch = document.getElementById('toggle_switch_' + clusterId);
            
            if (!content) return;
            
            if (content.style.display === 'none' || content.style.display === '') {
                // Expanding: hide illustrations, show content, show toggle
                content.style.display = 'block';
                if (toggle) toggle.textContent = '▼';
                if (illustrations && illustrations.classList && illustrations.classList.contains('cluster-illustrations')) {
                    illustrations.style.display = 'none';
                }
                if (toggleSwitch) {
                    toggleSwitch.style.display = 'inline-block';
                }
            } else {
                // Collapsing: show illustrations, hide content, hide toggle
                content.style.display = 'none';
                if (toggle) toggle.textContent = '▶';
                if (illustrations && illustrations.classList && illustrations.classList.contains('cluster-illustrations')) {
                    illustrations.style.display = 'block';
                }
                if (toggleSwitch) {
                    toggleSwitch.style.display = 'none';
                }
            }
        };
        
        window.changeClusterMode = function(clusterId) {
            const modeSelect = document.getElementById('mode_' + clusterId);
            const treeContent = document.getElementById('tree_content_' + clusterId);
            const flatContent = document.getElementById('flat_content_' + clusterId);
            
            if (!modeSelect) return;
            
            if (modeSelect.value === 'flat') {
                // Flat mode
                if (treeContent) treeContent.style.display = 'none';
                if (flatContent) flatContent.style.display = 'block';
            } else {
                // Tree mode
                if (treeContent) treeContent.style.display = 'block';
                if (flatContent) flatContent.style.display = 'none';
            }
        };
        
        // Also define as global functions for compatibility
        function toggleCluster(clusterId) {
            return window.toggleCluster(clusterId);
        }
        
        function changeClusterMode(clusterId) {
            return window.changeClusterMode(clusterId);
        }
        </script>
        """
        
        # Render the root cluster
        html_output += render_cluster(clusters)
        html_output += cluster_js
        html_output += '</div>\n'
        
        # Add tree-specific JavaScript to avoid conflicts
        tree_specific_js = f"""
        <script>
        // Tree-specific functions for {tree_id}
        window.toggleCluster_{tree_id} = function(clusterId) {{
            const content = document.getElementById('content_' + clusterId);
            const toggle = document.getElementById('toggle_' + clusterId);
            const header = toggle ? toggle.closest('.cluster-header') : null;
            const illustrations = header ? header.nextElementSibling : null;
            const toggleSwitch = document.getElementById('toggle_switch_' + clusterId);
            
            if (!content) return;
            
            if (content.style.display === 'none' || content.style.display === '') {{
                // Expanding: hide illustrations, show content, show toggle
                content.style.display = 'block';
                if (toggle) toggle.textContent = '▼';
                if (illustrations && illustrations.classList && illustrations.classList.contains('cluster-illustrations')) {{
                    illustrations.style.display = 'none';
                }}
                if (toggleSwitch) {{
                    toggleSwitch.style.display = 'inline-block';
                }}
            }} else {{
                // Collapsing: show illustrations, hide content, hide toggle
                content.style.display = 'none';
                if (toggle) toggle.textContent = '▶';
                if (illustrations && illustrations.classList && illustrations.classList.contains('cluster-illustrations')) {{
                    illustrations.style.display = 'block';
                }}
                if (toggleSwitch) {{
                    toggleSwitch.style.display = 'none';
                }}
            }}
        }};
        
        window.changeClusterMode_{tree_id} = function(clusterId) {{
            const modeSelect = document.getElementById('mode_' + clusterId);
            const treeContent = document.getElementById('tree_content_' + clusterId);
            const flatContent = document.getElementById('flat_content_' + clusterId);
            
            if (!modeSelect) return;
            
            if (modeSelect.value === 'flat') {{
                // Flat mode
                if (treeContent) treeContent.style.display = 'none';
                if (flatContent) flatContent.style.display = 'block';
            }} else {{
                // Tree mode
                if (treeContent) treeContent.style.display = 'block';
                if (flatContent) flatContent.style.display = 'none';
            }}
        }};
        </script>
        """
        
        html_output += tree_specific_js
        
        if enable_timing:
            timing_report['cluster_section_html_generation'].append(time.time() - cluster_section_start)
        return html_output

    # Helper function to filter line_ids based on lines_to_display
    def _filter_line_ids(line_ids):
        if lines_to_display is None:
            return line_ids

        # Convert range to list if needed
        if isinstance(lines_to_display, range):
            display_list = list(lines_to_display)
        else:
            display_list = lines_to_display

        # Filter line_ids to only include those in lines_to_display
        return [line_id for line_id in line_ids if line_id in display_list]

    # Process partitions if available.
    if enable_timing:
        partition_start = time.time()
    if hasattr(node, 'grouping_result') and 'partitions' in node.grouping_result:
        partitions = node.grouping_result['partitions']
        grouping_view = node.view().get("grouping", {})
        col_order_names = [ci["name"] for ci in grouping_view.get("column_info", [])]
        for i, partition in enumerate(partitions):
            if n_groups is not None and i >= n_groups:
                break
            partition_id = partition.get('id', 0)
            partition_label = partition.get('label', f'Partition {partition_id}')
            line_ids = partition.get('line_ids', [])

            # Apply lines_to_display filter
            filtered_line_ids = _filter_line_ids(line_ids)
            line_count = len(filtered_line_ids)

            info = partition.get("info", {})
            if info:
                ordered = [(k, info[k]) for k in col_order_names if k in info]
                info_str = ", ".join(f"{k}: {v:g}" if isinstance(v, float) else f"{k}: {v}"
                                     for k, v in ordered)
                info_html = (f"<br><span style='font-size:90%;color:#555;'>"
                             f"{info_str}</span>")
            else:
                info_html = ""

            # Apply ordering if available.
            if hasattr(node, 'ordering_result') and 'sort_keys' in node.ordering_result:
                partition_sort_keys = {line_id: node.ordering_result["sort_keys"][line_id]
                                       for line_id in filtered_line_ids if line_id in node.ordering_result["sort_keys"]}
                sorted_line_ids = sorted(partition_sort_keys, key=partition_sort_keys.get)
            else:
                sorted_line_ids = filtered_line_ids

            partition_line_ids = sorted_line_ids if n is None or n < 1 else sorted_line_ids[:n]

            # Skip partition if no lines remain after filtering
            if not partition_line_ids:
                continue

            partition_class = f"partition-{i}"
            html_output += f"""
            <tr onclick="togglePartition('{partition_class}')" style="cursor: pointer; background-color: #eee;">
                <td style="text-align: center;" colspan="{4 + (len(metadata_columns) if metadata_columns else 0) + len(ranking_cols)}">
                    <b>▶ {partition_label} ({line_count} line{'s' if line_count != 1 else ''})</b>{info_html}
                </td>
            </tr>
            """
            html_output += _generate_lines_html(
                subset,
                partition_line_ids,
                token_attr,
                metadata_columns,
                row_class=f"partition-row {partition_class}",
                    hidden=True,
                    ranking_values=ranking_values,
                    ranking_cols=ranking_cols,
                    tokens_by_line=tokens_by_line,
                    metadata_by_line=metadata_by_line,
                    span_lookup=span_lookup,
                    enable_timing=enable_timing,
                    timing_report=timing_report
                )
        html_output += "</table>\n"
        if enable_timing:
            timing_report['partition_processing'].append(time.time() - partition_start)
        return html_output
    if enable_timing:
        timing_report['partition_processing'].append(time.time() - partition_start)
    
    # Process clusters if available and requested
    elif show_clusters and has_clusters:
        if enable_timing:
            cluster_start = time.time()
        clusters = v["grouping"]["cluster"]
        # Add cluster visualization as a separate section (no table to close since we didn't open one)
        html_output += _generate_cluster_section_html(concordance, node, clusters, subset, token_attr, 
                                                     metadata_columns, ranking_cols, n, cluster_max_depth,
                                                     tokens_by_line, metadata_by_line, span_lookup,
                                                     enable_timing, timing_report)
        if enable_timing:
            timing_report['cluster_processing'].append(time.time() - cluster_start)
        if enable_timing:
            timing_report['total_time'].append(time.time() - start_time)
        return html_output

    else:
        # Non-partitioned node.
        if enable_timing:
            non_partition_start = time.time()
        line_ids = metadata['line_id'].unique().tolist()

        # Apply lines_to_display filter
        filtered_line_ids = _filter_line_ids(line_ids)

        if hasattr(node, 'ordering_result') and 'sort_keys' in node.ordering_result:
            sort_keys = node.ordering_result['sort_keys']
            node_sort_keys = {line_id: sort_keys[line_id] for line_id in filtered_line_ids if line_id in sort_keys}
            sorted_line_ids = sorted(node_sort_keys, key=node_sort_keys.get)
        else:
            sorted_line_ids = filtered_line_ids

        selected_line_ids = sorted_line_ids if n is None or n < 1 else sorted_line_ids[:n]
        html_output += _generate_lines_html(subset, selected_line_ids, token_attr, metadata_columns, 
                                           ranking_values=ranking_values, ranking_cols=ranking_cols,
                                           tokens_by_line=tokens_by_line, metadata_by_line=metadata_by_line, span_lookup=span_lookup,
                                           enable_timing=enable_timing, timing_report=timing_report)

        html_output += "</table>\n"
        if enable_timing:
            timing_report['non_partition_processing'].append(time.time() - non_partition_start)
    
    if enable_timing:
        timing_report['total_time'].append(time.time() - start_time)
    return html_output


def generate_concordance_html_with_timing(concordance, node, n=None, n_groups=None, token_attr='word', extra_token_attrs=None,
                                          metadata_columns=None, lines_to_display=None, show_clusters=False, cluster_max_depth=None):
    """
    Generate concordance HTML with detailed timing instrumentation.
    
    Returns:
        tuple: (html_output, timing_report)
    """
    timing_report = defaultdict(list)
    html_output = generate_concordance_html(concordance, node, n, n_groups, token_attr, extra_token_attrs,
                                           metadata_columns, lines_to_display, show_clusters, cluster_max_depth,
                                           enable_timing=True, timing_report=timing_report)
    return html_output, timing_report


def print_timing_report(timing_report):
    """
    Print a detailed timing report.
    """
    print("=" * 80)
    print("DETAILED TIMING REPORT FOR generate_concordance_html")
    print("=" * 80)
    
    # Calculate total time
    total_times = timing_report.get('total_time', [])
    if total_times:
        total_time = total_times[0]  # Should only be one total time
        print(f"TOTAL EXECUTION TIME: {total_time:.4f} seconds")
        print()
    
    # Print individual timing sections
    sections = [
        ('subset_retrieval', 'Subset Retrieval'),
        ('ranking_columns', 'Ranking Columns Processing'),
        ('precompute_structures', 'Precompute Data Structures'),
        ('html_structure_build', 'HTML Structure Building'),
        ('lines_html_generation', 'Lines HTML Generation'),
        ('partition_processing', 'Partition Processing'),
        ('cluster_processing', 'Cluster Processing'),
        ('cluster_section_html_generation', 'Cluster Section HTML Generation'),
        ('non_partition_processing', 'Non-Partition Processing')
    ]
    
    for key, description in sections:
        times = timing_report.get(key, [])
        if times:
            total_section_time = sum(times)
            avg_time = total_section_time / len(times)
            percentage = (total_section_time / total_time * 100) if total_time > 0 else 0
            print(f"{description:35} | Total: {total_section_time:.4f}s | Avg: {avg_time:.4f}s | Calls: {len(times)} | {percentage:.1f}%")
    
    print("=" * 80)
    
    # Show breakdown by number of calls
    print("\nCALL FREQUENCY ANALYSIS:")
    print("-" * 40)
    for key, description in sections:
        times = timing_report.get(key, [])
        if times:
            print(f"{description:35} | {len(times)} calls")
    
    print("=" * 80)


def generate_analysis_tree_html(concordance, suppress_line_info=True, mark=None, list_annotations=False):
    """
    Generates an HTML representation of the analysis tree in a human-readable manner.

    Parameters:
        concordance: The Concordance object.
        suppress_line_info (bool, optional): If True, suppresses output of 'selected_lines',
            'order_result', 'sort_keys', and 'rank_keys'. Default is True.

    Returns:
        str: An HTML string representing the analysis tree.
    """
    # Display the query above the tree.
    html_output = (
        f"<div style='margin-bottom:10px;'><strong>Query:</strong> "
        f"{concordance.info.get('query', '')}</div>\n<ul style='list-style-type:none;'>\n"
    )

    def process_node(node):
        nt = node.node_type
        node_id = node.id
        depth = node.depth
        label = getattr(node, "label", None)
        label_str = f'"{label}" ' if label is not None and label != "" else ""
        has_children = bool(node.children)
        # Use 👉 for marked node, 🔎 for subset nodes and 🔀 for arrangement nodes.
        icon = "🔎" if nt == "subset" else "🔀"
        if getattr(node, "bookmarked", False):
            icon = "🏷️ " + icon
        if mark is not None and node_id == mark:
            icon = "👉 " + icon

        indent = "    " * depth

        # For subset nodes, display the line count.
        line_count = f'({node.line_count})' if nt == "subset" else ""
        html = f"{indent}<li>[{node_id}] {label_str}{icon} {nt} {line_count}: "

        # Add algorithm information if available.
        if hasattr(node, "algorithms"):
            algo_html = ""
            i = 0
            for algo_type in node.algorithms:
                algos = node.algorithms[algo_type]
                if algos is None:
                    continue
                if not isinstance(algos, list):
                    algos = [algos]
                for a in algos:
                    if i > 0:
                        algo_html += "<br/>"
                    i += 1
                    args = a['args'].copy()
                    if suppress_line_info:
                        args.pop('active_node', None)
                        args.pop('selected_lines', None)
                        args.pop('order_result', None)
                        args.pop('sort_keys', None)
                        args.pop('rank_keys', None)
                    algo_html += f"&#9881; {a['algorithm_name']} {args}"
            html += algo_html
        html += "</li>\n"

        # Process child nodes recursively.
        if has_children:
            html += f"{indent}<ul style='list-style-type:none;'>\n"
            for child in node.children:
                html += process_node(child)
            html += f"{indent}</ul>\n"

        return html

    html_output += process_node(concordance.root)
    html_output += "</ul>\n"
    if list_annotations:
        html_output += (
                "<p>🖍 <b>Annotations applied:</b>\n<ul>\n"
                + "\n  ".join(f"<li>{a['algorithm']} {a['args']}</li>"
                          for a in concordance.annotations)
                + "\n</ul></p>"
        )

    return html_output
