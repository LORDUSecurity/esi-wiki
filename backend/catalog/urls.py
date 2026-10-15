from django.urls import path

from . import views

urlpatterns = [
    path("semesters/", views.semesters),
    path("modules/", views.modules),
    path("modules/<slug:slug>/", views.module_detail),
    path("stats/", views.stats),
    path("hub/courses/", views.hub_courses),
    path("hub/reports/", views.hub_reports),
    path("hub/meta/", views.hub_meta),
]
