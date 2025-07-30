import time
from workflows.cached_newsletter import generate_newsletter_with_cache
from tools.cache import clear_cache_for_profession, get_cache_key, redis_client
from tools.profession_validator import validate_and_correct_profession
from tools.url_extractor import extract_urls_from_newsletter, get_detailed_explanation


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
        if not profession:
            print("Please enter a valid profession or 'q' to quit.")
            continue

        # Validate profession with LLM
        print("🤔 Validating profession...")
        is_valid, corrected, explanation = validate_and_correct_profession(profession)

        if not is_valid:
            print(f"❌ '{profession}' doesn't seem to be a valid profession.")
            if explanation:
                print(f"💡 {explanation}")
            print("Please try again with a different profession.")
            continue

        # Check if spelling was corrected (and it's a meaningful correction)
        if corrected.lower() != profession.lower() and corrected.lower() not in [
            "n/a",
            "none",
            "",
        ]:
            print(f"🔧 Did you mean '{corrected}'?")
            print("1. Yes, use the corrected version")
            print("2. No, keep my original input")

            while True:
                choice = input("\nEnter your choice (1-2) [q to quit]: ").strip()
                if choice.lower() == "q":
                    return None
                elif choice == "1":
                    profession = corrected
                    break
                elif choice == "2":
                    # Keep original, no change needed
                    break
                else:
                    print("Please enter 1, 2, or 'q' to quit.")

        print(f"✅ Great! Using profession: {profession}")
        return profession.lower()


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
            # Cache cleared silently
            return deleted > 0
        except Exception as e:
            # Error clearing cache - fail silently
            return False
    return False


def show_post_answer_menu(profession: str, time_period: str):
    """Show options after displaying the newsletter"""
    print("\n" + "=" * 60)
    print("What would you like to do next?")
    print("=" * 60)
    print("a) Ask about another profession")
    print("b) Generate fresh results for current profession")
    print("c) Get more info on one of the points")
    print("q) Quit")

    while True:
        choice = input("\nEnter your choice (a/b/c/q): ").strip().lower()
        if choice == "a":
            return "new_profession"
        elif choice == "b":
            return "fresh_results"
        elif choice == "c":
            return "detailed_info"
        elif choice == "q":
            return "quit"
        else:
            print("Please enter a, b, c, or q.")


def get_point_selection(newsletter_text: str) -> int:
    """Get user's selection of which point they want more info about"""
    # Extract URLs to determine how many points are available
    url_map = extract_urls_from_newsletter(newsletter_text)
    max_points = len(url_map)

    if max_points == 0:
        print("❌ No points with URLs found in this newsletter.")
        return None

    print(
        f"\n📋 This newsletter has {max_points} points with additional information available."
    )
    print("Which point would you like to learn more about?")

    while True:
        choice = input(f"Enter point number (1-{max_points}) [q to go back]: ").strip()
        if choice.lower() == "q":
            return None

        try:
            point_num = int(choice)
            if 1 <= point_num <= max_points:
                return point_num
            else:
                print(
                    f"Please enter a number between 1 and {max_points}, or 'q' to go back."
                )
        except ValueError:
            print(
                f"Please enter a number between 1 and {max_points}, or 'q' to go back."
            )


def show_detailed_explanation(newsletter_text: str, profession: str):
    """Handle the detailed explanation flow"""
    point_number = get_point_selection(newsletter_text)

    if point_number is None:
        return  # User chose to go back

    print(f"\n🔍 Getting detailed information for point {point_number}...")
    print("This may take a moment while I extract and analyze the content...")

    # Get detailed explanation
    result = get_detailed_explanation(newsletter_text, point_number, profession)

    if not result["success"]:
        print(f"\n❌ {result['error']}")
        if "url" in result:
            print(f"💡 You can try visiting the URL directly: {result['url']}")
        return

    # Display the detailed explanation
    print("\n" + "=" * 80)
    print(f"📖 DETAILED EXPLANATION - Point {point_number}")
    print("=" * 80)
    print(f"🔗 Source: {result['url']}")
    print("\n" + result["detailed_explanation"])
    print("\n" + "=" * 80)


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


def handle_insufficient_results(profession: str, time_period: str):
    """Handle case when insufficient results are found"""
    print(
        f"\n⚠️ Cannot find sufficient high-quality information on {profession}s in the last {time_period}."
    )
    print("This could be because:")
    print("• Limited recent AI developments for this profession")
    print("• Search results didn't meet quality threshold (score > 0.5)")
    print()
    print("What would you like to do?")
    print("1. Try another profession")
    print("2. Expand time range for current profession")

    while True:
        choice = input("\nEnter your choice (1-2) [q to quit]: ").strip()
        if choice.lower() == "q":
            return "quit"
        elif choice == "1":
            return "new_profession"
        elif choice == "2":
            return "expand_time"
        else:
            print("Please enter 1, 2, or 'q' to quit.")


