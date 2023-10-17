from django.urls import path
from api.views import AccoutView

app_name = "api"

urlpatterns = [
    path("contas/", AccoutView.as_view()),
    path("contas/saldo/", AccoutView.as_view()),
    path("contas/extrato/", AccoutView.as_view()),
    path("contas/<str:number_account>/usuario/", AccoutView.as_view()),
    path("contas/<str:number_account>/", AccoutView.as_view()),
]
