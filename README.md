# Site Feasibility Agent – Proof‑of‑Concept

## 1. Purpose

Build a **single‑file, hard‑coded PoC** that demonstrates:

* A LangChain **agent** orchestrated with **LangChain Graph (RunnableGraph)**.
* A handful of **tools** (weather, solar‑yield, cost, transmission) that return **stubbed values**.
* A minimal **RAG pipeline** that answers follow‑up questions based on a *toy document* embedded in a local vector‑store.
* Everything runs locally; the LLM talks to an **Ollama/llama‑cpp** endpoint (or mocks if no GPU).

The end‑user should be able to ask:

> *"Is it feasible to build a 20 MW solar farm at 37.2 N, ‑121.9 W?"*
>
> *"What would it cost to deliver that power to San José, CA?"*

…and get coherent, cited, stub‑based answers.

---

## 2. Tech Stack

| Layer         | Choice                                       | Notes                                                           |
| ------------- | -------------------------------------------- | --------------------------------------------------------------- |
| LLM runtime   | **Ollama** with `mistral:7b-instruct-q4_K_M` | Fits in 12 GB VRAM; swap with llama‑cpp if needed.              |
| Orchestration | **LangChain Graph (RunnableGraph)**          | Clear, node‑based flow; easier than classic `initialize_agent`. |
| Vector DB     | **Chroma** (in‑memory)                       | One toy doc ⇒ no disk i/o required.                             |
| Embeddings    | `sentence-transformers/all-MiniLM-L6-v2`     | CPU‑only, \~80 MB.                                              |
| Tools         | `langchain.tools.@tool` decorators           | Each returns a hard‑coded value.                                |

---

## 3. Directory Structure

```
site_feasibility_agent/
├─ README.md                 # this document
├─ data/
│   └─ toy_grid_doc.txt      # 1‑2 paragraph text for RAG demo
├─ src/
│   ├─ tools.py              # all stubbed tools here
│   ├─ rag.py                # build vector‑store & RAG chain
│   └─ graph_agent.py        # glue everything with LangChain Graph
└─ requirements.txt
```

---

## 4. Setup Instructions

1. **Install Ollama** (if not already installed):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull the model**:
   ```bash
   ollama pull mistral:7b-instruct-q4_K_M
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the agent**:
   ```bash
   cd src
   python graph_agent.py
   ```

---

## 5. Example Usage

```python
from src.graph_agent import run_site_agent

# Question 1: Site feasibility
q1 = "Is it feasible to build a 20 MW solar farm at 37.2 N, -121.9 W?"
result1 = run_site_agent({"prompt": q1})
print(result1)

# Question 2: Transmission costs
q2 = "How much would it cost to deliver that power to San José, CA (37.3 N, -122.0 W)?"
result2 = run_site_agent({"prompt": q2})
print(result2)
```

---

## 6. Hard‑coded Data & Assumptions

* **Weather outlook** – fixed monthly GHI, temp values for any lat/lon (returned as CSV string).
* **Solar yield** – returns 1,600 kWh/kWp‑year × capacity.
* **Transmission cost** – flat \$0.03 per kWh per 100 km airline distance.
* **CapEx / OpEx** – \$1 M/MW CapEx, \$20 k/MW‑year OpEx.
* **Toy RAG document** – California ISO interconnection queue summary, 2023. 