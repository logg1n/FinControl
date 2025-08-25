 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from services.advice_generator import get_ai_advice

@login_required
def dashboard_view(request):
    advice_text = get_ai_advice(request.user, days=30)
    return render(request, "dashboard.html", {"advice_text": advice_text})
