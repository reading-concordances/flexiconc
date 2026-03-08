from ipywidgets import (
    Dropdown, VBox, HBox, Button, Output, Label, RadioButtons, Text,
    IntText, FloatText, Checkbox
)
import ipywidgets as widgets
from IPython.display import clear_output, display, HTML, Javascript
from IPython import get_ipython
import json
import ast
import html
from flexiconc.visualization.html_visualizer import generate_concordance_html, generate_analysis_tree_html
from typing import Optional


def show_algorithm_dropdown(
    obj,
    algo_type_filter=None,
    with_column_names=False
):
    import json
    import ast
    from ipywidgets import VBox, Dropdown, Text, IntText, FloatText, Checkbox, Label, Textarea, HBox

    if hasattr(obj, "available_algorithms"):
        available = obj.available_algorithms if isinstance(obj.available_algorithms, dict) else obj.available_algorithms()
    else:
        available = {}

    if algo_type_filter is None:
        allowed_types = None
    elif isinstance(algo_type_filter, str):
        allowed_types = {algo_type_filter}
    else:
        allowed_types = set(algo_type_filter)

    opts = [
        (meta.get("name", name), name)
        for name, meta in available.items()
        if allowed_types is None
           or meta.get("algorithm_type") in allowed_types
    ]
    if not opts:
        return VBox([Label("No algorithms available.")]), (lambda: ("", {}, [] if with_column_names else {}))

    algo_drop = Dropdown(options=opts, description="Algorithm:")
    args_box = VBox()
    widgets_dict = {}
    colname_widget = None
    if with_column_names:
        colname_widget = Text(
            value="",
            placeholder="(space-separated strings)",
            layout={"width": "auto"}
        )

    def schema_for(algo_name):
        if hasattr(obj, "schema_for"):
            return obj.schema_for(algo_name)
        elif hasattr(obj, "root") and hasattr(obj.root, "schema_for"):
            return obj.root.schema_for(algo_name)
        raise RuntimeError("No schema_for method available")

    def build_widgets(algo_name):
        schema = schema_for(algo_name)
        widgets_dict.clear()
        rows = []

        # Dynamic label width
        arg_names = list(schema.get("properties", {}).keys())
        if with_column_names:
            arg_names.append("Column name(s)")
        max_arg_len = max(len(x) for x in arg_names) if arg_names else 18
        pixels_per_char = 9
        label_width = f"{max_arg_len * pixels_per_char}px"

        for arg, spec in schema.get("properties", {}).items():
            dtype = spec.get("type")
            default = spec.get("default")
            enum = spec.get("enum")
            item_type = spec.get("items", {}).get("type") if dtype == "array" else None

            label = widgets.HTML(
                value=f'<span title="{html.escape(spec.get("description") or "")}">{html.escape(arg)}</span>',
                layout={"width": label_width}
            )

            if enum:
                w = Dropdown(
                    options=enum,
                    value=default if default in enum else enum[0],
                    layout={"width": "auto"}
                )
            elif dtype == "string":
                w = Text(value=default or "", layout={"width": "auto"})
            elif dtype in ("integer", "number"):
                if default is None:
                    placeholder = "int" if dtype == "integer" else "float"
                    w = Text(value="", placeholder=placeholder, layout={"width": "auto"})
                    w._expect_num = dtype
                else:
                    if dtype == "integer":
                        w = IntText(value=default, layout={"width": "auto"})
                    else:
                        w = FloatText(value=default, layout={"width": "auto"})
            elif dtype == "boolean":
                w = Checkbox(value=bool(default))
                w.layout = {"width": "auto", "flex": "0 0 auto", "margin-left": "6px"}
                widgets_dict[arg] = w
                rows.append(HBox([label, w], layout={"align_items": "flex-start", "justify_content": "flex-start"}))
                continue
            elif dtype == "array":
                placeholder = f"(space-separated {item_type or 'string'}s)"
                w = Text(
                    value=",".join(map(str, default)) if isinstance(default, list) else "",
                    placeholder=placeholder,
                    layout={"width": "auto"}
                )
                w._item_type = item_type or "string"
            elif isinstance(dtype, list):
                w = Text(
                    value=json.dumps(default) if default not in (None, {}) else "",
                    placeholder="JSON value (string | number | array)",
                    layout={"width": "auto"}
                )
                w._expect_json = True
            elif dtype == "object":
                try:
                    default_value = repr(default) if default is not None else ""
                except Exception:
                    default_value = ""
                w = Textarea(
                    value=default_value,
                    placeholder="Python expression, e.g. {'attr': ['val1']}",
                    layout={"width": "400px", "height": "60px"},
                )
                w._expect_pyexpr = True
            else:
                continue  # unsupported

            widgets_dict[arg] = w
            rows.append(HBox([label, w]))

        # Column names as a final row
        if with_column_names and colname_widget is not None:
            label = Label(
                value="Column name(s)",
                layout={"width": label_width}
            )
            rows.append(HBox([label, colname_widget]))

        args_box.children = rows

    build_widgets(algo_drop.value)
    algo_drop.observe(lambda c: build_widgets(c["new"]), names="value")

    def collect():
        args = {}
        for arg_name, w in widgets_dict.items():
            val = w.value
            if isinstance(w, Text) and getattr(w, "_item_type", None):
                parts = [p.strip() for p in val.split(" ") if p.strip()]
                if parts:
                    conv = int if w._item_type == "integer" else float if w._item_type == "number" else str
                    val = [conv(p) for p in parts]
                else:
                    continue
            elif getattr(w, "_expect_num", None):
                if str(val).strip() == "":
                    continue
                try:
                    val = int(val) if w._expect_num == "integer" else float(val)
                except ValueError as e:
                    raise ValueError(f"Argument '{arg_name}' expects a number: {e}") from None
            elif getattr(w, "_expect_json", False):
                if str(val).strip() == "":
                    continue
                try:
                    val = json.loads(val)
                except Exception as e:
                    raise ValueError(f"Argument '{arg_name}' expects a valid JSON literal: {e}") from None
            elif getattr(w, "_expect_pyexpr", False):
                if str(val).strip() == "":
                    continue
                try:
                    val = ast.literal_eval(val)
                except Exception as e:
                    raise ValueError(f"Argument '{arg_name}' expects a valid Python expression: {e}") from None
            elif isinstance(w, Text) and val.strip() == "":
                continue
            args[arg_name] = val
        if with_column_names and colname_widget is not None:
            colval = colname_widget.value.strip()
            colnames = [s for s in colval.split() if s] if colval else None
            return algo_drop.value, args, colnames
        else:
            return algo_drop.value, args

    container = VBox([algo_drop, args_box])
    return container, collect


