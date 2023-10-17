import re
import json
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
import phonenumbers
from validate_docbr import CPF
from email_validator import validate_email, EmailNotValidError

from api.models import Accounts, Bank, User, Deposit, Withdraw, Transfer


class AccoutView(APIView):
    def get(self, request):
        path = request.path
        if "saldo" in path:
            is_valid = self.balance(request)
            if is_valid.get("saldo"):
                return JsonResponse(is_valid, status=200)
            else:
                return JsonResponse(is_valid, status=400)

        elif "extrato" in path:
            is_valid = self.extract(request)
            if isinstance(is_valid, dict):
                return JsonResponse(is_valid, status=400)
            else:
                return JsonResponse(is_valid, safe=False, status=200)

        else:
            is_valid = self.index(request)
            if isinstance(is_valid, dict):
                return JsonResponse(is_valid, status=400)
            else:
                return JsonResponse(is_valid, safe=False, status=200)

    def index(self, request):
        password_bank_is_valid = self.__middleware(request)
        if isinstance(password_bank_is_valid, dict):
            return password_bank_is_valid
        accounts_qs = Accounts.objects.all()
        accounts_list = []

        for account in accounts_qs:
            account_info = {
                "numero": account.number,
                "saldo": account.balance,
                "usuario": {
                    "nome": account.user.name,
                    "cpf": account.user.cpf,
                    "data_nascimento": account.user.birth_date,
                    "telefone": account.user.phone,
                    "email": account.user.email,
                    "senha": account.user.password,
                },
            }
            accounts_list.append(account_info)

        return accounts_list

    def balance(self, request):
        account_number = request.GET.get("numero_conta")
        password = request.GET.get("senha")

        if not password:
            return {"message": "Digite a senha"}

        account = self.__clean_account_number(account_number)
        if isinstance(account, dict):
            return account

        if password != account.first().user.password:
            return {"message": "Senha incorreta"}

        return {"saldo": account.first().balance}

    def extract(self, request):
        account_number = request.GET.get("numero_conta")
        password = request.GET.get("senha")

        if not password:
            return {"message": "Digite a senha"}

        account = self.__clean_account_number(account_number)
        if isinstance(account, dict):
            return account

        extract_account = {
            "depositos": [],
            "saques": [],
            "tranferencias_enviadas": [],
            "tranferencias_recebidas": [],
        }

        deposits_qs = Deposit.objects.filter(number_account=account.first().pk)
        extract_account["depositos"] = self.__deposit_and_withdraw_list(deposits_qs)

        withdraw_qs = Withdraw.objects.filter(number_account=account.first().pk)
        extract_account["saques"] = self.__deposit_and_withdraw_list(withdraw_qs)

        transfer_sent = Transfer.objects.filter(number_account_origin=account_number)
        extract_account["tranferencias_enviadas"] = self.__transfers_list(transfer_sent)

        transfer_received = Transfer.objects.filter(
            number_account_destiny=account_number
        )
        extract_account["tranferencias_recebidas"] = self.__transfers_list(
            transfer_received
        )

        return extract_account

    def post(self, request):
        data = json.loads(request.body)
        body = {
            "name": data.get("nome"),
            "cpf": data.get("cpf"),
            "birth_date": data.get("data_nascimento"),
            "phone": data.get("telefone"),
            "email": data.get("email"),
            "password": data.get("senha"),
        }

        valid, validated_data = self.__clean_data(body).values()
        if not valid:
            return JsonResponse(validated_data, status=400)

        new_user = User.objects.create(**validated_data)
        last_number = Accounts.objects.latest("pk").pk + 1
        Accounts.objects.create(
            number=last_number, user=get_object_or_404(User, id=new_user.pk)
        )

        return HttpResponse(status=201)

    def put(self, request, number_account):
        req_body = json.loads(request.body)
        body = {
            "name": req_body.get("nome"),
            "cpf": req_body.get("cpf"),
            "birth_date": req_body.get("data_nascimento"),
            "phone": req_body.get("telefone"),
            "email": req_body.get("email"),
            "password": req_body.get("senha"),
        }

        valid, validated_data = self.__clean_data(body, number_account).values()
        if not valid:
            return JsonResponse(validated_data, status=400)

        User.objects.filter(cpf=body.get("cpf")).update(**validated_data)

        return HttpResponse(status=204)

    def delete(self, request, number_account):
        account = Accounts.objects.filter(number=number_account).first()
        User.objects.filter(pk=account.user.pk).delete()
        account.delete()

        return HttpResponse(status=204)

    def __middleware(self, request):
        password_bank = Bank.objects.first().password
        req_query = request.GET.get("senha_banco")
        if not req_query:
            return {"message": "Senha não enviada"}
        if req_query != password_bank:
            return {"message": "Senha invalida"}
        return True

    def __clean_data(self, data, number_account=None):
        errors = {}

        validated_name = self.__clean_name(data.get("name"))
        if validated_name.get("message"):
            errors["message_name"] = validated_name.get("message")

        validated_cpf = self.__clean_cpf(data.get("cpf"), number_account)
        if validated_cpf.get("message"):
            errors["message_cpf"] = validated_cpf.get("message")

        validated_email = self.__clean_email(data.get("email"), number_account)
        if validated_email.get("message"):
            errors["message_email"] = validated_email.get("message")

        validated_phone = self.__clean_phone(data.get("phone"))
        if validated_phone.get("message"):
            errors["message_phone"] = validated_phone.get("message")

        validated_password = self.__clean_password(data.get("password"))
        if validated_password.get("message"):
            errors["message_password"] = validated_password.get("message")

        validated_birth_date = self.__clean_birth_date(data.get("birth_date"))
        if validated_birth_date.get("message"):
            errors["message_birth_date"] = validated_birth_date.get("message")

        if errors:
            return {"valid": False, "errors": errors}

        validated_data = {
            "name": validated_name.get("name"),
            "cpf": validated_cpf.get("cpf"),
            "phone": validated_phone.get("phone"),
            "email": validated_email.get("email"),
            "password": validated_password.get("password"),
            "birth_date": validated_birth_date.get("birth_date"),
        }

        return {"valid": True, "data": validated_data}

    def __clean_name(self, name: str):
        if not name:
            return {"message": "Digite o nome"}

        full_name = name.strip().split(" ")
        if len(full_name) < 2:
            return {"message": "Digite nome e sobrenome"}

        if len(full_name[0]) < 3 or len(full_name[-1]) < 3:
            return {"message": "Não utilize abreviações"}

        return {"name": name}

    def __clean_cpf(self, cpf: str, number_account=None):
        if not cpf:
            return {"message": "Digite um cpf"}

        cleaned_cpf = re.sub(r"\D", "", cpf)
        valid_cpf = CPF()
        if not valid_cpf.validate(cleaned_cpf):
            return {"message": "Digite um cpf valido"}

        cpf_exist = User.objects.filter(cpf=cpf).first()
        if cpf_exist:
            if number_account:
                account = Accounts.objects.filter(user__cpf=cpf).first()
                if account.number == number_account:
                    return {"cpf": cleaned_cpf}

            return {"message": "Cpf já cadastrado"}

        return {"cpf": cleaned_cpf}

    def __clean_email(self, email: str, number_account=None):
        if not email:
            return {"message": "Digite o email"}

        try:
            validate_email(email)
        except EmailNotValidError:
            return {"message": "Digite um email valido"}

        email_exist = User.objects.filter(email=email).first()
        if email_exist:
            if number_account:
                account = Accounts.objects.filter(user__email=email).first()
                if account.number == number_account:
                    return {"email": email}

            return {"message": "Email já cadastrado"}

        return {"email": email}

    def __clean_phone(self, phone: str):
        if not phone:
            return {"message": "Digite o telefone"}

        cleaned_phone = re.sub(r"\D", "", phone)
        parsed_phone = phonenumbers.parse(cleaned_phone, "BR")
        if phonenumbers.is_valid_number(parsed_phone) == False:
            return {"message": "Digite um telefone valido"}

        return {"phone": cleaned_phone}

    def __clean_password(self, password: str):
        if not password:
            return {"message": "Digite a senha"}

        if len(password) < 6:
            return {"message": "A senha deve ter no minimo 6 caracteres"}

        return {"password": password}

    def __clean_birth_date(self, birth_date: str):
        if not birth_date:
            return {"message": "Digite sua data de nascimento"}

        date_split = birth_date.split("-")
        if len(date_split) != 3:
            return {"message": "Digite a data no padrão correto: yyyy-mm-dd"}

        if (
            len(date_split[0]) != 4
            or len(date_split[1]) != 2
            or len(date_split[2]) != 2
        ):
            return {"message": "Digite a data no padrão correto: yyyy-mm-dd"}

        return {"birth_date": birth_date}

    def __clean_account_number(self, account_number):
        if not account_number:
            return {"message": "numero da conta é obrigatorio"}
        account = Accounts.objects.filter(number=account_number)
        if not account:
            return {"message": "A conta não foi encontrada"}
        return account

    def __deposit_and_withdraw_list(self, queryset):
        data_list = []
        for data in queryset:
            date_string = data.date.strftime("%Y-%m-%d %H:%M:%S")
            data_dict = {
                "data": date_string,
                "numero_conta": data.number_account.number,
                "valor": data.value,
            }
            data_list.append(data_dict)

        return data_list

    def __transfers_list(self, queryset):
        print("teste")
        print()

        data_list = []
        for data in queryset:
            date_string = data.date.strftime("%Y-%m-%d %H:%M:%S")
            data_dict = {
                "data": date_string,
                "numero_conta_origin": data.number_account_origin,
                "numero_conta_destiny": data.number_account_destiny,
                "valor": data.value,
            }
            data_list.append(data_dict)

        return data_list
