from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import User, Product, ProductImage, Category


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        self.fields['username'].widget.attrs['placeholder'] = 'Имя пользователя'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Имя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Фамилия'
        self.fields['phone'].widget.attrs['placeholder'] = 'Телефон'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Подтверждение пароля'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'description', 'price', 'category', 'stock', 'available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название товара'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL-адрес (slug)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание товара'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Количество на складе'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['available'].initial = True


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Описание изображения'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm,
    extra=3,
    can_delete=True
)