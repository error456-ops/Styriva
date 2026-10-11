from django import forms
from .models import StyleConsultation


class StyleConsultationForm(forms.ModelForm):
    class Meta:
        model = StyleConsultation
        fields = [
            'gender', 'occasion', 'vibe', 'weather', 'user_model_photo',
            'top_1', 'top_2', 'top_3',
            'bottom_1', 'bottom_2', 'bottom_3',
            'dress_1', 'dress_2', 'dress_3',
            'shoe_1', 'shoe_2', 'shoe_3',
            'scarf_1', 'scarf_2', 'scarf_3',
        ]

    def clean(self):
        cleaned = super().clean()

        garment_fields = [
            f"{prefix}_{i}"
            for prefix in ("top", "bottom", "dress")
            for i in range(1, 4)
        ]

        if not any(cleaned.get(name) for name in garment_fields):
            raise forms.ValidationError(
                "Please upload at least one top, bottom or one-piece."
            )

        return cleaned