# Solar Feasibility Agent

## 1. Purpose

This project demonstrates an AI agent for solar site feasibility analysis. It showcases:

*   An agent orchestrated with **LangChain**, leveraging OpenAI's `gpt-3.5-turbo` for tool calling and reasoning.
*   A set of **tools** including real API integrations (NREL, OpenWeatherMap, Geocoding, Web Search) and some helper/stubbed tools for cost and grid information.
*   A structured project layout with configuration management, logging, and a CLI entry point.

This system is designed to assist in the initial stages of evaluating potential solar energy project sites by intelligently invoking tools to gather data and provide AI-generated feasibility summaries.

---

## Highlight on Tools

This project features a range of tools to showcase a comprehensive solar feasibility analysis. Here's a breakdown:

**Implemented & Functional Tools (Real Data/APIs):**
*   **`web_search`**: Leverages DuckDuckGo for general web searches and up-to-date information.
*   **`nrel_solar_data`**: Integrates with the NREL API to fetch crucial solar irradiance data. Includes fallback estimations.
*   **`real_solar_calculator`**: Performs calculations for potential solar energy production based on location, system capacity, and NREL data.
*   **`openweathermap_data`**: Connects to OpenWeatherMap API for current weather conditions, with fallback mechanisms.
*   **`geocode_location`**: Utilizes Nominatim (OpenStreetMap) for converting textual location descriptions into precise geographic coordinates.
*   **`energy_news_search`**: A specialized tool for finding recent news within the energy sector.
*   **`market_analysis_search`**: Designed to search for market analysis reports and regulatory information relevant to solar projects.

**Placeholder/Stubbed Tools (Illustrative):**
These tools are currently implemented with simplified or dummy logic to demonstrate the agent's capability to integrate with a broader set of functionalities. They represent areas for future development with real data sources or more complex models.
*   **`cost_model`**: Provides placeholder estimates for capital (CapEx) and operational expenditures (OpEx).
*   **`transmission_cost`**: Offers stubbed estimations for the costs associated with electricity transmission.
*   **`grid_connection_info`**: Returns illustrative information regarding grid connection feasibility and requirements.

This blend of operational and conceptual tools allows for a realistic demonstration of an AI agent's potential in the renewable energy domain, while also highlighting pathways for future enhancement.

---

## 2. Tech Stack

| Layer                 | Choice                                           | Notes                                                                 |
| --------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| LLM                   | **OpenAI `gpt-3.5-turbo`**                       | Utilized for its strong tool-calling and reasoning capabilities.      |
| Core Framework        | **LangChain**                                    | For agent structure, tool integration, and prompt management.         |
| API Tools             | NREL, OpenWeatherMap, DuckDuckGo, Nominatim      | For solar data, weather, web search, geocoding.                       |
| Helper/Stubbed Tools  | Cost Model, Transmission, Grid Info              | Provide estimates for financial and grid aspects.                     |
| Vector DB             | **Chroma** (in-memory)                           | For RAG (if RAG components are actively used).                        |
| Embeddings            | `sentence-transformers/all-MiniLM-L6-v2`         | For RAG (if RAG components are actively used).                        |
| Configuration         | YAML (`config/config.yaml`) & `.env` (root)      | For managing settings and API keys.                                   |
| Logging               | Python `logging` module                          | Centralized logging setup.                                            |
| CLI                   | Python `argparse`                                | For application interaction.                                          |

---

## 3. Project Structure

