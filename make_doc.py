"""Run every script and build the progress document (Avance_Proyecto_La_Nube.docx)."""
import subprocess
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"


def run(script, *args):
    """Run a script and save an image of its console output as execution evidence."""
    res = subprocess.run([sys.executable, "-I", str(HERE / script), *args], capture_output=True, text=True, encoding="utf-8", check=True)
    shown = f"> python {script} {' '.join(repr(a) for a in args)}\n{res.stdout}"
    lines = shown.splitlines()
    fig = plt.figure(figsize=(11, 0.19 * len(lines) + 0.4))
    fig.patch.set_facecolor("#1e1e1e")
    fig.text(0.01, 0.99, shown, family="monospace", fontsize=8.5, color="#e6e6e6", va="top")
    png = OUT / f"console_{Path(script).stem}{'_custom' if args else ''}.png"
    fig.savefig(png, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return png


consoles = {
    "classifier": run("prototype/classifier.py"),
    "search": run("prototype/semantic_search.py"),
    "search_custom": run("prototype/semantic_search.py", "who authorizes a refund"),
    "practice": run("practice/practice_exercises.py"),
}
run("diagrams/diagrams.py")

doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)
H, P = doc.add_heading, doc.add_paragraph


def table(rows, header):
    t = doc.add_table(rows=1, cols=len(header), style="Light Grid Accent 1")
    for c, h in zip(t.rows[0].cells, header):
        c.text = h
    for r in rows:
        for c, v in zip(t.add_row().cells, r):
            c.text = v


def picture(path, caption, width=6.3):
    doc.add_picture(str(path), width=Inches(width))
    P(caption).runs[0].italic = True


H("Knowledge Management Project - Progress Report", 0)
P("La Nube Supermarket\nFelix Yael\nStudent ID: AL07003384\nUniversidad Tecmilenio")

H("1. Description of the Fictional Company", 1)
P("La Nube is a small neighborhood supermarket in Mexico that sells groceries, convenience products and fresh "
  "meat by the kilo at its own butcher counter. It operates two checkout registers, one butcher counter with a "
  "label scale and one local server inside the store. The store keeps selling even when the internet is down, "
  "and the owner checks sales from a phone. The organization is based on our team's GitHub repository "
  "insfra-super-la-nube, the point-of-sale system we are building for this store.")
table([
    ("Type of organization", "Retail - supermarket (mini super) with butcher counter"),
    ("Core activities", "Selling products at two registers, selling meat by weight, buying from suppliers, "
                        "managing inventory and meat breakdown, customer credit, daily cash cut"),
    ("Knowledge / documents handled", "Manuals (cashier, owner, installation), reports (daily sales, margins, "
                                      "shrinkage, audit), sales documents (tickets, invoices, promotions, credit), "
                                      "inventory records (purchase orders, receipts, counts, kardex) and policies"),
    ("People", "Owner, manager, cashiers, butcher, technician, suppliers and customers"),
], ["Element", "Description"])

H("2. Knowledge Lifecycle Map", 1)
P("The map follows how knowledge moves through La Nube. It is a cycle: what the store learns in each round "
  "(reports, audit, incidents) feeds the next round of creation.")
picture(HERE / "diagrams" / "lifecycle_map.png", "Figure 1. Knowledge lifecycle map of La Nube (diagrams/lifecycle_map.png).", 6.0)
table([
    ("Creation / acquisition", "Each sale, scale label, supplier invoice and cash cut creates data; cashiers and the "
                              "owner create experience (tacit knowledge) that is written into manuals."),
    ("Storage / documentation", "PostgreSQL database on the in-store server; manuals in Markdown in the repository; "
                               "nightly encrypted backups to a USB disk and cloud storage."),
    ("Organization / classification", "Documents are tagged as Manual, Report, Sales, Inventory or Policy by the "
                                     "automatic classifier and linked to concepts through the ontology."),
    ("Sharing", "Semantic search over documents, admin panel, owner's phone through Tailscale, printed tickets "
                "and training of new cashiers with the manuals."),
    ("Application", "Knowledge is used in daily decisions: cash cut, pricing, purchase orders, meat breakdown "
                    "and credit approval."),
    ("Update / improvement", "Audit log, shrinkage and sales reports and incident reports show what to change; "
                             "manuals and the POS get new versions."),
], ["Stage", "How it happens at La Nube"])

H("3. Ontology / Conceptual Graph", 1)
P("The ontology (diagrams/la-nube-ontology.ttl, OWL in Turtle format, 96 triples) represents how knowledge "
  "is structured in the store. It has 12 main domain concepts, 5 document types under the class Document, 4 "
  "subclasses and 17 object properties. Example individuals link real documents of the corpus to concepts, "
  "e.g. D04 (Manual) describes the process CashClosing.")
table([
    ("Main concepts", "Employee, Customer, Product, Department, Supplier, Sale, Payment, CashRegister, CashCut, "
                      "InventoryMovement, Process, Document"),
    ("Subclasses", "Cashier, Manager, Butcher (is-a Employee); MeatCut (is-a Product)"),
    ("Document types", "Manual, Report, SalesDocument, InventoryRecord, Policy (is-a Document)"),
    ("Concept-concept relations", "buys, contains, paidWith, recordedAt, operates, closes, belongsTo, supplies, "
                                  "changesStock, executes, authors"),
    ("Document-concept relations", "Manual describes Process; Policy regulates Process; Report summarizes Sale "
                                   "and cites CashCut; SalesDocument records Sale; InventoryRecord registers "
                                   "InventoryMovement"),
], ["Element", "Content"])
picture(HERE / "diagrams" / "ontology_graph.png", "Figure 2. Conceptual graph of organizational knowledge (diagrams/ontology_graph.png).")

