from typing import Optional, Dict, List, Union
import requests
import pandas as pd
from flexiconc.resources import ResourceRegistry


def register_sketchengine_frequency_list(
    self,
    resource_name: str,
    corpname: str,
    wlattr: str = 'lc',
    wlstruct_attr: Union[str, List[str]] = 'word',
    wlnums: str = 'frq',
    wlminfreq: int = 1,
    wlmaxitems: int = 1000000000,
    wlpat: str = '.*',
    include_nonwords: int = 1,
    relfreq: int = 1,
    wlicase: int = 0,
    wltype: str = 'simple',
    info: dict = None,
    api_username: str = 'anonymous',
    api_key: str = ''
):
    """
    Fetches a frequency list from the SketchEngine Struct Wordlist API
    and registers it as a 'frequency_list' resource in the provided Concordance.

    Parameters:
    - concordance: Concordance instance with a ResourceRegistry at .resources
    - resource_name: name to register the frequency list under
    - corpname: SketchEngine corpus name (e.g. 'preloaded/bnc2_tt21')
    - wlattr: wordlist attribute for frequency (default 'lc')
    - wlnums: numeric field to fetch (default 'frq')
    - wlminfreq: minimum frequency (default 1),
    - wlmaxitems: maximum number of items to fetch (default 1e9)
    - wlpat: regex pattern to match (default '.*')
    - include_nonwords: include non-words (0 or 1)
    - relfreq: include relative frequency (0 or 1)
    - wlicase: case sensitivity (0 or 1)
    - wltype: type of wordlist (default 'simple')
    - info: optional metadata dict
    """
    # Build API URL and parameters
    url = 'https://api.sketchengine.eu/search/struct_wordlist'
    auth = (api_username, api_key)
    params = {
        'corpname': corpname,
        'wlattr': wlattr,
        'wlnums': wlnums,
        'wlminfreq': wlminfreq,
        'wlmaxitems': wlmaxitems,
        'wlpat': wlpat,
        'include_nonwords': include_nonwords,
        'relfreq': relfreq,
        'wlicase': wlicase,
        'wltype': wltype
    }
    if isinstance(wlstruct_attr, str):
        wlstruct_attr = [wlstruct_attr]

    # Add wlstruct_attr1, wlstruct_attr2, ...
    for i, val in enumerate(wlstruct_attr, start=1):
        params[f'wlstruct_attr{i}'] = val

    # Make GET request
    response = requests.get(url, params=params, auth=auth)
    response.raise_for_status()
    data = response.json()

    # Extract items
    blocks = data.get('Blocks', [])
    if not blocks:
        raise ValueError('No Blocks returned from SketchEngine API')

    sample_size = blocks[0].get('totalfrq')

    items = blocks[0].get('Items', [])
    if not items:
        raise ValueError('No Items in Blocks[0]')

    # Build DataFrame
    records = []
    for item in items:
        type_list = item.get('Word', [])
        if not type_list:
            continue
        values = [attr.get('n') for attr in type_list]
        freq = item.get(wlnums)

        record = {key: value for key, value in zip(wlstruct_attr, values)}
        record['f'] = freq
        records.append(record)

    df = pd.DataFrame.from_records(records, columns=wlstruct_attr + ['f'])

    # Register in registry
    self.resources.register_frequency_list(
        name=resource_name,
        df=df,
        sample_size=sample_size,
        info={**(info or {}), 'source': 'sketchengine', 'corpname': corpname, 'token_attrs': wlstruct_attr}
    )

    return None

def register_cwb_frequency_list(
    self,
    resource_name: str,
    corpus_name: str,
    registry_dir: str = "",
    token_attribute: str = "word",
    min_freq: int = 1,
    info: dict = None
):
    """
    Runs cwb-lexdecode to generate and register a frequency list from a CWB corpus.

    Parameters:
    - resource_name: name to register the frequency list under
    - corpus_name: CWB corpus name
    - registry_dir: path to CWB registry directory
    - p_att: positional attribute (default: 'word')
    - min_freq: minimum frequency threshold (default: 2)
    - info: optional metadata dict
    """
    from ccc.counts import cwb_lexdecode

    try:
        df, sample_size = cwb_lexdecode(
            corpus_name=corpus_name,
            registry_dir=registry_dir,
            p_att=token_attribute,
            min_freq=min_freq
        )
    except Exception:
        from flexiconc import CONFIG
        fallback_dir = CONFIG.get('Paths', 'CWB_REGISTRY_DIR')
        df, sample_size = cwb_lexdecode(
            corpus_name=corpus_name,
            registry_dir=fallback_dir,
            p_att=token_attribute,
            min_freq=min_freq
        )

    df = df.rename(columns={'freq': 'f'})
    df.reset_index(drop=True, inplace=True)
    df = df[[token_attribute, 'f']]

    self.resources.register_frequency_list(
        name=resource_name,
        df=df,
        sample_size=int(sample_size),
        info={**(info or {}), 'source': 'cwb', 'corpus': corpus_name, 'token_attrs': [token_attribute]}
    )

    return None


def register_wordfreq_frequency_list(
    self,
    name: str = "wordfreq_list",
    lang: str = "en",
    p_attr: str = "word",
    top_n: Optional[int] = None
) -> None:
    """Register a frequency list generated from *wordfreq* using
    :func:`wordfreq.get_frequency_dict`.

    Parameters
    ----------
    self : Concordance
        The concordance whose resources registry will be updated.
    name : str, default ``"wordfreq_list"``
        Identifier under which the list is stored.
    lang : str, default ``"en"``
        Language tag accepted by *wordfreq*.
    top_n : int | None, optional
        Keep only the *n* most frequent items.  If *None* (default) the
        entire dictionary returned by *wordfreq* is used.
    p_attr : str, default ``"word"``
        Column name used for the token string – must match the positional
        attribute expected by FlexiConc algorithms (e.g. ``"word"`` or
        ``"lemma"``).
    """

    import wordfreq

    if lang not in wordfreq.available_languages():
        raise ValueError(
            f"Language '{lang}' is not supported by wordfreq. "
            f"Choose from: {', '.join(sorted(wordfreq.available_languages()))}"
        )

    freq_dict = wordfreq.get_frequency_dict(lang)
    if top_n is not None:
        # get the *n* most frequent items
        items = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    else:
        items = freq_dict.items()

    words, freqs = zip(*items) if items else ([], [])
    df = pd.DataFrame({p_attr: list(words), "rel_f": list(freqs)})
    df.reset_index(drop=True, inplace=True)
    df = df[[p_attr, "rel_f"] + [c for c in df.columns if c not in {p_attr, "rel_f"}]]

    self.resources.register_frequency_list(
        name=name,
        df=df,
        sample_size=None,
        info={"lang": lang, "source": "wordfreq", "top_n": top_n, "token_attrs": [p_attr]}
    )
