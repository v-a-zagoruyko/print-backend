from django import forms
from .models import ContractorUser, ContractorOrder, OrderSupply

class OrderSupplyForm(forms.ModelForm):
    class Meta:
        model = OrderSupply
        fields = "__all__"
        # ["created_at", "date", "orders"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["orders"].queryset = ContractorOrder.objects.filter(
            contractor_user__status=ContractorUser.Status.ACTIVE,
            status=ContractorOrder.Status.CREATED
        )