class _NodeHandle:
    """Light‑weight proxy returned by *add_node_ui*.
    After the user clicks **OK** it exposes the freshly created
    :class:`AnalysisTreeNode` via attribute access **and** the textual
    *code* that reproduces the action.
    """
    def __init__(self):
        # Store these attributes directly on the proxy
        super().__setattr__('_t', None)
        super().__setattr__('code', None)

    def __getattr__(self, name):
        if self._t is None:
            raise AttributeError("Node not created yet – click OK")
        return getattr(self._t, name)

    def __setattr__(self, name, value):
        # Always store _t and code on the proxy itself
        if name in ('_t', 'code'):
            super().__setattr__(name, value)
        else:
            # If the real node is created, set attribute on it
            if self._t is not None:
                setattr(self._t, name, value)
            else:
                # Otherwise, store temporarily on the proxy
                super().__setattr__(name, value)

    def __repr__(self):
        return (
            "<Pending Node>" if self._t is None else
            f"<{self._t!r} – code={self.code!r}>"
        )

def _disable(widget):
    if hasattr(widget, "disabled"):
        widget.disabled = True
    for c in getattr(widget, "children", ()):
        _disable(c)


def add_node_ui(parent, *, execute: bool = True):
    """Interactive helper to add *subset* / *arrangement* nodes.

    Parameters
    ----------
    parent   : AnalysisTreeNode
        Parent node below which the new node will be attached (when
        *execute=True*).
    execute  : bool, default **True**
        * **True** – create the node immediately and print the generated
          snippet below the widget.
        * **False** – *dry‑run*: the analysis tree is untouched; instead the
          snippet is inserted into a new notebook cell right below the current
          one so the user can inspect / run it manually.
    """

    handle = _NodeHandle()

    # ------------- top‑level widgets ---------------------------------- #
    node_type   = RadioButtons(options=["subset", "arrangement"], description="Node:")
    config_box  = VBox()
    ok_btn      = Button(description="OK", button_style="success")
    log         = Output(layout={"border": "1px solid #dee2e6", "padding": "2px"})

    # ------------------------------------------------------------------ #
    # UI factory helpers – each returns (ui_widget, collect_fn)          #
    # ------------------------------------------------------------------ #

    def subset_ui():
        box, coll = show_algorithm_dropdown(parent, "selecting")
        return VBox([box]), coll  # coll → (algo_name, args)

    def arrangement_ui():
        # ---------- grouping selector ---------------------------------- #
        grp_container, grp_collect = VBox(), []
        
        def add_group(_=None):
            box, coll = show_algorithm_dropdown(parent, ["partitioning", "clustering"])
            def remove_group(_=None):
                grp_collect.clear()
                grp_container.children = (add_grp_btn,)
                # Clear labelling when grouping is removed
                lbl_collect.clear()
                lbl_container.children = (Label("Labelling (requires grouping)"),)
            rm = Button(description="🗑", layout={"width": "28px"})
            rm.on_click(remove_group)
            grp_collect[:] = [coll]
            grp_container.children = (
                VBox([box, rm], layout={"border": "1px solid #ccc", "padding": "4px"}),
            )
            # Update labelling UI to show add button when grouping exists
            if not lbl_collect:
                lbl_container.children = (add_lbl_btn,)

        add_grp_btn = Button(description="+", layout={"width": "28px"})
        add_grp_btn.on_click(add_group)
        grp_container.children = (add_grp_btn,)
        
        # ---------- labelling selector (similar to grouping, only one) -------------- #
        lbl_container, lbl_collect = VBox(), []
        max_depth_widget = IntText(value=0, description="Max depth:", layout={"width": "auto"})

        def add_labelling(_=None):
            if not grp_collect:
                return  # Can't add labelling without grouping
            lbl_box, lbl_coll = show_algorithm_dropdown(parent, ["labelling"])
            def remove_labelling(_=None):
                lbl_collect.clear()
                max_depth_widget.value = 0
                lbl_container.children = (add_lbl_btn,)
            rm = Button(description="🗑", layout={"width": "28px"})
            rm.on_click(remove_labelling)
            lbl_collect[:] = [lbl_coll]
            lbl_container.children = (
                VBox([
                    Label("Labelling:"),
                    lbl_box,
                    max_depth_widget,
                    rm
                ], layout={"border": "1px solid #ccc", "padding": "4px"}),
            )

        add_lbl_btn = Button(description="+", layout={"width": "28px"})
        add_lbl_btn.on_click(add_labelling)
        # Only show add button if grouping exists
        if grp_collect:
            lbl_container.children = (add_lbl_btn,)
        else:
            lbl_container.children = (Label("Labelling (requires grouping)"),)

        # ---------- ordering stack ------------------------------------ #
        ord_container, ord_blocks = HBox(), []

        def refresh_ord():
            ord_container.children = tuple(b["w"] for b in ord_blocks) + (add_ord_btn,)
            for i, b in enumerate(ord_blocks):
                b["left"].disabled  = i == 0
                b["right"].disabled = i == len(ord_blocks) - 1

        def add_order(_=None):
            box, coll = show_algorithm_dropdown(parent, ["sorting", "ranking"])
            left  = Button(description="⬅️", layout={"width": "28px"})
            right = Button(description="➡️", layout={"width": "28px"})
            rm    = Button(description="🗑", layout={"width": "28px"})

            wrapper = VBox(
                [box, HBox([left, right, rm], layout={"justify_content": "center"})],
                layout={"border": "1px solid #ccc", "padding": "4px", "margin": "0 6px"},
            )
            blk = {"w": wrapper, "c": coll, "left": left, "right": right, "rm": rm}

            left .on_click(lambda _:(ord_blocks.insert(ord_blocks.index(blk) - 1, ord_blocks.pop(ord_blocks.index(blk))), refresh_ord()))
            right.on_click(lambda _:(ord_blocks.insert(ord_blocks.index(blk) + 1, ord_blocks.pop(ord_blocks.index(blk))), refresh_ord()))
            rm   .on_click(lambda _:(ord_blocks.remove(blk), refresh_ord()))

            ord_blocks.append(blk); refresh_ord()

        add_ord_btn = Button(description="+", layout={"width": "28px"})
        add_ord_btn.on_click(add_order)
        refresh_ord()

        layout = HBox(
            [
                VBox([Label("Grouping"), grp_container]), 
                VBox([Label("Ordering"), ord_container]),
                VBox([Label("Labelling"), lbl_container])
            ],
            layout={"gap": "60px"},
        )

        def collect_specs():
            grouping  = grp_collect[0]() if grp_collect else None
            ordering  = [b["c"]() for b in ord_blocks]
            labelling = lbl_collect[0]() if lbl_collect else None
            max_depth = max_depth_widget.value if max_depth_widget.value else 0
            return grouping, ordering, labelling, max_depth

        return layout, collect_specs

    # ------------------------------------------------------------------ #
    # Track currently selected builder                                  #
    # ------------------------------------------------------------------ #

    current = {"collect": None, "kind": None, "creator": None}

    def switch(kind):
        if kind == "subset":
            ui, collect = subset_ui()
            creator = lambda spec: parent.add_subset_node(spec)  # type: ignore[arg-type]
        else:
            ui, collect = arrangement_ui()
            creator = lambda spec: parent.add_arrangement_node(
                ordering=spec[1], 
                grouping=spec[0], 
                labelling=spec[2] if len(spec) > 2 and spec[2] else None,
                max_depth=spec[3] if len(spec) > 3 else 0
            )
        current.update(collect=collect, kind=kind, creator=creator)
        config_box.children = (ui,)

    switch(node_type.value)
    node_type.observe(lambda c: switch(c["new"]), names="value")

    # ------------------------------------------------------------------ #
    # OK handler – build snippet, then execute / insert ---------------- #
    # ------------------------------------------------------------------ #

    def on_ok(_):
        with log:
            clear_output()
            try:
                spec = current["collect"]()
                if current["kind"] == "subset":
                    algo_name, args = spec
                    code_snippet = f"add_subset_node(({algo_name!r}, {args!r}))"
                else:
                    grouping, ordering, labelling, max_depth = spec
                    grouping_str = f"{None if grouping is None else (grouping[0], grouping[1])!r}"
                    ordering_str = f"{[(o[0], o[1]) for o in ordering]!r}"
                    labelling_str = f"{None if labelling is None else (labelling[0], labelling[1])!r}"
                    max_depth_str = f"{max_depth}"
                    code_snippet = (
                        "add_arrangement_node("  # noqa: E501
                        f"grouping={grouping_str}, "
                        f"ordering={ordering_str}, "
                        f"labelling={labelling_str}, "
                        f"max_depth={max_depth_str})"
                    )

                handle.code = code_snippet  # expose snippet

                if execute:
                    new_node = current["creator"](spec)
                    handle._t = new_node
                    print(code_snippet)
                else:
                    get_ipython().set_next_input(code_snippet, replace=False)
                    display(Javascript(
                        """(function() {
                              try {
                                const nb = (typeof Jupyter !== 'undefined' && Jupyter.notebook) ? Jupyter.notebook :
                                           (typeof IPython !== 'undefined' && IPython.notebook) ? IPython.notebook : null;
                                if (nb) {
                                    const idx = nb.get_selected_index();
                                    nb.select(idx + 1);
                                }
                              } catch (e) { console.warn(e); }
                            })();"""
                    ))
                    print(code_snippet)
            except Exception as e:
                # all errors go to the log box
                print("Error:", e)

    ok_btn.on_click(on_ok)

    display(VBox([node_type, config_box, ok_btn, log]))
    return handle


