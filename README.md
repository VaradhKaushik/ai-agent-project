# Solar Feasibility Agent

## 1. Purpose

This project demonstrates an AI agent for solar site feasibility analysis. It showcases:

*   An agent orchestrated with **LangChain**, leveraging OpenAI's `gpt-3.5-turbo` for tool calling and reasoning.
*   A set of **tools** including real API integrations (NREL, OpenWeatherMap, Geocoding, Web Search) and some helper/stubbed tools for cost and grid information.
*   A structured project layout with configuration management, logging, and a CLI entry point.

This system is designed to assist in the initial stages of evaluating potential solar energy project sites by intelligently invoking tools to gather data and provide AI-generated feasibility summaries.

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

## 5. Running the Agent

To run the agent, navigate to the project's root directory (`ai-agent-project/`) in your terminal.
Then use the following commands:

*   **Interactive Mode:**
    ```bash
    python src/app_main.py --interactive
    ```
    If no arguments are provided, it also defaults to interactive mode:
    ```bash
    python src/app_main.py
    ```

*   **Single Query Mode:**
    ```bash
    python src/app_main.py --query "Your question here?"
    ```

*   **Demo Mode (Predefined Queries):**
    ```bash
    python src/app_main.py --demo
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