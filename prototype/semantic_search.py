"""Basic semantic search for La Nube: TF-IDF query vector + cosine similarity.

Usage:  python semantic_search.py "how do I close the register"   (no argument = demo queries)
"""
import csv
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "data" / "documents.csv", encoding="utf-8") as f:
    docs = list(csv.DictReader(f))

# shortcut: TF-IDF only matches shared words (no synonyms); upgrade to sentence embeddings if queries miss.
vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
doc_matrix = vectorizer.fit_transform(d["title"] + ". " + d["text"] for d in docs)


def search(query, k=3):
    """i. receive a natural-language query, ii. vectorize it, iii. cosine similarity, iv. top-k."""
    scores = cosine_similarity(vectorizer.transform([query]), doc_matrix)[0]
    ranked = scores.argsort()[::-1][:k]
    return [(docs[i], scores[i]) for i in ranked if scores[i] > 0]


def show(query, k=3):
    lines = [f'Query: "{query}"']
    results = search(query, k)
    for rank, (d, s) in enumerate(results, 1):
        lines.append(f"  {rank}. [{s:.3f}] {d['id']} {d['title']} ({d['category']})")
    if not results:
        lines.append("  No relevant documents found.")
    return "\n".join(lines)


if __name__ == "__main__":
    queries = sys.argv[1:] or [
        "how do I close the register at the end of my shift",
        "which customers owe money on credit",
        "meat waste and yield of beef",
        "what happens if the internet goes down",
        "charge with debit card terminal",
        "rules for keeping meat cold and clean",
    ]
    out = "\n\n".join(show(q) for q in queries)
    print(out)
    if not sys.argv[1:]:
        (ROOT / "outputs" / "search_results.txt").write_text(out, encoding="utf-8")
        # self-check: the end-of-shift query must find the cash-cut manual first
        assert search(queries[0])[0][0]["id"] == "D04", search(queries[0])[0][0]["id"]
