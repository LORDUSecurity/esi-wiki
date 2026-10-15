"""Answers computed from the database: no key, no network, no invented numbers.

The shareable sample build ships without an API key. This keeps the assistant
usable offline, and because every figure is read from the models it can only
state what the wiki actually holds — the failure mode is "je ne sais pas", not
a plausible-sounding rule.
"""

import re
import unicodedata

from catalog.models import HubCourse, HubReport, Module, Resource, Semester
from core.models import Faq, Major

STOPWORDS = set(
    """le la les un une des du de d au aux et ou a a sa son ses ce cet cette ces mon ma notre
    vos leur leurs qui que quoi dont pour par sans avec sur dans chez est sont etre etre puis
    je tu il elle on nous vous ils elles me te se y en as eu fait faire peut peux combien quel
    quelle quels quelles ya avait ont plus moins tres bien merci bonjour svp comme comment
    aussi donc voici voila apres avant toute tous encore juste""" .split()
)

KIND_LABEL = {
    "cours": "polycopié",
    "tp": "TP",
    "td": "TD",
    "exam": "examen",
    "resume": "résumé",
    "autre": "autre",
}

# Words every rule text contains; they cannot identify a subject on their own.
CATALOGUE_TERMS = {
    "module", "modules", "cours", "support", "supports", "document", "documents",
    "semestre", "semestres", "matiere", "matieres", "ue", "ubr",
}


def _fold(text):
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _tokens(text):
    # Two-letter words are elisions and articles ("qu", "ce", "au") and match any FAQ that
    # quotes them; semester codes are the only 2-char token worth keeping.
    return {
        t
        for t in re.findall(r"[a-z0-9][a-z0-9.]{1,}", _fold(text))
        if t not in STOPWORDS and (len(t) >= 3 or re.fullmatch(r"s[1-6]", t))
    }


MENTION_ORDER = ["Très Bien", "Bien", "Assez Bien", "Passable"]


def _mentions():
    """Thresholds read out of the FAQ text, never hardcoded here, so the rule has one source."""
    for faq in Faq.objects.filter(question__icontains="mention"):
        values = [
            float(v.replace(",", "."))
            for v in re.findall(r"(\d+(?:[.,]\d+)?)\s*/\s*20", _fold(faq.answer))
        ]
        if len(values) >= 2:
            pairs = sorted(zip(values, MENTION_ORDER), key=lambda p: p[0], reverse=True)
            return pairs, faq.answer.strip()
    return [], ""


def _grade(question_raw):
    """'Quelle mention pour 17 ?' shares no word with the rule — the number is the only clue."""
    folded = _fold(question_raw)
    if "mention" not in folded:
        return None

    ratios = re.findall(r"(\d{1,2}(?:[.,]\d+)?)\s*/\s*20", folded)
    if ratios:
        averages = [float(r.replace(",", ".")) for r in ratios]
    else:
        averages = [
            float(v.replace(",", "."))
            for v in re.findall(r"(?<![\d.])\d{1,2}(?:[.,]\d+)?(?![\d.])", folded)
        ]
    averages = [a for a in averages if 0 < a <= 20]

    grades, bareme = _mentions()
    if not grades or not averages:
        return None
    average = max(averages)
    awarded = next(((t, name) for t, name in grades if average >= t), None)
    if awarded is None:
        return (
            f"Pour {average:g}/20 : aucune mention (la plus basse s'obtient à "
            f"{grades[-1][0]:g}/20).\nBarème : {bareme}"
        )
    above = [t for t, _ in grades if t > average]
    gap = f" Il manque {min(above) - average:g}/20 pour la mention supérieure." if above else ""
    return f"Pour {average:g}/20 : {awarded[1]} (seuil {awarded[0]:g}/20).{gap}\nBarème : {bareme}"


def _hits(token, hay, fuzzy=True):
    # Prefix matching on a 6-char stem: singular/plural and accented variants of the
    # same word must not cost a match, or a rule question reads as "not documented".
    # 5 is too loose — "comme" then matches "Comment" and every FAQ ties.
    # Both words need 6 characters: "queries" used to match the article "qu" in
    # « Qu'est-ce qu'une année de réserve ? », and a fuzzy hit on a rule answers
    # `matched`, which shuts the corpus and the models out of the question.
    if token in hay:
        return True
    return bool(
        fuzzy
        and len(token) >= 6
        and any(h.startswith(token[:6]) or token.startswith(h[:6]) for h in hay if len(h) >= 6)
    )


def _covered(question_tokens, text, fuzzy=True):
    hay = _tokens(text)
    return [t for t in question_tokens if _hits(t, hay, fuzzy)]


def _score(question_tokens, text, fuzzy=True):
    return len(_covered(question_tokens, text, fuzzy))


