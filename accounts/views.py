from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

def style_auth_form(form):
    for field in form.fields.values():
        field.widget.attrs.setdefault('class', 'form-control')
    return form

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = style_auth_form(AuthenticationForm(data=request.POST))
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    else:
        form = style_auth_form(AuthenticationForm())
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = style_auth_form(UserCreationForm(request.POST))
        if form.is_valid():
            login(request, form.save())
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = style_auth_form(UserCreationForm())
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
