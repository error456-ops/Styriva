import json
from openai import OpenAI


class EvolutionBrain:
    """
    STYRIVA Style Evolution AI

    This AI does NOT create a new outfit.
    It enhances the already generated winning look.
    """

    def __init__(self, consultation, styling_result, extras, style_preference):
        self.consultation = consultation
        self.styling_result = styling_result
        self.extras = extras
        self.style_preference = style_preference
        self.client = OpenAI()

    def build_prompt(self):

        print("\n========== BUILD PROMPT ==========")

        selected_top = self.styling_result.selected_top or ""
        selected_bottom = self.styling_result.selected_bottom or ""
        selected_scarf = self.styling_result.selected_scarf or ""

        # NEW: shoes (getattr keeps old saved looks working)
        selected_shoe = (
            getattr(self.styling_result, "selected_shoe", "") or ""
        )

        previous_makeup = (
            self.styling_result.makeup_recommendation or ""
        )

        previous_hair = (
            self.styling_result.hair_recommendation or ""
        )

        previous_accessories = (
            self.styling_result.accessory_recommendation or ""
        )

        previous_reasoning = (
            self.styling_result.styling_rationale or ""
        )

        wardrobe = (
            ", ".join(self.extras)
            if self.extras
            else "No additional wardrobe pieces selected."
        )

        shoe_text = (
            f"Shoes: {selected_shoe}"
            if selected_shoe
            else "Shoes: None"
        )

        shoe_rule = (
            "- NEVER change the selected shoes."
            if selected_shoe
            else "- No shoes are part of the winning outfit."
        )

        scarf_text = (
            f"Scarf: {selected_scarf}"
            if selected_scarf
            else "Scarf: None"
        )

        scarf_rule = (
            "- NEVER change the selected scarf."
            if selected_scarf
            else "- No scarf is part of the winning outfit."
        )

        prompt = f"""
You are STYRIVA EVOLUTION.

You are NOT creating a brand new outfit.

Your mission is to elevate the existing winning outfit.

CURRENT LOOK

Top: {selected_top}
Bottom: {selected_bottom}
{shoe_text}
{scarf_text}

ORIGINAL STYLING

Occasion: {self.consultation.occasion}
Weather: {self.consultation.weather}
Desired Vibe: {self.consultation.vibe}

USER OWNS

{wardrobe}

STYLE PREFERENCE

{self.style_preference}

PREVIOUS MAKEUP

{previous_makeup}

PREVIOUS HAIR

{previous_hair}

PREVIOUS ACCESSORIES

{previous_accessories}

ORIGINAL REASONING

{previous_reasoning}

RULES

- NEVER change the selected top.
- NEVER change the selected bottom.
{shoe_rule}
{scarf_rule}
- Only enhance the look.
- Only use wardrobe items listed above.
- Do NOT invent clothing the user doesn't own.
- Keep the outfit realistic.
- The render_prompt must describe the full outfit, including the shoes if there are any.
- Return ONLY valid JSON.

Return exactly:

{{
    "added_items": [],
    "reasoning": "",
    "makeup_recommendation": "",
    "hair_recommendation": "",
    "accessory_recommendation": "",
    "render_prompt": ""
}}
"""

        print("BUILD PROMPT FINISHED")
        print("========== END BUILD ==========\n")

        return prompt

    def generate(self):

        print("\n========== EVOLUTION DEBUG ==========")
        print("STEP 1 - generate() entered")

        prompt = self.build_prompt()

        print("STEP 2 - prompt built")
        print("STEP 3 - calling OpenAI")

        try:

            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=700,
                response_format={
                    "type": "json_object"
                },
                timeout=30,
            )

            print("STEP 4 - OpenAI returned")

        except Exception as e:

            print("\n!!!!!!!! OPENAI ERROR !!!!!!!!")
            print(type(e).__name__)
            print(str(e))
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            raise

        raw = response.choices[0].message.content

        print("STEP 5 - content extracted")

        raw = (
            raw.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:

            result = json.loads(raw)

            print("STEP 6 - JSON parsed successfully")
            print(json.dumps(result, indent=4))
            print("========== END DEBUG ==========\n")

            return result

        except json.JSONDecodeError:

            print(raw)

            raise Exception(
                "EvolutionBrain returned invalid JSON."
            )