def get_expanded_time_period(current_period: str):
    """Get expanded time period based on current selection"""
    if current_period == "day":
        print(f"\n⏰ Expanding from 'day' to broader time ranges:")
        print("1. Week (last 7 days)")
        print("2. Month (last 30 days)")

        while True:
            choice = input("\nEnter your choice (1-2) [q to quit]: ").strip()
            if choice.lower() == "q":
                return None
            elif choice == "1":
                return "week"
            elif choice == "2":
                return "month"
            else:
                print("Please enter 1, 2, or 'q' to quit.")

    elif current_period == "week":
        print(f"\n⏰ Expanding from 'week' to:")
        print("1. Month (last 30 days)")

        while True:
            choice = input("\nEnter your choice (1) [q to quit]: ").strip()
            if choice.lower() == "q":
                return None
            elif choice == "1":
                return "month"
            else:
                print("Please enter 1 or 'q' to quit.")

    else:  # month
        print(f"\n⚠️ Already at maximum time range (month).")
        print("Would you like to try a different profession instead?")
        print("1. Yes, try another profession")
        print("2. No, quit")

        while True:
            choice = input("\nEnter your choice (1-2): ").strip()
            if choice == "1":
                return "new_profession"
            elif choice == "2":
                return None
            else:
                print("Please enter 1 or 2.")


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
        while True:  # Loop for handling insufficient results with time period expansion
            try:
                result = generate_newsletter_interactive(profession, time_period)

                if result == "quit":  # User wants to quit during cache choice
                    print("\n👋 Thanks for using AI Newsletter Agent!")
                    print("Stay updated with the latest AI developments!")
                    return

                # Check for insufficient results
                if result.get("final_summary") == "insufficient_results":
                    action = handle_insufficient_results(profession, time_period)

                    if action == "quit":
                        print("\n👋 Thanks for using AI Newsletter Agent!")
                        print("Stay updated with the latest AI developments!")
                        return
                    elif action == "new_profession":
                        break  # Break out of time period loop to get new profession
                    elif action == "expand_time":
                        expanded_period = get_expanded_time_period(time_period)
                        if (
                            expanded_period is None
                        ):  # User quit or no expansion possible
                            print("\n👋 Thanks for using AI Newsletter Agent!")
                            print("Stay updated with the latest AI developments!")
                            return
                        elif expanded_period == "new_profession":
                            break  # Break out to get new profession
                        else:
                            time_period = expanded_period
                            print(
                                f"\n🔄 Retrying with expanded time period: {time_period}"
                            )
                            continue  # Try again with expanded time period
                    continue

                # Display the newsletter (successful result)
                print("\n" + "=" * 60)
                print("📰 YOUR AI NEWSLETTER")
                print("=" * 60)
                print(result["newsletter"])

                # No need to show source info to user

                break  # Break out of time period loop - successful result

            except Exception as e:
                print(f"\n❌ Error generating newsletter: {e}")
                break  # Break out to get new inputs

        # Continue only if we have a successful result (not insufficient results leading to new profession)
        if result != "quit" and result.get("final_summary") != "insufficient_results":
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
                        result = generate_newsletter_interactive(
                            profession, time_period
                        )

                        if result == "quit":  # User wants to quit during cache choice
                            print("\n👋 Thanks for using AI Newsletter Agent!")
                            print("Stay updated with the latest AI developments!")
                            return

                        # Check for insufficient results in fresh generation
                        if result.get("final_summary") == "insufficient_results":
                            action = handle_insufficient_results(
                                profession, time_period
                            )
                            if action == "quit":
                                print("\n👋 Thanks for using AI Newsletter Agent!")
                                print("Stay updated with the latest AI developments!")
                                return
                            elif action == "new_profession":
                                print("\n" + "=" * 40)
                                print("Let's explore another profession!")
                                print("=" * 40)
                                break
                            # For expand_time in post-answer menu, we just continue to show menu again
                            continue

                        print("\n" + "=" * 60)
                        print("📰 FRESH AI NEWSLETTER")
                        print("=" * 60)
                        print(result["newsletter"])
                        # No need to show source info to user
                    except Exception as e:
                        print(f"\n❌ Error generating fresh newsletter: {e}")
                    # Stay in post-answer menu loop to show options again
                    continue
                elif next_action == "detailed_info":
                    show_detailed_explanation(result["newsletter"], profession)
                    continue
                elif next_action == "quit":
                    print("\n👋 Thanks for using AI Newsletter Agent!")
                    print("Stay updated with the latest AI developments!")
                    return  # Exit the entire application


if __name__ == "__main__":
    main()
