from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=255)
    Country = CountryField(max_length=20)
    Website = models.URLField(max_length=255, blank=True, null=True)
    Address = models.CharField(max_length=1023, blank=True, null=True)
    AccountManager = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        """Meta definition for Customers."""

        indexes = [
            models.Index(fields=['AccountManager',]),
            models.Index(fields=['Country',]),
        ]

class CustomerContact(models.Model):
    id = models.AutoField(primary_key=True)
    Customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    Name = models.CharField(max_length=255)
    Designation = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)

    class Meta:
        """Meta definition for Contact persons in customer."""

        indexes = [
            models.Index(fields=['Customer',]),
        ]

class CustomerContactDetails(models.Model):
    id = models.AutoField(primary_key=True)
    Customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    CustomerContact = models.ForeignKey(CustomerContact, on_delete=models.CASCADE, blank=True, null=True)
    PhoneNumber = models.CharField(max_length=50, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)

    class Meta:
        """Meta definition for contact details of customers."""

        indexes = [
            models.Index(fields=['Customer',]),
        ]