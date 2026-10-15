from django.db import models


class Major(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=160)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    career_paths = models.JSONField(default=list, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Faq(models.Model):
    CATEGORY_CHOICES = [
        ("general", "Général & Administratif"),
        ("ingenieur", "Cycle Ingénieur"),
        ("examens", "Examens & Évaluations"),
        ("stages", "Stages & PFE"),
        ("discipline", "Règles Disciplinaires"),
    ]

    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["category", "order"]

    def __str__(self):
        return self.question[:60]


class NewsItem(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    tag = models.CharField(max_length=40, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    FULLNESS = [("prospective", "Étudiant pressenti"), ("student", "Étudiant actuel"),
                ("partner", "Partenaire"), ("other", "Autre")]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    profile = models.CharField(max_length=20, choices=FULLNESS, default="prospective")
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject}"
