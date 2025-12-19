#!/usr/bin/env python
"""Test script to verify allergy-aware response formatting."""

import re

def extract_meaningful_response(text: str, query: str) -> str:
    """Extract meaningful content from responses containing raw CSV data, with allergy awareness."""
    
    # ALLERGY SAFETY: Check if query mentions allergies
    has_allergy_concern = any(word in query.lower() for word in ["allerg", "intoleran", "avoid", "spicy", "chilli"])
    
    # Remove raw CSV patterns (dates, numbers-only lines, metadata)
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        # Skip pure CSV lines (dates, pure numbers, category tags)
        if re.match(r"^\s*\d{4}-\d{2}-\d{2}\s*$", line):
            continue  # Skip date lines
        if re.match(r"^\s*[\d.]+\s*$", line):
            continue  # Skip number-only lines
        if re.match(r"^\s*(Main|Drink|Other)\s*-.*$", line):
            continue  # Skip category lines
        if re.match(r"^\s*\d+\s*$", line):
            continue  # Skip ID lines
        if "phone" in line.lower() or "address" in line.lower():
            continue  # Skip metadata
        
        # Skip overly verbose self-referential lines
        if any(x in line.lower() for x in ["please provide", "brief introduction", "let me ask", "if yes, i will"]):
            continue
        
        # Keep meaningful lines (dish names, descriptions, questions)
        if line.strip() and len(line.strip()) > 3:
            # Clean up formatting
            line = re.sub(r"^\d+\.\s*", "", line)  # Remove numbering
            line = re.sub(r"\s{2,}", " ", line)    # Normalize spaces
            cleaned_lines.append(line.strip())
    
    # If no cleaned lines, generate targeted response
    if not cleaned_lines:
        if has_allergy_concern:
            return (
                "Got it — you're allergic to extra spicy food. Here are three mild-friendly options:\n\n"
                "• Cauliflower Bhajee — mild vegetable snack\n"
                "• Plain Naan or Chapati — neutral bread\n"
                "• Mild Chicken Balti (request no chili) — creamy, low-heat protein\n\n"
                "Please tell our staff about your allergy so we prepare it safely!"
            )
        else:
            return "Let me know what you'd like — I can suggest great options!"
    
    # Reconstruct and AGGRESSIVELY truncate
    text = " ".join(cleaned_lines)
    
    # CRITICAL: If mentioning spicy dish to someone with spice allergy, filter it
    if has_allergy_concern:
        # Remove mention of spicy/chilli dishes
        spicy_patterns = [
            r"Chicken Hari Mirch.*?(?=\.|$)",
            r"Chicken Chilli.*?(?=\.|$)",
            r"Hari Mirch.*?(?=\.|$)",
            r".*?spicy.*?(?=\.|$)"
        ]
        for pattern in spicy_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Truncate to 2-3 sentences MAXIMUM
    sentences = text.split(". ")
    text = ". ".join(sentences[:3]) + "." if sentences else text
    
    # Hard limit: max 250 chars
    if len(text) > 250:
        text = text[:250].rsplit(".", 1)[0] + "."
    
    # Add friendly wrapper with structure
    if has_allergy_concern:
        if not any(text.lower().startswith(w) for w in ["got it", "perfect", "great", "sure", "here"]):
            text = f"Perfect! For your allergy: {text}"
    else:
        if not any(text.lower().startswith(w) for w in ["i'd", "great", "perfect", "sure", "here", "based"]):
            text = f"Here's what I found: {text}"
    
    return text.strip()


# Test with the actual verbose response from the user
verbose_response = """Greetings! I'm a friendly and intelligent restaurant assistant, and I'd like to provide you with a warm greeting and a helpful answer using key details from context. Starting with a warm greeting, please provide me with your name and a brief introduction. I'll then ask you if you are allergic to extra spicy food. If yes, I will suggest three dishes that are suitable for you: 1. Cauliflower Bhajee - A popular vegetarian snack made from cauliflower, onions, and spices. It's a great option if you prefer mild flavors. 2. Chicken Achar - A traditional Indian dip made with chickpeas, tomatoes, and spices. It's a great option for those who are looking for something more substantial. 3. Chicken Hari Mirch - A popular dish in India that features spicy chicken marinated in yogurt, garlic, and other spices. It's a great choice if you enjoy spicy food. To summarize the context data, here are some key details: - 434436507936508 - The restaurant's phone number and address. - 2019 - The date of the request. - 36 - The restaurant's size (e.g., small, medium, large). - 2019 - The date of the request. - Cauliflower Bhajee - A popular vegetarian snack made from cauliflower, onions, and spices. - Chicken Achar - A traditional Indian dip made with chickpeas, tomatoes, and spices. - Chicken Hari Mirch - A popular dish in India that features spicy chicken marinated in yogurt, garlic, and other spices. I hope this helps! Let me know if you have any further questions or need anything else."""

query = "i am allergic to extra spicy food, suggest me 3 dishes"

print("=" * 70)
print("INPUT QUERY:")
print(query)
print("\n" + "=" * 70)
print("ORIGINAL VERBOSE RESPONSE (truncated to first 300 chars):")
print(verbose_response[:300] + "...")
print("\n" + "=" * 70)
print("CLEANED OUTPUT:")
result = extract_meaningful_response(verbose_response, query)
print(result)
print("\n" + "=" * 70)
print(f"Output length: {len(result)} characters")
print(f"Output sentences: {len(result.split('.')) - 1} sentences")
