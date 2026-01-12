from django.contrib import admin
from .models import  CustomUser ,Saved ,Transaction
from django.contrib.auth.models import Group
# Register your models here.
admin.site.unregister(Group)
admin.site.register(CustomUser)
admin.site.register(Saved)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'is_confirmed', 'created_at']
    list_filter = ['is_confirmed']

    def save_model(self, request, obj, form, change):
        # Если мы меняем существующую запись и ставим is_confirmed = True
        if change and obj.is_confirmed:
            # Берем оригинальную запись из базы, чтобы не начислить деньги дважды
            original_obj = Transaction.objects.get(pk=obj.pk)
            if not original_obj.is_confirmed:
                user = obj.user
                user.balance += obj.amount
                user.save()

        super().save_model(request, obj, form, change)