def _kind_counts(module):
    counts = {}
    for kind in module.resources.values_list("kind", flat=True):
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _format_counts(counts):
    parts = []
    for kind, label in KIND_LABEL.items():
        if counts.get(kind):
            n = counts[kind]
            parts.append(f"{n} {label}{'s' if n > 1 else ''}")
    return ", ".join(parts)


def _numbers(question_tokens, question_raw=""):
    """Facts about the catalogue, straight out of the tables."""
    text = " ".join(question_tokens)
    raw = _fold(question_raw)
    lines = []

    if "semestre" in text:
        held = ", ".join(s.code for s in Semester.objects.all())
        indexed = ", ".join(sorted({c.semester for c in HubCourse.objects.only("semester")}))
        trunk = Module.objects.filter(origin="depot").values_list("semester__code", flat=True)
        lines.append(
            f"Le cycle ingénieur compte 6 semestres (S1 à S6). Ce wiki porte des modules et des "
            f"documents pour {held} : {' et '.join(sorted(set(trunk)))} viennent du dépôt de cours "
            f"du repo, S3 à S5 depuis le miroir du corpus EsiHub. EsiHub indexe {indexed}. "
            f"S6 n'a pas de modules : c'est l'année du PFE, avec {HubReport.objects.count()} "
            "rapports listés sur /esihub."
        )
    # "Il y a des modules en S6 ?" names a semester, so answer for that semester — but only
    # when the question is actually about the catalogue, not "un plan de révision pour S1".
    named = sorted({t.upper() for t in question_tokens if re.fullmatch(r"s[1-6]", t)})
    about_catalogue = (
        "module", "cours", "support", "document", "combien", "nombre", "index", "liste", "il y a",
    )
    if not any(w in raw for w in about_catalogue):
        named = []
    # A question that names a filière wants that filière's numbers, not the semester's total.
    branch = next(
        (
            b
            for b in Module.objects.exclude(branch="").values_list("branch", flat=True).distinct()
            if _fold(b) in question_tokens
        ),
        "",
    )
    for code in named:
        scope = {"semester__code": code, **({"branch": branch} if branch else {})}
        local_n = Module.objects.filter(**scope).count()
        mirrored_n = Module.objects.filter(**scope, origin="esihub").count()
        docs = Resource.objects.filter(**{"module__" + k: v for k, v in scope.items()})
        docs_n = docs.count()
        # A sample build carries the rows without the files: say where the documents actually open.
        here_n = sum(1 for r in docs if r.is_local)
        hub_n = HubCourse.objects.filter(
            semester=code, **({"branch": branch} if branch else {})
        ).count()
        label = f"{code} {branch}".strip()
        if local_n == hub_n == 0:
            lines.append(
                f"{label} : aucun module au catalogue, ni ici ni sur EsiHub"
                + (
                    f" — c'est l'année du PFE, avec {HubReport.objects.count()} rapports de stage "
                    "référencés sur /esihub."
                    if code == "S6"
                    else "."
                )
            )
        else:
            if here_n == docs_n:
                here = f"{local_n} modules et {docs_n} documents ouverts depuis ce wiki"
            elif here_n:
                here = f"{local_n} modules et {docs_n} documents, dont {here_n} copiés ici"
            else:
                here = f"{local_n} modules et {docs_n} documents, qui s'ouvrent depuis leur Drive"
            if mirrored_n:
                here += f" ({local_n - mirrored_n} du dépôt de cours, {mirrored_n} du corpus EsiHub)"
            lines.append(f"{label} : {here}, et {hub_n} cours indexés par EsiHub.")
    if "filiere" in text or "specialite" in text:
        majors = [f"{m.code} ({m.name})" for m in Major.objects.order_by("order")]
        lines.append(f"Filières décrites : {' ; '.join(majors)}.")
    if not named and ("module" in text or "matiere" in text or "cours" in text):
        lines.append(
            f"Ce wiki indexe {Module.objects.count()} modules et {Resource.objects.count()} documents."
        )
    # « Combien de documents sur les réseaux ? » is a count. Handed the module list, a model adds
    # it up and answers 16 — the right number, arrived at by luck. Counting belongs to the tables.
    subject = [
        t
        for t in question_tokens
        if t not in CATALOGUE_TERMS and not re.fullmatch(r"s[1-6]", t)
    ]
    if (
        subject
        and ("document" in text or "support" in text)
        and any(w in raw for w in ("combien", "nombre", "beaucoup"))
    ):
        # The module's own name, not its summary: "gestion électronique des documents" mentions
        # a réseau somewhere, and counting it made « les réseaux » answer 33 instead of 16.
        scored = sorted(
            (
                (_score(subject, f"{m.code} {m.title}"), m)
                for m in Module.objects.select_related("semester")
            ),
            key=lambda pair: -pair[0],
        )
        matching = [(score, module) for score, module in scored if score]
        if matching:
            total = sum(module.resources.count() for _, module in matching)
            listed = ", ".join(
                f"{module.code} {module.title} ({module.resources.count()})"
                for _, module in matching[:6]
            )
            lines.append(
                f"Les {len(matching)} modules sur « {' '.join(subject[:3])} » regroupent {total} "
                f"documents : {listed}."
            )
    if "esihub" in text or "annale" in text and "locale" not in text:
        courses = HubCourse.objects.all()
        if courses.exists():
            mirrored = Resource.objects.filter(origin="esihub").count()
            lines.append(
                f"EsiHub (esihub.net), relayé sur la page /esihub, indexe {courses.count()} modules "
                f"en S1 à S5 avec {sum(c.link_count for c in courses)} liens Drive, "
                f"et {HubReport.objects.count()} rapports de PFE. "
                + (
                    f"Une copie de {mirrored} de ces documents (S3 à S5) est téléchargée dans le "
                    "corpus du wiki et ouverte depuis le catalogue ; les autres restent sur leur Drive."
                    if mirrored
                    else "Ces fichiers restent sur leur Drive."
                )
            )
    if "pfe" in text or "rapport" in text:
        reports = HubReport.objects.exclude(report_url="")
        if reports.exists():
            top = ", ".join(r.title for r in reports[:3])
            lines.append(
                f"{HubReport.objects.count()} rapports de PFE sont référencés ({reports.count()} avec PDF "
                f"direct), par exemple : {top}. Le PFE occupe le semestre S6 : cette année-là ne "
                f"comporte pas de modules, seulement le stage et la soutenance."
            )
    return lines


