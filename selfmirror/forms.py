from django import forms
from .models import StyleConsultation


class StyleConsultationForm(forms.ModelForm):
    class Meta:
        model = StyleConsultation
        fields = [
            'occasion', 'vibe', 'weather', 'user_model_photo',
            'top_1', 'top_2', 'top_3',
            'bottom_1', 'bottom_2', 'bottom_3',
            'shoe_1', 'shoe_2', 'shoe_3',
            'scarf_1', 'scarf_2', 'scarf_3',
        ]