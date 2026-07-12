"""
Automated Copywriting & Tone Transformer
Project 2 - DecodeLabs Generative AI Internship
"""
 
import os
import argparse
from pydantic import BaseModel, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential
 
INTRO_PATTERNS = [
    "here's a rewritten version",
    "here is a rewritten version",
    "here's the rewritten",
    "here is the rewritten",
    "sure, here's",
    "sure, here is",
    "here's your",
    "here is your",
]
 
 
def clean_ai_intro(text: str) -> str:
    """Strips a leading intro line if the model added one despite instructions."""
    lines = text.strip().split("\n")
    if lines and any(p in lines[0].lower() for p in INTRO_PATTERNS):
        lines = lines[1:]
    return "\n".join(lines).strip()
 
 
def compact_for_csv(text: str) -> str:
    """Collapses blank lines/paragraph breaks into single spaces so a CSV
    cell displays as one clean block instead of stretching across rows."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return " ".join(lines)
 
 
class MarketingCopy(BaseModel):
    product_name: str
    platform: str
    tone: str
    copy_text: str
 
    @field_validator("copy_text")
    @classmethod
    def copy_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Generated copy is empty or too short.")
        return v.strip()
 
 
def build_master_prompt(product_name: str, platform: str, tone: str, raw_description: str) -> str:
    platform_rules = {
        "linkedin": "Write a professional LinkedIn post, 150-300 words, no more than 3 emojis, end with a call-to-action and relevant hashtags.",
        "instagram": "Write a catchy Instagram caption, under 150 words, casual and energetic, use 3-5 emojis and 5-8 hashtags.",
        "email": "Write a marketing email with a subject line and a short persuasive body (under 200 words), formal greeting, clear CTA at the end."
    }
 
    platform_key = platform.strip().lower()
    if platform_key not in platform_rules:
        raise ValueError(f"'{platform}' is not supported. Choose from: linkedin, instagram, email.")
 
    rules = platform_rules[platform_key]
 
    return f"""You are a professional marketing copywriter who writes in simple, natural, everyday English - the way a real human copywriter would write, not like an AI.
 
Product Name: {product_name}
Target Platform: {platform}
Tone: {tone}
 
Raw Product Description:
\"\"\"{raw_description}\"\"\"
 
Platform Rules: {rules}
 
Writing Style Rules:
- Use simple, easy-to-understand words. No overly formal or "fancy" vocabulary.
- Do not sound like an AI. Avoid phrases like "unlock", "elevate", "game-changer", "unparalleled".
- Do not start with an introduction like "Here is..." - start directly with the copy.
- Write like a real person talking to another real person.
 
Task: Rewrite the description above into polished, ready-to-publish marketing copy
that matches the tone and follows the platform and style rules.
Output ONLY the final copy - no explanations, no notes, no formatting.
"""
 
 
def generate_copy(prompt: str, temperature: float = 0.7, top_p: float = 0.9) -> str:
    """
    Sends the prompt to an AI provider and returns the generated copy.
    Falls back through Claude -> Gemini -> Ollama if one is unavailable.
    """
 
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
 
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
        def call_claude():
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                temperature=temperature,
                top_p=top_p,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
 
        result = call_claude()
        print("[INFO] Generated with Claude.")
        return result
 
    except Exception as e:
        print(f"[WARNING] Claude failed: {e}")
 
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-2.0-flash")
 
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
        def call_gemini():
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=500
                )
            )
            return response.text
 
        result = call_gemini()
        print("[INFO] Generated with Gemini.")
        return result
 
    except Exception as e:
        print(f"[WARNING] Gemini failed: {e}")
 
    try:
        import ollama
 
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
        def call_ollama():
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature, "top_p": top_p}
            )
            return response["message"]["content"]
 
        result = call_ollama()
        print("[INFO] Generated with Ollama (local).")
        return result
 
    except Exception as e:
        print(f"[ERROR] Ollama failed too: {e}")
        return "Sorry, all three providers (Claude, Gemini, Ollama) failed."
 
 
def main():
    parser = argparse.ArgumentParser(description="Automated Copywriting & Tone Transformer")
    parser.add_argument("--product", required=True, help="Product name, e.g. 'Comfy Running Shoes'")
    parser.add_argument("--platform", required=True, choices=["linkedin", "instagram", "email"])
    parser.add_argument("--tone", required=True, help="e.g. 'professional' or 'witty'")
    parser.add_argument("--description", required=True, help="Raw product description")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.9)
 
    args = parser.parse_args()
 
    prompt = build_master_prompt(
        product_name=args.product,
        platform=args.platform,
        tone=args.tone,
        raw_description=args.description
    )
 
    print("----- Generating copy... -----\n")
    final_copy = generate_copy(prompt, temperature=args.temperature, top_p=args.top_p)
    final_copy = clean_ai_intro(final_copy)
 
    try:
        validated = MarketingCopy(
            product_name=args.product,
            platform=args.platform,
            tone=args.tone,
            copy_text=final_copy
        )
        print("\n----- Final Marketing Copy -----")
        print(validated.copy_text)
    except Exception as e:
        print(f"\n[VALIDATION ERROR] {e}")
 
 
if __name__ == "__main__":
    main()
 