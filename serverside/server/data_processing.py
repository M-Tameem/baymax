import pandas as pd
import os
import pickle
import logging
from pathlib import Path

from embedding import embed

# Resolve paths relative to this file so the module works regardless of working directory
_BASE_DIR = Path(__file__).resolve().parent.parent
DDI_PATH = str(_BASE_DIR / "data" / "ddinter" / "ddinter_combined.csv")
DDI_CACHE = str(_BASE_DIR / "data" / "pkl" / "ddinter_embeddings_final.pkl")

logger = logging.getLogger(__name__)

# British→US spelling normalization
_brit2us = {
    "sulphate": "sulfate",
    "aluminium": "aluminum",
}


def normalize_name(s: str) -> str:
    s = s.lower().strip()
    for brit, us in _brit2us.items():
        s = s.replace(brit, us)
    return s


def load_ddinter_data():
    """Load DDInter CSV, normalize drug names, and attach pre-computed embeddings from cache."""
    logger.info(f"Loading DDInter data from {DDI_PATH}")
    ddinter_df = pd.read_csv(DDI_PATH)

    ddinter_df["A_norm"] = ddinter_df["Drug_A"].astype(str).apply(normalize_name)
    ddinter_df["B_norm"] = ddinter_df["Drug_B"].astype(str).apply(normalize_name)
    ddinter_df["Drug_A"] = ddinter_df["A_norm"]
    ddinter_df["Drug_B"] = ddinter_df["B_norm"]

    ddinter_df["combo"] = (
        ddinter_df["Drug_A"] + " and " + ddinter_df["Drug_B"]
        + " interaction (" + ddinter_df["Level"] + ")"
    )
    ddinter_df = ddinter_df[ddinter_df["Level"].str.lower() != "unknown"]

    if not os.path.exists(DDI_CACHE):
        raise FileNotFoundError(f"Embedding cache not found at {DDI_CACHE}")

    logger.info(f"Loading embeddings from cache: {DDI_CACHE}")
    with open(DDI_CACHE, "rb") as f:
        cache = pickle.load(f)

    embs = cache["embeddings"]
    combos_cached = cache["combos"]
    assert len(embs) == len(combos_cached), (
        f"Cache mismatch: {len(embs)} embeddings vs {len(combos_cached)} combos"
    )

    combo_to_emb = dict(zip(combos_cached, embs))
    ddinter_df["embedding"] = ddinter_df["combo"].map(combo_to_emb)

    unmatched = ddinter_df["embedding"].isnull().sum()
    if unmatched > 0:
        logger.warning(f"Dropping {unmatched} rows not found in embedding cache")
        ddinter_df = ddinter_df[ddinter_df["embedding"].notnull()]

    return ddinter_df
