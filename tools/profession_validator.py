import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def validate_profession(profession: str) -> dict:
    """
    Validate if the input could reasonably be a profession

    Returns:
        dict with keys:
        - is_valid: bool
        - corrected: str (corrected spelling if needed)
        - explanation: str (why it was rejected, if applicable)
    """

    if not profession or len(profession.strip()) < 2:
        return {
            "is_valid": False,
            "corrected": profession,
            "explanation": "Please enter a profession with at least 2 characters.",
        }

    prompt = f"""Is "{profession}" a valid profession or job title? Be VERY lenient and accept:
- Real professions (doctor, teacher, engineer)
- Unusual but real jobs (bed tester, fortune cookie writer, professional cuddler)
- Creative/emerging roles (content creator, influencer, AI trainer)
- Misspelled professions (fil maker = filmmaker)

REJECT only clearly non-profession things like:
- Objects (sofa, table, car)
- Animals (unless it's a job like "dog trainer")
- Abstract concepts (love, happiness)
- Fantasy creatures (unicorn, dragon)
- Random gibberish (kjhgfkvghtf)

If it's a misspelled profession that you can recognize, provide the corrected version.
If it's completely unrecognizable or random text, do NOT provide a correction - just mark as invalid.

Respond in this format:
VALID: yes/no
CORRECTED: [corrected spelling if it's a recognizable misspelling, otherwise write "NONE"]
REASON: [brief explanation if rejected]

Input: "{profession}" """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful profession validator. Be very lenient and accept anything that could reasonably be a job or profession, including unusual ones. Only reject clear non-professions. Only suggest corrections for recognizable misspellings, not for random text.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.1,
        )

        result = response.choices[0].message.content.strip()

        # Parse the response
        lines = result.split("\n")
        valid_line = next(
            (line for line in lines if line.startswith("VALID:")), "VALID: yes"
        )
        corrected_line = next(
            (line for line in lines if line.startswith("CORRECTED:")),
            f"CORRECTED: NONE",
        )
        reason_line = next(
            (line for line in lines if line.startswith("REASON:")), "REASON: "
        )

        is_valid = "yes" in valid_line.lower()
        corrected_text = corrected_line.split(":", 1)[1].strip()

        # Only use correction if it's not "NONE" and actually different from input
        if (
            corrected_text.upper() == "NONE"
            or corrected_text.lower() == profession.lower()
        ):
            corrected = profession  # No meaningful correction
        else:
            corrected = corrected_text

        explanation = (
            reason_line.split(":", 1)[1].strip()
            if len(reason_line.split(":", 1)) > 1
            else ""
        )

        return {
            "is_valid": is_valid,
            "corrected": corrected,
            "explanation": explanation,
        }

    except Exception as e:
        # If validation fails, be lenient and allow it
        print(f"⚠️ Profession validation error: {e}")
        return {"is_valid": True, "corrected": profession, "explanation": ""}


def validate_and_correct_profession(profession: str) -> tuple[bool, str, str]:
    """
    Convenience function that returns (is_valid, corrected_profession, explanation)
    """
    result = validate_profession(profession)
    return result["is_valid"], result["corrected"], result["explanation"]
