"""Semantic search with embeddings for La Nube (improvement 1 of the roadmap).

TF-IDF only finds documents that share words with the query, so "balance the till"
never reaches the "end of shift cut" manual. Embeddings map words with similar
meaning to nearby vectors, so the search works on meaning instead of exact words.

Engine: WordLlama (pip install wordllama). It is a ~16 MB static embedding model
distilled from an LLM: it runs on CPU, needs no GPU and no internet once installed,
so it fits the store's local server, which keeps selling when the internet is down.

Usage:
    python prototype/embedding_search.py "who still owes us money"
    python prototype/embedding_search.py --engine hybrid "balance the till"
Engines: tfidf | embeddings (default) | hybrid (average of both scores)
"""
import argparse
import csv
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from wordllama import WordLlama

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "data" / "documents.csv", encoding="utf-8") as f:
    DOCS = list(csv.DictReader(f))
TEXTS = [d["title"] + ". " + d["text"] for d in DOCS]

# Baseline: the same TF-IDF configuration as prototype/semantic_search.py
_tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
_tfidf_matrix = _tfidf.fit_transform(TEXTS)

# Embeddings: every document is encoded once; queries are encoded on demand
_model = WordLlama.load()
_doc_vectors = _model.embed(TEXTS, norm=True)


def scores_tfidf(query):
    return cosine_similarity(_tfidf.transform([query]), _tfidf_matrix)[0]


def scores_embeddings(query):
    q = _model.embed([query], norm=True)[0]
    return _doc_vectors @ q  # cosine similarity (vectors are normalized)


def scores_hybrid(query, alpha=0.5):
    """Average of both engines: exact words (TF-IDF) + meaning (embeddings)."""
    return alpha * scores_tfidf(query) + (1 - alpha) * scores_embeddings(query)


ENGINES = {"tfidf": scores_tfidf, "embeddings": scores_embeddings, "hybrid": scores_hybrid}


def search(query, k=3, engine="embeddings"):
    scores = np.asarray(ENGINES[engine](query), dtype=float)
    ranked = scores.argsort()[::-1][:k]
    return [(DOCS[i], float(scores[i])) for i in ranked]


def show(query, k=3, engine="embeddings"):
    lines = [f'Query ({engine}): "{query}"']
    for rank, (d, s) in enumerate(search(query, k, engine), 1):
        lines.append(f"  {rank}. [{s:.3f}] {d['id']} {d['title']} ({d['category']})")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="*", help="natural-language question")
    parser.add_argument("--engine", choices=ENGINES, default="embeddings")
    parser.add_argument("-k", type=int, default=3)
    args = parser.parse_args()
    queries = [" ".join(args.query)] if args.query else [
        "balance the till before going home",
        "who still owes us money",
        "what to do when the web connection is lost",
    ]
    print("\n\n".join(show(q, args.k, args.engine) for q in queries))
