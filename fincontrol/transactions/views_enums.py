import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from .enums.service import get_enum_service

# Добавление категории
@login_required
@require_POST
def category_add_ajax(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        name = (data.get("name") or "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Некорректный запрос"}, status=400)

    if not name:
        return JsonResponse({"success": False, "error": "Название не может быть пустым"}, status=400)

    svc = get_enum_service()
    if not svc.add_category(name):
        return JsonResponse({"success": False, "error": "Такая категория уже существует"}, status=400)

    return JsonResponse({"success": True, "categories": svc.list_categories()})

# Получение подкатегорий по категории
@login_required
@require_GET
def subcategories_json(request):
    cat = (request.GET.get("category") or "").strip()
    svc = get_enum_service()
    subs = svc.list_subcategories(cat) if cat else []
    return JsonResponse({"category": cat, "subcategories": subs})

# Добавление подкатегории
@login_required
@require_POST
def subcategory_add_ajax(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        category = (data.get("category") or "").strip()
        name = (data.get("name") or "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Некорректный запрос"}, status=400)

    if not category or not name:
        return JsonResponse({"success": False, "error": "Категория и название обязательны"}, status=400)

    svc = get_enum_service()
    if not svc.add_subcategory(category, name):
        return JsonResponse({"success": False, "error": "Такая подкатегория уже существует"}, status=400)

    return JsonResponse({"success": True, "subcategories": svc.list_subcategories(category)})
