"""System evaluation: classification, retrieval, recommendations, chatbot.
Writes outputs/metrics.json (shown in the app's Metrics tab). Run: python evaluate.py
Optional: --minilm also scores all-MiniLM-L6-v2 retrieval as an offline comparison."""
import json
import sys
import time

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

import knowledge as kb

J = json.load(open(kb.ROOT / "data" / "judgments.json", encoding="utf-8"))
OUT = kb.ROOT / "outputs" / "metrics.json"


def p_at(ranked, rel, k):
    return len(set(ranked[:k]) & rel) / k


def r_at(ranked, rel, k):
    return len(set(ranked[:k]) & rel) / len(rel)


def rr(ranked, rel):
    return next((1 / (i + 1) for i, d in enumerate(ranked) if d in rel), 0.0)


def ndcg(ranked, rel, k):
    dcg = sum(1 / np.log2(i + 2) for i, d in enumerate(ranked[:k]) if d in rel)
    return dcg / sum(1 / np.log2(i + 2) for i in range(min(k, len(rel))))


def mean(xs):
    return round(float(np.mean(xs)), 3)


def classification():
    y = [d["category"] for d in kb.DOCS]
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    models = {"naive_bayes_tfidf": make_pipeline(TfidfVectorizer(stop_words="english"), MultinomialNB())}
    models |= {f"logreg_{k}": kb.make_classifier(k) for k in ("tfidf", "embeddings", "hybrid")}
    res = {}
    for name, m in models.items():
        pred = cross_val_predict(m, kb.TEXTS, y, cv=cv)
        rep = classification_report(y, pred, output_dict=True, zero_division=0)
        res[name] = {"accuracy": round(rep["accuracy"], 3),
                     "macro_precision": round(rep["macro avg"]["precision"], 3),
                     "macro_recall": round(rep["macro avg"]["recall"], 3),
                     "macro_f1": round(rep["macro avg"]["f1-score"], 3),
                     "per_class": {c: {k: round(rep[c][k], 3) for k in ("precision", "recall", "f1-score")}
                                   for c in kb.CATEGORIES},
                     "confusion": confusion_matrix(y, pred, labels=kb.CATEGORIES).tolist(),
                     "errors": [f"{kb.DOCS[i]['id']} {kb.DOCS[i]['title']}: {y[i]} -> {pred[i]}"
                                for i in range(len(y)) if y[i] != pred[i]]}
    best = max(res, key=lambda n: res[n]["macro_f1"])
    return {"protocol": f"stratified 5-fold cross-validation, {len(kb.DOCS)} docs, 5 classes",
            "labels": kb.CATEGORIES, "models": res, "best": best, "in_app": "logreg_" + kb.CLASSIFIER_KIND}


def retrieval(score_fns):
    out = {}
    for engine, fn in score_fns.items():
        out[engine] = {}
        for s in ("keyword", "paraphrase"):
            rows = [r for r in J["retrieval"] if r["set"] == s]
            ranks = [[kb.DOCS[i]["id"] for i in np.argsort(fn(r["q"]))[::-1]] for r in rows]
            rels = [set(r["relevant"]) for r in rows]
            out[engine][s] = {"n": len(rows),
                              "P@3": mean([p_at(a, b, 3) for a, b in zip(ranks, rels)]),
                              "R@5": mean([r_at(a, b, 5) for a, b in zip(ranks, rels)]),
                              "MRR": mean([rr(a, b) for a, b in zip(ranks, rels)])}
    return out


