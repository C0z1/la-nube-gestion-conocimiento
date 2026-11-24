"""Core of the La Nube knowledge system: corpus, search, classifier, recommender,
chatbot and knowledge graph. The Streamlit app (app.py) and evaluate.py import it.

Embeddings: model2vec potion-multilingual-128M (static, Spanish-capable, float16 ~250 MB, CPU only,
no torch) so it runs on the store's local server and
on Streamlit Community Cloud's free tier without torch.
"""
import csv
import json
import re
import urllib.request
from pathlib import Path

import networkx as nx
import numpy as np
from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from model2vec import StaticModel

ROOT = Path(__file__).resolve().parent
LN = Namespace("http://www.example.org/la-nube#")

with open(ROOT / "data" / "documents.csv", encoding="utf-8") as f:
    DOCS = list(csv.DictReader(f))
for d in DOCS:
    d["concepts"] = d["concepts"].split(";")
BY_ID = {d["id"]: i for i, d in enumerate(DOCS)}
TEXTS = [d["title"] + ". " + d["text"] for d in DOCS]
CATEGORIES = sorted({d["category"] for d in DOCS})
CONCEPTS = sorted({c for d in DOCS for c in d["concepts"]})

# ---------- vectors ----------
_model = StaticModel.from_pretrained("minishlab/potion-multilingual-128M", quantize_to="float16")


def embed(texts):
    v = _model.encode(list(texts)).astype(np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


# sklearn only ships English stop words; this short Spanish list covers the corpus' function words
STOP_ES = ("a al algo ante antes como con cual cuando de del desde donde el ella en entre es esa ese eso esta este esto "
           "fue ha hay la las le les lo los mas me mi muy no nos o para pero por que se si sin sobre su sus te tu un una "
           "uno unos y ya yo quien cuanto cuanta cuantos cuantas hago puedo tengo hola ayer hoy").split()  # accent-free: matched after strip_accents
TFIDF_ARGS = dict(stop_words=STOP_ES, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True)
TFIDF = TfidfVectorizer(**TFIDF_ARGS)
TFIDF_MATRIX = TFIDF.fit_transform(TEXTS)
DOC_VECS = embed(TEXTS)


# ---------- search ----------
def scores(query, engine="hybrid", alpha=0.5):
    tf = (TFIDF_MATRIX @ TFIDF.transform([query]).T).toarray().ravel()  # tf-idf rows are L2-normalised
    if engine == "tfidf":
        return tf
    em = DOC_VECS @ embed([query])[0]
    return em if engine == "embeddings" else alpha * tf + (1 - alpha) * em


def search(query, k=5, engine="hybrid", category=None):
    s = scores(query, engine)
    order = [i for i in s.argsort()[::-1] if category in (None, DOCS[i]["category"])]
    return [(DOCS[i], float(s[i])) for i in order[:k]]


# ---------- recommendations ----------
def related(doc_id, k=5):
    """Documents most similar in meaning to doc_id (cosine over embeddings)."""
    i = BY_ID[doc_id]
    s = DOC_VECS @ DOC_VECS[i]
    s[i] = -1
    return [(DOCS[j], float(s[j])) for j in s.argsort()[::-1][:k]]


def recommend(queries=(), viewed=(), k=5, decay=0.5):
    """Personalised suggestions from the session context: a profile vector built
    from recent queries and opened documents, newest weighted most (decay per step)."""
    items = [embed([q])[0] for q in queries[-5:]] + [DOC_VECS[BY_ID[d]] for d in viewed[-5:]]
    if not items:
        return []
    # queries and views are interleaved in time only approximately; recency within each list is kept
    w = np.array([decay ** a for a in range(len(queries[-5:]))][::-1]
                 + [decay ** a for a in range(len(viewed[-5:]))][::-1])
    profile = (w[:, None] * np.array(items)).sum(0)
    s = DOC_VECS @ (profile / np.linalg.norm(profile))
    seen = {BY_ID[d] for d in viewed}
    return [(DOCS[j], float(s[j])) for j in s.argsort()[::-1] if j not in seen][:k]


# ---------- classification ----------
def make_classifier(kind="hybrid"):
    """tfidf: TF-IDF + LogReg (Phase I). embeddings: model2vec + LogReg.
    hybrid: both feature sets side by side."""
    tfidf = TfidfVectorizer(**TFIDF_ARGS)
    emb = FunctionTransformer(embed)
    if kind == "tfidf":
        feats = tfidf
    elif kind == "embeddings":
        feats = emb
    else:
        from sklearn.pipeline import FeatureUnion
        feats = FeatureUnion([("tfidf", tfidf), ("emb", emb)])
    return make_pipeline(feats, LogisticRegression(max_iter=2000, C=10))


CLASSIFIER_KIND = "hybrid"  # best macro-F1 in evaluate.py (see outputs/metrics.json)
_clf = make_classifier(CLASSIFIER_KIND).fit(TEXTS, [d["category"] for d in DOCS])


def classify(text):
    proba = _clf.predict_proba([text])[0]
    return sorted(zip(_clf.classes_, proba.tolist()), key=lambda x: -x[1])


# ---------- chatbot ----------
NOT_FOUND = 0.19  # below this hybrid score the top document is unrelated (gap measured in evaluate.py)
NOT_FOUND_MSG = "No encontré eso en los documentos de la tienda."


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) > 3]


