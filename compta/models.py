from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from uuid import uuid4
from decimal import Decimal
from compta.datiti.compta import OperationUtils


class Account(models.Model):
    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')

    id = models.CharField(_('Identifier'), primary_key=True, editable=True, max_length=25)
    label = models.CharField(_('Label'), max_length=255)
    description = models.CharField(_('Description'), max_length=1024, blank=True)

    def __str__(self):
        return self.label


class OperationManager(models.Manager):
    def operation_count(self, account):
        return self.filter(account=account).count()


class Operation(models.Model):
    class Meta:
        verbose_name = _('Operation')
        verbose_name_plural = _('Operations')

    DEBIT = -1
    CREDIT = 1
    DEBIT_OR_CREDIT = (
        (DEBIT, _('Debit')),
        (CREDIT, _('Credit')),
    )

    id = models.UUIDField(_('Identifier'), primary_key=True, default=uuid4, editable=False)
    operation_date = models.DateField(_('Operation Date'))
    input_date = models.DateField(_('Input Date'), auto_now_add=True)
    label = models.CharField(_('Label'), max_length=128)
    debit_or_credit = models.IntegerField(_('Debit or credit'), choices=DEBIT_OR_CREDIT)

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name=_('Account'),
        related_name='operations'  # If you want reverse access, otherwise keep '+'
    )

    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    all_tax_included = models.BooleanField(_('All tax included'), default=True)
    apply_vat = models.BooleanField(_('Do apply VAT?'), default=True)
    vat_rate = models.DecimalField(_('VAT rate'), max_digits=5, decimal_places=2, default=Decimal('0.00'), blank=True)
    apply_provision = models.BooleanField(_('Do apply provision?'), default=True)
    provision_rate = models.DecimalField(_('Provision rate'), max_digits=5, decimal_places=2, default=Decimal('40.00'), blank=True)
    comment = models.CharField(_('Comment'), max_length=1024, blank=True)

    objects = OperationManager()
    utils = None  # For internal use only

    def init_utils(self):
        if not self.utils:
            self.utils = OperationUtils(
                amount=self.amount,
                vat_rate=self.vat_rate,
                apply_vat=self.apply_vat,
                all_tax_included=self.all_tax_included,
                apply_provision=self.apply_provision,
                provision_rate=self.provision_rate,
                debit_or_credit=self.debit_or_credit,
            )

    @property
    def gross_amount(self) -> Decimal:
        self.init_utils()
        return Decimal(self.utils.gross_amount())
    gross_amount.fget.short_description = _('Gross Amount (€)')

    @property
    def vat_amount(self) -> Decimal:
        self.init_utils()
        return Decimal(self.utils.vat_amount())
    vat_amount.fget.short_description = _('VAT Amount (€)')

    @property
    def provision_amount(self) -> Decimal:
        self.init_utils()
        return Decimal(self.utils.provision_amount())
    provision_amount.fget.short_description = _('Provision Amount (€)')

    def clean(self):
        errors = []

        # Normalize VAT/provision rates based on toggles
        if not self.apply_vat:
            self.vat_rate = Decimal('0.00')

        if not self.apply_provision:
            self.provision_rate = Decimal('0.00')

        if self.amount <= 0:
            errors.append(ValidationError(_('Amount must be a positive number')))

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        try:
            return f"[{_('Operation Date')}:{self.operation_date.strftime('%Y %b %d')}] " \
                   f"[{_('Account')}:{self.account}] {self.label}: {self.gross_amount} €"
        except Exception:
            return f"{self.label or _('Operation')} (invalid data)"
