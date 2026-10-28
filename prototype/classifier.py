"""Automated document classifier for La Nube: TF-IDF + Naive Bayes / Logistic Regression."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42

# i. Load the sample documents
with open(ROOT / "data" / "documents.csv", encoding="utf-8") as f:
    docs = list(csv.DictReader(f))
texts = [d["title"] + ". " + d["text"] for d in docs]
labels = [d["category"] for d in docs]
print(f"Loaded {len(docs)} documents, categories: {sorted(set(labels))}")

X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.3, stratify=labels, random_state=SEED)

# ii + iii. TF-IDF vectorization and two simple models (settings picked by 5-fold CV, see practice/)
models = {
    "Naive Bayes": make_pipeline(TfidfVectorizer(stop_words="english", sublinear_tf=True), MultinomialNB(alpha=0.5)),
    "Logistic Regression": make_pipeline(TfidfVectorizer(stop_words="english", sublinear_tf=True), LogisticRegression(C=10, max_iter=1000)),
}
lines = []
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    lines += [f"=== {name} (train={len(X_train)}, test={len(X_test)}) ===", f"Accuracy: {acc:.2f}",
              classification_report(y_test, pred, zero_division=0)]
    ConfusionMatrixDisplay.from_predictions(y_test, pred, cmap="Blues", colorbar=False)
    plt.title(f"Confusion matrix - {name}")
    plt.tight_layout()
    plt.savefig(OUT / f"confusion_{name.lower().replace(' ', '_')}.png", dpi=130)
    plt.close()
    assert acc >= 0.6, f"{name} accuracy too low: {acc}"  # self-check

# iv. Classify new, unseen documents into the predefined categories
best = models["Logistic Regression"]
new_docs = [
    "Guide for the new cashier: press F12 to charge and choose the payment method on the screen.",
    "Weekly summary of revenue and margin per department compared with last month.",
    "Ticket 001020 paid in cash: two kilos of chicken and one bottle of oil, change returned.",
    "Received 40 kg of pork from the supplier, checked against the purchase order and added to stock.",
    "Employees must never share their PIN and accounts are locked after failed attempts.",
]
lines.append("=== Classification of new documents (Logistic Regression) ===")
for text, cat, proba in zip(new_docs, best.predict(new_docs), best.predict_proba(new_docs)):
    lines.append(f"[{cat:<9} {proba.max():.2f}] {text}")
expected = ["Manual", "Report", "Sales", "Inventory", "Policy"]
hits = sum(c == e for c, e in zip(best.predict(new_docs), expected))
lines.append(f"Correct on new documents: {hits}/{len(new_docs)}")

report = "\n".join(lines)
print(report)
(OUT / "classification_results.txt").write_text(report, encoding="utf-8")
