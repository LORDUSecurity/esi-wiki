import json
import urllib.error
import urllib.request

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalog import corpus
from catalog.models import HubCourse, HubReport, Resource, Semester
from core.models import Faq, Major

from .local import answer_locally

MAX_TURNS = 12
CONTEXT_CHARS = 12000


def build_context():
    """Ground the assistant in what this site actually documents.

    Kept compact and complete on purpose: an earlier version truncated the module list
    mid-way and the model happily reported a wrong count.
    """
    parts = [
        "Le cycle ingénieur de l'ESI compte six semestres, S1 à S6. S6 n'a pas de modules : "
        "c'est l'année du PFE (stage + soutenance), indexée via les rapports de stage."
    ]
    parts.append("Filières:")
    for m in Major.objects.all():
        parts.append(f"- {m.code}: {m.name} — {m.tagline}")

    for sem in Semester.objects.prefetch_related("modules__resources"):
        mods = list(sem.modules.all())
        parts.append(f"\n{sem.title} ({sem.code}) — {len(mods)} modules:")
        # From S3 on the same unit number exists in several filières: naming the filière keeps
        # "le module 4.2" from being answered with another branch's documents.
        for mod in mods:
            parts.append(
                f"- {mod.branch or 'tronc commun'} {mod.code} {mod.title} "
                f"[{mod.resources.count()} docs]"
            )

    parts.append("\nRèglement / FAQ:")
    for f in Faq.objects.all():
        parts.append(f"- Q: {f.question}\n  R: {f.answer}")

    courses = HubCourse.objects.all()
    if courses.exists():
        branches = sorted({c.branch for c in courses})
        mirrored = Resource.objects.filter(origin="esihub").count()
        local_note = (
            f"{mirrored} de ces documents (les semestres S3 à S5) ont été téléchargés : ils sont "
            "comptés dans le catalogue local ci-dessus et s'ouvrent depuis ce wiki. Les autres "
            "restent sur le Google Drive d'EsiHub et ne comptent pas ici."
            if mirrored
            else "Ces fichiers sont hébergés sur le Google Drive d'EsiHub, pas dans ce wiki : "
            "ils ne comptent pas dans les documents du catalogue local."
        )
        parts.append(
            f"\nDépôt externe EsiHub (esihub.net), relayé sur la page /esihub : "
            f"{courses.count()} modules indexés pour les filières {', '.join(branches)} "
            f"sur les semestres S1 à S5, et {HubReport.objects.count()} rapports de PFE. "
            + local_note
        )
    return "\n".join(parts)[:CONTEXT_CHARS]


SYSTEM_PROMPT = (
    "Tu es l'assistant du Wiki ESI (École de Sciences de l'Information, Rabat). "
    "Réponds en français de façon concise et utile à un étudiant. "
    "Deux régimes, ne les confonds jamais. "
    "1) Ce qui regarde l'ESI elle-même — règles, notes, mentions, semestres, modules, documents : "
    "réponds uniquement à partir du contexte vérifié fourni ; s'il ne couvre pas la question, "
    "dis-le et renvoie au catalogue ou à la FAQ plutôt que d'inventer une règle ou une note. "
    "2) Un concept informatique général (DHCP, switch, SQL, récursivité) : explique-le de toi-même, "
    "simplement et correctement, puis dis en une ligne si les polycopiés de l'ESI en parlent — "
    "sans jamais faire passer ton explication pour un cours de l'ESI. "
    "Ne compte jamais toi-même : un nombre de modules, de documents, une note ou un seuil "
    "d'obtention se lit dans le contexte vérifié, et s'il n'y est pas, renvoie l'étudiant au "
    "catalogue au lieu de l'estimer. "
    "Réponds directement, sans exposer ton raisonnement."
)

# Anonymous, no-signup endpoint. Only reached when no provider key is configured, because it is
# the unreliable one — a sample with no key has nothing else, so it stays.
KEYLESS_ENDPOINTS = [
    ("https://text.pollinations.ai/openai", "openai"),
]

