# llm-tavily-agent

A modular LLM agent built with [Langraph](https://github.com/langraph/langraph) and [Tavily](https://www.tavily.com/) (RAG) integration.

This agent generates a short, curated **AI newsletter** tailored to the user’s profession (e.g. software engineer, filmmaker, musician). It searches the web for relevant updates using Tavily, then summarizes them using an LLM.

---

## 🚀 Quickstart

1. **Clone the repo:**
    ```bash
    git clone https://github.com/<your-username>/llm-tavily-agent.git
    cd llm-tavily-agent
    ```

2. **Set up environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Create your `.env` file:**
    ```bash
    cp .env.example .env
    ```
    Add your API keys to `.env`:
    ```
    TAVILY_API_KEY=your_key
    OPENAI_API_KEY=your_key  # if/when LLM is used
    ```

4. **Run the agent:**
    ```bash
    python workflows/ai_newsletter_graph.py
    ```

---

## 📌 Use Case

Users enter a profession like:

> `"software engineer"`

The agent will:
- 🔍 Use **Tavily** to search for the latest AI-related updates in that field
- 🧠 Use an **LLM** to summarize results into a short, readable newsletter
- 📬 Return the newsletter text to the user

---

## 📂 Project Structure

llm-tavily-agent/
├── workflows/
│ └── ai_newsletter_graph.py # Langraph workflow definition
├── tools/
│ └── tavily.py # Tavily API integration
├── .env.example
├── requirements.txt
└── README.md