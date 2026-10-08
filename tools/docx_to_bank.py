"""Convert a Word file with exam questions into a built-in question bank (JSON).

Usage (needs: pip install python-docx):
    python tools/docx_to_bank.py EGZAMIN.docx data/builtin/patent_strzelecki.json \
        --slug patent-strzelecki --title-pl "Egzamin na patent strzelecki" \
        --title-en "Shooting licence exam (Polish)"

Supported layout (mixed freely in one document):
    * question as a numbered list item or as plain text "12. Question...";
    * 3 options as a Word list (letters added by Word) or as text "a. ..." / "A ...",
      also on soft line breaks (Shift+Enter) inside the question paragraph;
    * answer line "Poprawna odpowiedź: b. text" / "Prawidłowa odpowiedź: B" / only the answer text.

The correct option must agree by letter AND by text; anything doubtful is reported and the file
is NOT written, so a broken document never silently becomes a broken test.
Exact duplicate questions are dropped. On the next app start the bank is updated automatically.
"""
import argparse
import difflib
import json
import re
import sys

import docx

ANSWER_RE = re.compile(r"^\s*(?:poprawna|prawid[łl]?owa)\s+odpowied[źz]\s*:?\s*(.*)$", re.I)
LABEL_RE = re.compile(r"^\s*([a-cA-C])(?:[\.\)]\s*|\s+)(?=\S)")      # "a. ", "b) ", "C "
QNUM_RE = re.compile(r"^\s*\d+\s*[\.\)]\s*")                        # "9.   "


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ").replace("\t", " ")).strip()


def norm(s):
    return re.sub(r"[\s\.;,:!\"„”“'’]+", " ", clean(s).casefold()).strip()


def strip_label(s):
    m = LABEL_RE.match(s)
    return (m.group(1).upper(), s[m.end():].strip()) if m else (None, s.strip())


def read_lines(path):
    lines = []
    for p in docx.Document(path).paragraphs:
        is_list = p._p.pPr is not None and p._p.pPr.numPr is not None
        for part in p.text.split("\n"):  # soft line breaks
            part = clean(part)
            if part:
                lines.append({"text": part, "list": is_list})
    return lines


def parse(lines):
    questions, problems, cur, pending = [], [], None, False
    for i, ln in enumerate(lines):
        text = ln["text"]
        if i == 0 and "EGZAMIN" in text.upper():
            continue  # document title
        if pending:
            cur["answer"] = text; questions.append(cur); cur, pending = None, False
            continue
        m = ANSWER_RE.match(text)
        if m:
            if cur is None:
                problems.append(f"answer without a question: {text[:80]}")
            elif m.group(1).strip():
                cur["answer"] = m.group(1).strip(); questions.append(cur); cur = None
            else:
                pending = True
            continue
        if cur is None:
            cur = {"text": QNUM_RE.sub("", text), "options": []}
            continue
        label, body = strip_label(text)
        if (ln["list"] or label is not None) and len(cur["options"]) < 3:
            cur["options"].append(body)
        elif not cur["options"]:
            cur["text"] += " " + text
        else:
            problems.append(f"Q{len(questions) + 1}: unexpected extra line: {text[:70]}")
    if cur is not None:
        problems.append(f"last question has no answer: {cur['text'][:80]}")

    result = []
    for n, q in enumerate(questions, start=1):
        opts = [o.rstrip(" ;,") for o in q["options"]]
        if len(opts) != 3:
            problems.append(f"Q{n}: {len(opts)} options instead of 3: {q['text'][:70]}")
            continue
        label, body = strip_label(q["answer"])
        by_text = None
        exact = [k for k in range(3) if norm(body) == norm(opts[k])]
        if len(exact) == 1:
            by_text = exact[0]
        elif body:
            scores = [difflib.SequenceMatcher(None, norm(body), norm(o)).ratio() for o in opts]
            best = max(range(3), key=lambda k: scores[k])
            if scores[best] >= 0.6 and sorted(scores)[-2] < scores[best] - 0.05:
                by_text = best
        by_letter = "ABC".index(label) if label else None
        if by_letter is not None and by_text is not None and by_letter != by_text:
            problems.append(f"Q{n}: answer letter {label} but its text matches option {'ABC'[by_text]}")
            continue
        correct = by_letter if by_letter is not None else by_text
        if correct is None:
            problems.append(f"Q{n}: cannot find the correct option for '{q['answer'][:70]}'")
            continue
        result.append({"id": str(n), "text": q["text"].strip(), "options": opts, "correct": correct})
    return result, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx"); ap.add_argument("out")
    ap.add_argument("--slug", required=True, help="stable id, e.g. patent-strzelecki")
    ap.add_argument("--title-pl", required=True); ap.add_argument("--title-en", required=True)
    args = ap.parse_args()

    questions, problems = parse(read_lines(args.docx))
    if problems:
        print(f"{len(problems)} problem(s) — fix the document and run again:")
        for p in problems:
            print("  !", p)
        sys.exit(1)

    seen, unique, dropped = set(), [], []
    for q in questions:
        key = (q["text"].casefold(), tuple(sorted(o.casefold().rstrip(" .;") for o in q["options"])))
        if key in seen:
            dropped.append(q["id"])
        else:
            seen.add(key); unique.append(q)
    bank = {
        "slug": args.slug,
        "title": {"pl": args.title_pl, "en": args.title_en},
        "source": args.docx.replace("\\", "/").split("/")[-1],
        "note": "IDs are the question numbers from the source document; exact duplicates removed: "
                + (", ".join(dropped) or "none"),
        "questions": unique,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)
    print(f"OK: {len(unique)} questions written to {args.out} (duplicates dropped: {', '.join(dropped) or 'none'})")


if __name__ == "__main__":
    main()
