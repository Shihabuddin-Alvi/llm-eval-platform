import json

GOLD_PATH = "data/gold/gold_v1.jsonl"
SCORED_PATH = "data/gold/gold_v1_scored.jsonl"

BAD_QUESTIONS = {
    "What is the capital of Japan?",
    "Who wrote Romeo and Juliet?",
    "What is the chemical symbol for gold?",
    "What is the square root of 144?",
    "Who painted the Mona Lisa?",
    "What is the boiling point of water in Celsius?",
    "What is the longest river in the world?",
    "How many continents are there?",
    "What is the capital of Australia?",
    "What is the currency of Japan?",
    "What is the capital of Canada?",
    "What is the capital of Egypt?",
    "What is the tallest mountain in the world?",
    "What is the capital of Brazil?",
    "What planet is known as the Red Planet?",
}

REPLACEMENT_FACTS = [
    ("What is the capital of New Zealand?", "Wellington", "Auckland"),
    ("Who composed the Ninth Symphony?", "Ludwig van Beethoven", "Johann Sebastian Bach"),
    ("What metal has the chemical symbol Fe?", "Iron", "Tin"),
    ("What is 9 squared?", "81", "72"),
    ("Who discovered penicillin?", "Alexander Fleming", "Louis Pasteur"),
    ("What is the largest ocean on Earth?", "The Pacific Ocean", "The Atlantic Ocean"),
    ("How many bones are in the adult human body?", "206", "208"),
    ("What is the capital of South Korea?", "Seoul", "Busan"),
    ("Who wrote The Great Gatsby?", "F. Scott Fitzgerald", "Ernest Hemingway"),
    ("What is the atomic number of hydrogen?", "1", "2"),
    ("What year did the Titanic sink?", "1912", "1915"),
    ("What is the capital of Kenya?", "Nairobi", "Mombasa"),
    ("Who directed the movie Jaws?", "Steven Spielberg", "George Lucas"),
    ("What is the hardest natural substance on Earth?", "Diamond", "Quartz"),
    ("What is the capital of Argentina?", "Buenos Aires", "Cordoba"),
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

print(f"kept {len(clean_rows)} clean items, dropping {len(bad_rows)} contaminated items")

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

print(f"generated {len(new_rows)} new replacement items")

final_rows = clean_rows + new_rows
with open(GOLD_PATH, "w") as f:
    for r in final_rows:
        f.write(json.dumps(r) + "\n")

print(f"wrote {len(final_rows)} total items to {GOLD_PATH}")

bad_ids = {r["id"] for r in bad_rows}
scored = [json.loads(l) for l in open(SCORED_PATH)]
kept_scored = [e for e in scored if e["id"] not in bad_ids]
with open(SCORED_PATH, "w") as f:
    for e in kept_scored:
        f.write(json.dumps(e) + "\n")
print(f"scored file: kept {len(kept_scored)}, dropped {len(scored) - len(kept_scored)}")