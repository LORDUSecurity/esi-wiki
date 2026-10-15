"""Build the catalog from the folders already in the repo — no hand-maintained list to drift."""
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Module, Resource, Semester

SEMESTERS = [("seson1", "S1", "Semestre 1"), ("seson2", "S2", "Semestre 2")]

# Grouping labels for the numbered blocks; the numbering itself comes from the folders.
BLOCK_LABELS = {
    1: "Fondamentaux informatiques",
    2: "Mathématiques",
    3: "Programmation",
    4: "Documentation et GED",
    5: "Réseaux et web",
    6: "Mathématiques appliquées et savoir",
    7: "Économie et gestion",
    8: "Communication et langues",
}

SUMMARIES = {
    "1.1": "Fonctionnement d'un ordinateur : représentation des données, architecture du processeur, mémoire et bus.",
    "1.2": "Concepts de système d'exploitation : processus, ordonnancement, gestion mémoire, fichiers et permissions.",
    "2.1": "Algèbre linéaire appliquée : matrices, déterminants, espaces vectoriels, diagonalisation.",
    "2.2": "Analyse réelle : suites, séries, calcul différentiel, intégration, mesures.",
    "3.1": "Bases de l'algorithmique : variables, structures conditionnelles et itératives, tableaux, procédures.",
    "3.2": "Pratique du langage Python : types, contrôle de flux, fonctions, numpy et matplotlib.",
    "4.1": "Gestion électronique des documents : cycle de vie du document, classement, numérisation, workflow.",
    "4.2": "Documents structurés : XML, schémas, transformation et modélisation de contenu.",
    "5.1": "Réseaux informatiques : modèle OSI et TCP/IP, adressage, commutation, routage, sécurité de base.",
    "5.2": "Réseaux sans fil et mobiles : Wi-Fi, protocoles cellulaires, mobilité et sécurité radio.",
    "6.1": "Théorie des graphes : chemins, arbres, coloration, flots et applications.",
    "6.2": "Optimisation : programmation linéaire, simplexe et modélisation de problèmes.",
    "7.1": "Économie générale : mécanismes de marché, offre, demande, acteurs et indicateurs.",
    "7.2": "Microéconomie et macroéconomie : comportement des agents, politique économique.",
    "8.1": "Techniques d'expression et de communication : écrit professionnel, prise de parole, argumentation.",
    "1.1s2": "Analyse et conception des systèmes d'information relationnels : modélisation conceptuelle et logique.",
    "1.2s2": "SGBDR et SQL : langage de définition et de manipulation de données, index, transactions.",
    "2.2s2": "Statistique descriptive : séries, dispersion, lois, échantillonnage et estimation.",
    "3.1s2": "Technologies web : HTML, CSS, JavaScript, protocole HTTP et intégration.",
    "3.2s2": "Programmation web en PHP : syntaxe, formulaires, POO et application dynamique.",
    "4.1s2": "Algorithmique avancée : structures de données complexes, récursivité, complexité.",
    "4.2s2": "Programmation avancée : objets, design patterns et code de qualité.",
    "5.1s2": "Enterprise Content Management : gestion du contenu d'entreprise et workflows documentaires.",
    "5.2s2": "E-services : services électroniques, commerce en ligne et dématérialisation.",
    "6.1s2": "Knowledge Management : capitalisation, partage et gouvernance du savoir organisationnel.",
    "6.2s2": "Veille technologique : collecte, analyse et diffusion de l'information stratégique.",
    "7.1s2": "Management et marketing : organisations, stratégie commerciale et pilotage.",
    "7.2s2": "Comptabilité générale : écritures, bilan, compte de résultat et normes.",
    "8.2s2": "English for General Purposes : communication professionnelle en anglais.",
}

KIND_RULES = [
    (re.compile(r"^\s*(tp|travaux\s*pratiques)", re.I), "tp"),
    (re.compile(r"^\s*(td|t\.d)", re.I), "td"),
    (re.compile(r"examen|corrige|corrigé|exame|rattrap", re.I), "exam"),
    (re.compile(r"resume|résumé|summary|synth", re.I), "resume"),
    (re.compile(r"cours|chapter|chapitre|lecture|crs|amphi|séance|seance", re.I), "cours"),
]


def kind_of(name):
    for pattern, kind in KIND_RULES:
        if pattern.search(name):
            return kind
    return "autre"


def clean(name):
    return unicodedata.normalize("NFC", name).replace("’", "'").strip()


class Command(BaseCommand):
    help = "Scan courses/ and (re)build semesters, modules and resources."

    def add_arguments(self, parser):
        parser.add_argument("--root", default=str(Path(settings.MEDIA_ROOT)))

    def handle(self, *args, **opts):
        root = Path(opts["root"])
        if not root.exists():
            self.stderr.write(self.style.ERROR(f"No such courses root: {root}"))
            return

        # Only this command's own rows: seed_mirror owns the mirrored semesters, and wiping
        # them from here would silently take S3-S5 out of the catalogue.
        Module.objects.filter(origin="depot").delete()
        Semester.objects.filter(code__in=[code for _, code, _ in SEMESTERS]).delete()

        modules = resources = 0
        for order, (folder, code, title) in enumerate(SEMESTERS, start=1):
            sem_dir = root / folder
            if not sem_dir.is_dir():
                self.stderr.write(self.style.WARNING(f"Missing folder {sem_dir}"))
                continue
            sem = Semester.objects.create(code=code, title=title, order=order)
            for mod_dir in sorted(p for p in sem_dir.iterdir() if p.is_dir()):
                name = clean(mod_dir.name)
                match = re.match(r"^(\d+(?:\.\d+)?)\s*[-–]\s*(.+)$", name)
                if match:
                    mod_code, mod_title = match.group(1), match.group(2)
                else:
                    mod_code, mod_title = "0.0", name
                block = int(mod_code.split(".")[0])
                summary_key = mod_code if order == 1 else f"{mod_code}s2"
                slug = slugify(f"{code}-{mod_code}-{mod_title}")[:200]
                module = Module.objects.create(
                    code=mod_code,
                    title=clean(mod_title),
                    slug=slug,
                    semester=sem,
                    block=block,
                    folder=f"{folder}/{mod_dir.name}",
                    summary=SUMMARIES.get(summary_key, ""),
                    tags=[BLOCK_LABELS.get(block, f"Bloc {block}")],
                )
                modules += 1
                for path in sorted(mod_dir.rglob("*")):
                    if not path.is_file() or path.suffix.lower() not in {
                        ".pdf", ".docx", ".doc", ".pptx", ".zip", ".rar", ".txt", ".xlsx", ".csv", ".sql", ".accdb"
                    }:
                        continue
                    Resource.objects.create(
                        module=module,
                        title=clean(path.stem).replace("_", " ")[:300],
                        path=str(path.relative_to(root)).replace("\\", "/"),
                        kind=kind_of(path.name),
                        file_type=path.suffix.lower().lstrip("."),
                        size_kb=max(1, path.stat().st_size // 1024),
                    )
                    resources += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {modules} modules / {resources} resources"))
