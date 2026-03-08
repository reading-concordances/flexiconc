import requests
import sqlite3
import pandas as pd
import numpy as np
from flexiconc import TextImport
from tqdm import tqdm

def download_db(
    corpus_name,
    username,
    password,
    db_filename="file.db",
    verbose=True
):
    url = f"https://ucrel-wmatrix7.lancaster.ac.uk/cgi-bin/wmatrix7/show_file.pl?{corpus_name}/file.db"
    with requests.get(url, auth=(username, password), stream=True) as response:
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192
            pbar = None
            if verbose:
                pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc=db_filename, ncols=80)
            with open(db_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        if verbose and pbar is not None:
                            pbar.update(len(chunk))
            if verbose and pbar is not None:
                pbar.close()
                print("✅ Download complete!")
            return db_filename
        else:
            if verbose:
                print("Failed to download:", response.status_code)
            return None

def prune_db(db_filename, keep_table="corpus"):
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()

    # Remove all views
    cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
    for (view,) in cur.fetchall():
        cur.execute(f'DROP VIEW IF EXISTS "{view}"')

    # Remove all tables except keep_table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (table,) in cur.fetchall():
        if table != keep_table:
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')

    conn.commit()
    cur.execute("VACUUM")
    conn.commit()
    conn.close()
    return db_filename

def process_pruned_db(db_filename):
    conn = sqlite3.connect(db_filename)
    tokens = pd.read_sql_query("SELECT * FROM corpus", conn)

    # Rename columns (do this early)
    if 'word' in tokens.columns:
        tokens = tokens.rename(columns={'word': 'word_lowercase'})
    if 'orig' in tokens.columns:
        tokens = tokens.rename(columns={'orig': 'word'})

    # Mark sentence tags efficiently
    sentence_mask = tokens['word'].isin(['<s>', '</s>']).values
    token_mask = ~sentence_mask

    # Build map from old idx to new cpos (using numpy where for speed)
    kept_indices = np.flatnonzero(token_mask)
    orig_idx_to_cpos = np.zeros(len(tokens), dtype=int) - 1
    orig_idx_to_cpos[kept_indices] = np.arange(len(kept_indices))
    tokens_clean = tokens.iloc[kept_indices].reset_index(drop=True)
    tokens_clean['cpos'] = np.arange(len(tokens_clean))

    # --- SENTENCE SPANS ---
    # Find all <s> and </s> positions as numpy arrays
    sent_starts = np.flatnonzero(tokens['word_lowercase'] == '<s>')
    sent_ends = np.flatnonzero(tokens['word_lowercase'] == '</s>')

    # Make sure they're matched
    n_sent = min(len(sent_starts), len(sent_ends))
    sent_starts, sent_ends = sent_starts[:n_sent], sent_ends[:n_sent]

    spans_s = []
    for i in range(n_sent):
        real_start = sent_starts[i] + 1
        real_end = sent_ends[i]
        # Must have at least one real token
        real_token_indices = [idx for idx in range(real_start, real_end) if orig_idx_to_cpos[idx] != -1]
        if real_token_indices:
            new_start = orig_idx_to_cpos[real_token_indices[0]]
            new_end = orig_idx_to_cpos[real_token_indices[-1]]  # inclusive
            if new_start <= new_end:
                spans_s.append({'id': len(spans_s), 'start': int(new_start), 'end': int(new_end)})

    # --- FILE SPANS ---
    spans_file = []
    if 'file' in tokens_clean.columns:
        file_array = tokens_clean['file'].to_numpy()
        if len(file_array) > 0:
            change_points = np.flatnonzero(np.r_[True, file_array[1:] != file_array[:-1]])
            file_values = file_array[change_points]
            ends = np.r_[change_points[1:], len(file_array)] - 1  # make end inclusive
            for i, (start, end, file_val) in enumerate(zip(change_points, ends, file_values)):
                if start <= end:
                    spans_file.append({'id': i, 'start': int(start), 'end': int(end), 'file': file_val})

    # Ensure column order: cpos, word, ...
    cols = list(tokens_clean.columns)
    reordered_cols = ['cpos']
    if 'word' in cols:
        reordered_cols.append('word')
    reordered_cols += [col for col in cols if col not in ('cpos', 'word')]
    tokens_clean = tokens_clean[reordered_cols]

    # Write tokens and spans to db
    tokens_clean.to_sql('tokens', conn, index=False, if_exists='replace')
    if spans_s:
        pd.DataFrame(spans_s).to_sql('spans_s', conn, index=False, if_exists='replace')
    if spans_file:
        pd.DataFrame(spans_file).to_sql('spans_file', conn, index=False, if_exists='replace')

    # Remove the old corpus table if it exists
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='corpus'")
    if cur.fetchone():
        cur.execute("DROP TABLE corpus")

    # Vacuum the database to reduce file size
    cur.execute("VACUUM")
    conn.commit()
    conn.close()

def load(
    corpus_name=None,
    username=None,
    password=None,
    db_filename="file.db"
):
    # If only db_filename is provided, just load the local file
    if corpus_name is None and username is None and password is None and db_filename:
        return TextImport(db_filename)

    # Otherwise, require all three to be specified
    if not (corpus_name and username and password):
        raise ValueError(
            "Either specify corpus_name, username, and password, or just db_filename for a local file."
        )

    db_path = download_db(
        corpus_name=corpus_name,
        username=username,
        password=password,
        db_filename=db_filename
    )
    if not db_path:
        raise RuntimeError("Download failed")
    prune_db(db_path)
    process_pruned_db(db_path)
    return TextImport(db_path)

