from django.contrib import admin
from django.contrib.auth.models import Group
from .models import CustomUser, Saved, Transaction
from decimal import Decimal


try:
    admin.site.unregister(Group)
except admin.exceptions.NotRegistered:
    pass

# Обычная регистрация твоих моделей
admin.site.register(CustomUser)
admin.site.register(Saved)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'created_at', 'is_confirmed']
    fields = ['user', 'amount', 'is_confirmed']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            try:
                Decimal(str(obj.amount))
            except:
                obj.amount = Decimal('0.00')
        return form

    def save_model(self, request, obj, form, change):
        # Начисляем деньги только при подтверждении
        if change and obj.is_confirmed:
            old_obj = Transaction.objects.filter(pk=obj.pk).first()
            if old_obj and not old_obj.is_confirmed:
                user = obj.user
                user.balance += obj.amount
                user.save()

        super().save_model(request, obj, form, change)