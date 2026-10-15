"""Import the majors and the regulation FAQ that the old static pages carried inline."""
from django.core.management.base import BaseCommand

from core.models import Faq, Major, NewsItem

MAJORS = [
    ("ISSIC", "Ingénierie des Systèmes et Sécurité des SI et des Communications",
     "Sécurité des systèmes d'information, cryptographie, gestion des risques et audit.",
     ["Ingénieur cybersécurité", "Auditeur SI", "Administrateur sécurité", "Consultant en gestion des risques"]),
    ("ISITD", "Ingénierie des Systèmes d'Information et Technologies du Document",
     "Bibliothèques numériques, gestion documentaire et systèmes d'archivage.",
     ["Ingénieur documentaire", "Responsable GED/ECM", "Archiviste numérique"]),
    ("INN", "Ingénierie Numérique et Networks",
     "Réseaux, cloud, infrastructure et développement logiciel moderne.",
     ["Ingénieur réseau", "Administrateur systèmes", "Cloud engineer", "Développeur"]),
    ("ICSD", "Ingénierie des Connaissances et Science des Données",
     "Science des données, intelligence artificielle, connaissance et décision.",
     ["Data scientist", "Ingénieur big data", "Consultant business intelligence"]),
]

FAQS = [
    ("general", "Quelle est la mission principale de l'ESI ?",
     "Former des ingénieurs en sciences de l'information, assurer la recherche, et contribuer au développement de la société de l'information au Maroc."),
    ("general", "Quels diplômes sont délivrés par l'ESI ?",
     "Ingénieur d'État, Master, Master Spécialisé, et Doctorat."),
    ("general", "Quels sont les partenaires internationaux de l'ESI ?",
     "Ajman University, CNAM (France), Université de Montréal, Oracle Academy, Huawei ICT Academy."),
    ("ingenieur", "Comment valider un module en Cycle Ingénieur ?",
     "Note ≥ 12/20, avec aucun élément de module < 5/20. Compensation possible si moyenne ≥ 6/20."),
    ("ingenieur", "Quels sont les stages obligatoires en Cycle Ingénieur ?",
     "Stage Ouvrier (SO), Stage d'Études (SE), et Stage de Fin d'Études (SFE) avec PFE."),
    ("ingenieur", "Comment est calculée la Moyenne Générale des Études (MGE) ?",
     "MGE = (MA1 + MA2 + MS5 + MS6) / 4."),
    ("ingenieur", "Quelles mentions existent pour le diplôme d'Ingénieur ?",
     "Très Bien (≥ 18/20), Bien (≥ 16/20), Assez Bien (≥ 14/20), Passable (≥ 12/20)."),
    ("ingenieur", "Qu'est-ce qu'une « année de réserve » ?",
     "Redoublement partiel si moyenne ≥ 6/20, pour repasser uniquement les modules non validés."),
    ("ingenieur", "Quels sont les débouchés de la filière ICSD ?",
     "Data Scientist, Ingénieur Big Data, Consultant en Business Intelligence."),
    ("ingenieur", "Quelles compétences vise la filière Cyberdéfense (ISSIC) ?",
     "Sécurité des SI, cryptographie, gestion des risques, audit de sécurité."),
    ("examens", "Comment sont organisées les sessions d'examens finaux ?",
     "Sur 8 jours en fin de semestre, avec 2 éléments de modules différents évalués par jour."),
    ("examens", "Que se passe-t-il en cas d'absence à un examen ?",
     "Note zéro, mais droit au rattrapage si justifiée (sauf pour les soutenances)."),
    ("examens", "Quelles sanctions pour fraude aux examens ?",
     "Exclusion, note zéro, blâme, redoublement, ou exclusion définitive selon la gravité."),
    ("examens", "Comment consulter ses copies après correction ?",
     "Les étudiants ont 48h pour contester une note après consultation."),
    ("examens", "Quel est le délai de communication des notes ?",
     "15 jours maximum après l'évaluation."),
    ("stages", "Que risque un étudiant en retard pour déposer son rapport de stage ?",
     "Pénalités de 2 à 6 points selon le retard, plafonnement à 12/20, ou refus après 15 jours."),
    ("stages", "Comment est évalué le Projet de Fin d'Études (PFE) ?",
     "Par un jury (note intégrant mémoire, soutenance, et évaluation du tuteur)."),
    ("stages", "Peut-on changer d'organisme d'accueil pour un stage ?",
     "Oui, une seule fois, avec décharge de l'organisme initial et nouvelle convention."),
    ("discipline", "Que se passe-t-il si un étudiant dépasse 30% d'absences ?",
     "Note zéro pour l'élément et non-validation du module."),
    ("discipline", "Comment sont gérés les plagiats ?",
     "Sanctions similaires à la fraude (note zéro, non-validation, exclusion possible)."),
    ("discipline", "Quels outils sont utilisés pour l'enseignement à distance ?",
     "Plateformes de l'ESI, avec ≤ 20% du volume horaire d'un module à distance."),
]

NEWS = [
    ("Wiki ESI en ligne", "Cours, TP, TD et annales des deux semestres, regroupés par module et par filière.", "Ressources"),
    ("Assistant IA du règlement", "Posez une question sur les modules, les examens, les stages ou les filières.", "Nouveauté"),
    ("Bibliothèque documentaire", "Plus de 190 supports : polycopiés, fiches de TP, sujets et corrigés.", "Campus"),
]


class Command(BaseCommand):
    help = "Load majors, FAQ and news items."

    def handle(self, *args, **opts):
        Major.objects.all().delete()
        for order, (code, name, tagline, careers) in enumerate(MAJORS, start=1):
            Major.objects.create(code=code, name=name, tagline=tagline,
                                 description=tagline, career_paths=careers, order=order)

        Faq.objects.all().delete()
        counters = {}
        for category, question, answer in FAQS:
            counters[category] = counters.get(category, 0) + 1
            Faq.objects.create(category=category, question=question, answer=answer,
                               order=counters[category])

        NewsItem.objects.all().delete()
        for title, body, tag in NEWS:
            NewsItem.objects.create(title=title, body=body, tag=tag)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Major.objects.count()} majors / {Faq.objects.count()} FAQ / {NewsItem.objects.count()} news"))
