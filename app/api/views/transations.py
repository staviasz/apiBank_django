import json
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from api.models import Accounts, Deposit, Withdraw, Transfer


class TransationsView(APIView):
    def post(self, request):
        path = request.path

        if "depositar" in path:
            is_valid = self.deposit(request)
            if isinstance(is_valid, dict):
                return JsonResponse(is_valid, status=400)
            return HttpResponse(status=204)

        if "sacar" in path:
            is_valid = self.withdraw(request)
            if isinstance(is_valid, dict):
                return JsonResponse(is_valid, status=400)
            return HttpResponse(status=204)

        if "transferir" in path:
            is_valid = self.transfer(request)
            if isinstance(is_valid, dict):
                return JsonResponse(is_valid, status=400)
            return HttpResponse(status=204)

    def deposit(self, request):
        req_body = json.loads(request.body)

        account_number = req_body.get("numero_conta")
        account = self.__clean_account_number(account_number)
        if isinstance(account, dict):
            return account

        value = self.__clean_value(req_body)
        if isinstance(value, dict):
            return value

        new_balance = account.first().balance + value
        account.update(balance=new_balance)
        Deposit.objects.create(number_account=account.first(), value=value)
        return

    def withdraw(self, request):
        req_body = json.loads(request.body)
        if not req_body.get("senha"):
            return {"message": "Digite a senha"}

        value = self.__clean_value(req_body)
        if isinstance(value, dict):
            return value

        account_number = req_body.get("numero_conta")
        account = self.__clean_account_number(account_number)
        if isinstance(account, dict):
            return account

        if account.first().user.password != req_body.get("senha"):
            return {"message": "Senha invalida"}

        if account.first().balance < value:
            return {"message": "Saldo insuficiente"}

        new_balance = account.first().balance - value
        account.update(balance=new_balance)
        Withdraw.objects.create(number_account=account.first(), value=value)
        return

    def transfer(self, request):
        req_body = json.loads(request.body)
        if not req_body.get("senha"):
            return {"message": "Digite a senha"}

        account_number_origin = req_body.get("numero_conta_origem")
        account_origin = self.__clean_account_number(account_number_origin)
        if isinstance(account_origin, dict):
            account_origin["message"] = account_origin.get("message").replace(
                "conta", "conta de origem"
            )
            return account_origin

        account_number_destiny = req_body.get("numero_conta_destino")
        account_destiny = self.__clean_account_number(account_number_destiny)
        if isinstance(account_destiny, dict):
            account_destiny["message"] = account_destiny.get("message").replace(
                "conta", "conta de destino"
            )
            return account_destiny

        value = self.__clean_value(req_body)
        if isinstance(value, dict):
            return value

        if account_origin.first().user.password != req_body.get("senha"):
            return {"message": "Senha invalida"}

        if account_origin.first().balance < value:
            return {"message": "Saldo insuficiente"}

        new_balance_origin = account_origin.first().balance - value
        account_origin.update(balance=new_balance_origin)

        new_balance_destiny = account_destiny.first().balance + value
        account_destiny.update(balance=new_balance_destiny)

        Transfer.objects.create(
            number_account_origin=account_origin.first().number,
            number_account_destiny=account_destiny.first().number,
            value=value,
        )

        return

    def __clean_account_number(self, account_number):
        if not account_number:
            return {"message": "numero da conta é obrigatorio"}
        account = Accounts.objects.filter(number=account_number)
        if not account:
            return {"message": "A conta não foi encontrada"}
        return account

    def __clean_value(self, req_body):
        value = req_body.get("valor")
        if not value:
            return {"message": "O valor é obrigatorio"}
        if 0 >= float(value):
            return {"message": "O valor deve ser Maior que zero"}
        return float(value)
