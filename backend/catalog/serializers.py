from rest_framework import serializers

from .models import HubCourse, HubReport, Module, Resource, Semester


class ResourceSerializer(serializers.ModelSerializer):
    url = serializers.CharField(read_only=True)
    # False when the mirrored copy is not on this machine and the link goes to Drive.
    is_local = serializers.BooleanField(read_only=True)

    class Meta:
        model = Resource
        fields = ["id", "title", "kind", "origin", "is_local", "file_type", "size_kb", "path", "url"]


class ModuleListSerializer(serializers.ModelSerializer):
    semester = serializers.CharField(source="semester.title", read_only=True)
    semester_code = serializers.CharField(source="semester.code", read_only=True)
    resource_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Module
        fields = ["id", "slug", "code", "title", "block", "branch", "origin", "semester",
                  "semester_code", "resource_count", "summary", "tags"]


class ModuleDetailSerializer(ModuleListSerializer):
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta(ModuleListSerializer.Meta):
        fields = ModuleListSerializer.Meta.fields + ["resources", "folder"]


class SemesterSerializer(serializers.ModelSerializer):
    modules = ModuleListSerializer(many=True, read_only=True)
    module_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Semester
        fields = ["id", "code", "title", "order", "module_count", "modules"]


class HubCourseSerializer(serializers.ModelSerializer):
    link_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HubCourse
        fields = ["id", "branch", "semester", "year", "code", "title", "links", "link_count"]


class HubReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HubReport
        fields = ["id", "title", "engineer", "organisation", "promotion", "language",
                  "tags", "abstract", "report_url", "page"]
