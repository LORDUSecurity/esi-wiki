from django.urls import path

from . import views

urlpatterns = [
    path("majors/", views.majors),
    path("faqs/", views.faqs),
    path("news/", views.news),
    path("overview/", views.overview),
    path("contact/", views.contact),
    path("contact-info/", views.contact_info),
]
