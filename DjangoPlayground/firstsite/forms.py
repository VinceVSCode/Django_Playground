from django import forms
from .models import Note, Tag

class NoteForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),  # Initial empty queryset
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    class Meta:
        model = Note
        fields = ["title", "content",  "is_pinned", "is_archived","tags"]
    def __init__(self, *args, **kwargs):
        # Extract the user from kwargs
        user = kwargs.pop('user', None)
        # Call the parent constructor
        super().__init__(*args, **kwargs)
        # Dynamically set the queryset for tags based on the user
        if user is not None:
            self.fields['tags'].queryset = Tag.objects.filter(owner=user).order_by('name')
