from django.conf import settings
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalog.models import Module

from .models import ContactMessage, Faq, Major, NewsItem
from .serializers import ContactSerializer, FaqSerializer, MajorSerializer, NewsSerializer


@api_view(["GET"])
def majors(request):
    return Response(MajorSerializer(Major.objects.all(), many=True).data)


@api_view(["GET"])
def faqs(request):
    items = Faq.objects.all()
    grouped = {}
    for f in items:
        grouped.setdefault(f.category, {"category": f.category,
                                        "label": f.get_category_display(), "items": []})
        grouped[f.category]["items"].append(FaqSerializer(f).data)
    return Response(list(grouped.values()))


@api_view(["GET"])
def news(request):
    return Response(NewsSerializer(NewsItem.objects.all()[:12], many=True).data)


@api_view(["GET"])
def overview(request):
    return Response({
        "majors": Major.objects.count(),
        "modules": Module.objects.count(),
        "blocks": sorted(set(Module.objects.values_list("block", flat=True))),
        "faqs": Faq.objects.count(),
    })


@api_view(["GET"])
def contact_info(request):
    """What the site publishes as its own address, so the number never has to be in the repo."""
    return Response({"email": settings.CONTACT_EMAIL, "phone": settings.CONTACT_PHONE})


@api_view(["POST"])
def contact(request):
    serializer = ContactSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"status": "received"}, status=201)