def retrieve_answer(question, k=3):
    """Extractive answer: the sentences of the top documents closest to the question."""
    hits = search(question, k)
    if not hits or hits[0][1] < NOT_FOUND:
        return NOT_FOUND_MSG, hits
    cands = [(s, d) for d, _ in hits for s in _sentences(d["text"])]
    sents = [s for s, _ in cands]  # same hybrid score as search: exact words + meaning
    sv = 0.5 * (TFIDF.transform(sents) @ TFIDF.transform([question]).T).toarray().ravel() \
        + 0.5 * embed(sents) @ embed([question])[0]
    top = sorted(np.argsort(sv)[::-1][:3], key=lambda i: i)  # keep document order
    return " ".join(f"{cands[i][0]} [{cands[i][1]['id']}]" for i in top), hits


def llm_answer(question, hits, api_key, model="deepseek-chat"):
    context = "\n".join(f"[{d['id']}] {d['title']}: {d['text']}" for d, _ in hits)
    body = {"model": model, "temperature": 0.2, "max_tokens": 300, "messages": [
        {"role": "system", "content": "Eres el asistente de conocimiento de La Nube, un mini-súper. "
         "Responde en español SOLO con los documentos dados, en 2-4 oraciones, y cita los ids como [D04]. "
         "Si los documentos no contienen la respuesta, dilo."},
        {"role": "user", "content": f"Documentos:\n{context}\n\nPregunta: {question}"}]}
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def chat(question, api_key=None):
    """Returns (answer, source hits, mode). Uses the LLM only if a key is configured
    and falls back to the extractive answer on any API error."""
    answer, hits = retrieve_answer(question)
    if api_key and hits and hits[0][1] >= NOT_FOUND:
        try:
            return llm_answer(question, hits, api_key), hits, "llm"
        except Exception:
            pass
    return answer, hits, "extractive"


# ---------- ontology / knowledge graph ----------
CATEGORY_CLASS = {"Manual": "Manual", "Reporte": "Report", "Ventas": "SalesDocument",
                  "Inventario": "InventoryRecord", "Política": "Policy"}
# Phase II topics anchored to the Phase I ontology classes they involve
TOPIC_INVOLVES = {
    "Audit": ["Manager"], "Backup": ["Manager"], "Butchery": ["MeatCut", "Butcher"],
    "CardPayment": ["Payment"], "CashClosing": ["CashCut", "Cashier"], "CashRegister": ["CashRegister"],
    "CustomerCredit": ["Customer", "Payment"], "Hardware": ["CashRegister"], "Hygiene": ["Butcher"],
    "Invoicing": ["Customer", "Sale"], "Offline": ["CashRegister"], "Pricing": ["Product"],
    "ProductCatalog": ["Product"], "Promotion": ["Product", "Sale"], "Purchasing": ["Supplier"],
    "Refund": ["Sale", "Manager"], "Sale": ["Sale"], "Scale": ["MeatCut"], "Security": ["Employee"],
    "ShiftOpening": ["CashRegister", "Cashier"], "Shrinkage": ["InventoryMovement"],
    "Staffing": ["Employee"], "Stock": ["InventoryMovement", "Product"],
}


def build_ontology():
    """Phase I ontology + Phase II expansion: every document typed by its category class
    and linked (ln:about) to topics, which link (ln:involves) back to Phase I classes."""
    g = Graph().parse(ROOT / "ontology" / "phase1.ttl")
    g.bind("ln", LN)
    g.add((LN.Topic, RDF.type, OWL.Class))
    for p, dom, rng in [("about", "Document", "Topic"), ("involves", "Topic", None)]:
        g.add((LN[p], RDF.type, OWL.ObjectProperty))
        g.add((LN[p], RDFS.domain, LN[dom]))
        if rng:
            g.add((LN[p], RDFS.range, LN[rng]))
    for t, classes in TOPIC_INVOLVES.items():
        g.add((LN["topic_" + t], RDF.type, LN.Topic))
        g.add((LN["topic_" + t], RDFS.label, Literal(t)))
        for c in classes:
            g.add((LN["topic_" + t], LN.involves, LN[c]))
    for d in DOCS:
        node = LN[d["id"]]
        g.add((node, RDF.type, LN[CATEGORY_CLASS[d["category"]]]))
        g.add((node, RDFS.label, Literal(d["title"])))
        for c in d["concepts"]:
            g.add((node, LN.about, LN["topic_" + c]))
    return g