# A key per provider and that provider's own slugs, tried in turn until one answers. The first three
# are free tiers — free in money, not in credits — and their order is how much room each gives before
# it starts saying no. The fourth bills, so it sits last and spends nothing while a free lane works.
PROVIDERS = [
    {
        "name": "Gemini",
        "key": "GEMINI_API_KEY",
        # Every provider issues keys in its own shape. Checked before the request, so a key pasted
        # with spaces, or copied from the wrong console, is named as such instead of coming back as
        # an opaque HTTP 400 on every slug. Google issues both shapes: the long-standing `AIza…` key
        # and the newer `AQ.…` one AI Studio hands out — a single prefix would skip a working key.
        "prefixes": ("AIza", "AQ."),
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
    },
    {
        "name": "NVIDIA",
        "key": "NVIDIA_API_KEY",
        "prefixes": ("nvapi-",),
        "url": "https://integrate.api.nvidia.com/v1",
        # Without reasoning_effort this model writes its chain of thought into the answer and
        # takes ~83 s instead of ~4 s. Measured on this key, 2026-10-11.
        "models": ["nvidia/nemotron-3.5-lightning-30b-a3b"],
        "payload": {"reasoning_effort": "none"},
    },
    {
        "name": "OpenRouter",
        "key": "OPENROUTER_API_KEY",
        "prefixes": ("sk-or-",),
        "url": "https://openrouter.ai/api/v1",
        # $0 routes only: a shared sample must never be able to bill anyone by accident. Slugs are
        # re-checked against GET /api/v1/models filtered on ':free' — free routes move to paid
        # without notice (llama-3.3-70b and deepseek-v3 both did, and answer 404 now).
        "models": [
            "nvidia/nemotron-3.5-lightning:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
        ],
        "payload": {"reasoning": {"effort": "none"}},
        "headers": {"HTTP-Referer": "http://localhost:5173", "X-Title": "ESI Wiki"},
    },
    {
        # Last on purpose, and the only entry here that is not a free tier: OpenAI bills a card per
        # token. Putting it after the three free lanes means the free ones answer when they can, so
        # this one only spends money when nothing else would have replied at all.
        "name": "OpenAI",
        "key": "OPENAI_API_KEY",
        "prefixes": ("sk-proj-", "sk-svcacct-", "sk-"),
        # An OpenRouter key is `sk-or-…`, which also starts with `sk-`. Without this the shape check
        # would wave a mis-pasted OpenRouter token through to api.openai.com, which logs it — a key
        # must only ever reach the host that minted it.
        "rejects": ("sk-or-",),
        "url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4.1-mini"],
    },
]


def _system(history, verified=""):
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXTE:\n{build_context()}"
    if verified:
        prompt += f"\n\nCE QUE LA BASE LOCALE CONTIENT DEJA (source verifiee):\n{verified}"
    return [{"role": "system", "content": prompt}] + history


def _post(url, payload, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode())


def _content(body):
    reply = (body["choices"][0]["message"]["content"] or "").strip()
    if not reply:
        raise ValueError("empty completion")
    return reply


