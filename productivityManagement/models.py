from django.db import models

#Recycle departments class from apparel management
from apparelManagement.models import Department

from apparelManagement import models as appModels

class OperationsBank (models.Model):
    """Data model for all the production operations."""

    id = models.AutoField(primary_key=True)
    Code = models.CharField(max_length=50)
    Name = models.CharField (max_length=255)
    Section = models.CharField (max_length=50)
    Category = models.CharField (max_length=50)
    SkillLevel = models.PositiveIntegerField()
    SMV = models.FloatField(default=0.0)
    MachineReq = models.BooleanField (default=True, blank=True, null=True)
    MachineType = models.CharField (max_length=50)
    Rate = models.FloatField (default=0.0)

class StitchOB (models.Model):
    """Data model for a style's stitching OB."""

    id = models.AutoField (primary_key=True)
    Style = models.ForeignKey (appModels.StyleCard, on_delete=models.CASCADE)
    Sequence = models.PositiveIntegerField(null=True, blank=True, default=1)
    Operation = models.ForeignKey (OperationsBank, on_delete=models.PROTECT, blank=True, null=True)
    Section = models.CharField (max_length=255, blank=True, null=True
                                ,help_text='Will choose OB section if blank.')
    IsStart = models.BooleanField (blank=True, null=True, default=False)
    IsEnd = models.BooleanField (blank=True, null=True, default=False)

    class Meta:
        #This reduces the loading time when reading the database, but increases writing time.
        indexes = [
            models.Index(fields=['Style']),
            models.Index(fields=['Section']),
        ]

class FinishOB (models.Model):
    """Data model for a style's Finishing OB."""

    id = models.AutoField (primary_key=True)
    Style = models.ForeignKey (appModels.StyleCard, on_delete=models.CASCADE)
    Sequence = models.PositiveIntegerField(null=True, blank=True, default=1)
    Operation = models.ForeignKey (OperationsBank, on_delete=models.PROTECT, blank=True, null=True)
    IsStart = models.BooleanField (blank=True, null=True, default=False)
    IsEnd = models.BooleanField (blank=True, null=True, default=False)

    class Meta:
        #This reduces the loading time when reading the database, but increases writing time.
        indexes = [
            models.Index(fields=['Style']),
        ]