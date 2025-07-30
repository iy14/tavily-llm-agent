from .ai_newsletter_graph import build_graph
from tools.cache import get_cached_newsletter, cache_newsletter, get_cache_stats


def generate_newsletter_with_cache(profession: str, time_period: str = "day") -> dict:
    """
    Generate newsletter with Redis caching

    Args:
        profession: Target profession (e.g., "filmmaker", "musician")
        time_period: Time range - "day", "week", or "month"

    Returns:
        dict with newsletter and cache info
    """

    # Check cache first
    cached_newsletter = get_cached_newsletter(profession, time_period)
    if cached_newsletter:
        return {
            "newsletter": cached_newsletter,
            "source": "cache",
            "profession": profession,
            "time_period": time_period,
        }

    # Cache miss - generate new newsletter
    print(f"🔄 Generating fresh newsletter for {profession} ({time_period})")

    try:
        # Build and run the workflow
        graph = build_graph()
        result = graph.invoke({"profession": profession, "time_period": time_period})

        newsletter = result.get("newsletter", "")

        if newsletter:
            # Cache the result
            cache_newsletter(profession, time_period, newsletter)

            return {
                "newsletter": newsletter,
                "source": "fresh",
                "profession": profession,
                "time_period": time_period,
                "final_summary": result.get("final_summary", ""),
                "summaries": result.get("summaries", []),
            }
        else:
            return {
                "newsletter": "Error generating newsletter",
                "source": "error",
                "profession": profession,
                "time_period": time_period,
            }

    except Exception as e:
        print(f"❌ Error generating newsletter: {e}")
        return {
            "newsletter": f"Error generating newsletter: {str(e)}",
            "source": "error",
            "profession": profession,
            "time_period": time_period,
        }


def get_newsletter_cache_info() -> dict:
    """Get cache statistics for monitoring"""
    return get_cache_stats()