def _about_filiere(raw):
    return any(w in raw for w in ("filiere", "specialite", "debouche", "parcours", "cycle"))


def _find_module(question_tokens, question_raw):
    raw = _fold(question_raw)
    # Catalogue words say what is being asked for, not which module: in « combien de documents
    # sur les réseaux », "documents" is a counting word, and counting it as subject matter ranked
    # the ECM module (whose summary talks about documents) above the networks answer.
    specific = [t for t in question_tokens if t not in CATALOGUE_TERMS]
    best, best_score = None, 0
    for module in Module.objects.select_related("semester"):
        # Mirrored modules are titled by their filière's own numbering, and their summary is
        # boilerplate ("documents EsiHub … corpus local") that would match any such question.
        haystack = " ".join([module.code, module.title, " ".join(module.tags or [])])
        if module.origin == "depot":
            haystack += " " + module.summary
        score = _score(specific, haystack) * 2
        # A bare code has to stand alone: "doc" inside « documents » and "5" inside « S5 »
        # are not somebody naming module DOC or module 5.
        code = _fold(module.code)
        if re.search(rf"(?<![\w.]){re.escape(code)}(?![\w.])", raw):
            score += 12  # an explicit module code outranks any word overlap
        if score > best_score:
            best, best_score = module, score
    return (best, best_score) if best_score >= 3 else (None, best_score)


def _find_faq(question_tokens):
    # Catalogue words are in every rule ("comment valider un module"), so they cannot carry
    # a match on their own: "combien de modules en S3" would otherwise fetch the grading rule.
    specific = [t for t in question_tokens if t not in CATALOGUE_TERMS]
    if not specific:
        return None, 0
    best, best_score = None, 0
    for faq in Faq.objects.all():
        in_q = set(_covered(specific, faq.question))
        in_a = set(_covered(specific, faq.answer))
        if not in_q:
            continue
        # One shared word is not a subject: « réussir l'année de césure » and « année de réserve »
        # have only "année" in common, and quoting the redoublement rule there is a wrong answer
        # that reads like the right one. Two words, or half the question, or say nothing.
        if len(in_q | in_a) < 2 and len(in_q | in_a) / len(specific) < 0.5:
            continue
        # A word in the question counts double: rules are indexed by how they are asked.
        score = 2 * len(in_q) + len(in_a)
        if score > best_score:
            best, best_score = faq, score
    return (best, best_score) if best_score >= 2 else (None, best_score)


def _find_major(question_tokens, question_raw=""):
    # Exact words only: every filière tagline names technologies ("réseaux", "cloud"), so a
    # fuzzy stem would answer a technical question with a career sheet. And even exact words
    # are only enough when the question is actually about a filière — « un diagramme de Gantt
    # en gestion de projet » shares "gestion" and "projet" with the ISSIC tagline.
    raw = _fold(question_raw)
    about_filiere = _about_filiere(raw)
    for major in Major.objects.all():
        if _fold(major.code) in question_tokens:
            return major
        # The tagline names the trades ("réseaux, cloud, infrastructure"), which the official
        # title often does not — and only a question about filières may reach for it.
        haystack = f"{major.code} {major.name}"
        if about_filiere:
            haystack += f" {major.tagline}"
        if about_filiere and _score(question_tokens, haystack, fuzzy=False):
            return major
    return None


