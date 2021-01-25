from django import forms


class ColorField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.update(initial='#FFFFFF')
        if 'choices' not in kwargs:
            colors = '#f1948a', '#af7ac5', '#f7dc6f', '#73c6b6', '#5dade2', '#82e0aa','#f1948a', '#af7ac5', '#f7dc6f'
            kwargs.update(choices=[[color, color] for color in colors])
        super().__init__(*args, **kwargs)
