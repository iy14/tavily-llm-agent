import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def summarize_content(state):
    """Summarize EACH search result into numbered points"""
    profession = state.get("profession", "professionals")
    content_type = state.get("content_type", "tools")  # "news" or "tools"

    # Get results from the appropriate field based on content_type
    if content_type == "news":
        results = state.get("news_results", [])
    else:  # tools
        results = state.get("tools_results", [])

    if not results:
        return {
            **state,
            f"{content_type}_summary": f"No recent AI {content_type} found.",
        }

    # Prepare content for OpenAI (max 5 results)
    search_content = ""
    for i, result in enumerate(results[:5], 1):
        search_content += f"\n{i}. {result.get('title', '')}\n"
        search_content += f"   {result.get('content', '')}\n"
        search_content += f"   Source: {result.get('url', '')}\n"

    prompt = f"""Based on the following search results about AI {content_type} for {profession}, 
create a numbered point for EACH result provided. Each point should be:
- Numbered sequentially (1., 2., 3., etc.)
- Concise but informative summary of that specific result
- Specifically relevant to {profession}
- Based SOLELY on the provided search results
- MUST end with exactly "read more at: [URL]" (plain text, no markdown links)

Create one numbered point for each of the {len(results[:5])} results provided.

Search Results:
{search_content}

Please provide your response as numbered points, one for each result, ensuring each point ends with exactly "read more at: [URL]" in plain text format:"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional AI {content_type} summarizer. Create one numbered point for each search result provided. Use plain text formatting only, no markdown links.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,  # Increased for more points
            temperature=0.3,
        )

        summary = response.choices[0].message.content.strip()
        return {f"{content_type}_summary": summary}

    except Exception as e:
        return {
            f"{content_type}_summary": f"Error summarizing {content_type}: {str(e)}"
        }


def select_top_points(state):
    """Select 5 most relevant and non-redundant points from both news and tools summaries"""
    profession = state.get("profession", "professionals")
    news_summary = state.get("news_summary", "")
    tools_summary = state.get("tools_summary", "")

    if not news_summary and not tools_summary:
        return {**state, "final_summary": "No relevant AI updates found."}

    # Combine all points
    all_points = f"""AI News Points:
{news_summary}

AI Tools Points:
{tools_summary}"""

    prompt = f"""From the following numbered points about AI news and tools for {profession}, 
select the MOST RELEVANT and important points for a {profession} looking for a general industry update.

Requirements:
- Choose AT MOST 5 points, but can be fewer if there isn't enough genuinely relevant information
- Only include points that are truly valuable and relevant to a {profession}
- No redundancy - avoid selecting points that cover similar topics
- Focus on practical value and actionable insights
- Re-number the selected points starting from 1.
- Keep the "read more at: [URL]" format exactly as provided (plain text, no markdown links)
- Mix news and tools based on relevance, not quota
- Quality over quantity - better to have 2-3 highly relevant points than 5 mediocre ones

All Available Points:
{all_points}

Please provide only the most relevant points (1-5 max), re-numbered sequentially, keeping the exact "read more at: [URL]" format:"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert curator selecting the most relevant AI updates for {profession}s. Focus on practical value and avoid redundancy. Use plain text formatting only, no markdown links.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.2,
        )

        final_summary = response.choices[0].message.content.strip()
        return {**state, "final_summary": final_summary}

    except Exception as e:
        return {**state, "final_summary": f"Error selecting top points: {str(e)}"}
