from django import forms
from .models import Note, Tag

# Form for creating and updating notes
class NoteForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),  # Initial empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False  # Tags are optional
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

# Form for creating and updating tags
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if self.user:
            qs = Tag.objects.filter(owner=self.user, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("You already have a tag with that name.")
        return name