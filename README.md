# Site Feasibility Agent

## 1. Purpose

This project demonstrates an AI agent for solar site feasibility analysis. It showcases:

*   An agent orchestrated with **LangChain**.
*   A set of **tools** (weather, solar-yield, cost, transmission, grid info). Currently, these are primarily **stubbed values**, but the framework allows for easy integration of real APIs.
*   A **RAG (Retrieval Augmented Generation) pipeline** using a local vector store (ChromaDB) and a small document set to answer contextual questions.
*   LLM interaction via **Hugging Face Transformers** (e.g., with `microsoft/phi-2` or other compatible models) or a mock LLM if issues arise.
*   A structured project layout with configuration management, logging, and a CLI entry point.

This system is designed to assist in the initial stages of evaluating potential solar energy project sites by integrating various data points and providing AI-generated summaries.

---

## 2. Tech Stack

| Layer                 | Choice                                           | Notes                                                                 |
| --------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| LLM Runtime           | **Hugging Face Transformers** (`microsoft/phi-2` default) | Runs models locally. Mock LLM available.                              |
| Core Framework        | **LangChain**                                    | For agent structure, tool integration, RAG.                         |
| Vector DB             | **Chroma** (in-memory)                           | For RAG.                                                              |
| Embeddings            | `sentence-transformers/all-MiniLM-L6-v2`         | For RAG, runs on CPU.                                               |
| Configuration         | YAML (`config/config.yaml`) & `.env`             | For managing settings and API keys.                                   |
| Logging               | Python `logging` module                          | Centralized logging setup.                                            |
| CLI                   | Python `argparse`                                | For application interaction.                                          |

---

## 3. Project Structure

```
ai-agent-project/
├── config/                     # Configuration files
│   └── config.yaml             # Main configuration (LLM, RAG, tools defaults)
├── data/                       # Data files for RAG or tools
│   └── toy_grid_doc.txt        # Example document for RAG
├── src/                        # Source code
│   ├── __init__.py
│   ├── agent/                  # Core agent logic
│   │   ├── __init__.py
│   │   └── agent_core.py       # Main SiteFeasibilityAgent class
│   ├── llm/                    # LLM loading and interaction
│   │   ├── __init__.py
│   │   └── llm_loader.py       # Loads Hugging Face or Mock LLM
│   ├── rag/                    # RAG pipeline components
│   │   ├── __init__.py
│   │   └── rag_pipeline.py     # SiteFeasibilityRAG class
│   ├── tools/                  # Agent tools
│   │   ├── __init__.py
│   │   └── stubbed_tools.py    # Current stubbed tool implementations
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration loader
│   │   └── logging_config.py   # Logging setup
│   └── app_main.py             # Main application CLI entry point
├── tests/                      # Unit and integration tests (to be added)
│   └── __init__.py
├── .gitignore                  # Specifies intentionally untracked files
├── LICENSE                     # Project license (MIT)
├── README.md                   # This document
└── requirements.txt            # Python dependencies
```

---

## 4. Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/VaradhKaushik/ai-agent-project.git
    cd ai-agent-project
    ```

2.  **Set up a Python virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    This will install `transformers`, `torch`, and other necessary libraries. The first time you run the agent with a new Hugging Face model (specified in `config/config.yaml`), it will be downloaded automatically. This download process may take some time depending on the model size and your internet connection.

4.  **Configure Environment Variables (Optional):**
    *   Create a `.env` file in the `config/` directory if you need to add API keys for future tool integrations:
        ```bash
        touch config/.env
        ```
    *   Add any necessary API keys if you integrate tools that require them (e.g., `WEATHER_API_KEY=your_key_here`).

5.  **Review Configuration (`config/config.yaml`):**
    *   The primary LLM provider can be set to `huggingface` or `mock`. By default, it's set to `mock` for quick testing.
    *   The default Hugging Face model is `microsoft/phi-2`. You can change `llm.huggingface_model_id` in `config/config.yaml` to use other compatible models from the Hugging Face Hub (e.g., `gpt2`, `distilgpt2`, `google/flan-t5-base`). Be mindful of model size for local execution, as larger models require more resources (RAM/VRAM) and will be slower on CPU.
    *   To use the mock LLM (recommended for quick testing without model downloads), ensure `llm.provider: "mock"` in `config/config.yaml`.
    *   Review other settings for RAG, tools, and logging if needed.

---

## 5. Running the Agent

To run the agent, navigate to the project's root directory (`ai-agent-project/`) in your terminal.
Then use the following commands:

*   **Interactive Mode:**
    ```bash
    python -m src.app_main --interactive
    ```
    If no arguments are provided, it also defaults to interactive mode:
    ```bash
    python -m src.app_main
    ```

*   **Single Query Mode:**
    ```bash
    python -m src.app_main --query "Your question here?"
    ```

*   **Demo Mode (Predefined Queries):**
    ```bash
    python -m src.app_main --demo
    ```

---

## 6. Key Data & Assumptions (Current Stubbed Implementation)

*   **Weather Outlook (`stubbed_tools.py`):** Fixed monthly GHI, temp values (CSV string).
*   **Solar Yield (`stubbed_tools.py`):** Returns a value based on a fixed 1600 kWh/kWp-year specific yield multiplied by capacity.
*   **Cost Model (`stubbed_tools.py`):** Fixed $1M/MW CapEx, $20k/MW-year OpEx by default.
*   **Transmission Cost (`stubbed_tools.py`):** Uses Haversine distance and a flat $0.03/kWh/100km cost by default.
*   **Grid Connection Info (`stubbed_tools.py`):** Returns stubbed regional info based on coarse lat/lon bucketing.
*   **RAG Document (`data/toy_grid_doc.txt`):** A small text file for RAG demonstration.

---

## 7. Dependencies

The project uses the following key dependencies (see `requirements.txt` for complete list):

*   **LangChain** (0.1.0) - Core framework for agent orchestration
*   **Transformers** (4.36.2) - Hugging Face model loading
*   **ChromaDB** (0.4.22) - Vector database for RAG
*   **Sentence Transformers** (2.2.2) - Embeddings for RAG
*   **PyTorch** (2.1.2) - ML framework for model inference
*   **PyYAML** (6.0.1) - Configuration file parsing
*   **Python-dotenv** (1.0.1) - Environment variable management

---

## 8. Potential Future Enhancements

This project serves as a foundation. Potential areas for future development include:

*   **Integration of Real APIs:** Replace more stubbed tools with calls to actual external APIs.
*   **Expanded RAG Document Set:** Utilize a more diverse and larger set of documents for the RAG pipeline.
*   **Implementation of Robust Unit & Integration Tests:** Add comprehensive tests in the `tests/` directory.
*   **Advanced Error Handling & Resilience:** Further improve error handling.
*   **Asynchronous Operations:** For tools involving network calls, implement asynchronous operations.
*   **Service-Oriented Architecture:** Expose the agent via a REST API (e.g., using FastAPI).
*   **Evaluation Framework:** Develop a systematic framework to evaluate and improve agent responses.
*   **User Interface:** Create a simple web-based UI.
*   **Support for More Data Sources:** Extend tool capabilities for grid planning.
*   **Sophisticated Cost Modeling:** Enhance cost models. 