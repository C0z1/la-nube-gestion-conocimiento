"""Draw the knowledge lifecycle map and build the La Nube ontology (Turtle file + graph PNG)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import FancyBboxPatch
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL

HERE = Path(__file__).parent

# ---------- 1. Knowledge lifecycle map ----------
stages = [
    ("1. Creation /\nAcquisition", "Sales at registers, scale labels,\nsupplier invoices, cashier\nexperience, owner decisions", "#f6c445"),
    ("2. Storage /\nDocumentation", "PostgreSQL on the in-store\nserver, manuals (Markdown),\nnightly encrypted backups", "#9cc7f0"),
    ("3. Organization /\nClassification", "TF-IDF + ML classifier tags\nManual, Report, Sales,\nInventory, Policy; ontology", "#a8d5a2"),
    ("4. Sharing", "Semantic search, admin panel,\nowner's phone (Tailscale),\nprinted tickets, training", "#f4a6a6"),
    ("5. Application", "Cash cut, pricing, purchase\norders, meat breakdown,\ncredit approval", "#c9b3e6"),
    ("6. Update /\nImprovement", "Audit log, shrinkage and sales\nreports, new versions of\nmanuals and the POS", "#ffd59e"),
]
fig, ax = plt.subplots(figsize=(15, 11.5))
angles = np.pi / 2 - np.arange(6) * 2 * np.pi / 6
pts = [(4.6 * np.cos(a), 3.7 * np.sin(a)) for a in angles]
for i, ((title, desc, color), (x, y)) in enumerate(zip(stages, pts)):
    ax.add_patch(FancyBboxPatch((x - 1.55, y - 1.0), 3.1, 2.0, boxstyle="round,pad=0.08", fc=color, ec="#333", lw=1.5))
    ax.text(x, y + 0.5, title, ha="center", va="center", fontsize=12, fontweight="bold")
    ax.text(x, y - 0.4, desc, ha="center", va="center", fontsize=9)
    nx_, ny = pts[(i + 1) % 6]
    a, b = np.array([x, y]), np.array([nx_, ny])
    ax.annotate("", xy=a + 0.68 * (b - a), xytext=a + 0.32 * (b - a),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#555", connectionstyle="arc3,rad=-0.15"))
ax.add_patch(plt.Circle((0, 0), 1.25, fc="white", ec="#333", lw=1.5))
ax.text(0, 0, "La Nube\nSupermarket\nknowledge", ha="center", va="center", fontsize=13, fontweight="bold")
ax.set_xlim(-6.5, 6.5); ax.set_ylim(-5.0, 5.0); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Knowledge Lifecycle Map - La Nube Supermarket", fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(HERE / "lifecycle_map.png", dpi=150)
plt.close()

# ---------- 2. Ontology ----------
LN = Namespace("http://www.example.org/la-nube#")
g = Graph(); g.bind("ln", LN)
concepts = ["Employee", "Customer", "Product", "Department", "Supplier", "Sale", "Payment",
            "CashRegister", "CashCut", "InventoryMovement", "Process", "Document"]
doc_types = ["Manual", "Report", "SalesDocument", "InventoryRecord", "Policy"]
subclasses = {"Cashier": "Employee", "Manager": "Employee", "Butcher": "Employee", "MeatCut": "Product"}
relations = [  # (property, domain, range) - concept-concept and document-concept relations
    ("buys", "Customer", "Sale"), ("contains", "Sale", "Product"), ("paidWith", "Sale", "Payment"),
    ("recordedAt", "Sale", "CashRegister"), ("operates", "Employee", "CashRegister"),
    ("closes", "CashCut", "CashRegister"), ("belongsTo", "Product", "Department"),
    ("supplies", "Supplier", "Product"), ("changesStock", "InventoryMovement", "Product"),
    ("executes", "Employee", "Process"), ("authors", "Employee", "Document"),
    ("describes", "Manual", "Process"), ("summarizes", "Report", "Sale"),
    ("records", "SalesDocument", "Sale"), ("registers", "InventoryRecord", "InventoryMovement"),
    ("regulates", "Policy", "Process"), ("cites", "Report", "CashCut"),
]
for c in concepts + doc_types + list(subclasses):
    g.add((LN[c], RDF.type, OWL.Class))
for d in doc_types:
    g.add((LN[d], RDFS.subClassOf, LN.Document))
for c, p in subclasses.items():
    g.add((LN[c], RDFS.subClassOf, LN[p]))
for p, d, rng in relations:
    g.add((LN[p], RDF.type, OWL.ObjectProperty)); g.add((LN[p], RDFS.domain, LN[d])); g.add((LN[p], RDFS.range, LN[rng]))
# example individuals linking real corpus documents to concepts
for ind, cls, label in [("D04", "Manual", "Cashier manual - end of shift cut"), ("D14", "Report", "Shrinkage and waste report"),
                        ("D21", "SalesDocument", "Sales ticket 000845"), ("CashClosing", "Process", "End of shift cash cut"),
                        ("Register1", "CashRegister", "Register 1"), ("GroundBeef", "MeatCut", "Ground beef")]:
    g.add((LN[ind], RDF.type, LN[cls])); g.add((LN[ind], RDFS.label, Literal(label)))
g.add((LN.D04, LN.describes, LN.CashClosing))
g.add((LN.D21, LN.records, LN.Sale))
g.add((LN.D14, LN.summarizes, LN.Sale))
g.serialize(HERE / "la-nube-ontology.ttl", format="turtle")

# self-check: every relation endpoint is a declared class
classes = set(g.subjects(RDF.type, OWL.Class))
assert all(LN[d] in classes and LN[rng] in classes for _, d, rng in relations)
print(f"Ontology OK: {len(g)} triples, {len(classes)} classes, {len(relations)} object properties")

G = nx.MultiDiGraph()
for p, d, rng in relations:
    G.add_edge(d, rng, label=p)
for d in doc_types:
    G.add_edge(d, "Document", label="is-a")
for c, p in subclasses.items():
    G.add_edge(c, p, label="is-a")
pos = nx.kamada_kawai_layout(G.to_undirected())
# hand nudges so no edge crosses a node
pos["CashCut"] = pos["CashRegister"] + np.array([0.12, -0.28])
pos["Policy"] = pos["Policy"] + np.array([0.05, -0.22])
fig, ax = plt.subplots(figsize=(18, 14))
color = {n: "#9cc7f0" if n in doc_types + ["Document"] else "#f6c445" if n in concepts else "#d9d9d9" for n in G}
nx.draw_networkx_nodes(G, pos, node_color=[color[n] for n in G], node_size=4300, edgecolors="#333", ax=ax)
nx.draw_networkx_labels(G, pos, labels={n: n.replace("Movement", "\nMovement").replace("Document", "\nDocument").replace("Record", "\nRecord").replace("Register", "\nRegister") if n != "Document" else n for n in G}, font_size=9, font_weight="bold", ax=ax)
for u, v, d in G.edges(data=True):
    isa = d["label"] == "is-a"
    doc_rel = u in doc_types and not isa
    c = "#888" if isa else "#2e6db4" if doc_rel else "#c0392b"
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], style="dashed" if isa else "solid", edge_color=c,
                           arrowsize=20, width=1.6, node_size=4300, ax=ax)
    (x1, y1), (x2, y2) = pos[u], pos[v]
    ax.text((x1 + x2) / 2, (y1 + y2) / 2, d["label"], ha="center", va="center", fontsize=9, color=c,
            fontweight="bold", bbox=dict(fc="white", ec="none", alpha=0.85))
ax.set_title("La Nube Supermarket - Ontology / Conceptual Graph\n(yellow = domain concepts, blue = document types, grey = subclasses;"
             " red = concept relations, blue arrows = document-concept relations, dashed = is-a)", fontsize=14)
ax.margins(0.06); ax.axis("off")
plt.tight_layout()
plt.savefig(HERE / "ontology_graph.png", dpi=150)
print("wrote lifecycle_map.png, ontology_graph.png, la-nube-ontology.ttl")
