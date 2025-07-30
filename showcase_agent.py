from workflows.cached_newsletter import generate_newsletter_with_cache
from tools.url_extractor import extract_urls_from_newsletter, get_detailed_explanation

PROFESSION = "filmmaker"
TIME_PERIOD = "week"
POINT_TO_EXPLORE = 1  # Show deep dive for the first point

print("=== AI Profession Newsletter Agent Showcase ===\n")

# 1. Generate a newsletter for a profession and time period (should be fresh)
print(f"Generating newsletter for: {PROFESSION.title()} (last {TIME_PERIOD})\n")
result = generate_newsletter_with_cache(PROFESSION, TIME_PERIOD)
newsletter = result["newsletter"]
print("📰 AI NEWSLETTER:\n" + "=" * 60)
print(newsletter)
print(f"\n(Source: {result.get('source', 'unknown')})\n")

# 2. Generate again for the same profession/time (should be cache)
print(
    f"Generating newsletter again for: {PROFESSION.title()} (last {TIME_PERIOD}) to demonstrate caching...\n"
)
result_cached = generate_newsletter_with_cache(PROFESSION, TIME_PERIOD)
newsletter_cached = result_cached["newsletter"]
print("📰 AI NEWSLETTER (CACHED):\n" + "=" * 60)
print(newsletter_cached)
print(f"\n(Source: {result_cached.get('source', 'unknown')})\n")

# 3. Extract URLs and show which points are available for follow-up
detected_urls = extract_urls_from_newsletter(newsletter)
if not detected_urls:
    print("No points with URLs found for follow-up.")
else:
    print(
        f"Found {len(detected_urls)} points with URLs. Showing detailed explanation for point {POINT_TO_EXPLORE}...\n"
    )
    # 4. Get a detailed explanation for a specific point
    detailed = get_detailed_explanation(newsletter, POINT_TO_EXPLORE, PROFESSION)
    if detailed["success"]:
        print("📖 DETAILED EXPLANATION:")
        print(f"Point {POINT_TO_EXPLORE} - {detailed['url']}")
        print("-" * 60)
        print(detailed["detailed_explanation"])
    else:
        print(f"❌ Could not get detailed explanation: {detailed['error']}")
        if "url" in detailed:
            print(f"URL: {detailed['url']}")

print("\n=== END OF SHOWCASE ===")
