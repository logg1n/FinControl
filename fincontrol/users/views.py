from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import ProfileForm
from .forms import RegisterForm

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход
            return redirect("transaction_list")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("transaction_list")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")



@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, "users/profile.html", {
        "form": form,
        "telegram_id": profile.telegram_id,
        "telegram_link_code": profile.telegram_link_code
    })

@login_required
def generate_telegram_code(request):
    profile = request.user.profile
    profile.generate_link_code()
    messages.info(request, "Код для привязки Telegram сгенерирован")
    return redirect('profile')