H("4. How the Prototype Works", 1)
P("The corpus (data/documents.csv) has 50 sample documents written from the real processes of the POS "
  "repository, 10 for each category: Manual, Report, Sales, Inventory and Policy. Each document has an id, "
  "title, category and text.")
H("4.1 Automated classification (prototype/classifier.py)", 2)
for s in ["Loads the 50 documents from the CSV file and joins title + text.",
          "Splits them into 70% training and 30% test, stratified by category (seed 42).",
          "Vectorizes the text with TF-IDF (English stop words removed, sublinear term frequency).",
          "Trains two simple models: Multinomial Naive Bayes (alpha=0.5) and Logistic Regression (C=10). The "
          "settings were selected with 5-fold cross-validation (practice exercise 2).",
          "Reports accuracy, precision, recall, F1 and a confusion matrix, and classifies 5 new documents."]:
    doc.add_paragraph(s, style="List Number")
H("4.2 Semantic search (prototype/semantic_search.py)", 2)
for s in ["Receives a natural-language query (command-line argument or demo queries).",
          "Converts the query into a TF-IDF vector with the vectorizer fitted on the documents (unigrams and bigrams).",
          "Calculates the cosine similarity between the query vector and every document vector.",
          "Shows the 3 most relevant documents with their similarity score and category."]:
    doc.add_paragraph(s, style="List Number")
P("Limitation: TF-IDF matches shared words, not meaning, so synonyms are missed (\"debt\" does not match "
  "\"balance\"). A next step is to use sentence embeddings for real semantic similarity.")

H("5. Evidence of Prototype Development", 1)
P("All results below were produced by running make_doc.py, which executes each script. Images are captures "
  "of the console output.")
H("5.1 Classification results", 2)
picture(consoles["classifier"], "Figure 3. Console output of classifier.py.")
table([("Naive Bayes", "0.60", "0.78 +/- 0.15"), ("Logistic Regression", "0.87", "0.86 +/- 0.08")],
      ["Model", "Hold-out accuracy (15 docs)", "5-fold CV accuracy"])
P("Logistic Regression is the better model: 0.87 accuracy on the test set and 5 of 5 new documents classified "
  "correctly. Naive Bayes confuses Reports with Sales because both talk about sales and registers. With only "
  "35 training documents the scores vary a lot between splits, so the CV value is the more reliable estimate.")
picture(OUT / "confusion_logistic_regression.png", "Figure 4. Confusion matrix - Logistic Regression.", 3.6)
picture(OUT / "confusion_naive_bayes.png", "Figure 5. Confusion matrix - Naive Bayes.", 3.6)
H("5.2 Semantic search examples", 2)
picture(consoles["search"], "Figure 6. Console output of semantic_search.py with the demo queries.")
picture(consoles["search_custom"], "Figure 7. Free query typed by the user.", 5.5)
P("The query \"how do I close the register at the end of my shift\" returns the cash-cut manual (D04) first "
  "with a clear margin (0.44 vs 0.06). For \"what happens if the internet goes down\" it finds the offline "
  "policy and the troubleshooting manual, which use the words internet and selling.")

H("6. Practical Exercises (Topics 1 to 6)", 1)
P("These exercises were done while building the project and shaped its decisions (practice/practice_exercises.py).")
table([
    ("Topics 1-2: knowledge and its lifecycle", "Identification of the knowledge and document types of La Nube and "
                                                "the lifecycle map (Figure 1)."),
    ("Topic 3: conceptual representation", "Ontology / conceptual graph in OWL (Figure 2); earlier ontology "
                                           "exercise for IT technical support used as a model."),
    ("Topic 4: text representation", "Exercise 1: bag of words vs TF-IDF top terms per category."),
    ("Topic 5: classification tests", "Exercise 2: 5-fold CV of Naive Bayes and Logistic Regression with "
                                      "unigrams vs bigrams; selected the prototype settings."),
    ("Topic 6: information retrieval", "Exercise 3: precision@3 and MRR of the search on 8 queries with known "
                                       "relevant documents (mean P@3 = 0.71, MRR = 1.00)."),
], ["Topic", "Activity and evidence"])
picture(consoles["practice"], "Figure 8. Console output of the practice exercises.")
P("Exercise 3 shows that the first result is always relevant (MRR = 1.00) but some lists contain unrelated "
  "documents in positions 2-3, e.g. \"returns and refunds\" also returns the offline and pricing policies. "
  "This supports the planned move to embeddings and adding more documents per category.")

H("7. Next Steps", 1)
for s in ["Grow the corpus with the real manuals and reports of the POS (Spanish) and retrain.",
          "Replace TF-IDF search with sentence embeddings for true semantic similarity.",
          "Use the ontology to expand queries (e.g. a search for \"cash cut\" also returns documents about CashRegister).",
          "Connect the classifier to the admin panel so new documents are tagged automatically."]:
    doc.add_paragraph(s, style="List Bullet")

out = HERE / "Avance_Proyecto_La_Nube.docx"
doc.save(out)
print("wrote", out)
