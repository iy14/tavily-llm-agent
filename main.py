from workflows.cached_newsletter import (
    generate_newsletter_with_cache,
    get_newsletter_cache_info,
)


def run_cache_demo():
    """Run the original cache demonstration"""
    print("=== CACHE DEMO ===")
    # Test the cached newsletter generation
    profession = "filmmaker"
    time_period = "day"

    print("=== First Request (Should be Cache MISS) ===")
    result1 = generate_newsletter_with_cache(profession, time_period)
    print(f"Source: {result1['source']}")
    print("Newsletter:")
    print(result1["newsletter"])

    print("\n=== Second Request (Should be Cache HIT) ===")
    result2 = generate_newsletter_with_cache(profession, time_period)
    print(f"Source: {result2['source']}")
    print("Newsletter:")
    print(result2["newsletter"])

    print("\n=== Cache Statistics ===")
    cache_stats = get_newsletter_cache_info()
    print(cache_stats)

    # Test different time period (should be cache miss)
    print("\n=== Different Time Period (Should be Cache MISS) ===")
    result3 = generate_newsletter_with_cache(profession, "week")
    print(f"Source: {result3['source']}")
    print("Newsletter:")
    print(result3["newsletter"])


if __name__ == "__main__":
    print("🤖 AI Newsletter Agent")
    print("=" * 40)
    print("Choose how to run:")
    print("1. Interactive Agent (full experience)")
    print("2. Cache Demo (for testing)")

    while True:
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == "1":
            print("\n🚀 Starting Interactive Agent...")
            print("Run: python interactive_agent.py")
            print("\nOr you can run it directly from here:")

            from interactive_agent import main as interactive_main

            interactive_main()
            break
        elif choice == "2":
            run_cache_demo()
            break
        else:
            print("Please enter 1 or 2.")
