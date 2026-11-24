"""Asistente de conocimiento de La Nube — app Streamlit. Ejecutar: streamlit run app.py"""
import base64
import html
import json
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="La Nube · Asistente", page_icon="☁️", layout="wide")


@st.cache_resource(show_spinner="Cargando documentos y modelos…")
def load():
    import knowledge
    return knowledge


kb = load()
ss = st.session_state
ss.setdefault("queries", [])   # búsquedas y preguntas, la más reciente al final (para recomendaciones)
ss.setdefault("viewed", [])    # documentos abiertos
ss.setdefault("messages", [])  # historial del chat

M = json.load(open(kb.ROOT / "outputs" / "metrics.json", encoding="utf-8"))
st.html(f"<style>{(kb.ROOT / 'style.css').read_text(encoding='utf-8')}</style>")

# gráfico del recorrido: pregunta -> documentos -> temas -> respuesta (--d = etapa del pulso)
NODES = {"q": (30, 75), "d1": (135, 28), "d2": (135, 75), "d3": (135, 122), "t1": (240, 50), "t2": (240, 100), "a": (330, 75)}
EDGES = [("q", "d1", 0), ("q", "d2", 0), ("q", "d3", 0), ("d1", "t1", 1), ("d2", "t1", 1), ("d2", "t2", 1),
         ("d3", "t2", 1), ("t1", "a", 2), ("t2", "a", 2)]

ASK_EXAMPLES = ["¿Qué tecla presiono para vender a crédito?", "¿Qué hago si se cae el internet?",
                "¿A qué temperatura se guarda la carne?"]
FAIL_EXAMPLE = "Receta de pastel de chocolate"


def level(score):
    """Puntaje híbrido -> palabra que entiende cualquiera."""
    return "Alta" if score >= 0.45 else "Media" if score >= kb.NOT_FOUND else "Baja"


def hero():
    lines = "".join(f'<line class="e" x1="{NODES[a][0]}" y1="{NODES[a][1]}" x2="{NODES[b][0]}" y2="{NODES[b][1]}"/>'
                    f'<line class="f" style="--d:{d}" x1="{NODES[a][0]}" y1="{NODES[a][1]}" x2="{NODES[b][0]}" y2="{NODES[b][1]}"/>'
                    for a, b, d in EDGES)
    dots = "".join(f'<circle class="{"hot" if n in ("q", "a") else "n"}" style="--d:{0 if n == "q" else 2}" '
                   f'cx="{x}" cy="{y}" r="{8 if n in ("q", "a") else 5}"/>' for n, (x, y) in NODES.items())
    # el pulso recorre pregunta -> documentos -> temas -> respuesta 3 veces; sin animación con reduced motion
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
    steps = [("1", "Pregunta algo de la tienda, con tus palabras"), ("2", "Revisa de qué documento salió la respuesta"),
             ("3", "Intenta engañarla con algo que no sea de la tienda")]
    # el contador cambia la imagen en cada pregunta, así el pulso se repite
    st.html(f"""<div class="hero">
      <div><p class="eyebrow">Gestión del conocimiento · Mini-súper La Nube</p>
        <h1>Asistente de La Nube</h1>
        <p class="lede">Los cajeros nuevos preguntan lo mismo cada semana y las respuestas están regadas en
        {len(kb.DOCS)} manuales, reportes y políticas. Este asistente las encuentra por ti y te dice de dónde las sacó.
        Si algo no está en los documentos, te lo dice en vez de inventar.</p>
        <div class="kpis">{"".join(f'<div class="kpi"><b>{n}</b><span>{t}</span></div>' for n, t in steps)}</div>
      </div>
      <img class="net" src="{src}" alt="">
    </div>""")


def remember_query(q):
    if q and (not ss.queries or ss.queries[-1] != q):
        ss.queries.append(q)