```
ai-agent-project/
├── config/                     # Configuration files
│   └── config.yaml             # Main configuration (LLM, tools defaults)
├── data/                       # Data files for RAG or tools (if used)
│   └── toy_grid_doc.txt        # Example document for RAG
├── src/                        # Source code
│   ├── __init__.py
│   ├── agent/                  # Core agent logic
│   │   ├── __init__.py
│   │   └── agent_core.py       # SolarFeasibilityAgent class
│   ├── llm/                    # LLM loading and interaction
│   │   ├── __init__.py
│   │   └── llm_loader.py       # Loads the OpenAI LLM
│   ├── rag/                    # RAG pipeline components (if used)
│   │   ├── __init__.py
│   │   └── rag_pipeline.py     # RAG class
│   ├── tools/                  # Agent tools
│   │   ├── __init__.py
│   │   ├── api_tools.py        # Tools interacting with external APIs
│   │   └── stubbed_tools.py    # Stubbed or simplified tool implementations
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration loader
│   │   └── logging_config.py   # Logging setup
│   └── app_main.py             # Main application CLI entry point
├── tests/                      # Unit and integration tests (to be added)
│   └── __init__.py
├── .env                        # Environment variables (e.g., API keys) - ROOT LEVEL
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
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Create a `.env` file in the **project root directory**:
        ```bash
        touch .env
        ```
    *   Add your OpenAI API key and any other necessary API keys to this `.env` file:
        ```env
        OPENAI_API_KEY="your_openai_api_key_here"
        # NREL_API_KEY="your_nrel_api_key_here" # Optional, for more accurate solar data
        # OPENWEATHERMAP_API_KEY="your_openweathermap_api_key_here" # Optional, for more detailed weather
        ```
        The agent can function with estimated data if NREL or OpenWeatherMap keys are not provided, but real API keys are recommended for accuracy.

5.  **Review Configuration (`config/config.yaml`):**
    *   The LLM provider is now primarily OpenAI.
    *   You can adjust tool-specific default parameters in `config.yaml` if needed.

---

## Recommended Way to Run

For the application to correctly resolve all internal module imports, it's best to run it as a package from the project's root directory.

*   **Interactive Mode (Recommended):**
    ```bash
    python -m src.app_main --interactive
    ```
    This command tells Python to run the `app_main` module located within the `src` package.

---

## RAG Quick Start (New)

To use the RAG capabilities with the two NREL PDFs:

1.  **Ensure PDFs are in `data/source_docs/`**:
    - `60272.pdf` (PVWatts v5 Technical Manual)
    - `86621.pdf` (U.S. Solar PV System & Storage Cost Benchmarks Q1 2023)
    *(You may need to download these manually and place them in the specified directory)*

2.  **Install dependencies (if you haven't already):**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ingest documents into ChromaDB (one-time setup per document set):**
    ```bash
    python -m scripts.ingest_docs
    ```
    This will process the PDFs and create a local vector store in `data/chroma/`.

4.  **Query using the RAG-enabled agent:**
    The `rag_lookup` tool will be automatically used by the agent if your query is best answered by the ingested documents.

    *   **Using a specific query (from project root):**
        ```bash
        python -m src.app_main --query "What is the BOS cost per watt in 2023?"
        ```
    *   **In interactive mode (from project root):**
        ```bash
        python -m src.app_main --interactive
        ```
        Then, when prompted, enter your query:
        ```
        Your Query: What is the BOS cost per watt in 2023
        ```

    **Example RAG Interaction:**

    When you run the agent with a query like "What is the BOS cost per watt in 2023" or "what is Plane-of-Array Irradiance?", you should see output similar to this (log details and exact LLM responses may vary):

    ```
    (.venv) varadh@DESKTOP-HF5G2UF:~/Project/ai-agent-project$ python -m src.app_main --interactive
    /home/varadh/Project/ai-agent-project/agent/tools/rag_tool.py:16: LangChainDeprecationWarning: The method `Chain.run` was deprecated in langchain 0.1.0 and will be removed in 1.0. Use :meth:`~invoke` instead.
      return rag_chain.run(query)

    I'm sorry, I cannot accurately answer this question as I do not have enough information about the BOS (balance of system) cost trends in the solar industry for the year 2023. It is best to consult a solar industry expert or do further research on projected BOS cost trends for a more accurate answer.I don't have specific data on the BOS (balance of system) cost per watt in 2023. It's recommended to consult a solar industry expert or conduct further research on projected BOS cost trends for accurate information.

    > Finished chain.
    2025-05-30 13:03:39,297 - src.agent.agent_core - INFO - LLM analysis completed successfully. Response length: 215

    Agent Response:
    I don't have specific data on the BOS (balance of system) cost per watt in 2023. It's recommended to consult a solar industry expert or conduct further research on projected BOS cost trends for accurate information.

    Your Query: what is Plane-of-Array Irradiance?
    2025-05-30 13:04:15,915 - __main__ - INFO - Interactive query: what is Plane-of-Array Irradiance?
    2025-05-30 13:04:15,916 - src.agent.agent_core - INFO - Starting LLM-driven analysis for query: what is Plane-of-Array Irradiance?


    > Entering new AgentExecutor chain...

    Invoking: `rag_lookup` with `Plane-of-Array Irradiance`


     The plane-of-array irradiance is the total amount of solar irradiance that hits the surface of a solar panel. It is calculated by summing the beam, diffuse, and ground-reflected components of irradiance using a specific algorithm.**FEASIBILITY ANALYSIS**

    **Location & Solar Resource:**
    The plane-of-array irradiance represents the total solar irradiance that hits the surface of a solar panel, crucial for determining the energy production potential of a solar system.

    **Technical Assessment:**
    Understanding the plane-of-array irradiance is essential for accurate solar energy production estimates and system design.

    **Financial Analysis:**
    It impacts the efficiency and output of a solar system, influencing the financial returns and payback period of the project.

    **Market Conditions:**
    Knowledge of the plane-of-array irradiance helps in assessing the competitiveness and viability of solar projects in different locations.

    **Recommendation:**
    Consider the plane-of-array irradiance data in the design and evaluation of solar projects to optimize energy production and financial returns.

    > Finished chain.
    2025-_05-30 13:04:20,562 - src.agent.agent_core - INFO - LLM analysis completed successfully. Response length: 866

    Agent Response:
    **FEASIBILITY ANALYSIS**

    **Location & Solar Resource:**
    The plane-of-array irradiance represents the total solar irradiance that hits the surface of a solar panel, crucial for determining the energy production potential of a solar system.

    **Technical Assessment:**
    Understanding the plane-of-array irradiance is essential for accurate solar energy production estimates and system design.

    **Financial Analysis:**
    It impacts the efficiency and output of a solar system, influencing the financial returns and payback period of the project.

    **Market Conditions:**
    Knowledge of the plane-of-array irradiance helps in assessing the competitiveness and viability of solar projects in different locations.

    **Recommendation:**
    Consider the plane-of-array irradiance data in the design and evaluation of solar projects to optimize energy production and financial returns.

    Your Query: quit
    2025-05-30 13:04:44,772 - __main__ - INFO - Exiting interactive mode.
    2025-05-30 13:04:44,773 - __main__ - INFO - Solar Feasibility Agent Application Finished.
    ```

---

## 5. Running the Agent

To run the agent, navigate to the project's root directory (`ai-agent-project/`) in your terminal.
Always use the `python -m src.app_main` command to ensure modules are loaded correctly.

*   **Interactive Mode (Recommended):**
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

## 6. Agent Capabilities & Tools

The agent leverages a suite of tools to gather information and perform analysis. The primary tools currently include:

*   **`web_search`**: Uses DuckDuckGo to find general information and recent news.
*   **`nrel_solar_data`**: Fetches solar irradiance data from NREL (National Renewable Energy Laboratory) API. Falls back to estimations if API key is missing or fails.
*   **`real_solar_calculator`**: Calculates potential solar energy production based on location, capacity, and NREL solar data.
*   **`openweathermap_data`**: Retrieves current weather conditions from OpenWeatherMap API. Falls back to an alternative source if API key is missing.
*   **`geocode_location`**: Converts location names (e.g., "Austin, Texas") into geographic coordinates (latitude, longitude) using Nominatim (OpenStreetMap).
*   **`energy_news_search`**: A specialized search for recent energy industry news.
*   **`market_analysis_search`**: Searches for market analysis and regulatory information.
*   **`cost_model` (Stubbed)**: Provides estimated capital and operational expenditures based on project capacity.
*   **`transmission_cost` (Stubbed)**: Estimates transmission costs based on distance and energy.
*   **`grid_connection_info` (Stubbed)**: Returns stubbed information about grid connection.

The agent intelligently selects which tool(s) to use based on the user's query.

---

## 7. Demo Interaction

Here's an example of the agent responding to a query and the tools it invokes:

**User Query:** `Is it feasible to build a solar power station at 37.2, -121.9?`

**Agent Execution Log (summary):**
```
> Entering new AgentExecutor chain...

