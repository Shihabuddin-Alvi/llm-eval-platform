import json

GOLD_PATH = "data/gold/gold_v1.jsonl"

BAD_QUESTIONS = {
    "What is 9 squared?",
    "Who discovered penicillin?",
    "How many bones are in the adult human body?",
    "What is the capital of South Korea?",
    "What is the hardest natural substance on Earth?",
}

REPLACEMENT_FACTS = [
    ("What is the capital of Thailand?", "Bangkok", "Chiang Mai"),
    ("Who wrote The Catcher in the Rye?", "J.D. Salinger", "Ernest Hemingway"),
    ("What is the largest hot desert in the world?", "The Sahara Desert", "The Gobi Desert"),
    ("Who painted The Starry Night?", "Vincent van Gogh", "Claude Monet"),
    ("What is the currency of India?", "Indian Rupee", "Pakistani Rupee"),
]

OFF_TOPIC = [
    "That's an interesting question. There are many perspectives worth considering here.",
    "I'm not sure, but this topic has a lot of history behind it worth reading about.",
    "Great question, this is definitely something people study in school.",
    "There's a lot of debate around topics like this depending on who you ask.",
    "This is the kind of question that comes up a lot in trivia games.",
]

def make_variant(kind, ref, wrong, idx):
    if kind == "exact":
        return ref
    if kind == "wrong":
        return wrong
    if kind == "paraphrase":
        return f"The answer to that is {ref}."
    if kind == "verbose_correct":
        return (f"That's a good question. After considering the most relevant facts, "
                 f"the answer is {ref}, which is well documented in standard references.")
    if kind == "verbose_wrong":
        return (f"That's a good question. After considering the most relevant facts, "
                 f"the answer is {wrong}, which is well documented in standard references.")
    if kind == "partial":
        return f"It's probably {ref}, though I'm not fully certain."
    if kind == "off_topic":
        return OFF_TOPIC[idx % len(OFF_TOPIC)]
    raise ValueError(kind)

VARIANT_TYPES = ["exact", "wrong", "paraphrase", "verbose_correct", "verbose_wrong", "partial", "off_topic"]

gold_rows = [json.loads(l) for l in open(GOLD_PATH)]
clean_rows = [r for r in gold_rows if r["input"] not in BAD_QUESTIONS]
bad_rows = [r for r in gold_rows if r["input"] in BAD_QUESTIONS]

print(f"kept {len(clean_rows)} items, dropping {len(bad_rows)} still-contaminated items")

max_id = max(r["id"] for r in gold_rows)
new_rows = []
next_id = max_id + 1
for i, (q, ref, wrong) in enumerate(REPLACEMENT_FACTS):
    start = i % len(VARIANT_TYPES)
    chosen = [VARIANT_TYPES[start], VARIANT_TYPES[(start + 1) % len(VARIANT_TYPES)]]
    for kind in chosen:
        pred = make_variant(kind, ref, wrong, i)
        new_rows.append({
            "id": next_id,
            "input": q,
            "prediction": pred,
            "reference": ref,
            "category": kind,
            "correct": None
        })
        next_id += 1

print(f"generated {len(new_rows)} new items")

final_rows = clean_rows + new_rows
with open(GOLD_PATH, "w") as f:
    for r in final_rows:
        f.write(json.dumps(r) + "\n")

print(f"wrote {len(final_rows)} total items to {GOLD_PATH}")