@st.dialog("Documento", width="large")
def open_doc(doc_id):
    d = kb.DOCS[kb.BY_ID[doc_id]]
    if not ss.viewed or ss.viewed[-1] != doc_id:
        ss.viewed.append(doc_id)
    st.subheader(f"{d['id']} · {d['title']}")
    st.caption(f"Tipo de documento: **{d['category']}**")
    st.write(d["text"])
    st.markdown("**Documentos parecidos**")
    for r, _ in kb.related(doc_id, 4):
        st.markdown(f"- `{r['id']}` {r['title']} · *{r['category']}*")


def doc_row(d, score, key):
    c1, c2 = st.columns([6, 1], vertical_alignment="center")
    c1.html(f"""<div class="doc"><div class="meta"><span class="id">{d['id']}</span><span class="cat">{d['category']}</span></div>
      <div class="title">{html.escape(d['title'])}</div><p class="snip">{html.escape(d['text'][:150])}…</p>
      <div class="rel">coincidencia <span class="bar"><i style="width:{max(0, min(score / 0.6, 1)) * 100:.0f}%"></i></span>{level(score)}</div></div>""")
    if c2.button("Abrir", key=key, width="stretch"):
        open_doc(d["id"])


def example_buttons(examples, target, prefix):
    """Botones que llenan la pregunta: el profesor puede probar sin escribir."""
    for c, q in zip(st.columns(len(examples)), examples):
        if c.button(q, key=prefix + q, width="stretch"):
            ss[target] = q


hero()
t_chat, t_search, t_classify, t_tech = st.tabs(
    ["💬 Preguntar", "🔎 Buscar documentos", "🏷️ Clasificar un texto", "⚙️ Cómo funciona"])

# ---------- preguntar ----------
with t_chat:
    try:
        key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:  # sin archivo de secretos en local
        key = None
    st.markdown("Escribe una pregunta como se la harías a un compañero con experiencia, o toca un ejemplo. "
                "La respuesta sale **solo** de los documentos de la tienda y marca la fuente, por ejemplo **[D04]**.")
    example_buttons(ASK_EXAMPLES + ["🧪 " + FAIL_EXAMPLE], "ask", "a")
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"], unsafe_allow_html=True)
    prompt = st.chat_input("Escribe tu pregunta…") or ss.pop("ask", None)
    if prompt:
        prompt = prompt.removeprefix("🧪 ")
        remember_query(prompt)
        ss.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        t0 = time.perf_counter()
        answer, hits, mode = kb.chat(prompt, key)
        ms = (time.perf_counter() - t0) * 1000
        if answer == kb.NOT_FOUND_MSG:
            reply = (f"🤔 **{answer}** Esto es a propósito: prefiere decir que no sabe antes que inventar. "
                     "Prueba con algo de la tienda: caja, cobros, crédito a clientes, carnicería, inventario, respaldos…")
        else:
            srcs = "".join(f"<li><code>{d['id']}</code> {html.escape(d['title'])}</li>"
                           for d in {d['id']: d for d, _ in hits if f"[{d['id']}]" in answer}.values())
            reply = f"{answer}\n\n<div><b>Fuentes</b><ul>{srcs}</ul></div>"
        rows = "".join(f"<tr><td>{d['id']}</td><td>{level(s)} ({s:.2f})</td><td>{html.escape(d['title'])}</td></tr>"
                       for d, s in hits)
        how = "redactada por IA con esos documentos" if mode == "llm" else "armada con las frases más cercanas a tu pregunta"
        reply += (f"\n\n<details class='trace'><summary>¿Cómo llegó a esta respuesta?</summary>"
                  f"<p>Buscó los 3 documentos más parecidos a tu pregunta (por palabras y por significado) "
                  f"y la respuesta fue {how}. Tardó {ms:.0f} ms. Si la coincidencia más alta es menor a "
                  f"{kb.NOT_FOUND}, responde que no lo encontró.</p><table>{rows}</table></details>")
        ss.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply, unsafe_allow_html=True)
    if ss.messages and st.button("Borrar conversación"):
        ss.messages = []
        st.rerun()