Invoking: `nrel_solar_data` with `{\'lat\': 37.2, \'lon\': -121.9}`
[NREL API call, falls back to estimation due to missing API key in this demo]
--> Output: 
**Estimated Solar Resource Data for (37.2, -121.9)**
Note: These are rough estimates. For accurate data, sign up for a free NREL API key.
Average Global Horizontal Irradiance: ~4.5 kWh/m²/day
Average Direct Normal Irradiance: ~5.5 kWh/m²/day
Latitude zone: 37.2° (mid-latitude)

Invoking: `real_solar_calculator` with `{\'lat\': 37.2, \'lon\': -121.9, \'capacity_mw\': 10}` 
[Calls nrel_solar_data internally, then calculates]
--> Output:
**Real Solar Production Analysis**
Location: (37.2, -121.9)
System Size: 10.0 MW AC (12.0 MW DC)
Panel Tilt: 37.2°
**Solar Resource:**
Annual GHI: 5.00 kWh/m²/day (Note: Uses a default/fallback if NREL direct value extraction fails)
**Performance Estimates:**
Year 1 Production: 18,615 MWh
Capacity Factor: 21.25%
Specific Yield: 1,861,500 kWh/kWp
25-Year Total: 437,452 MWh
**System Assumptions:**
DC/AC Ratio: 1.2
System Efficiency: 85.0%
Annual Degradation: 0.5%

