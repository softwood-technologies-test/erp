from django.db import models

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