# ---------- buscar ----------
with t_search:
    st.markdown("Busca documentos aunque no sepas el nombre exacto: entiende el **significado**, no solo las palabras.")
    example_buttons(["quién nos debe dinero", "se cayó la conexión", "cuánta carne se pierde al cortar la res"], "q", "s")
    c1, c2 = st.columns([4, 1.4])
    q = c1.text_input("¿Qué buscas?", key="q", placeholder="por ejemplo: cómo cierro la caja")
    cat = c2.selectbox("Tipo de documento", ["Todos"] + kb.CATEGORIES)
    if q:
        remember_query(q)
        for i, (d, s) in enumerate(kb.search(q, 5, "hybrid", None if cat == "Todos" else cat)):
            doc_row(d, s, f"s{i}{d['id']}")
    with st.expander(f"Ver los {len(kb.DOCS)} documentos de la tienda"):
        st.dataframe(pd.DataFrame(kb.DOCS)[["id", "title", "category"]].rename(
            columns={"id": "ID", "title": "Título", "category": "Tipo"}), hide_index=True, width="stretch")

# ---------- clasificar ----------
with t_classify:
    st.markdown("Pega el texto de un documento nuevo y el sistema adivina **de qué tipo es** "
                f"({', '.join(kb.CATEGORIES)}). Aprendió de los {len(kb.DOCS)} documentos que ya existen. "
                "Prueba también con un texto raro para ver qué tan seguro está.")
    examples = {"— elige un ejemplo —": "",
                "Pedido a proveedor": "Pedido a Carnes Selectas: 3 cuartos de res y 20 kg de cerdo para entregar el jueves.",
                "Regla de higiene": "Los carniceros deben lavarse las manos y cambiar guantes después de tocar dinero.",
                "Reporte de ventas": "Las ventas del domingo fueron 31,200 pesos, 12 por ciento más que el domingo pasado."}
    ex = st.selectbox("Cargar un ejemplo", list(examples))
    text = st.text_area("Texto del documento", examples[ex], height=120)
    if text.strip():
        ranked = kb.classify(text)
        p = ranked[0][1]
        sure = "muy seguro" if p >= 0.6 else "algo seguro" if p >= 0.4 else "con dudas"
        st.success(f"Parece un documento de tipo **{ranked[0][0]}** · el sistema está {sure} ({p:.0%})")
        st.bar_chart(pd.DataFrame(ranked, columns=["tipo", "probabilidad"]).set_index("tipo"), horizontal=True)
        st.markdown("**Documentos existentes más parecidos**")
        for d, _ in kb.search(text, 3, "embeddings"):
            st.markdown(f"- `{d['id']}` {d['title']} · *{d['category']}*")

