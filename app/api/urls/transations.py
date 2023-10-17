from django.urls import path
from api.views import TransationsView

app_name = "api"

urlpatterns = [
    path("transacoes/depositar/", TransationsView.as_view()),
    path("transacoes/sacar/", TransationsView.as_view()),
    path("transacoes/transferir/", TransationsView.as_view()),
]
