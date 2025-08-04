from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Roles, Datasets, Dashboards, Chart_Types, Social_Comment, Selected_Columns , Dataset_Columns, Charts
from django.contrib.auth.models import User


# Sign up form
class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
        'id': 'floatingEmail'
    }))
    
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'id': 'floatingUsername'
    }))
    
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name',
        'id': 'floatingFirstName'
    }))
    
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name',
        'id': 'floatingLastName'
    }))
    
    password1 = forms.CharField(required=True, label="Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'id': 'floatingPassword'
    }))
    
    password2 = forms.CharField(required=True, label="Confirm Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm your password',
        'id': 'floatingConfirmPassword'
    }))

    agree_terms = forms.BooleanField(required=True, label="I agree to the terms and conditions", widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'type': 'checkbox',
        'id': 'gridCheck'
    }))


    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


# Login form
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'id': 'floatingUsername'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'id': 'floatingPassword'
    }))

    class Meta:
        model = User
        field = ('username', 'password')


# Upload CSV file form
class DatasetForm(forms.ModelForm):
    file_path = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control',
        'type': 'file',
        'id': 'datasetFile',
        'accept': '.csv',
    }))

    class Meta:
        model = Datasets
        fields = ['file_path']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.dashboard = kwargs.pop('dashboard', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('file_path') is False:
            if instance.file_path:
                instance.file_path.delete(save=False)
            instance.file_path = None
        if self.user:
            instance.user = self.user
        if self.dashboard:
            instance.dashboard = self.dashboard
        if commit:
            instance.save()
        return instance


class DashboardForm(forms.ModelForm):
    chart_type = forms.ModelChoiceField(
        queryset=Chart_Types.objects.all(),
        required=False,
        empty_label=None,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'chartTypeSelection',
        })
    )

    status = forms.ChoiceField(
        choices=[
            (False, 'Public'),
            (True, 'Private'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'chartTypeSelection',
        })
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea({
            'class': 'form-control',
            'id': 'dashboardDescriptionTextArea',
            'rows': 3,
            'placeholder': 'Description',
        })
    )

    class Meta:
        model = Dashboards
        fields = ['name', 'description', 'status', 'chart_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'dashboardNameInput',
                'placeholder': 'Untitled Name',
            }),
        }
        


#  Select columns form
class SelectedColumnsForm(forms.ModelForm):
    x_axis = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'id': 'xAxisInput'
    }))

    y_axis = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'id': 'yAxisInput'
    }))
    category = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'id': 'categoryInput'
    }))
    series = forms.CharField(required=False, widget=forms.TextInput(attrs=({
        'class': 'form-control',
        'id': 'seriesInput'
    })))

    class Meta:
        model = Selected_Columns
        fields = ['x_axis', 'y_axis']
            


class CommentForm(forms.ModelForm):
    class Meta:
        model = Social_Comment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Leave your comment here...'
            })
        }





