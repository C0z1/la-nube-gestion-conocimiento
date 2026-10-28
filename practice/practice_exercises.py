"""Practice exercises (Topics 1-6) that fed the project: term weighting, classifier tests, retrieval evaluation."""
import csv
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "data" / "documents.csv", encoding="utf-8") as f:
    docs = list(csv.DictReader(f))
X = [d["title"] + ". " + d["text"] for d in docs]
y = np.array([d["category"] for d in docs])
out = []

# Exercise 1 - Bag of words vs TF-IDF: which terms describe each category
out.append("EXERCISE 1 - Top terms per category: raw counts (BoW) vs TF-IDF weight")
bow, tfidf = CountVectorizer(stop_words="english"), TfidfVectorizer(stop_words="english")
B, T = bow.fit_transform(X), tfidf.fit_transform(X)
terms = bow.get_feature_names_out()
for cat in sorted(set(y)):
    rows = y == cat
    top_bow = terms[np.asarray(B[rows].sum(0)).ravel().argsort()[::-1][:6]]
    top_tfidf = tfidf.get_feature_names_out()[np.asarray(T[rows].mean(0)).ravel().argsort()[::-1][:6]]
    out.append(f"  {cat:<9} BoW:    {', '.join(top_bow)}")
    out.append(f"  {'':<9} TF-IDF: {', '.join(top_tfidf)}")
out.append("  Note: TF-IDF promotes more specific terms (label, margin, paid, closing) over generic ones (shows, recorded, purchase).\n")

# Exercise 2 - Classification tests: 5-fold cross-validation of settings
out.append("EXERCISE 2 - Classification tests (5-fold stratified CV, accuracy mean +/- std)")
cv = StratifiedKFold(5, shuffle=True, random_state=42)
for ngram in [(1, 1), (1, 2)]:
    for name, clf in [("NB alpha=0.1", MultinomialNB(alpha=0.1)), ("NB alpha=0.5", MultinomialNB(alpha=0.5)),
                      ("LogReg C=1", LogisticRegression(C=1, max_iter=1000)), ("LogReg C=10", LogisticRegression(C=10, max_iter=1000))]:
        s = cross_val_score(make_pipeline(TfidfVectorizer(stop_words="english", ngram_range=ngram, sublinear_tf=True), clf), X, y, cv=cv)
        out.append(f"  ngrams={ngram}  {name:<13} {s.mean():.2f} +/- {s.std():.2f}")
out.append("  Decision: unigrams, NB alpha=0.5 and LogReg C=10 are used in the prototype.\n")

# Exercise 3 - Information retrieval: precision@3 and MRR on queries with known relevant documents
out.append("EXERCISE 3 - Retrieval evaluation (TF-IDF + cosine similarity)")
judged = {
    "close the register at end of shift": {"D04", "D48", "D13"},
    "customer debt and credit limit": {"D03", "D16", "D25", "D30", "D44"},
    "meat cuts weight and waste": {"D14", "D34", "D40", "D06", "D28"},
    "backup of the database": {"D10", "D47"},
    "returns and refunds": {"D27", "D46"},
    "supplier delivery and purchase order": {"D31", "D32", "D36"},
    "card payment terminal": {"D08", "D20", "D22"},
    "low stock products to buy": {"D35", "D15"},
}
vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
M = vec.fit_transform(X)
p_at_3, rr = [], []
for q, rel in judged.items():
    top = [docs[i]["id"] for i in cosine_similarity(vec.transform([q]), M)[0].argsort()[::-1][:3]]
    hits = [t in rel for t in top]
    p_at_3.append(sum(hits) / 3)
    rr.append(1 / (hits.index(True) + 1) if any(hits) else 0)
    out.append(f"  {q:<38} top3={top}  P@3={p_at_3[-1]:.2f}")
out.append(f"  Mean P@3 = {np.mean(p_at_3):.2f}   MRR = {np.mean(rr):.2f}\n")
assert np.mean(rr) >= 0.5, "retrieval regressed"  # self-check

# Exercise 4 - Conceptual representation: documents per category in the corpus
out.append("EXERCISE 4 - Corpus balance used to define the ontology document types")
out.append("  " + ", ".join(f"{k}: {v}" for k, v in sorted(Counter(y).items())))

text = "\n".join(out)
print(text)
(ROOT / "outputs" / "practice_results.txt").write_text(text, encoding="utf-8")
