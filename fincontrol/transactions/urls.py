from django.urls import path
from . import views
from . import views_enums as ev

urlpatterns = [
    path("", views.dashboard_view, name="transactions"),
    path("add/", views.transaction_add, name="transaction_add"),

    # AJAX для категорий и подкатегорий
    path("enums/category/add/ajax/", ev.category_add_ajax, name="category_add_ajax"),
    path("enums/subcategories.json", ev.subcategories_json, name="subcategories_json"),
    path("enums/subcategory/add/ajax/", ev.subcategory_add_ajax, name="subcategory_add_ajax"),

    # AJAX для таблицы
    path("table-block/", views.transactions_table_block, name="transactions_table_block"),

    # CRUD
    path("<int:pk>/edit/", views.transaction_edit, name="transaction_edit"),
    path("<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
]
