<div align="center">

# ☁️🛒 La Nube — Gestión del Conocimiento

**Clasificación automática y búsqueda semántica de documentos para un mini súper con carnicería**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?logo=scikitlearn&logoColor=white)
![OWL](https://img.shields.io/badge/Ontología-OWL%20%2F%20Turtle-6A1B9A)
![Accuracy](https://img.shields.io/badge/LogReg%20accuracy-0.87-2E7D32)
![MRR](https://img.shields.io/badge/búsqueda%20MRR-1.00-2E7D32)
![Estado](https://img.shields.io/badge/estado-avance%201-FFB300)

*Felix Yael · Universidad Tecmilenio · Basado en el POS `insfra-super-la-nube` (privado)*

</div>

---

## 🧭 ¿De qué trata?

**La Nube** es un supermercado de barrio en México: 2 cajas 🧾🧾, 1 carnicería con báscula 🥩⚖️ y 1 servidor local 🖥️ que sigue vendiendo aunque se caiga el internet.
Este proyecto organiza **todo el conocimiento del negocio** — manuales, reportes, tickets, inventario y políticas — para que cualquiera lo encuentre en segundos.

| 📘 Manual | 📊 Report | 🧾 Sales | 📦 Inventory | 📜 Policy |
|:-:|:-:|:-:|:-:|:-:|
| 10 docs | 10 docs | 10 docs | 10 docs | 10 docs |
| Cómo cobrar, corte de caja, F6 crédito | Ventas, márgenes, merma | Tickets, facturas, promos | Kardex, compras, despiece | Crédito, higiene, offline |

---

## 🗺️ Mapa del proyecto

```mermaid
flowchart LR
    A[(📄 50 documentos<br/>documents.csv)] --> B[🔤 TF-IDF]
    B --> C{🤖 Clasificador}
    C -->|Naive Bayes| C1[0.60]
    C -->|Logistic Regression| C2[✅ 0.87]
    B --> D[🔎 Búsqueda semántica<br/>coseno top-3]
    A --> G[🧠 Embeddings<br/>WordLlama] --> D
    O[🕸️ Ontología OWL<br/>12 conceptos · 17 relaciones] -.-> D
    C2 --> E[🏷️ Etiqueta docs nuevos]
    D --> F[💬 Respuesta al cajero / dueño]
```

---

## ♻️ Ciclo de vida del conocimiento

```mermaid
flowchart LR
    C1[✍️ Creación<br/>ventas, etiquetas, cortes] --> C2[💾 Almacenamiento<br/>PostgreSQL + backups]
    C2 --> C3[🗂️ Organización<br/>clasificador + ontología]
    C3 --> C4[🤝 Compartir<br/>búsqueda, panel, celular]
    C4 --> C5[⚙️ Aplicación<br/>precios, compras, crédito]
    C5 --> C6[📈 Mejora<br/>auditoría, merma, incidentes]
    C6 --> C1
```

<p align="center"><img src="diagrams/lifecycle_map.png" width="85%" alt="Mapa del ciclo de vida del conocimiento"></p>

---

## 🕸️ Ontología

`diagrams/la-nube-ontology.ttl` (OWL, 96 triples) — ábrela en **Protégé**.

```mermaid
graph TD
    Employee --> Cashier & Manager & Butcher
    Product --> MeatCut
    Document --> Manual & Report & SalesDocument & InventoryRecord & Policy
    Manual -- describes --> Process
    Policy -- regulates --> Process
    Report -- summarizes --> Sale
    SalesDocument -- records --> Sale
    Customer -- buys --> Sale
    Sale -- contains --> Product
    CashCut -- closes --> CashRegister
```

<p align="center"><img src="diagrams/ontology_graph.png" width="85%" alt="Grafo conceptual"></p>

---

## 📊 Resultados

### 🤖 Clasificación

| Modelo | Hold-out (15 docs) | 5-fold CV | Docs nuevos |
|---|:-:|:-:|:-:|
| Naive Bayes | 🟠 0.60 | 0.78 ± 0.15 | — |
| **Logistic Regression** | 🟢 **0.87** | **0.86 ± 0.08** | **5/5** ✅ |

<p align="center">
  <img src="outputs/confusion_logistic_regression.png" width="42%" alt="Matriz de confusión LogReg">
  <img src="outputs/confusion_naive_bayes.png" width="42%" alt="Matriz de confusión NB">
</p>

### 🔎 Búsqueda semántica

| Pregunta | 🥇 Primer resultado | Score |
|---|---|:-:|
| *how do I close the register at the end of my shift* | D04 Cashier manual – end of shift cut | 0.441 |
| *which customers owe money on credit* | D44 Customer credit policy | 0.243 |
| *meat waste and yield of beef* | D14 Shrinkage and waste report | 0.317 |
| *what happens if the internet goes down* | D50 Offline operation policy | 0.246 |
| *charge with debit card terminal* | D22 Sales ticket – card payment | 0.309 |

**Precisión@3 = 0.71 · MRR = 1.00** → el primer resultado siempre es relevante.

### 🧠 Mejora implementada: búsqueda con embeddings

TF-IDF solo encuentra documentos que **comparten palabras** con la pregunta. Si el cajero escribe *"balance the till"* en lugar de *"close the register"*, no encuentra el manual del corte. Los **embeddings** representan el significado: palabras distintas con sentido parecido quedan cerca.

`prototype/embedding_search.py` usa **WordLlama** (~16 MB, CPU, sin GPU y sin internet una vez instalado), así que corre en el servidor local del súper. Tiene tres motores: `tfidf`, `embeddings` y `hybrid` (promedio de ambos).

`prototype/compare_search.py` mide los tres motores con dos conjuntos de preguntas juzgadas:

| Conjunto | TF-IDF (antes) | Embeddings | Híbrido |
|---|:-:|:-:|:-:|
| A. Palabras clave (8 preguntas) | P@3 0.71 · MRR 1.00 | P@3 0.75 · MRR 1.00 | **P@3 0.79** · MRR 1.00 |
| B. Parafraseo cotidiano (12 preguntas) | P@3 0.14 · MRR 0.29 | **P@3 0.42 · MRR 0.69** | P@3 0.36 · MRR 0.60 |

➡️ Cuando la gente pregunta **como habla**, el primer resultado relevante sube de **MRR 0.29 a 0.69** (×2.4) y la precisión de los 3 primeros **se triplica**, sin perder nada en las preguntas con palabras clave.

<p align="center"><img src="outputs/search_comparison.png" width="90%" alt="TF-IDF vs embeddings vs híbrido"></p>

Detalle por pregunta: `outputs/search_comparison.txt`. Aún falla en casos como *"balance the till"* y *"which items are running out"*: lo atacan el corpus en español y la expansión con la ontología.

<details>
<summary>📸 Capturas de consola</summary>

![Clasificador](outputs/console_classifier.png)
![Búsqueda](outputs/console_semantic_search.png)
![Consulta libre](outputs/console_semantic_search_custom.png)
![Ejercicios](outputs/console_practice_exercises.png)

</details>

---

## 🚀 Lo que vamos a hacer (roadmap)

```mermaid
timeline
    title Ruta del proyecto La Nube
    ✅ Avance 1 : Empresa ficticia : Ciclo de vida : Ontología OWL : Clasificador TF-IDF : Búsqueda TF-IDF
    🔜 Fase 2 : Corpus real en español (manuales y reportes del POS) : Reentrenar y comparar modelos
    ✅ Fase 3 (adelantada) : Embeddings con WordLlama : Búsqueda por significado, MRR 0.29 → 0.69 en parafraseo
    🔜 Fase 4 : Expansión de consultas con la ontología : "corte de caja" ⇒ CashRegister
    🎯 Final : Clasificador conectado al panel admin : Etiquetado automático de docs nuevos
```

- [x] 🏪 Describir la empresa ficticia
- [x] ♻️ Mapa del ciclo de vida del conocimiento
- [x] 🕸️ Ontología / grafo conceptual
- [x] 🤖 Prototipo de clasificación (Naive Bayes vs LogReg)
- [x] 🔎 Búsqueda semántica básica (TF-IDF + coseno)
- [x] 📝 Documento de avance + evidencias
- [ ] 🇲🇽 Crecer el corpus con documentos reales del POS en español
- [x] 🧠 Búsqueda con embeddings (WordLlama) + comparación contra TF-IDF
- [ ] 🔗 Expandir búsquedas usando la ontología
- [ ] 🖥️ Integrar el clasificador al panel de administración

---

## 📁 Estructura

| Punto de la actividad | Archivo |
|---|---|
| 1. Empresa ficticia | `Avance_Proyecto_La_Nube.docx` (sección 1) |
| 2. Mapa del ciclo de vida | `diagrams/lifecycle_map.png` |
| 3. Ontología / grafo | `diagrams/ontology_graph.png`, `diagrams/la-nube-ontology.ttl` |
| 4. Clasificación (TF-IDF + NB / LogReg) | `prototype/classifier.py` |
| 5. Búsqueda semántica | `prototype/semantic_search.py` |
| Mejora: búsqueda con embeddings | `prototype/embedding_search.py` |
| Comparación antes / después | `prototype/compare_search.py`, `outputs/search_comparison.txt`, `outputs/search_comparison.png` |
| 6. Documento de avance + evidencias | `Avance_Proyecto_La_Nube.docx`, `outputs/` |
| Ejercicios de práctica (Temas 1–6) | `practice/practice_exercises.py`, `outputs/practice_results.txt` |
| Corpus (50 docs, 5 categorías) | `data/documents.csv` |

## ▶️ Ejecutar

```bash
pip install scikit-learn matplotlib networkx rdflib python-docx wordllama
python make_doc.py                                              # corre todo y regenera el .docx
python prototype/semantic_search.py "who authorizes a refund"   # búsqueda libre (TF-IDF)
python prototype/embedding_search.py "who still owes us money"  # búsqueda con embeddings
python prototype/compare_search.py                              # antes vs después (tabla + gráfica)
```

> La primera vez, WordLlama descarga su tokenizer desde Hugging Face (unos KB); después funciona sin internet.
