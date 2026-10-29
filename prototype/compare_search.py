"""Before / after: TF-IDF vs embeddings vs hybrid on two sets of judged queries.

Set A - the 8 keyword-style queries already judged in practice/practice_exercises.py.
Set B - 12 everyday paraphrases: how a cashier, butcher or owner would really ask,
        using words that mostly do NOT appear in the right document.

Metrics: Precision@3 (share of the top 3 that is relevant) and MRR (1 / rank of the
first relevant document). Writes outputs/search_comparison.txt and .png.

Usage: python prototype/compare_search.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embedding_search import ROOT, search  # noqa: E402

KEYWORD_QUERIES = {  # same judgments as practice_exercises.py, exercise 3
    "close the register at end of shift": {"D04", "D48", "D13"},
    "customer debt and credit limit": {"D03", "D16", "D25", "D30", "D44"},
    "meat cuts weight and waste": {"D14", "D34", "D40", "D06", "D28"},
    "backup of the database": {"D10", "D47"},
    "returns and refunds": {"D27", "D46"},
    "supplier delivery and purchase order": {"D31", "D32", "D36"},
    "card payment terminal": {"D08", "D20", "D22"},
    "low stock products to buy": {"D35", "D15"},
}

PARAPHRASE_QUERIES = {  # relevant documents judged by reading the corpus
    "balance the till before going home": {"D04", "D13", "D48"},
    "who still owes us money": {"D16", "D44", "D30", "D25", "D03"},
    "spoiled products thrown away": {"D37", "D27", "D14"},
    "what to do when the web connection is lost": {"D50", "D09"},
    "give money back to a client": {"D27", "D46"},
    "pay with plastic money": {"D08", "D22", "D20", "D26"},
    "keep the steak refrigerated and sanitary": {"D45"},
    "which items are running out": {"D35", "D15"},
    "copy of the information in case the computer breaks": {"D10", "D47"},
    "secret number to log in": {"D43", "D01"},
    "how much money we earned last month": {"D12", "D11"},
    "busiest time of the day in the store": {"D19"},
}

ENGINES = ["tfidf", "embeddings", "hybrid"]
LABELS = {"tfidf": "TF-IDF (antes)", "embeddings": "Embeddings", "hybrid": "Hibrido"}


def evaluate(queries, engine):
    p3, rr, rows = [], [], []
    for q, relevant in queries.items():
        top = [d["id"] for d, _ in search(q, 3, engine)]
        hits = [t in relevant for t in top]
        p3.append(sum(hits) / 3)
        rr.append(1 / (hits.index(True) + 1) if any(hits) else 0.0)
        rows.append(f"    {q:<52} top3={top}  P@3={p3[-1]:.2f}  RR={rr[-1]:.2f}")
    return float(np.mean(p3)), float(np.mean(rr)), rows


def main():
    sets = {"A. Keyword queries (8)": KEYWORD_QUERIES, "B. Everyday paraphrases (12)": PARAPHRASE_QUERIES}
    results, out = {}, ["SEARCH COMPARISON - TF-IDF vs embeddings (WordLlama) vs hybrid", ""]
    for set_name, queries in sets.items():
        out.append(set_name)
        for engine in ENGINES:
            p3, mrr, rows = evaluate(queries, engine)
            results[(set_name, engine)] = (p3, mrr)
            out.append(f"  {engine:<11} P@3={p3:.2f}  MRR={mrr:.2f}")
            out.extend(rows)
        out.append("")
    out.append("SUMMARY")
    out.append(f"  {'':<30}" + "".join(f"{e:>22}" for e in ENGINES))
    for set_name in sets:
        cells = "".join(f"{'P@3 %.2f / MRR %.2f' % results[(set_name, e)]:>22}" for e in ENGINES)
        out.append(f"  {set_name:<30}{cells}")
    text = "\n".join(out)
    print(text)
    (ROOT / "outputs" / "search_comparison.txt").write_text(text, encoding="utf-8")
    plot(results, list(sets))
    return results


def plot(results, set_names):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"tfidf": "#9AA5B4", "embeddings": "#2F5FC4", "hybrid": "#E8892B"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, metric, idx in zip(axes, ["Precision@3", "MRR"], [0, 1]):
        x = np.arange(len(set_names))
        for j, e in enumerate(ENGINES):
            vals = [results[(s, e)][idx] for s in set_names]
            bars = ax.bar(x + (j - 1) * 0.26, vals, 0.24, label=LABELS[e], color=colors[e])
            ax.bar_label(bars, fmt="%.2f", fontsize=9)
        ax.set_xticks(x, ["Palabras clave", "Parafraseo cotidiano"])
        ax.set_title(metric)
        ax.set_ylim(0, 1.1)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle("La Nube - busqueda: antes (TF-IDF) vs despues (embeddings)")
    fig.tight_layout()
    fig.savefig(ROOT / "outputs" / "search_comparison.png", dpi=150)


if __name__ == "__main__":
    main()
