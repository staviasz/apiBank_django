from django.db import models


class Bank(models.Model):
    class Meta:
        verbose_name = "Banco"

    name = models.CharField("Nome", max_length=100, null=False)
    number = models.CharField("Numero da conta", max_length=20, null=False)
    agency = models.CharField("Agência", max_length=20, null=False)
    password = models.CharField("Senha", max_length=50, null=False)


class User(models.Model):
    class Meta:
        verbose_name = "Usuários"

    name = models.CharField("Nome", max_length=50, null=False)
    cpf = models.CharField("CPF", max_length=50, null=False, unique=True)
    phone = models.CharField("Telefone", max_length=50, null=False)
    email = models.EmailField("Email", max_length=254, null=False, unique=True)
    password = models.CharField("Senha", max_length=50, null=False)
    birth_date = models.DateField("Data de nascimento", null=False)


class Accounts(models.Model):
    class Meta:
        verbose_name = "Contas"

    number = models.CharField("Numero da Conta", max_length=50, null=False, unique=True)
    balance = models.FloatField("Saldo", null=False, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)


class Withdraw(models.Model):
    class Meta:
        verbose_name = "Saques"

    date = models.DateTimeField("Data", null=False, auto_now_add=True)
    number_account = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    value = models.FloatField("Valor", null=False)


class Deposit(models.Model):
    class Meta:
        verbose_name = "Depositos"

    date = models.DateTimeField("Data", null=False, auto_now_add=True)
    number_account = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    value = models.FloatField("Valor", null=False)


class Transfer(models.Model):
    class Meta:
        verbose_name = "Transferências"

    date = models.DateTimeField("Data", null=False, auto_now_add=True)
    number_account_origin = models.CharField(
        "Numero da conta", max_length=50, null=False
    )
    number_account_destiny = models.CharField(
        "Numero da conta", max_length=50, null=False
    )
    value = models.FloatField("Valor", null=False)
