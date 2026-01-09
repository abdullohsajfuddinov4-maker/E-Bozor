from django import forms
from .models import Product


class NewProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'title',
            'description',
            'price',
            'address',
            'category',
            'phone_number',
            'tg_username',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.user:
            product.author = self.user
        if commit:
            product.save()
        return product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'title',
            'description',
            'price',
            'address',
            'category',
            'phone_number',
            'tg_username',
        )