def _major_line(major):
    paths = ", ".join(major.career_paths[:3]) if major.career_paths else ""
    return (
        f"{major.code} — {major.name}. {major.tagline.strip()}"
        + (f" Débouchés : {paths}." if paths else "")
    )


def _find_documents(question_tokens):
    """Catalogue files whose name carries the words asked for.

    The retrieval tier reads inside these documents; this only knows their titles, which is
    enough to answer « il y a des polycopiés Oracle ? » with the files and where to open them.
    """
    specific = [
        t for t in question_tokens
        if t not in CATALOGUE_TERMS and not re.fullmatch(r"s[1-6]", t)
    ]
    if not specific:
        return []
    hits = []
    for resource in Resource.objects.select_related("module", "module__semester"):
        covered = _covered(specific, resource.title)
        # One loose word is not a subject; a one-word question is the exception.
        if covered and (len(covered) >= 2 or len(specific) == 1):
            hits.append((len(covered), resource))
    hits.sort(key=lambda pair: -pair[0])
    return [r for _, r in hits[:8]]


def answer_locally(question):
    """Database-backed answer. `matched` is the contract with the view: when the
    retrieval layer found the fact, that reply is final — a free model quoted here
    invents counts (114 modules) and mention thresholds, so figures never route to it."""
    qt = _tokens(question)
    reply, sources = [], []

    grade = _grade(question)
    if grade:
        reply.append(grade)
        sources.append("/faq")

    module, _ = _find_module(qt, question)
    major = _find_major(qt, question)
    # « Quelle filière mène à l'administration des réseaux ? » asks for a filière, even though a
    # mirrored module is titled almost exactly that.
    if module and major and _about_filiere(_fold(question)):
        module = None
    if module:
        counts = _kind_counts(module)
        reply.append(
            f"{module.code} — {module.title} ({module.semester.title}, bloc {module.block}) : "
            f"{module.resources.count()} document(s) — {_format_counts(counts)}."
        )
        if module.summary:
            reply.append(module.summary.strip())
        sources.append(f"/programmes/{module.slug}")

    # Catalogue counts come before rules: "combien de modules EsiHub" is a count, and
    # the word "module" alone would otherwise drag in the validation rule.
    numbers = _numbers(qt, question)
    if numbers and not reply:
        # « Quelle filière mène à l'administration des réseaux ? » wants one filière named,
        # not the four-line inventory the counts tier produce. « Combien de modules l'ISSIC a-t-elle
        # en S4 ? » names a filière too, but it wants the number first.
        about = major and _about_filiere(_fold(question))
        counting = any(w in _fold(question) for w in ("combien", "nombre"))
        if about and not counting:
            reply = [_major_line(major)]
            sources.append("/programmes")
        reply += numbers
        sources.append("/api/stats/")
        if about and counting:
            reply.append(_major_line(major))
            sources.append("/programmes")

    faq, _ = _find_faq(qt)
    if faq:
        reply.append(f"Règlement — {faq.question}\n{faq.answer.strip()}")
        sources.append(f"/faq#{faq.category}")

    # A loose filière match only speaks when nothing more specific answered:
    # "securite" appears in a tagline, but a PFE question wants the PFE count.
    if not reply and major:
        reply.append(_major_line(major))
        sources.append("/programmes")

    if not reply:
        docs = _find_documents(qt)
        if docs:
            listed = "; ".join(
                f"{d.title} [{d.module.semester.code}"
                + (f" {d.module.branch}" if d.module.branch else "")
                + f" · module {d.module.code}]"
                for d in docs
            )
            reply.append(
                f"{len(docs)} document(s) du catalogue portent ce nom : {listed}. "
                "Ouvre le module depuis /programmes pour le télécharger."
            )
            sources.extend(f"/programmes/{d.module.slug}" for d in docs[:3])
        else:
            return {
                "reply": (
                    "Cette question sort de ce que la base locale documente : je ne l'ai pas trouvée "
                    "dans les modules, les documents ou le règlement chargés ici. Je préfère le dire "
                    "plutôt que d'inventer une règle. Reformule avec un code de module (1.1, 3.2…), "
                    "un mot du règlement, ou cherche le terme dans /programmes : la recherche "
                    "couvre aussi les noms des documents téléchargés de S3 à S5."
                ),
                "mode": "local",
                "model": "base de données locale",
                "sources": [],
                "matched": False,
            }

    return {
        "reply": "\n\n".join(reply),
        "mode": "local",
        "model": "base de données locale",
        "sources": sorted(set(sources)),
        "matched": True,
    }
