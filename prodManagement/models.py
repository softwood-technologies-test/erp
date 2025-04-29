from django.db import models
from apparelManagement.models import Department

class Operation(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=511)
    Section = models.CharField(max_length=31)
    Category = models.CharField(max_length=31)
    SkillLevel = models.PositiveIntegerField()
    SMV = models.FloatField(null=True, blank=True)
    MachineRequirement = models.BooleanField(default=False)
    MachineType = models.CharField(max_length=31)
    Rate = models.FloatField(null=True, blank=True)
    Code = models.CharField(max_length=31, blank=True, null=True)

    class Meta:
        """Meta definition for Operations."""

        indexes = [
            models.Index(fields=['Section']),
            models.Index(fields=['MachineType']),
        ]

class Machines(models.Model):
    id = models.AutoField(primary_key=True)
    MachineId = models.CharField(max_length=31)
    PurchaseDate = models.DateField(auto_now_add=True)
    Type = models.CharField(max_length=63)
    FunctionStatus = models.CharField(max_length=15)
    Manufacturer = models.CharField(max_length=15, blank=True, null=True)
    ModelNumber = models.CharField(max_length=25, null=True, blank=True)
    SerialNumber = models.CharField(max_length=15, null=True, blank=True)
    Department = models.ForeignKey(Department, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        """Meta definition for Machines."""

        indexes = [
            models.Index(fields=['FunctionStatus', 'Department'])
        ]