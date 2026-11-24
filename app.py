"""La Nube knowledge assistant — Streamlit app. Run: streamlit run app.py"""
import base64
import html
import json
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="La Nube · Knowledge Assistant", page_icon="☁️", layout="wide")


@st.cache_resource(show_spinner="Loading documents and models…")
def load():
    import knowledge
    return knowledge


kb = load()
ss = st.session_state
ss.setdefault("queries", [])   # search context for recommendations, newest last
ss.setdefault("viewed", [])    # opened documents, newest last
ss.setdefault("messages", [])  # chat history


M = json.load(open(kb.ROOT / "outputs" / "metrics.json", encoding="utf-8"))
st.html(f"<style>{(kb.ROOT / 'style.css').read_text(encoding='utf-8')}</style>")

# retrieval-path graphic: query -> documents -> topics -> answer (--d = stage of the pulse)
NODES = {"q": (30, 75), "d1": (135, 28), "d2": (135, 75), "d3": (135, 122), "t1": (240, 50), "t2": (240, 100), "a": (330, 75)}
EDGES = [("q", "d1", 0), ("q", "d2", 0), ("q", "d3", 0), ("d1", "t1", 1), ("d2", "t1", 1), ("d2", "t2", 1),
         ("d3", "t2", 1), ("t1", "a", 2), ("t2", "a", 2)]


