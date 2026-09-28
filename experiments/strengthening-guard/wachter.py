#!/usr/bin/env python3
"""Versterkingswachter: is a later telling stronger than its source?

Compares a source with a later telling (a summary, a rewrite, a handover, an AI's answer) and
lists every place where the telling says more firmly what the source said less firmly:
- VOORBEHOUD_WEG   a hedge or limit in the source is gone ("may", "untested", "misschien", "alleen" …)
- ONTKENNING_WEG   a negation in the source is gone ("not", "niet", "geen" …): may flip a claim
- TREDE_OMHOOG     a status climbed a rung (candidate → established, lijkt op → is, partial → complete …)
- REIKWIJDTE_OMHOOG a quantifier widened (some → all, sommige → alle …)
- GETAL_ANDERS     a number in the telling is not a number of the source note it came from
- NOTITIE_WEG_MET_VOORBEHOUD  a whole source note is gone, and it carried a hedge or limit

No model, standard library only. It lists; it does not judge meaning. A flag is a place to look.

    python3 wachter.py source.txt telling.txt           # notes aligned by content
    python3 wachter.py --json source.txt telling.txt    # machine-readable
"""
import difflib, json, re, sys

HEDGES = [
    # English
    "may", "might", "possibly", "perhaps", "probably", "likely", "seems", "seem", "appears", "suggests",
    "could", "would", "whether", "if", "unless", "except", "so far", "not yet", "untested", "not tested",
    "unverified", "not verified", "unknown", "not known", "don't know", "do not know", "did not check",
    "not checked", "only", "seen only", "candidate", "provisional", "tentative", "partial", "partly",
    "not proven", "not established", "hypothesis", "estimate", "approximately", "about", "roughly", "~",
    "some", "claim", "claims", "reported",
    # Nederlands
    "misschien", "mogelijk", "wellicht", "lijkt", "lijken", "waarschijnlijk", "vermoedelijk", "kan",
    "kunnen", "zou", "zouden", "tenzij", "behalve", "tot nu toe", "nog niet", "niet getest",
    "niet bewezen", "niet nagegaan", "onbekend", "weet niet", "alleen", "slechts", "kandidaat",
    "voorlopig", "deels", "gedeeltelijk", "schatting", "ongeveer", "circa", "grofweg", "sommige",
    "enkele", "hint", "claim", "gemeld",
]
NEGATIONS = ["not", "no", "never", "cannot", "can't", "isn't", "doesn't", "didn't", "niet", "geen", "nooit", "niets", "nergens"]
LADDERS = {
    "status": [["dream", "droom", "droomdraad", "candidate", "kandidaat", "proposal", "voorstel", "hypothesis", "provisional", "voorlopig"],
               ["witnessed", "observed", "getuigenis", "tested", "getest", "seen", "gezien"],
               ["landed", "geland", "current", "confirmed", "established", "proven", "bewezen", "true", "waar", "canon", "fact", "feit"]],
    "identiteit": [["resembles", "similar", "like", "lijkt", "gelijkend", "naam", "name"],
                   ["same", "identical", "equals", "dezelfde", "hetzelfde", "identiek", "is hetzelfde", "is the same"]],
    "aanwezig": [["missing", "ontbreekt", "absent", "unknown", "onbekend", "not found", "niet gevonden"],
                 ["present", "found", "gevonden", "aanwezig", "exists", "bestaat"]],
    "af": [["partial", "partly", "deels", "gedeeltelijk", "started", "begonnen", "onaf"],
           ["complete", "full", "volledig", "done", "af", "finished", "implemented", "klaar"]],
    "poort": [["hold", "waiting", "wacht", "pending", "not authorized", "niet geautoriseerd"],
              ["pass", "ready", "authorized", "geautoriseerd", "approved", "goedgekeurd"]],
}
SCOPE = [["one", "een", "a few", "few", "several", "some", "sommige", "enkele", "een paar"],
         ["many", "most", "veel", "meeste", "meestal", "usually"],
         ["all", "every", "each", "always", "alle", "elk", "elke", "altijd", "iedereen", "overal"]]
NUM = re.compile(r"(?<![\w.])~?\d+(?:[.,]\d+)?%?")