def add_annotation_ui(concordance):
    """
    Interactive helper to add an annotation to a Concordance object.
    Uses show_algorithm_dropdown with algo_type_filter="annotation".
    Runs the annotation after confirmation, shows result or error below.
    """
    from IPython.display import display, clear_output
    from ipywidgets import Button, Output, VBox

    ok_btn = Button(description="Annotate", button_style="success")
    log = Output(layout={"border": "1px solid #dee2e6", "padding": "2px"})
    box, collector = show_algorithm_dropdown(concordance, "annotation", with_column_names=True)

    def on_ok(_):
        with log:
            clear_output()
            try:
                algo_name, args, colnames = collector()
                # Remove empty args for cleaner code output
                clean_args = {k: v for k, v in args.items() if v not in ("", None, [], {})}
                code = f"add_annotation(({algo_name!r}, {clean_args!r})"
                if colnames:
                    code += f", column_names={colnames!r}"
                code += ")"
                concordance.add_annotation((algo_name, args), column_names=colnames)
                print(code)
            except Exception as e:
                print("Error:", e)

    ok_btn.on_click(on_ok)
    display(VBox([box, ok_btn, log]))


def show_kwic(
    node,
    n: int = 0,
    n_groups=None,
    token_attr='word',
    extra_token_attrs=None,
    metadata_columns=None,
    lines_to_display=None,
    height: int = 600
):
    """
    Display a KWIC (Key Word in Context) table for the given analysis-tree node
    inside a Jupyter notebook.

    Parameters
    ----------
    node : AnalysisTreeNode
        The node whose concordance subset / arrangement should be shown.
    n : int, optional
        Maximum number of lines per partition (or overall if un-partitioned).
    n_groups : int, optional
        Maximum number of groups to show (if partitioned).
    token_attr : str, optional
        The token attribute to display.
    extra_token_attrs : list, optional
        Token attributes to show as subscript to the right.
    metadata_columns : list, optional
        Metadata columns to display per line.
    lines_to_display : list[int], optional
        List of line IDs to display. If None, all lines are shown.
        If specified, only these lines will be displayed in the KWIC table.
    height: int, optional
        Height of the scrollable area in pixels. Default is 600. If height is 0, no scrolling is applied.
    """
    conc = node.concordance()
    html = generate_concordance_html(
        conc, node,
        n=n,
        n_groups=n_groups,
        token_attr=token_attr,
        extra_token_attrs=extra_token_attrs,
        metadata_columns=metadata_columns,
        lines_to_display=lines_to_display,
        show_clusters=True
    )
    if height > 0:
        html = f"""
        <div style="max-height: {height}px; overflow-y: auto; border: 1px solid #ccc; padding: 0.5em;">
            {html}
        </div>
        """
    from IPython.display import display, HTML
    display(HTML(html))