Invoking: `cost_model` with `{\'ac_mw\': 10}`
--> Output: (10.0, 0.2) (Represents $10M CapEx, $0.2M/yr OpEx)

> Finished chain.
```

**Final Agent Response:**
```
**FEASIBILITY ANALYSIS**

**Location & Solar Resource:**
The location at (37.2, -121.9) has an average Global Horizontal Irradiance of approximately 4.5 kWh/m²/day, making it suitable for solar energy generation.

**Technical Assessment:**
- System Size: 10.0 MW AC (12.0 MW DC)
- Year 1 Production: 18,615 MWh
- 25-Year Total Production: 437,452 MWh
- Capacity Factor: 21.25%
- Specific Yield: 1,861,500 kWh/kWp

**Financial Analysis:**
- Capital Cost: $10 million
- Operating Cost: $0.2 million/year
- Payback Period: Calculated based on specific financial parameters

**Market Conditions:**
Further market analysis and incentives specific to the location are recommended to assess the economic viability comprehensively.

**Recommendation:**
Based on the solar potential, technical assessment, and initial cost estimates, building a 10 MW solar power station at (37.2, -121.9) is feasible. Conduct a detailed financial analysis and market research to determine the project\'s profitability and consider available incentives for solar projects in the area.
```
*(Note: The `real_solar_calculator`'s Capacity Factor and Specific Yield in the live demo output seem unusually high. This might indicate an issue in the tool's internal calculation or units that needs review. The GHI used by `real_solar_calculator` also defaulted to 5.00 despite NREL tool estimating 4.5, suggesting a parsing/fallback path was taken.)*


---

## 8. Dependencies

The project uses the following key dependencies (see `requirements.txt` for complete list):

*   **LangChain** (`langchain~=0.3.25`, `langchain-core~=0.3.63`) - Core framework.
*   **`langchain-openai`** (`~=0.3.18`) - OpenAI integration for LangChain.
*   **`openai`** (`~=1.82.1`) - Official OpenAI Python client.
*   **ChromaDB** (`~=0.4.22`) - Vector database for RAG (if used).
*   **Sentence Transformers** (`~=2.2.2`) - Embeddings for RAG (if used).
*   **PyYAML** (`~=6.0.1`) - Configuration file parsing.
*   **Python-dotenv** (`~=1.0.1`) - Environment variable management.
*   **Requests** (`~=2.31.0`) - For making HTTP requests in API tools.

---

## 9. Potential Future Enhancements

This project serves as a foundation. Potential areas for future development include:

*   **Refine Tool Calculations:** Review and improve the accuracy of tools like `real_solar_calculator`.
*   **Full API Integration for All Tools:** Replace any remaining stubbed logic with robust API calls.
*   **Expanded RAG Document Set:** If RAG is a focus, utilize a more diverse and larger set of documents.
*   **Implementation of Robust Unit & Integration Tests.**
*   **Advanced Error Handling & Resilience.**
*   **Asynchronous Operations for all API tools.**
*   **Service-Oriented Architecture (e.g., FastAPI).**
*   **Evaluation Framework for agent responses.**
*   **User Interface.**
*   **Sophisticated Financial Modeling:** More detailed payback period, LCOE, etc.
``` 