# ---------- cómo funciona (técnico) ----------
with t_tech:
    ch, c, r = M["chatbot"], M["classification"], M["retrieval"]["hybrid"]
    st.markdown("Esta pestaña es para quien quiera ver **qué hay detrás**. Resumen en palabras simples, "
                f"medido con preguntas revisadas a mano (`evaluate.py`):")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Encuentra el documento correcto", f"{ch['source_hit@3']:.0%}", help="entre los 3 primeros, en "
              f"{ch['n']} preguntas con respuesta conocida")
    k2.metric("La respuesta trae el dato exacto", f"{ch['fact_in_answer']:.0%}")
    k3.metric("Rechaza preguntas fuera de tema", ch["out_of_scope_refused"])
    k4.metric("Acierta el tipo de documento", f"{c['models'][c['in_app']]['accuracy']:.0%}",
              help="validación cruzada de 5 particiones")

    with st.expander("🕸️ Mapa del conocimiento (ontología)"):
        st.caption("Documentos (puntos) → tipo (cajas) y temas (rombos) → clases de la ontología de la Fase I (gris). "
                   "Las líneas punteadas unen documentos con significado muy parecido. Puedes arrastrar y hacer zoom.")
        c1, c2, c3 = st.columns(3)
        cats = c1.multiselect("Tipos", kb.CATEGORIES)
        tops = c2.multiselect("Temas", kb.CONCEPTS, default=["CashClosing", "CustomerCredit"])
        focus = c3.selectbox("Centrar en un documento", ["—"] + [d["id"] for d in kb.DOCS])
        c4, c5 = st.columns(2)
        thr = c4.slider("Qué tan parecidos para unirlos", 0.6, 0.95, 0.85, 0.01)
        classes = c5.toggle("Mostrar clases de la ontología", True)
        G = kb.knowledge_graph(cats, tops, None if focus == "—" else focus, thr, classes)
        st.caption(f"{G.number_of_nodes()} nodos · {G.number_of_edges()} conexiones")
        if G.number_of_nodes() > 250:
            st.warning("Gráfico grande: filtra por tipo o tema para que se lea mejor.")
        components.html(kb.graph_html(G), height=670)
        st.download_button("Descargar la ontología (Turtle)", kb.build_ontology().serialize(format="turtle"),
                           "la-nube-ontologia.ttl", "text/turtle")

    with st.expander("📊 Métricas completas"):
        st.markdown(f"**Motor:** búsqueda híbrida (TF-IDF + embeddings multilingües model2vec) · clasificador "
                    f"`{c['in_app']}` · {M['corpus']['documents']} documentos · {M['corpus']['ontology_triples']} "
                    "tripletas en la ontología · todo corre en CPU.")
        st.markdown("**Clasificación** · " + c["protocol"])
        st.dataframe(pd.DataFrame({n: {k: v[k] for k in ("accuracy", "macro_precision", "macro_recall", "macro_f1")}
                                   for n, v in c["models"].items()}).T, width="stretch")
        best = c["models"][c["in_app"]]
        a, b = st.columns(2)
        a.markdown(f"Por tipo · {c['in_app']} (el de la app)")
        a.dataframe(pd.DataFrame(best["per_class"]).T, width="stretch")
        b.markdown("Matriz de confusión (filas = real, columnas = predicho)")
        b.dataframe(pd.DataFrame(best["confusion"], index=c["labels"], columns=c["labels"]), width="stretch")
        st.markdown(f"**Búsqueda** · {sum(v['n'] for v in M['retrieval']['hybrid'].values())} consultas juzgadas a mano "
                    "(keyword = con las palabras del documento, paraphrase = con otras palabras)")
        st.dataframe(pd.DataFrame({(e, s): v for e, sets in M["retrieval"].items() for s, v in sets.items()}).T
                     .drop(columns="n"), width="stretch")
        rec = M["recommendation"]
        a, b = st.columns(2)
        a.markdown(f"**Documentos parecidos** · {rec['n_seeds']} documentos con relacionados etiquetados")
        a.dataframe(pd.DataFrame(rec["related_docs"]).T, width="stretch")
        b.markdown(f"**Efecto del historial** · {rec['session_context']['n']} sesiones")
        b.dataframe(pd.Series(rec["session_context"]).drop("n").rename("valor"), width="stretch")
        st.markdown(f"**Chatbot** · {ch['n']} preguntas · umbral de 'no lo encontré' = {ch['threshold']} "
                    f"(mínimo en tema {ch['min_in_scope_score']}, máximo fuera de tema {ch['max_out_of_scope_score']})")
        st.dataframe(pd.DataFrame(ch["detail"]), hide_index=True, width="stretch")
        u = kb.ROOT / "outputs" / "usability.json"
        if u.exists():
            st.markdown("**Usabilidad (SUS)**")
            st.json(json.load(open(u, encoding="utf-8")))

# ---------- barra lateral: al final para ver las búsquedas de esta ejecución ----------
with st.sidebar:
    st.subheader("Te puede interesar")
    recs = kb.recommend(ss.queries, ss.viewed, k=5)
    if recs:
        st.caption("Según lo que has buscado y abierto.")
        for d, _ in recs:
            if st.button(f"{d['id']} · {d['title']}", key="rec" + d["id"], width="stretch"):
                open_doc(d["id"])
    else:
        st.info("Haz una pregunta o búsqueda y aquí aparecerán documentos recomendados.")
    if ss.queries:
        st.caption("Lo último que buscaste: " + " · ".join(f"“{q}”" for q in ss.queries[-5:]))
        if st.button("Empezar de cero"):
            ss.queries, ss.viewed, ss.messages = [], [], []
            st.rerun()
