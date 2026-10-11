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

        # getattr keeps old saved looks working
        selected_top = (
            getattr(self.styling_result, "selected_top", "") or ""
        )
        selected_bottom = (
            getattr(self.styling_result, "selected_bottom", "") or ""
        )
        selected_dress = (
            getattr(self.styling_result, "selected_dress", "") or ""
        )
        selected_scarf = (
            getattr(self.styling_result, "selected_scarf", "") or ""
        )
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

        # -------------------------------------------------
        # CURRENT LOOK and RULES, built from what the
        # winning outfit actually contains
        # -------------------------------------------------

        look_lines = []
        rule_lines = []

        if selected_dress:

            look_lines.append(f"One-piece: {selected_dress}")

            rule_lines.append(
                "- NEVER change the selected one-piece."
            )
            rule_lines.append(
                "- Do NOT add a separate top or bottom. "
                "The one-piece is the complete outfit."
            )

        else:

            if selected_top:
                look_lines.append(f"Top: {selected_top}")
                rule_lines.append("- NEVER change the selected top.")
            else:
                look_lines.append(
                    "Top: None (the person keeps the top "
                    "from their own photo)"
                )

            if selected_bottom:
                look_lines.append(f"Bottom: {selected_bottom}")
                rule_lines.append("- NEVER change the selected bottom.")
            else:
                look_lines.append(
                    "Bottom: None (the person keeps the bottom "
                    "from their own photo)"
                )

        if selected_shoe:
            look_lines.append(f"Shoes: {selected_shoe}")
            rule_lines.append("- NEVER change the selected shoes.")
        else:
            look_lines.append("Shoes: None")
            rule_lines.append(
                "- No shoes are part of the winning outfit."
            )

        if selected_scarf:
            look_lines.append(f"Scarf: {selected_scarf}")
            rule_lines.append("- NEVER change the selected scarf.")
        else:
            look_lines.append("Scarf: None")
            rule_lines.append(
                "- No scarf is part of the winning outfit."
            )

        current_look_text = "\n".join(look_lines)
        rules_text = "\n".join(rule_lines)

        prompt = f"""
You are STYRIVA EVOLUTION.

You are NOT creating a brand new outfit.

Your mission is to elevate the existing winning outfit.

CURRENT LOOK

{current_look_text}

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

{rules_text}
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