def _reason(e):
    """One line a student can read, instead of a stack trace nobody sees."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            detail = json.loads(e.read().decode())["error"]["message"]
        except Exception:
            detail = ""
        return f"HTTP {e.code} {detail}".strip()[:160]
    return e.__class__.__name__


def _failure_line(prefix, failures, limit=3):
    """Two slugs failing the same way is one provider, not two: say which names actually broke."""
    unique = list(dict.fromkeys(failures))
    line = prefix + "; ".join(unique[:limit])
    return line + "…" if len(unique) > limit else line


def _ask_keyless(history, verified, failures):
    """Best-effort anonymous tier: no key, no account, nothing to leak.

    Pollinations is deprecating this legacy endpoint (it now answers 402 for signed-up
    traffic and 500 when its disk is full), so treat it as intermittent and never let a
    silent skip here look like the assistant thinking for itself.
    """
    for url, model in KEYLESS_ENDPOINTS:
        try:
            body = _post(
                url,
                {"model": model, "messages": _system(history, verified), "temperature": 0.3},
            )
            return _content(body), model
        except Exception as e:
            failures.append(f"sans clé: {_reason(e)}")
            continue
    return None


def _ask(provider, model, history, verified):
    payload = {
        "model": model,
        "messages": _system(history, verified),
        "temperature": 0.3,
        **provider.get("payload", {}),
    }
    headers = {
        "Authorization": f"Bearer {getattr(settings, provider['key'])}",
        **provider.get("headers", {}),
    }
    body = _post(f"{provider['url']}/chat/completions", payload, headers)
    return _content(body), body.get("model", model)


@api_view(["POST"])
def chat(request):
    messages = request.data.get("messages")
    if not isinstance(messages, list) or not messages:
        return Response({"detail": "Field 'messages' must be a non-empty list."}, status=400)

    history = [
        {"role": m["role"], "content": str(m.get("content", ""))[:4000]}
        for m in messages[-MAX_TURNS:]
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
    ]
    if not history:
        return Response({"detail": "No valid turns in history."}, status=400)

    question = history[-1]["content"]
    local = answer_locally(question)
    if local["matched"]:
        # Retrieval settled it. A free model quoting the same question returns invented
        # counts, so figures and rules only ever come from the tables.
        return Response(local)

    # Mirrored EsiHub documents: real course text, searchable offline. Absent in the sample
    # build, where this simply returns nothing and the tiers behave as before.
    hits = corpus.search(question)
    verified = local["reply"]
    # Five chunks often come from three files; the list shown to the user is the files, once each.
    sources = list(dict.fromkeys(corpus.cite(h) for h in hits))
    if hits:
        verified += (
            "\n\nEXTRAITS DES POLYCOPIÉS DU WIKI (source vérifiée, cite le nom du fichier):\n"
            + "\n\n---\n\n".join(corpus.clip(h["text"], 1200) for h in hits)
        )

    # 1. every provider a key is configured for, 2. anonymous keyless endpoints, 3. the honest
    # "not documented".
    failures = []
    for provider in PROVIDERS:
        key = getattr(settings, provider["key"], "")
        if not key:
            continue
        expected = "… ou ".join(provider["prefixes"])
        token = key.strip()
        if token.startswith(provider.get("rejects", ())):
            # Say what actually happened: the shape is valid-looking but belongs to a rival host, so
            # "format attendu sk-…" alone would send someone in circles.
            failures.append(f"{provider['name']}: clé ignorée, ce format est celui d'un autre "
                            "fournisseur — remettez-la dans sa propre variable…")
            continue
        if not token.startswith(provider["prefixes"]):
            failures.append(f"{provider['name']}: clé ignorée, format attendu {expected}…")
            continue
        for model in provider["models"]:
            try:
                reply, used = _ask(provider, model, history, verified)
            except Exception as e:
                # Free tiers are shared or capped: 429 when the day's requests are spent, 404 when
                # a slug went paid, 502 now and then. The next slug, then the next provider, picks
                # it up — a dead lane should never take the answer down with it.
                failures.append(f"{provider['name']}: {_reason(e)}")
                continue
            return Response(
                {
                    "reply": reply,
                    "mode": "provider",
                    "provider": provider["name"],
                    "model": used,
                    "sources": sources,
                }
            )

    answered = _ask_keyless(history, verified, failures)
    if answered:
        reply, used = answered
        # The anonymous lane answered — but a recipient who pasted their own key needs to know it
        # was not what spoke, or a broken .env reads like a working one.
        dead_key = _failure_line("Clé configurée mais non rejointe (", failures) + \
            ") — réponse donnée par le modèle sans clé." if failures else ""
        return Response({"reply": reply, "mode": "keyless", "model": used,
                         "sources": sources, "note": dead_key})

    note = _failure_line("Aucun modèle joignable — ", failures) if failures else ""

    if hits:
        # No model reachable, but the mirrored documents answer the question: quote them
        # verbatim rather than saying we know nothing.
        return Response({
            "reply": "\n\n".join(
                f"{corpus.cite(h)}\n{corpus.clip(h['text'])}" for h in corpus.best_documents(hits)
            ),
            "mode": "corpus",
            "model": "corpus indexé du wiki",
            "sources": sources,
            "matched": True,
            "note": note,
        })
    local["note"] = note or local.get("note", "")
    return Response(local)
