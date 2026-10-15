from rest_framework import serializers

from .models import ContactMessage, Faq, Major, NewsItem


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ["code", "name", "tagline", "description", "career_paths"]


class FaqSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Faq
        fields = ["id", "question", "answer", "category", "category_label"]


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = ["id", "title", "body", "tag", "published_at"]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "profile", "subject", "message"]

    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message trop court.")
        return value.strip()