def show_kwic_timed(
    node,
    n: int = 0,
    n_groups=None,
    token_attr='word',
    extra_token_attrs=None,
    metadata_columns=None,
    lines_to_display=None,
    height: int = 600
):
    """
    Display a KWIC (Key Word in Context) table for the given analysis-tree node
    inside a Jupyter notebook with detailed timing information.
    
    This function provides the same functionality as show_kwic but includes
    detailed timing instrumentation to identify performance bottlenecks.

    Parameters
    ----------
    node : AnalysisTreeNode
        The node whose concordance subset / arrangement should be shown.
    n : int, optional
        Maximum number of lines per partition (or overall if un-partitioned).
    n_groups : int, optional
        Maximum number of groups to show (if partitioned).
    token_attr : str, optional
        The token attribute to display.
    extra_token_attrs : list, optional
        Token attributes to show as subscript to the right.
    metadata_columns : list, optional
        Metadata columns to display per line.
    lines_to_display : list[int], optional
        List of line IDs to display. If None, all lines are shown.
        If specified, only these lines will be displayed in the KWIC table.
    height: int, optional
        Height of the scrollable area in pixels. Default is 600. If height is 0, no scrolling is applied.
    """
    from flexiconc.visualization.html_visualizer import generate_concordance_html_with_timing, print_timing_report
    
    conc = node.concordance()
    html, timing_report = generate_concordance_html_with_timing(
        conc, node,
        n=n,
        n_groups=n_groups,
        token_attr=token_attr,
        extra_token_attrs=extra_token_attrs,
        metadata_columns=metadata_columns,
        lines_to_display=lines_to_display,
        show_clusters=True
    )
    
    # Print timing report
    print_timing_report(timing_report)
    
    if height > 0:
        html = f"""
        <div style="max-height: {height}px; overflow-y: auto; border: 1px solid #ccc; padding: 0.5em;">
            {html}
        </div>
        """
    from IPython.display import display, HTML
    display(HTML(html))


def show_analysis_tree(concordance, suppress_line_info: bool = True, mark=None, list_annotations: Optional[bool] = None):
    """
    Display an analysis-tree overview for *concordance* inside a Jupyter notebook.
    """
    html = generate_analysis_tree_html(
        concordance,
        suppress_line_info=suppress_line_info,
        mark=mark,
        list_annotations=list_annotations
    )
    display(HTML(html))