def recommendations():
    tf = (kb.TFIDF_MATRIX @ kb.TFIDF_MATRIX.T).toarray()
    rng = np.random.default_rng(0)
    res = {"embeddings (in app)": [], "tfidf": [], "random same category": []}
    for seed, rel in J["related"].items():
        rel, i = set(rel), kb.BY_ID[seed]
        lists = {"embeddings (in app)": [d["id"] for d, _ in kb.related(seed, 5)],
                 "tfidf": [kb.DOCS[j]["id"] for j in np.argsort(tf[i])[::-1] if j != i][:5],
                 "random same category": list(rng.permutation(
                     [d["id"] for d in kb.DOCS if d["category"] == kb.DOCS[i]["category"] and d["id"] != seed]))[:5]}
        for name, lst in lists.items():
            res[name].append((p_at(lst, rel, 5), ndcg(lst, rel, 5)))
    similarity = {n: {"P@5": mean([a for a, _ in v]), "nDCG@5": mean([b for _, b in v])} for n, v in res.items()}

    # Session context: an ambiguous paraphrase query alone vs. the same query after a related earlier search
    pairs = [(0, 12), (1, 13), (2, 18), (3, 15), (4, 20), (5, 16), (7, 22)]
    alone, with_ctx = [], []
    for a, b in pairs:
        prev, q = J["retrieval"][a]["q"], J["retrieval"][b]["q"]
        rel = set(J["retrieval"][b]["relevant"])
        alone.append(p_at([d["id"] for d, _ in kb.search(q, 5, "embeddings")], rel, 5))
        with_ctx.append(p_at([d["id"] for d, _ in kb.recommend([prev, q], k=5)], rel, 5))
    return {"related_docs": similarity, "n_seeds": len(J["related"]),
            "session_context": {"n": len(pairs), "P@5 query alone": mean(alone),
                                "P@5 with query history": mean(with_ctx)}}


def chatbot():
    hit, fact, rows = [], [], []
    for item in J["chat"]:
        ans, hits, _ = kb.chat(item["q"])
        h = bool({d["id"] for d, _ in hits} & set(item["docs"]))
        f = item["fact"] in ans.lower()
        hit.append(h), fact.append(f)
        rows.append({"q": item["q"], "source_in_top3": h, "fact_in_answer": f, "answer": ans})
    oos = [kb.chat(q)[0].startswith("I couldn't find") for q in J["out_of_scope"]]
    in_top = [kb.search(i["q"], 1)[0][1] for i in J["chat"]]
    oos_top = [kb.search(q, 1)[0][1] for q in J["out_of_scope"]]
    return {"n": len(J["chat"]), "mode": "extractive (no API key during evaluation)",
            "source_hit@3": mean(hit), "fact_in_answer": mean(fact),
            "out_of_scope_refused": f"{sum(oos)}/{len(oos)}",
            "threshold": kb.NOT_FOUND, "min_in_scope_score": round(min(in_top), 3),
            "max_out_of_scope_score": round(max(oos_top), 3), "detail": rows}


def latency():
    t = time.perf_counter()
    for r in J["retrieval"]:
        kb.search(r["q"])
    s = (time.perf_counter() - t) / len(J["retrieval"])
    t = time.perf_counter()
    for c in J["chat"]:
        kb.chat(c["q"])
    c = (time.perf_counter() - t) / len(J["chat"])
    return {"search_ms": round(s * 1000, 1), "chat_extractive_ms": round(c * 1000, 1)}


if __name__ == "__main__":
    engines = {e: (lambda q, e=e: kb.scores(q, e)) for e in ("tfidf", "embeddings", "hybrid")}
    if "--minilm" in sys.argv:
        from sentence_transformers import SentenceTransformer
        st = SentenceTransformer("all-MiniLM-L6-v2")
        mv = st.encode(kb.TEXTS, normalize_embeddings=True)
        engines["minilm (offline comparison)"] = lambda q: mv @ st.encode([q], normalize_embeddings=True)[0]
    else:  # keep a previous MiniLM result if this run skipped it
        prev = json.load(open(OUT)) if OUT.exists() else {}
    m = {"corpus": {"documents": len(kb.DOCS), "categories": len(kb.CATEGORIES), "topics": len(kb.CONCEPTS),
                    "ontology_triples": len(kb.build_ontology())},
         "classification": classification(), "retrieval": retrieval(engines),
         "recommendation": recommendations(), "chatbot": chatbot(), "latency": latency()}
    if "--minilm" not in sys.argv and "minilm (offline comparison)" in prev.get("retrieval", {}):
        m["retrieval"]["minilm (offline comparison)"] = prev["retrieval"]["minilm (offline comparison)"]
    OUT.parent.mkdir(exist_ok=True)
    json.dump(m, open(OUT, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: v for k, v in m.items() if k != "chatbot"} | {"chatbot": {k: v for k, v in m["chatbot"].items() if k != "detail"}},
                     indent=1, default=str)[:6000])
