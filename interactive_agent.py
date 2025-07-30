import time
from workflows.cached_newsletter import generate_newsletter_with_cache
from tools.cache import clear_cache_for_profession, get_cache_key, redis_client


def print_welcome():
    """Display welcome message and agent introduction"""
    print("=" * 60)
    print("🤖 AI Newsletter Agent")
    print("=" * 60)
    print()
    print("Welcome! I'm your AI Newsletter Agent.")
    print("I curate the latest AI news and tools specifically for your profession.")
    print()
    print("Here's what I do:")
    print("• Search for the latest AI news relevant to your field")
    print("• Find cutting-edge AI tools for your profession")
    print("• Summarize everything into the most important points")
    print("• Provide sources so you can read more")
    print()
    print("Let's get started!")
    print()


def get_user_profession():
    """Get profession from user with validation"""
    while True:
        profession = input(
            "🎯 What's your profession? (e.g., filmmaker, musician, doctor) [q to quit]: "
        ).strip()
        if profession.lower() == "q":
            return None  # Signal to quit
        if profession:
            return profession.lower()
        print("Please enter a valid profession or 'q' to quit.")


def get_user_time_period():
    """Get time period from user with validation"""
    print("\n⏰ Choose your time range:")
    print("1. Day (last 24 hours)")
    print("2. Week (last 7 days)")
    print("3. Month (last 30 days)")

    while True:
        choice = input("\nEnter your choice (1-3) [q to quit]: ").strip()
        if choice.lower() == "q":
            return None  # Signal to quit
        if choice == "1":
            return "day"
        elif choice == "2":
            return "week"
        elif choice == "3":
            return "month"
        else:
            print("Please enter 1, 2, 3, or 'q' to quit.")


def ask_fresh_results():
    """Ask user if they want fresh results when cache hit occurs"""
    print("\n🔄 I found recent results in my cache.")
    print("Would you like to:")
    print("1. Use cached results (faster)")
    print("2. Generate fresh results (latest data)")

    while True:
        choice = input("\nEnter your choice (1-2) [q to quit]: ").strip()
        if choice.lower() == "q":
            return "quit"  # Signal to quit
        if choice == "1":
            return False  # Use cache
        elif choice == "2":
            return True  # Generate fresh
        else:
            print("Please enter 1, 2, or 'q' to quit.")


def clear_cache_for_user(profession: str, time_period: str):
    """Clear specific cache key for fresh generation"""
    if redis_client:
        try:
            cache_key = get_cache_key(profession, time_period)
            deleted = redis_client.delete(cache_key)
            if deleted:
                print(f"🗑️ Cleared cache for {profession} ({time_period})")
            return deleted > 0
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")
            return False
    return False


def show_post_answer_menu(profession: str, time_period: str):
    """Show options after displaying the newsletter"""
    print("\n" + "=" * 60)
    print("What would you like to do next?")
    print("=" * 60)
    print("a) Ask about another profession")
    print("b) Generate fresh results for current profession")
    print("c) Get more info on one of the points (coming soon!)")
    print("q) Quit")

    while True:
        choice = input("\nEnter your choice (a/b/c/q): ").strip().lower()
        if choice == "a":
            return "new_profession"
        elif choice == "b":
            return "fresh_results"
        elif choice == "c":
            print("🚧 Feature coming soon! Please choose another option.")
            continue
        elif choice == "q":
            return "quit"
        else:
            print("Please enter a, b, c, or q.")


def generate_newsletter_interactive(profession: str, time_period: str):
    """Generate newsletter with interactive cache handling"""
    # First check if there's a cache hit
    from tools.cache import get_cached_newsletter

    cached_result = get_cached_newsletter(profession, time_period)

    if cached_result:
        # Cache hit - ask user what they want to do
        fresh_choice = ask_fresh_results()

        if fresh_choice == "quit":
            return "quit"  # Signal to quit

        use_cache = not fresh_choice

        if use_cache:
            print("\n✅ Using cached results...\n")
            return {
                "newsletter": cached_result,
                "source": "cache",
                "profession": profession,
                "time_period": time_period,
            }
        else:
            # User wants fresh results - clear cache and generate
            print("\n🔄 Clearing cache and generating fresh results...")
            clear_cache_for_user(profession, time_period)

    # Cache miss or user requested fresh - generate new
    print(f"\n🔍 Searching for the latest AI updates for {profession}s...")
    print("This may take a moment while I search and analyze the results...")

    return generate_newsletter_with_cache(profession, time_period)


def main():
    """Main interactive application loop"""
    print_welcome()

    while True:
        # Step 1 & 2: Get user inputs
        profession = get_user_profession()
        if profession is None:  # User wants to quit
            print("\n👋 Thanks for using AI Newsletter Agent!")
            print("Stay updated with the latest AI developments!")
            break

        time_period = get_user_time_period()
        if time_period is None:  # User wants to quit
            print("\n👋 Thanks for using AI Newsletter Agent!")
            print("Stay updated with the latest AI developments!")
            break

        # Step 3 & 4: Generate newsletter with cache handling
        try:
            result = generate_newsletter_interactive(profession, time_period)

            if result == "quit":  # User wants to quit during cache choice
                print("\n👋 Thanks for using AI Newsletter Agent!")
                print("Stay updated with the latest AI developments!")
                break

            # Display the newsletter
            print("\n" + "=" * 60)
            print("📰 YOUR AI NEWSLETTER")
            print("=" * 60)
            print(result["newsletter"])

            # Show source info
            if result["source"] == "cache":
                print(f"\n💡 Source: Cached results")
            else:
                print(f"\n💡 Source: Fresh search results")

        except Exception as e:
            print(f"\n❌ Error generating newsletter: {e}")
            continue

        # Step 5: Post-answer menu loop for current profession
        while True:
            next_action = show_post_answer_menu(profession, time_period)

            if next_action == "new_profession":
                print("\n" + "=" * 40)
                print("Let's explore another profession!")
                print("=" * 40)
                break  # Break out of post-answer loop to get new profession
            elif next_action == "fresh_results":
                print(f"\n🔄 Generating fresh results for {profession}s...")
                clear_cache_for_user(profession, time_period)
                try:
                    result = generate_newsletter_interactive(profession, time_period)

                    if result == "quit":  # User wants to quit during cache choice
                        print("\n👋 Thanks for using AI Newsletter Agent!")
                        print("Stay updated with the latest AI developments!")
                        return

                    print("\n" + "=" * 60)
                    print("📰 FRESH AI NEWSLETTER")
                    print("=" * 60)
                    print(result["newsletter"])
                    print(f"\n💡 Source: Fresh search results")
                except Exception as e:
                    print(f"\n❌ Error generating fresh newsletter: {e}")
                # Stay in post-answer menu loop to show options again
                continue
            elif next_action == "quit":
                print("\n👋 Thanks for using AI Newsletter Agent!")
                print("Stay updated with the latest AI developments!")
                return  # Exit the entire application


if __name__ == "__main__":
    main()
