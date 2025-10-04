from django import forms
from .models import Product, Artist

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Painting Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ArtistUpdateForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'profession', 'bio', 'profile_picture']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        } 