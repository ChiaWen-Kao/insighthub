from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("projects/", views.projects, name="projects"),
    path("dashboard/create/", views.create_dashboard, name="create_dashboard"),
    path("dashboard/<int:pk>", views.dashboard, name="dashboard"),
    path("dashboard/<int:pk>/delete", views.delete_dashboard, name="delete_dashboard"),
    path("publicprojects/", views.publicProjects, name="publicProjects"),
    path("publicProjects/<int:pk>", views.publicDashboard, name="publicDashboard"),
    path("publicProjects/<int:pk>/comment", views.create_publicDashboard_comment, name="create_publicDashboard_comment"),
    path("publicProjects/<int:pk>/like/", views.create_publicDashboard_like, name="create_publicDashboard_like"),
]