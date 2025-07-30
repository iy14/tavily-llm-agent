# AI Profession Newsletter Agent

## Overview

The AI Profession Newsletter Agent is an interactive agent that delivers the latest, most relevant AI updates for a given profession (e.g. accountant, doctor, musician). It leverages real-time web search, LLM summarization, and follow-up features to provide professionals with actionable, up-to-date insights.

## Video of the agent in action, running locally in my environment: 
https://drive.google.com/file/d/1EAMOEIfg7WXEKy953295UiR25haDYvvA/view?usp=sharing

---

## Features
- **Profession-aware**: Accepts any profession (with smart, lenient validation and typo correction)
- **Time range selection**: Choose day, week, or month for news recency
- **Parallel RAG workflow**: Simultaneously searches for both profession-relevant news and tools using Tavily search
- **Quality filtering**: Only includes results with a relevance score > 0.5
- **LLM Summarization**: Uses OpenAI to create concise, numbered summaries and detailed follow-ups
- **Caching**: Uses Redis Cloud for fast, cost-effective repeat queries
- **Interactive follow-up**: Users can request deep dives on any point in the newsletter, with full-article extraction using Tavily extract and summary using OpenAI.
- **Graceful interactive flow**: Always offers a clear next step, even on failures or insufficient results

---

## Setup & Running

### 1. Clone the Repository
```bash
git clone https://github.com/iy14/tavily-llm-agent.git
cd tavily-llm-agent
```

### 2. Set up virtual environment
    ```bash
    python -m venv .venv-tavily-llm-agent
    source .venv-tavily-llm-agent/bin/activate
    ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Rename `env.example` to `.env` and fill in your API keys:
```
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
REDIS_URL=redis://default:1Yyucr7QcxaIRCDnwrXGVyWVdpYwfgig@redis-13531.c250.eu-central-1-1.ec2.redns.redis-cloud.com:13531 (provided)
```

### 5. Run the Interactive Agent from the root
```bash
python main.py
```

### 6. Or run a simple script which showcases the agent's capabilities
```bash
python showcase_agent.py
```

---

## Design Decisions & RAG Architecture

### Retrieval-Augmented Generation (RAG)
- **Retrieval**: Uses Tavily API to fetch the latest, high-quality news and tools for the selected profession and time period.
- **Filtering**: Only results with a relevance score > 0.5 are considered, ensuring quality and relevance.
- **Augmentation**: Results are summarized and merged by OpenAI, producing a concise, profession-specific newsletter.
- **Generation**: The agent generates both high-level summaries and, on demand, detailed explanations by extracting and analyzing full articles.

### Parallel Workflow
- News and tools searches are run in parallel for speed and efficiency (using LangGraph's parallel state collection).
- Summaries are generated independently, then merged and deduplicated for the final output.

### Caching
- Redis Cloud is used to cache newsletters by profession and time period, reducing API costs and improving response time for repeat queries.
- Automatic cache expiration is tuned to the time period (8h for day, 2d for week, 1w for month). Users can also request a fresh search.

### Profession Validation
- An LLM-powered validator ensures that almost any plausible profession is accepted, while filtering out obvious non-professions and handling typos.

### Follow-up & Deep Dives
- Users can select any newsletter point for a detailed explanation.
- The agent extracts the full article using Tavily and generates a comprehensive, profession-specific summary with OpenAI.
- All errors (e.g., failed extraction) are handled gracefully, with clear user feedback.

---

## Example User Flow
```
🤖 AI Newsletter Agent
============================================================
Welcome! I'm your AI Newsletter Agent.
I curate the latest AI news and tools specifically for your profession.

🎯 What's your profession? filmmaker
✅ Great! Using profession: filmmaker

⏰ Choose your time range:
1. Day (last 24 hours)

🔍 Searching for the latest AI updates for filmmakers...

📰 YOUR AI NEWSLETTER
============================================================
1. Latest AI video editing tools... read more at: https://example.com
2. New AI-powered story generation... read more at: https://example2.com

What would you like to do next?
a) Ask about another profession
b) Generate fresh results  
c) Get more info on one of the points

>> c
📋 This newsletter has 2 points with additional information available.
Enter point number (1-2) [q to go back]: 1

🔍 Getting detailed information for point 1...

📖 DETAILED EXPLANATION - Point 1
==============================================================================
🔗 Source: https://example.com
[Comprehensive analysis tailored for your profession...]
```
