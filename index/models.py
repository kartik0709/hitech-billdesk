from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, null=False, validators=[MinLengthValidator(5,
                                message="Username cannot be less than 5 characters")], max_length=50, blank=False)
    hash = models.TextField(null=False, blank=False)
    name = models.CharField(null=False, blank=False, max_length=50)
    purchase_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=2, null=False,
                                         validators=[MinValueValidator(Decimal('0.00'))])
    sale_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=2, null=False,
                                     validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username


class Purchase(models.Model):
    pid = models.CharField(max_length=100, unique=True, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    vendor = models.CharField(max_length=500, null=False, blank=False)
    purchase_price = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                         validators=[MinValueValidator(Decimal('0.00'))])
    percent_gst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                      validators=[MinValueValidator(Decimal('0.00'))])
    purchase_gst = models.DecimalField(null=False, blank=False, max_digits=19, decimal_places=2,
                                       validators=[MinValueValidator(Decimal('0.00'))])
    percent_cgst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                       validators=[MinValueValidator(Decimal('0.00'))])
    percent_sgst = models.DecimalField(null=False, blank=False, max_digits=19, decimal_places=2,
                                       validators=[MinValueValidator(Decimal('0.00'))])
    percent_igst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                       validators=[MinValueValidator(Decimal('0.0'))])
    purchase_igst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.00'))])
    total_purchase_tax = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                             validators=[MinValueValidator(Decimal('0.00'))])
    purchase_total = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                         validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        ordering = ["pid"]

    def __str__(self):
        return "{}".format(self.pid)


class SalePrice(models.Model):
    pid = models.OneToOneField(Purchase, on_delete=models.CASCADE, primary_key=True)
    sale_price = models.DecimalField(blank=True, null=True, max_digits=19, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    sale_gst = models.DecimalField(blank=True, null=True, max_digits=19, decimal_places=2,
                                   validators=[MinValueValidator(Decimal('0.00'))])
    sale_igst = models.DecimalField(blank=True, null=True, max_digits=19, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))])
    sale_tax = models.DecimalField(blank=True, null=True, max_digits=19, decimal_places=2,
                                   validators=[MinValueValidator(Decimal('0.00'))])
    sale_total = models.DecimalField(blank=True, null=True, max_digits=19, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        ordering = ["pid"]

    def __str__(self):
        return "{}".format(self.pid)


class Buyer(models.Model):
    pid = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    sale_price = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    sale_gst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                   validators=[MinValueValidator(Decimal('0.00'))])
    sale_igst = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))])
    sale_tax = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                   validators=[MinValueValidator(Decimal('0.00'))])
    sale_total = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])

    def __str__(self):
        return "{}-{}-{}".format(self.pid, self.name, self.quantity)


def date_time():
    return timezone.localtime(timezone.now())


class Transaction(models.Model):
    pid = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    price = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                validators=[MinValueValidator(Decimal('0.00'))])
    tax = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                              validators=[MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(blank=False, null=False, max_digits=19, decimal_places=2,
                                validators=[MinValueValidator(Decimal('0.00'))])
    type = models.CharField(max_length=8, choices=(('purchase', 'purchase'), ('sale', 'sale')))
    datetime = models.DateTimeField(default=date_time)

    class Meta:
        ordering = ["-datetime"]

    def __str__(self):
        return "{}-{}-----{}-{}".format(self.pid, self.quantity, self.datetime.date(), self.type)


@receiver(post_save, sender=Purchase)
def create_purchase_history(sender, instance, **kwargs):
    new = getattr(instance, '_new')
    quantity = getattr(instance, '_q')
    if new:
        Transaction.objects.create(
            pid=instance,
            name=instance.vendor,
            quantity=quantity,
            price=instance.purchase_price,
            tax=instance.total_purchase_tax,
            total=instance.purchase_total,
            type='purchase'
        )
        try:
            SalePrice.objects.get(pid=instance)
        except ObjectDoesNotExist:
            SalePrice.objects.create(
                pid=instance,
            )


@receiver(post_save, sender=Buyer)
def create_sale_item(sender, instance, **kwargs):
    item = Purchase.objects.get(pid=instance.pid)
    Transaction.objects.create(
        pid=item,
        name=instance.name,
        quantity=instance.quantity,
        price=instance.sale_price,
        tax=instance.sale_tax,
        total=instance.sale_total,
        type='sale'
    )
