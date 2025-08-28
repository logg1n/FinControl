import csv
from io import BytesIO
from datetime import datetime
import openpyxl
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.template.loader import render_to_string
from xhtml2pdf import pisa   # заменили weasyprint на xhtml2pdf
from .utils import get_filtered_transactions

def _filename(prefix: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"

def _serialize_rows(qs):
    for tx in qs:
        yield [
            tx.date.strftime("%Y-%m-%d"),
            tx.type,
            float(tx.amount),
            tx.currency,
            tx.category,
            tx.subcategory,
            tx.tag,
            tx.payment_method,
        ]

@login_required
def export_transactions(request, fmt: str):
    fmt = (fmt or "").lower()
    if fmt not in {"excel", "pdf", "csv"}:
        raise Http404("Unknown export format")

    qs = get_filtered_transactions(request)

    # Excel
    if fmt == "excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Транзакции"
        ws.append(["Дата", "Тип", "Сумма", "Валюта", "Категория", "Подкатегория", "Метка", "Способ оплаты"])
        for row in _serialize_rows(qs):
            ws.append(row)
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        resp = HttpResponse(
            bio.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{_filename("transactions", "xlsx")}"'
        return resp

    # PDF через xhtml2pdf
    if fmt == "pdf":
        html_string = render_to_string("exporter/transactions_pdf.html", {"transactions": qs})
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
        if pisa_status.err:
            return HttpResponse("Ошибка генерации PDF", status=500)

        resp = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="{_filename("transactions", "pdf")}"'
        return resp

    # CSV
    def row_iter():
        yield ["Дата", "Тип", "Сумма", "Валюта", "Категория", "Подкатегория", "Метка", "Способ оплаты"]
        for row in _serialize_rows(qs):
            yield row

    class Echo:
        def write(self, value):
            return value

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    def stream():
        yield "\ufeff"  # BOM для Excel
        for row in row_iter():
            yield writer.writerow(row)

    resp = StreamingHttpResponse(stream(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_filename("transactions", "csv")}"'
    return resp
