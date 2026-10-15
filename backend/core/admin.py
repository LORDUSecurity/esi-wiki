from django.contrib import admin

from .models import ContactMessage, Faq, Major, NewsItem


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "order"]


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ["question", "category", "order"]
    list_filter = ["category"]
    search_fields = ["question", "answer"]


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ["title", "tag", "published_at"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "created_at"]
    search_fields = ["name", "email", "subject"]