COLORS = {"Manual": "#2563eb", "Reporte": "#d97706", "Ventas": "#16a34a", "Inventario": "#7c3aed",
          "Política": "#dc2626", "topic": "#0891b2", "class": "#64748b"}


def knowledge_graph(categories=None, topics=None, focus=None, sim_threshold=0.85, show_classes=True):
    """networkx graph for the explorer: documents, topics, categories and Phase I classes,
    plus 'similar' edges between documents above sim_threshold (embedding cosine).
    focus: a doc id -> only that document's neighbourhood (2 hops)."""
    G = nx.Graph()
    keep = [d for d in DOCS if (not categories or d["category"] in categories)
            and (not topics or set(topics) & set(d["concepts"]))]
    for d in keep:
        G.add_node(d["id"], label=d["id"], title=f"{d['title']} ({d['category']})",
                   color=COLORS[d["category"]], shape="dot", size=12, kind="doc")
        G.add_node(d["category"], label=d["category"], color=COLORS[d["category"]], shape="box", kind="category")
        G.add_edge(d["id"], d["category"], title="is a")
        for c in d["concepts"]:
            G.add_node(c, label=c, color=COLORS["topic"], shape="diamond", size=16, kind="topic")
            G.add_edge(d["id"], c, title="about")
    if show_classes:
        for t in [n for n, a in G.nodes(data=True) if a["kind"] == "topic"]:
            for c in TOPIC_INVOLVES[t]:
                G.add_node("class:" + c, label=c, color=COLORS["class"], shape="ellipse", kind="class")
                G.add_edge(t, "class:" + c, title="involves")
    ids = [BY_ID[d["id"]] for d in keep]
    sim = DOC_VECS[ids] @ DOC_VECS[ids].T
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            if sim[a, b] >= sim_threshold:
                G.add_edge(DOCS[ids[a]]["id"], DOCS[ids[b]]["id"], title=f"similar {sim[a, b]:.2f}",
                           dashes=True, color="#94a3b8")
    if focus and focus in G:
        G = G.subgraph(nx.ego_graph(G, focus, radius=2).nodes).copy()
    return G


def graph_html(G, height="650px"):
    from pyvis.network import Network
    net = Network(height=height, width="100%", bgcolor="#FCFCFA", cdn_resources="in_line")
    net.from_nx(G)
    net.set_options(json.dumps({"physics": {"solver": "forceAtlas2Based",
        "forceAtlas2Based": {"gravitationalConstant": -40, "springLength": 70},
        "stabilization": {"iterations": 300, "fit": True}},
        "nodes": {"font": {"size": 18}},
        "interaction": {"hover": True, "navigationButtons": True}}))
    # the iframe is drawn while its Streamlit tab is hidden (size 0): re-fit when it gets a real size
    fit = "<script>new ResizeObserver(() => network.fit()).observe(document.body);"           "network.once('stabilizationIterationsDone', () => network.fit());</script></body>"
    return net.generate_html().replace("</body>", fit)


if __name__ == "__main__":  # self-check
    assert len(DOCS) >= 100 and set(CONCEPTS) == set(TOPIC_INVOLVES)
    assert search("cerrar la caja al final de mi turno", 3)[0][0]["id"] in {"D04", "D99", "D13"}
    assert classify("Pedido al proveedor de res: 3 cuartos de canal")[0][0] == "Inventario"
    assert related("D04", 3)[0][0]["id"] != "D04"
    assert recommend(["quién nos debe dinero"], ["D16"])[0][0]["id"] != "D16"
    a, hits, mode = chat("¿qué hago si se cae el internet?")
    assert mode == "extractive" and "[D" in a, a
    assert chat("receta de pastel de chocolate")[0] == NOT_FOUND_MSG
    g = build_ontology()
    assert (LN.D04, LN.about, LN.topic_CashClosing) in g
    G = knowledge_graph(focus="D04")
    assert "D04" in G and "CashClosing" in G
    print("ok", len(g), "triples;", a)
