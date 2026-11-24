"""La Nube knowledge assistant — Streamlit app. Run: streamlit run app.py"""
import json

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
    c1, c2 = st.columns([5, 1])
    c1.markdown(f"**{d['id']} · {d['title']}**  \n*{d['category']}* · {d['text'][:140]}…")
    c2.caption(f"score {score:.2f}")
    if c2.button("Open", key=key):
        open_doc(d["id"])


t_search, t_chat, t_classify, t_graph, t_metrics = st.tabs(
    ["🔎 Search", "💬 Ask the assistant", "🏷️ Classify a document", "🕸️ Knowledge graph", "📊 Evaluation"])

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
        answer, hits, mode = kb.chat(prompt, key)
        src = "\n".join(f"- `{d['id']}` {d['title']} ({s:.2f})" for d, s in hits)
        reply = f"{answer}\n\n<details><summary>Sources · {mode}</summary>\n\n{src}\n</details>"
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
    m = json.load(open(kb.ROOT / "outputs" / "metrics.json", encoding="utf-8"))
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
    st.title("☁️ La Nube")
    st.caption("Knowledge assistant for a neighbourhood supermarket with a butcher counter.")
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
