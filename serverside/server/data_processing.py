import pandas as pd
import numpy as np
import os
import pickle
import logging

from embedding import embed

# Constants
DDI_PATH = "../data/ddinter/ddinter_combined.csv"
DDI_CACHE = "../data/pkl/ddinter_embeddings_final.pkl"

# Get logger
logger = logging.getLogger(__name__)

# British→US spelling map
brit2us = {
    "sulphate": "sulfate",
    "aluminium": "aluminum"
}

def normalize_name(s: str) -> str:
    s = s.lower().strip()
    for brit, us in brit2us.items():
        s = s.replace(brit, us)
    return s

def load_ddinter_data():
    """
    Load and process DDInter data, adding normalized name columns and matching embeddings by combo string.
    """
    logger.info(f"Loading DDInter data from {DDI_PATH}")
    ddinter_df = pd.read_csv(DDI_PATH)

    # Normalize names
    ddinter_df['A_norm'] = ddinter_df['Drug_A'].astype(str).apply(normalize_name)
    ddinter_df['B_norm'] = ddinter_df['Drug_B'].astype(str).apply(normalize_name)

    ddinter_df['Drug_A'] = ddinter_df['A_norm']
    ddinter_df['Drug_B'] = ddinter_df['B_norm']

    ddinter_df['combo'] = (
        ddinter_df['Drug_A'] + " and " + ddinter_df['Drug_B'] +
        " interaction (" + ddinter_df['Level'] + ")"
    )

    ddinter_df = ddinter_df[ddinter_df['Level'].str.lower() != 'unknown']

    if os.path.exists(DDI_CACHE):
        logger.info(f"Loading embeddings from cache: {DDI_CACHE}")
        with open(DDI_CACHE, 'rb') as f:
            cache = pickle.load(f)
        embs = cache['embeddings']
        combos_cached = cache['combos']

        assert len(embs) == len(combos_cached), (
            f"Mismatch: {len(embs)} embeddings vs {len(combos_cached)} combos"
        )

        # Create combo → embedding lookup
        combo_to_emb = dict(zip(combos_cached, embs))

        # Map embeddings to current DataFrame by combo
        ddinter_df['embedding'] = ddinter_df['combo'].map(combo_to_emb)

        # Drop rows that didn't match anything in the cache
        unmatched = ddinter_df['embedding'].isnull().sum()
        if unmatched > 0:
            logger.warning(f"Dropping {unmatched} unmatched rows (not found in embedding cache)")
            ddinter_df = ddinter_df[ddinter_df['embedding'].notnull()]
    else:
        raise FileNotFoundError(f"Embedding cache not found at {DDI_CACHE}")

    return ddinter_df
if __name__ == "__main__":
    exit
