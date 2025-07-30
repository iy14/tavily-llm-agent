import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

tavily_client = TavilyClient(TAVILY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def extract_urls_from_newsletter(newsletter_text: str) -> dict:
    """Extract URLs from newsletter points and map them to point numbers"""
    url_pattern = r"read more at: (https?://[^\s\)]+)"
    urls = re.findall(url_pattern, newsletter_text, re.IGNORECASE)

    # Map URLs to point numbers (assuming sequential order)
    url_map = {}
    for i, url in enumerate(urls, 1):
        url_map[i] = url

    return url_map


def extract_url_content(url: str) -> dict:
    """Extract content from a specific URL using Tavily extract"""
    try:
        response = tavily_client.extract(
            urls=[url], extract_depth="advanced", format="text"
        )

        if response.get("results") and len(response["results"]) > 0:
            result = response["results"][0]
            return {
                "success": True,
                "content": result.get("raw_content", ""),
                "url": result.get("url", url),
            }
        else:
            return {"success": False, "error": "No content extracted", "url": url}

    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def generate_detailed_summary(url: str, content: str, profession: str) -> str:
    """Generate a detailed summary of extracted content using OpenAI"""

    # Truncate content if too long (keep first 8000 chars for context)
    if len(content) > 8000:
        content = content[:8000] + "... [content truncated]"

    prompt = f"""Based on the following article content, provide a detailed and thorough explanation specifically for a {profession}. 

Focus on:
- Key insights and takeaways relevant to {profession}s
- Practical applications and implications
- Important details and context
- How this relates to their work or industry

Keep the explanation comprehensive but accessible. Use clear paragraphs and structure.

Article URL: {url}

Article Content:
{content}

Please provide a detailed explanation:"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert analyst providing detailed explanations for {profession}s. Be thorough and insightful while remaining accessible.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error generating detailed summary: {str(e)}"


def get_detailed_explanation(
    newsletter_text: str, point_number: int, profession: str
) -> dict:
    """Get detailed explanation for a specific point from the newsletter"""

    # Extract URLs from newsletter
    url_map = extract_urls_from_newsletter(newsletter_text)

    if point_number not in url_map:
        return {
            "success": False,
            "error": f"Point {point_number} not found or doesn't have a URL.",
        }

    url = url_map[point_number]

    # Extract content from URL
    extraction_result = extract_url_content(url)

    if not extraction_result["success"]:
        return {
            "success": False,
            "error": f"Failed to extract content from {url}. {extraction_result.get('error', '')}",
            "url": url,
        }

    # Generate detailed summary
    detailed_summary = generate_detailed_summary(
        url, extraction_result["content"], profession
    )

    return {
        "success": True,
        "url": url,
        "detailed_explanation": detailed_summary,
        "point_number": point_number,
    }
