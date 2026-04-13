from django.db import connection
from django.http import JsonResponse

def live(request):
    return JsonResponse({"status": "ok"})

def ready(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ready"})
