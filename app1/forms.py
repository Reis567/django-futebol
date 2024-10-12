from django.shortcuts import render, redirect
from django import forms
from .models import Time, Jogador

class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['nome', 'sigla', 'tecnico']

    # Campos para selecionar jogadores titulares e banco usando Select com filtro
    jogadores_titulares = forms.ModelMultipleChoiceField(
        queryset=Jogador.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Jogadores Titulares"
    )
    jogadores_banco = forms.ModelMultipleChoiceField(
        queryset=Jogador.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Jogadores Banco",
        required=False
    )
