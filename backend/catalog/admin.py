from django.contrib import admin

from .models import Module, Resource, Semester


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0
    search_fields = ["title"]


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "order"]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "semester", "block"]
    list_filter = ["semester", "block"]
    search_fields = ["title", "code"]
    inlines = [ResourceInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "module", "kind", "file_type", "size_kb"]
    list_filter = ["kind", "module__semester"]
    search_fields = ["title"]