def hero():
    lines = "".join(f'<line class="e" x1="{NODES[a][0]}" y1="{NODES[a][1]}" x2="{NODES[b][0]}" y2="{NODES[b][1]}"/>'
                    f'<line class="f" style="--d:{d}" x1="{NODES[a][0]}" y1="{NODES[a][1]}" x2="{NODES[b][0]}" y2="{NODES[b][1]}"/>'
                    for a, b, d in EDGES)
    dots = "".join(f'<circle class="{"hot" if n in ("q", "a") else "n"}" style="--d:{0 if n == "q" else 2}" '
                   f'cx="{x}" cy="{y}" r="{8 if n in ("q", "a") else 5}"/>' for n, (x, y) in NODES.items())
    # the pulse travels query -> documents -> topics -> answer 3 times, then rests; off with reduced motion
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 150"><style>
.e{{stroke:#8FB4F0;stroke-opacity:.28;stroke-width:1.5}}
.f{{stroke:#E8A472;stroke-width:2.5;stroke-linecap:round;stroke-dasharray:16 220;stroke-dashoffset:16;
animation:flow 2.4s ease-in-out 3 both;animation-delay:calc(var(--d)*.6s)}}
.n{{fill:#8FB4F0}} .hot{{fill:#E8A472;animation:glow 2.4s ease-in-out 3 both;animation-delay:calc(var(--d)*.6s)}}
@keyframes flow{{0%{{stroke-dashoffset:16}}35%,100%{{stroke-dashoffset:-140}}}}
@keyframes glow{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
@media (prefers-reduced-motion:reduce){{.f,.hot{{animation:none}}}}
</style><!-- run {len(ss.queries)} -->{lines}{dots}</svg>"""
    src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    c, r = M["classification"], M["retrieval"]["hybrid"]["paraphrase"]
    kpis = [(M["corpus"]["documents"], "documents"), (f"{c['models'][c['in_app']]['macro_f1']:.2f}", "classifier macro-F1"),
            (f"{r['MRR']:.2f}", "MRR, everyday questions")]
    # the run counter changes the image after every query, so the pulse replays on each retrieval
    st.html(f"""<div class="hero" data-run="{len(ss.queries)}">
      <div><p class="eyebrow">Knowledge management system · La Nube</p>
        <h1>Knowledge Assistant</h1>
        <p class="lede">Semantic search, recommendations, a cited-answer chatbot and a knowledge graph over the store's manuals, reports and policies.</p>
        <div class="kpis">{"".join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for v, k in kpis)}</div>
        <p class="engine">engine <i>hybrid TF-IDF + WordLlama 16 MB</i> · classifier <i>LogReg</i> · graph <i>rdflib → NetworkX → PyVis</i> ({M["corpus"]["ontology_triples"]} triples) · CPU only</p>
      </div>
      <img class="net" src="{src}" alt="">
    </div>""")


def remember_query(q):
    if q and (not ss.queries or ss.queries[-1] != q):
        ss.queries.append(q)


@st.dialog("Document", width="large")
def open_doc(doc_id):
    d = kb.DOCS[kb.BY_ID[doc_id]]
    if not ss.viewed or ss.viewed[-1] != doc_id:
        ss.viewed.append(doc_id)
    st.subheader(f"{d['id']} · {d['title']}")
    st.caption(f"Category: **{d['category']}** · Topics: {', '.join(d['concepts'])}")
    st.write(d["text"])
    st.markdown("**Related documents**")
    for r, s in kb.related(doc_id, 5):
        st.markdown(f"- `{r['id']}` {r['title']} · *{r['category']}* · similarity {s:.2f}")


def doc_row(d, score, key):
    c1, c2 = st.columns([6, 1], vertical_alignment="center")
    c1.html(f"""<div class="doc"><div class="meta"><span class="id">{d['id']}</span><span class="cat">{d['category']}</span></div>
      <div class="title">{html.escape(d['title'])}</div><p class="snip">{html.escape(d['text'][:150])}…</p>
      <div class="rel">relevance <span class="bar"><i style="width:{max(0, min(score, 1)) * 100:.0f}%"></i></span>{score:.3f}</div></div>""")
    if c2.button("Open", key=key, use_container_width=True):
        open_doc(d["id"])


hero()
t_search, t_chat, t_classify, t_graph, t_metrics = st.tabs(
    ["Search", "Ask the assistant", "Classify", "Knowledge graph", "Evaluation"])

# ---------- search ----------
with t_search:
    st.header("Search the store documents")
    st.caption("Write the way you talk — the search understands meaning, not only exact words.")
    c1, c2, c3 = st.columns([4, 1.4, 1.4])
    q = c1.text_input("What are you looking for?", placeholder="e.g. who still owes us money")
    engine = c2.selectbox("Engine", ["hybrid", "embeddings", "tfidf"],
                          help="hybrid = exact words (TF-IDF) + meaning (embeddings)")
    cat = c3.selectbox("Category", ["All"] + kb.CATEGORIES)
    if q:
        remember_query(q)
        for i, (d, s) in enumerate(kb.search(q, 5, engine, None if cat == "All" else cat)):
            doc_row(d, s, f"s{i}{d['id']}")
    else:
        st.markdown("**Try:** `who still owes us money` · `the web connection is lost` · `how much beef is lost when we cut it`")
        st.dataframe(pd.DataFrame(kb.DOCS)[["id", "title", "category"]], hide_index=True, use_container_width=True, height=300)

# ---------- chat ----------
with t_chat:
    st.header("Ask the assistant")
    try:
        key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:  # no secrets file locally
        key = None
    st.caption("Answers come only from the store documents and cite them like [D04]. "
               + ("Mode: generated answers (LLM) with extractive fallback." if key else
                  "Mode: extractive — the answer is built from the most relevant sentences."))
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if prompt := st.chat_input("e.g. What is the maximum credit limit for a customer?"):
        remember_query(prompt)
        ss.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        t0 = time.perf_counter()
        answer, hits, mode = kb.chat(prompt, key)
        ms = (time.perf_counter() - t0) * 1000
        rows = "".join(f"<tr><td>{d['id']}</td><td>{s:.3f}</td><td>{html.escape(d['title'])}</td></tr>" for d, s in hits)
        reply = (f"{answer}\n\n<details class='trace'><summary>retrieval trace · hybrid top-{len(hits)} · {mode} · {ms:.0f} ms"
                 f"</summary><table>{rows}</table></details>")
        ss.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply, unsafe_allow_html=True)
    if not ss.messages:
        st.markdown("**Try:** `What key do I press to sell on credit?` · `How long are old backups kept?` · "
                    "`At what temperature must meat be kept?`")

# ---------- classify ----------
with t_classify:
    st.header("Classify a new document")
    st.caption("Paste the text of a new manual, report, ticket, inventory record or policy. "
               f"Model: WordLlama embeddings + logistic regression trained on the {len(kb.DOCS)} store documents.")
    examples = {"—": "", "Supplier order": "Order to Carnes Selectas: 3 beef quarters and 20 kg of pork for Thursday delivery.",
                "Hygiene rule": "Butchers must wash their hands and change gloves after touching money.",
                "Sales summary": "Sales on Sunday were 31,200 pesos, 12 percent more than last Sunday."}
    ex = st.selectbox("Load an example", list(examples))
    text = st.text_area("Document text", examples[ex], height=140)
    if text.strip():
        ranked = kb.classify(text)
        st.success(f"Predicted category: **{ranked[0][0]}** ({ranked[0][1]:.0%} confidence)")
        st.bar_chart(pd.DataFrame(ranked, columns=["category", "probability"]).set_index("category"), horizontal=True)
        st.markdown("**Most similar existing documents**")
        for d, s in kb.search(text, 3, "embeddings"):
            st.markdown(f"- `{d['id']}` {d['title']} · *{d['category']}* · {s:.2f}")

# ---------- graph ----------
with t_graph:
    st.header("Knowledge graph")
    st.caption("Phase I ontology expanded: documents (dots) → categories (boxes) and topics (diamonds) → "
               "ontology classes (grey). Dashed lines join documents with very similar meaning.")
    c1, c2, c3 = st.columns(3)
    cats = c1.multiselect("Categories", kb.CATEGORIES)
    tops = c2.multiselect("Topics", kb.CONCEPTS, default=["CashClosing", "CustomerCredit"])
    focus = c3.selectbox("Focus on a document (2 hops)", ["—"] + [d["id"] for d in kb.DOCS])
    c4, c5 = st.columns(2)
    thr = c4.slider("Similarity edge threshold", 0.6, 0.95, 0.85, 0.01)
    classes = c5.toggle("Show ontology classes", True)
    G = kb.knowledge_graph(cats, tops, None if focus == "—" else focus, thr, classes)
    st.caption(f"{G.number_of_nodes()} nodes · {G.number_of_edges()} edges")
    if G.number_of_nodes() > 250:
        st.warning("Large graph: add filters to keep it readable.")
    components.html(kb.graph_html(G), height=670)
    st.download_button("Download the expanded ontology (Turtle)", kb.build_ontology().serialize(format="turtle"),
                       "la-nube-ontology.ttl", "text/turtle")

# ---------- metrics ----------
with t_metrics:
    st.header("System evaluation")
    m = M
    st.caption(f"Generated by `evaluate.py` · {m['corpus']['documents']} documents · {m['corpus']['topics']} topics · "
               f"{m['corpus']['ontology_triples']} ontology triples")
    c = m["classification"]
    st.subheader("Classification · " + c["protocol"])
    st.dataframe(pd.DataFrame({n: {k: v[k] for k in ("accuracy", "macro_precision", "macro_recall", "macro_f1")}
                               for n, v in c["models"].items()}).T, use_container_width=True)
    best = c["models"][c["in_app"]]
    a, b = st.columns(2)
    a.markdown(f"**Per class · {c['in_app']} (in the app)**")
    a.dataframe(pd.DataFrame(best["per_class"]).T, use_container_width=True)
    b.markdown("**Confusion matrix** (rows = true, columns = predicted)")
    b.dataframe(pd.DataFrame(best["confusion"], index=c["labels"], columns=c["labels"]), use_container_width=True)

    st.subheader(f"Retrieval · {sum(v['n'] for v in m['retrieval']['hybrid'].values())} hand-judged queries")
    st.dataframe(pd.DataFrame({(e, s): v for e, sets in m["retrieval"].items() for s, v in sets.items()}).T
                 .drop(columns="n"), use_container_width=True)
    r = m["recommendation"]
    st.subheader("Recommendations")
    a, b = st.columns(2)
    a.markdown(f"**Related documents** · {r['n_seeds']} seed docs with hand-labelled related sets")
    a.dataframe(pd.DataFrame(r["related_docs"]).T, use_container_width=True)
    b.markdown(f"**Query history effect** · {r['session_context']['n']} sessions")
    b.dataframe(pd.Series(r["session_context"]).drop("n").rename("value"), use_container_width=True)
    ch = m["chatbot"]
    st.subheader("Chatbot · " + str(ch["n"]) + " questions with a known answer")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Right source in top 3", f"{ch['source_hit@3']:.0%}")
    k2.metric("Answer contains the fact", f"{ch['fact_in_answer']:.0%}")
    k3.metric("Off-topic refused", ch["out_of_scope_refused"])
    k4.metric("Search latency", f"{m['latency']['search_ms']} ms")
    with st.expander("Answers in detail"):
        st.dataframe(pd.DataFrame(ch["detail"]), hide_index=True, use_container_width=True)
    st.subheader("Usability")
    u = kb.ROOT / "outputs" / "usability.json"
    if u.exists():
        st.json(json.load(open(u, encoding="utf-8")))
    else:
        st.info("User test in progress (SUS questionnaire + 3 tasks). Results will appear here.")

# ---------- sidebar: rendered last so it sees this run's searches ----------
with st.sidebar:
    st.subheader("Recommended for you")
    recs = kb.recommend(ss.queries, ss.viewed, k=5)
    if recs:
        st.caption("Based on your recent searches and opened documents.")
        for d, s in recs:
            if st.button(f"{d['id']} · {d['title']}", key="rec" + d["id"], use_container_width=True):
                open_doc(d["id"])
    else:
        st.info("Search or ask something and suggestions will appear here.")
    if ss.queries:
        st.caption("Your context: " + " · ".join(f"“{q}”" for q in ss.queries[-5:]))
        if st.button("Clear history"):
            ss.queries, ss.viewed, ss.messages = [], [], []
            st.rerun()
