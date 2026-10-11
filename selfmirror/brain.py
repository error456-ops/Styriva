
import base64
import io
import json

from openai import OpenAI
from PIL import Image

from .image_utils import local_path


class AIStylist:
    """
    Selects the best outfit candidate and returns styling recommendations.

    Candidate numbering is 1-based:
        Candidate 1 -> Python index 0
        Candidate 2 -> Python index 1
        Candidate N -> Python index N - 1
    """

    MAX_EDGE = 512
    KINDS = ("top", "bottom", "dress", "shoe", "scarf")
    MAX_SELECTION_ATTEMPTS = 2

    def __init__(self, ai_input):
        self.ai_input = ai_input
        self.client = OpenAI()

    def encode_image(self, image_path):
        """Resize and compress an image before sending it to the AI."""

        image = Image.open(local_path(image_path))

        if image.mode != "RGB":
            image = image.convert("RGB")

        width, height = image.size
        longest_edge = max(width, height)

        if longest_edge > self.MAX_EDGE:
            scale = self.MAX_EDGE / longest_edge
            new_size = (
                max(1, int(width * scale)),
                max(1, int(height * scale)),
            )

            resampling = getattr(Image, "Resampling", Image)
            image = image.resize(
                new_size,
                resampling.LANCZOS,
            )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=80,
            optimize=True,
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return encoded, "image/jpeg"

    def get_gender(self):
        """Normalize the styling profile."""

        gender = self.ai_input.get("gender", "") or ""
        return gender.strip().lower()

    # ======================================================
    # CATALOG
    # Send each unique clothing image once.
    # ======================================================

    def build_catalog(self, outfit_candidates):
        labels = {}
        counters = {kind: 0 for kind in self.KINDS}

        display_names = {
            "top": "Top",
            "bottom": "Bottom",
            "dress": "One-piece",
            "shoe": "Shoe",
            "scarf": "Scarf",
        }

        items = []
        candidate_lines = []

        for index, outfit in enumerate(
            outfit_candidates,
            start=1,
        ):
            parts = []

            for kind in self.KINDS:
                item = outfit.get(kind)

                if not item:
                    continue

                path = item["image_path"]

                if path not in labels:
                    counters[kind] += 1
                    labels[path] = (
                        f"{display_names[kind]} "
                        f"{counters[kind]}"
                    )
                    items.append((labels[path], path))

                parts.append(labels[path])

            notes = []

            if not outfit.get("dress"):
                if (
                    outfit.get("top")
                    and not outfit.get("bottom")
                ):
                    notes.append(
                        "No bottom uploaded; keep the bottom "
                        "the person is wearing in their photo."
                    )

                if (
                    outfit.get("bottom")
                    and not outfit.get("top")
                ):
                    notes.append(
                        "No top uploaded; keep the top "
                        "the person is wearing in their photo."
                    )

            if not outfit.get("shoe"):
                notes.append(
                    "No shoes uploaded; keep the shoes "
                    "from the person's photo."
                )

            line = (
                f"Outfit Candidate {index}: "
                + (", ".join(parts) if parts else "Original outfit")
            )

            if notes:
                line += " (" + "; ".join(notes) + ")"

            candidate_lines.append(line)

        return items, candidate_lines

    # ======================================================
    # PROMPT
    # ======================================================

    def build_prompt(self, num_candidates):
        gender = self.get_gender()

        if gender == "men":
            styling_rules = """
Styling rules:
- Use men's fashion conventions for silhouette,
  proportions, grooming, and accessories.
- Keep styling masculine or gender-neutral unless
  the requested vibe calls for something different.
- Use only uploaded clothing items.
- Do not add dresses, skirts, or unuploaded garments.
- Select a scarf only when it genuinely improves the outfit.
- Return an empty makeup_recommendation unless useful.
- Make hair and accessories appropriate for the look.
"""

        elif gender == "women":
            styling_rules = """
Styling rules:
- Use women's fashion conventions for silhouette,
  proportions, grooming, and accessories.
- Consider feminine or gender-neutral styling according
  to the requested vibe.
- Select a scarf only when it genuinely improves the outfit.
- Provide appropriate makeup, hair, and accessory advice
  when useful.
"""

        else:
            styling_rules = """
Styling rules:
- Use gender-neutral fashion conventions.
- Select a scarf only when it genuinely improves the outfit.
- Provide makeup, hair, and accessory advice only when useful.
"""

        return f"""
You are STYRIVA, an expert AI Styling Concierge.

Occasion: {self.ai_input['occasion']}
Weather: {self.ai_input['weather']}
Desired Vibe: {self.ai_input['vibe']}
Styling Profile: {gender or "not specified"}

{styling_rules}

You will receive labeled clothing images followed by
a list of outfit candidates.

Possible outfit types:
- A one-piece outfit (dress, long frock, or gown).
  It is complete by itself. Never add a separate top or bottom.
- A top and a bottom.
- A top only, keeping the person's existing bottom.
- A bottom only, keeping the person's existing top.

Candidates may also contain an optional shoe or scarf.
If no shoe is supplied, preserve the shoes in the person's photo.
Never invent or add uploaded clothing items that do not exist.

Evaluate every candidate based on:
- Color harmony
- Style compatibility
- Occasion suitability
- Weather suitability
- Desired vibe
- Overall fashion appeal

Choose exactly ONE best outfit.

CRITICAL CANDIDATE NUMBERING:
- There are exactly {num_candidates} candidates.
- Use the candidate numbers displayed in the candidate list.
- The first candidate is number 1, NOT number 0.
- The second candidate is number 2.
- The last candidate is number {num_candidates}.
- winning_outfit_number MUST be an integer from 1 to {num_candidates}.
- NEVER return 0, a negative number, or a Python list index.
- Do not invent a candidate number.
- Select only a candidate that actually appears in the list.

For selected_top, selected_bottom, selected_dress,
selected_shoe, and selected_scarf:
- Return the corresponding item label for the winning candidate.
- Return an empty string if the winning candidate does not
  contain that clothing type.
- For a one-piece outfit, selected_dress must be filled
  and selected_top and selected_bottom must be empty.

The render_prompt must describe the complete winning outfit.
Include its selected shoes when present.
For a one-piece outfit, do not describe a separate top or bottom.
If the person keeps part of their original outfit, explicitly
preserve that part in the render_prompt.

Return ONLY valid JSON in this exact structure:

{{
    "winning_outfit_number": 1,
    "selected_top": "",
    "selected_bottom": "",
    "selected_dress": "",
    "selected_shoe": "",
    "selected_scarf": "",
    "title": "",
    "confidence": 0,
    "styling_rationale": "",
    "makeup_recommendation": "",
    "hair_recommendation": "",
    "accessory_recommendation": "",
    "render_prompt": ""
}}
"""

    # ======================================================
    # API REQUEST
    # ======================================================

    def _request_styling(self, content, num_candidates):
        """Request structured styling output from the AI."""

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"},
            timeout=60,
        )

        raw = response.choices[0].message.content

        if not raw:
            raise Exception("AIStylist returned an empty response.")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Exception(
                f"AIStylist returned invalid JSON: {raw}"
            ) from exc

        if not isinstance(result, dict):
            raise Exception(
                "AIStylist response must be a JSON object."
            )

        winner_number = result.get("winning_outfit_number")

        # bool is a subclass of int in Python, so reject it explicitly.
        if (
            not isinstance(winner_number, int)
            or isinstance(winner_number, bool)
            or not 1 <= winner_number <= num_candidates
        ):
            raise ValueError(
                "AIStylist returned invalid "
                f"winning_outfit_number: {winner_number!r}. "
                f"Expected an integer from 1 to {num_candidates}."
            )

        return result

    # ======================================================
    # MAIN RECOMMENDATION FLOW
    # ======================================================

    def recommend(self):
        outfit_candidates = self.ai_input.get("outfit_candidates")

        if not isinstance(outfit_candidates, list) or not outfit_candidates:
            raise ValueError(
                "AIStylist requires at least one outfit candidate."
            )

        num_candidates = len(outfit_candidates)

        items, candidate_lines = self.build_catalog(
            outfit_candidates
        )

        content = [
            {
                "type": "text",
                "text": self.build_prompt(num_candidates),
            }
        ]

        # Send each unique clothing image once.
        for label, image_path in items:
            content.append(
                {
                    "type": "text",
                    "text": label,
                }
            )

            encoded, mime_type = self.encode_image(image_path)

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{mime_type};base64,{encoded}"
                        )
                    },
                }
            )

        # Provide the exact candidate numbers used for selection.
        content.append(
            {
                "type": "text",
                "text": (
                    "Outfit candidates:\n"
                    + "\n".join(candidate_lines)
                ),
            }
        )

        result = None
        last_error = None

        # Retry once if the AI returns an invalid candidate number.
        for attempt in range(1, self.MAX_SELECTION_ATTEMPTS + 1):
            try:
                result = self._request_styling(
                    content,
                    num_candidates,
                )
                break

            except ValueError as exc:
                last_error = exc

                print(
                    f"AIStylist selection attempt {attempt}/"
                    f"{self.MAX_SELECTION_ATTEMPTS} failed: {exc}"
                )

                if attempt < self.MAX_SELECTION_ATTEMPTS:
                    content = content + [
                        {
                            "type": "text",
                            "text": (
                                "CORRECTION REQUIRED: Your previous "
                                "response had an invalid "
                                "winning_outfit_number. "
                                f"There are {num_candidates} candidates. "
                                "Choose again and return an integer "
                                f"from 1 to {num_candidates}, inclusive. "
                                "Never return 0. Return valid JSON "
                                "using the requested schema."
                            ),
                        }
                    ]

            except Exception as exc:
                raise Exception(
                    f"AIStylist API or response processing failed: {exc}"
                ) from exc

        if result is None:
            raise Exception(
                "AIStylist failed to select a valid outfit after "
                f"{self.MAX_SELECTION_ATTEMPTS} attempts. "
                f"Last error: {last_error}"
            )

        # Convert 1-based AI numbering to a zero-based Python index.
        winner_number = result["winning_outfit_number"]
        winner_index = winner_number - 1

        winning_outfit = outfit_candidates[winner_index]
        result["winning_outfit"] = winning_outfit

        # Ensure all selected-item fields exist.
        for field in (
            "selected_top",
            "selected_bottom",
            "selected_dress",
            "selected_shoe",
            "selected_scarf",
        ):
            if field not in result:
                result[field] = ""

        print("\n===== STYLING RESULT =====")
        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False,
            )
        )
        print("==========================\n")

        return result