def rules_fingerprint():
    import hashlib
    return hashlib.sha256(json.dumps([HEDGES, NEGATIONS, LADDERS, SCOPE], sort_keys=True).encode()).hexdigest()


def norm(t):
    t = re.sub(r"[^\w~%'.,]+", " ", t.lower())
    t = re.sub(r"(?<!\d)[.,]|[.,](?!\d)", " ", t)   # keep 62.1 and 8,5; drop sentence punctuation
    return " " + re.sub(r"\s+", " ", t) + " "


def count(term, t):
    return len(re.findall(r"(?<![\w])" + re.escape(term) + r"(?![\w])", t))


def notes(text):
    """Split into notes: top-level bullets with their continuation lines, or paragraphs."""
    out, cur = [], []
    for line in text.splitlines():
        s = line.strip()
        starts = bool(re.match(r"^([-*+]|\d+[.)])\s+", line)) or line.startswith("#")
        if not s or starts:
            if cur: out.append(" ".join(cur))
            cur = [re.sub(r"^([-*+]|\d+[.)]|#+)\s*", "", s)] if s else []
        else:
            cur.append(s)
    if cur: out.append(" ".join(cur))
    return [n for n in out if len(n.split()) >= 3]


def similarity(a, b):
    wa, wb = set(norm(a).split()), set(norm(b).split())
    return len(wa & wb) / max(1, len(wa | wb))


def rung(ladder, t):
    r = -1
    for i, level in enumerate(ladder):
        if any(count(w, t) for w in level): r = i
    return r


def compare_note(src, tel):
    s, t = norm(src), norm(tel)
    flags = []
    for h in HEDGES:
        if count(h, s) > count(h, t):
            flags.append(("VOORBEHOUD_WEG", h))
    for n in NEGATIONS:
        if count(n, s) > count(n, t):
            flags.append(("ONTKENNING_WEG", n))
    for name, ladder in LADDERS.items():
        rs, rt = rung(ladder, s), rung(ladder, t)
        if rt > rs >= 0 or (rs == -1 and rt >= 1):
            flags.append(("TREDE_OMHOOG", f"{name}: {rs}→{rt}"))
    ss, st = rung(SCOPE, s), rung(SCOPE, t)
    if st > ss and st >= 1:
        flags.append(("REIKWIJDTE_OMHOOG", f"{ss}→{st}"))
    ns, nt = set(NUM.findall(src)), set(NUM.findall(tel))
    if ns and (nt - ns):
        flags.append(("GETAL_ANDERS", f"{sorted(ns)} → {sorted(nt)}"))
    return flags


def compare(source, telling, threshold=0.25):
    S, T = notes(source), notes(telling)
    result = []
    used = set()
    for i, sn in enumerate(S):
        best, bj = 0.0, None
        for j, tn in enumerate(T):
            sim = similarity(sn, tn)
            if sim > best: best, bj = sim, j
        if bj is None or best < threshold:
            carried = [h for h in HEDGES if count(h, norm(sn))] + [n for n in NEGATIONS if count(n, norm(sn))]
            if carried:
                result.append({"bron": sn, "vertelling": None, "gelijkenis": round(best, 2),
                               "vlaggen": [["NOTITIE_WEG_MET_VOORBEHOUD", ", ".join(carried[:5])]]})
            continue
        used.add(bj)
        f = compare_note(sn, T[bj])
        if f:
            result.append({"bron": sn, "vertelling": T[bj], "gelijkenis": round(best, 2), "vlaggen": [list(x) for x in f]})
    return result


def main(argv):
    as_json = "--json" in argv
    args = [a for a in argv[1:] if a != "--json"]
    if len(args) != 2: sys.exit(__doc__)
    src, tel = (open(p, encoding="utf-8").read() for p in args)
    res = compare(src, tel)
    if as_json:
        print(json.dumps({"regels_sha256": rules_fingerprint(), "plekken": res}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print("—", " · ".join(f"{k} ({v})" for k, v in r["vlaggen"]))
            print("   bron:      ", r["bron"][:160])
            print("   vertelling:", (r["vertelling"] or "(weg)")[:160])
        print(f"\n{len(res)} plek(ken) om te bekijken · regels {rules_fingerprint()[:16]}")
    return 1 if res else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
