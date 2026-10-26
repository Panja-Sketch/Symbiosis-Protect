"""Deterministic retrieval over the policy summary (also used to ground and to check the model)."""

import math
import re
from dataclasses import dataclass

from app.ai.schemas import PolicyContext

_TOKEN = re.compile(r"[a-z0-9$]+")


def stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def tokens(text: str, stop: set[str]) -> list[str]:
    return [stem(w) for w in _TOKEN.findall(text.lower()) if w not in stop and len(w) > 1]


@dataclass
class Item:
    kind: str            # coverage | endorsement | exclusion | note | glossary
    code: str            # coverage/endorsement/exclusion code, note key, or glossary term
    title: str
    text: str
    data: dict
    score: float = 0.0
    coverage: float = 0.0


def build_items(ctx: PolicyContext) -> list[Item]:
    items = []
    for c in ctx.coverages:
        body = " ".join([c["name_plain"], c["what_it_covers_plain"], c["what_it_does_not_plain"], *c.get("examples", [])])
        items.append(Item("coverage", c["code"], c["name_plain"], body, c))
    for e in ctx.endorsements:
        items.append(Item("endorsement", e["code"], e["name_plain"], f"{e['name_plain']} {e['why_it_matters_plain']}", e))
    for x in ctx.exclusions_plain:
        items.append(Item("exclusion", x["code"], x["title"], f"{x['title']} {x['plain']}", x))
    for n in ctx.coverage_notes:
        items.append(Item("note", n["key"], n["title"], f"{n['title']} {n['plain']}", n))
    for g in ctx.glossary:
        items.append(Item("glossary", g["term"], g["term"], f"{g['term']} {g['plain']}", g))
    return items


def expand_query(question: str, cfg: dict) -> tuple[list[str], list[str]]:
    stop = set(cfg["stopwords"])
    base = tokens(question, stop)
    extra = []
    for raw in _TOKEN.findall(question.lower()):
        extra += [stem(w) for w in cfg["synonyms"].get(raw, [])]
    return base, extra


def content_tokens(question: str, cfg: dict) -> list[str]:
    generic = {stem(w) for w in cfg.get("generic_words", [])}
    return [w for w in dict.fromkeys(tokens(question, set(cfg["stopwords"]))) if w not in generic]


def rank(ctx: PolicyContext, question: str, cfg: dict) -> list[Item]:
    stop = set(cfg["stopwords"])
    items = build_items(ctx)
    docs = [set(tokens(i.text, stop)) for i in items]
    titles = [set(tokens(i.title, stop)) for i in items]
    n = len(items)
    df: dict[str, int] = {}
    for d in docs:
        for w in d:
            df[w] = df.get(w, 0) + 1
    base, extra = expand_query(question, cfg)
    base = [w for w in base if w in set(content_tokens(question, cfg))]
    syn = {}
    for raw in _TOKEN.findall(question.lower()):
        syn[stem(raw)] = {stem(w) for w in cfg["synonyms"].get(raw, [])}
    for item, d, tt in zip(items, docs, titles, strict=True):
        item.coverage = (sum(1 for w in base if w in d or (syn.get(w, set()) & d)) / len(base)) if base else 0.0
        s = 0.0
        for w in set(base):
            if w in d:
                s += 1.0 + math.log((n + 1) / (df[w] + 0.5))
                if w in tt:  # words in the item's own title are a stronger signal than words in its body
                    s += 0.75 * (1.0 + math.log((n + 1) / (df[w] + 0.5)))
        for w in set(extra) - set(base):
            if w in d:
                s += 0.5 * (1.0 + math.log((n + 1) / (df[w] + 0.5)))
        # Policy items (coverage/endorsement/exclusion) outrank glossary/notes on a tie.
        item.score = s * (1.0 if item.kind != "glossary" else 0.8)
    return sorted((i for i in items if i.score > 0), key=lambda i: -i.score)


def top_hits(ctx: PolicyContext, question: str, cfg: dict) -> list[Item]:
    r = cfg["retrieval"]
    ranked = [i for i in rank(ctx, question, cfg) if i.score >= r["min_score"]]
    if not ranked or ranked[0].coverage < r["min_coverage"]:
        return []
    top = ranked[0].score
    return [i for i in ranked if i.score >= r["relative_min"] * top][: r["max_items"]]
