from django.db import models
from django.contrib.auth.models import User


# User's Role
class Roles(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name}"


# User (Custom User Model Extension)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to Django's user model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.ForeignKey("Roles", on_delete=models.SET_NULL, null=True, default=2)

    def __str__(self):
        return f"{self.id}"


# Chart Type
class Chart_Types(models.Model):
    chart_type = models.CharField(max_length=255)

    def __str__(self):
        return self.chart_type


# Datasets
class Datasets(models.Model):
    name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to="uploads/", blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dashboard = models.ForeignKey("Dashboards", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.id}"


# Dataset Columns
class Dataset_Columns(models.Model):
    column_name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255)
    dataset = models.ForeignKey("Datasets", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.column_name} ({self.dataset})"


# Selected Columns
class Selected_Columns(models.Model):
    AXIS_CHOICES = (
        ("x", "X Axis"),
        ("y", "Y Axis"),
        ("category", "Category"),
        ("series", "Series"),
    )
    axis_type = models.CharField(max_length=255, choices=AXIS_CHOICES)
    chart = models.ForeignKey("Charts", on_delete=models.CASCADE, null=True)
    column = models.ForeignKey("Dataset_Columns", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.axis_type} → {self.column.column_name} (Chart ID: {self.chart_id})"
        

# Dashboard
class Dashboards(models.Model):
    name = models.CharField(max_length=255, default="Untitled Dashboard")
    description = models.CharField(max_length=255, default="")
    status = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    chart = models.ForeignKey("Charts", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.id}"


# Chart
class Charts(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dashboard = models.ForeignKey("Dashboards", on_delete=models.SET_NULL, null=True)
    dataset = models.ForeignKey("Datasets", on_delete=models.SET_NULL, null=True)
    chart_type = models.ForeignKey("Chart_Types", on_delete=models.SET_NULL, null=True) 

    def __str__(self):
        return f"{self.id}"


# Social comment
class Social_Comment(models.Model):
    comment = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dashboard = models.ForeignKey("Dashboards", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.comment


# Social like
class Social_Like(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dashboard = models.ForeignKey("Dashboards", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.comment