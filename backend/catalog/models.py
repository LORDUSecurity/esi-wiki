from django.conf import settings
from django.db import models

# Where a row's files physically live: the git clone (`courses/`) or the mirrored EsiHub
# Drive corpus (`corpus/`, gitignored). It decides the URL prefix they are served under.
ORIGIN_CHOICES = [
    ("depot", "Dépôt de cours"),
    ("esihub", "Corpus EsiHub"),
]


class Semester(models.Model):
    code = models.CharField(max_length=8, unique=True)
    title = models.CharField(max_length=120)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Module(models.Model):
    """A teaching unit, named after the folder it lives in, e.g. '3.2 - Programmation Python'."""

    code = models.CharField(max_length=16)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    semester = models.ForeignKey(Semester, related_name="modules", on_delete=models.CASCADE)
    block = models.PositiveSmallIntegerField(default=1, help_text="Coeficient block 1-8")
    # Filière, known from S3 on; empty for the S1-S2 trunk every branch shares.
    branch = models.CharField(max_length=16, blank=True)
    origin = models.CharField(max_length=12, choices=ORIGIN_CHOICES, default="depot")
    folder = models.CharField(max_length=300, blank=True)
    summary = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["semester__order", "branch", "code"]
        indexes = [models.Index(fields=["block"]), models.Index(fields=["branch"])]
        unique_together = [("semester", "branch", "code")]

    def __str__(self):
        return f"{self.code} — {self.title}"


class Resource(models.Model):
    KIND_CHOICES = [
        ("cours", "Cours"),
        ("tp", "TP"),
        ("td", "TD"),
        ("exam", "Examen"),
        ("resume", "Résumé"),
        ("autre", "Autre"),
    ]

    module = models.ForeignKey(Module, related_name="resources", on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    path = models.CharField(max_length=600, help_text="Path relative to MEDIA_ROOT")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="autre")
    origin = models.CharField(max_length=12, choices=ORIGIN_CHOICES, default="depot")
    # Lets a mirrored document still open when the 2 Go corpus is not on the machine
    # (a clone, or the stripped sample build): the link falls back to its Drive page.
    drive_id = models.CharField(max_length=40, blank=True)
    file_type = models.CharField(max_length=20, blank=True)
    size_kb = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["title"]
        unique_together = [("module", "path")]

    def __str__(self):
        return self.title

    @property
    def url(self):
        if self.origin != "esihub":
            return f"/courses/{self.path}"
        # /polycopies/ is the mirrored corpus; see config.urls.
        if not self.drive_id or (settings.CORPUS_DIR / self.path).is_file():
            return f"/polycopies/{self.path}"
        return f"https://drive.google.com/file/d/{self.drive_id}/view"

    @property
    def is_local(self):
        return not self.url.startswith("http")


class HubCourse(models.Model):
    """A course listed on esihub.net; its files stay on Google Drive, we only link out."""

    branch = models.CharField(max_length=16, help_text="ICSD, IDC, IIN, ISSIC, ISITD, MSICS")
    semester = models.CharField(max_length=4, help_text="S1..S5")
    year = models.CharField(max_length=16, blank=True)
    code = models.CharField(max_length=16, blank=True)
    title = models.CharField(max_length=240)
    links = models.JSONField(default=dict, help_text="{'cours': url, 'examen': url, 'resume': url}")

    class Meta:
        ordering = ["branch", "semester", "code", "title"]
        # A course can be listed for two promotion years with different documents.
        unique_together = [("branch", "semester", "year", "title")]
        verbose_name = "cours EsiHub"
        verbose_name_plural = "cours EsiHub"

    def __str__(self):
        return f"{self.branch} {self.semester} — {self.title}"

    @property
    def link_count(self):
        return len(self.links)


class HubReport(models.Model):
    """A PFE report catalogued on esihub.net; the PDF itself stays on Google Drive."""

    title = models.CharField(max_length=300, unique=True)
    engineer = models.CharField(max_length=160, blank=True)
    organisation = models.CharField(max_length=300, blank=True)
    promotion = models.CharField(max_length=8, blank=True)
    language = models.CharField(max_length=16, blank=True)
    tags = models.JSONField(default=list, blank=True)
    abstract = models.TextField(blank=True)
    report_url = models.URLField(max_length=400, blank=True)
    page = models.URLField(max_length=400, blank=True)

    class Meta:
        ordering = ["-promotion", "title"]
        verbose_name = "rapport de PFE EsiHub"
        verbose_name_plural = "rapports de PFE EsiHub"

    def __str__(self):
        return self.title


class CorpusDoc(models.Model):
    """A file mirrored from an EsiHub Drive folder (see tools/esihub_fetch.py).

    Only the local copy is indexed; the originals stay on their Drive.
    """

    drive_id = models.CharField(max_length=40, unique=True)
    path = models.CharField(
        max_length=400,
        help_text="Relative to the corpus folder, or to courses/ for the repo's own files",
    )
    name = models.CharField(max_length=200)
    semester = models.CharField(max_length=4, blank=True)
    branch = models.CharField(max_length=16, blank=True)
    module_code = models.CharField(max_length=32, blank=True)
    kind = models.CharField(max_length=16, blank=True)
    bytes = models.PositiveIntegerField(default=0)
    pages = models.PositiveIntegerField(default=0)
    chars = models.PositiveIntegerField(default=0)
    indexed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["semester", "branch", "module_code", "name"]
        verbose_name = "document du corpus"
        verbose_name_plural = "documents du corpus"

    def __str__(self):
        return f"{self.name} ({self.branch} {self.semester} {self.module_code})"


class CorpusChunk(models.Model):
    """A slice of extracted text, addressed by rowid from the FTS5 index."""

    document = models.ForeignKey(CorpusDoc, related_name="chunks", on_delete=models.CASCADE)
    seq = models.PositiveIntegerField(default=0)
    text = models.TextField()

    class Meta:
        ordering = ["document", "seq"]
        unique_together = [("document", "seq")]

    def __str__(self):
        return f"{self.document.name} #{self.seq}"
