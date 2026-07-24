# scripts/generate_gold_pool.py
import json

FACTS = [
    ("What is the capital of France?", "Paris", "Lyon"),
    ("What is the capital of Japan?", "Tokyo", "Osaka"),
    ("Who wrote Romeo and Juliet?", "William Shakespeare", "Christopher Marlowe"),
    ("What is the chemical symbol for gold?", "Au", "Ag"),
    ("What is the largest planet in our solar system?", "Jupiter", "Saturn"),
    ("In what year did World War II end?", "1945", "1943"),
    ("What is the square root of 144?", "12", "14"),
    ("Who painted the Mona Lisa?", "Leonardo da Vinci", "Michelangelo"),
    ("What is the boiling point of water in Celsius?", "100", "90"),
    ("What is the longest river in the world?", "The Nile", "The Amazon"),
    ("How many continents are there?", "7", "6"),
    ("What is the capital of Australia?", "Canberra", "Sydney"),
    ("Who developed the theory of general relativity?", "Albert Einstein", "Isaac Newton"),
    ("What is the currency of Japan?", "Yen", "Won"),
    ("What gas do plants absorb from the atmosphere for photosynthesis?", "Carbon dioxide", "Oxygen"),
    ("What is the smallest prime number?", "2", "1"),
    ("Who was the first person to walk on the moon?", "Neil Armstrong", "Buzz Aldrin"),
    ("What is the capital of Canada?", "Ottawa", "Toronto"),
    ("What year did the Berlin Wall fall?", "1989", "1991"),
    ("What is 15 multiplied by 4?", "60", "45"),
    ("What is the freezing point of water in Fahrenheit?", "32", "0"),
    ("Who wrote 1984?", "George Orwell", "Aldous Huxley"),
    ("What is the capital of Egypt?", "Cairo", "Alexandria"),
    ("What is the tallest mountain in the world?", "Mount Everest", "K2"),
    ("What is the chemical formula for water?", "H2O", "CO2"),
    ("How many players are on a standard soccer team on the field?", "11", "10"),
    ("What is the capital of Brazil?", "Brasilia", "Rio de Janeiro"),
    ("Who is known as the father of computers?", "Charles Babbage", "Alan Turing"),
    ("What is the approximate speed of light in a vacuum, in km/s?", "300000", "150000"),
    ("What planet is known as the Red Planet?", "Mars", "Venus"),
]

OFF_TOPIC = [
    "That's an interesting question. There are many perspectives worth considering here.",
    "I'm not sure, but this topic has a lot of history behind it worth reading about.",
    "Great question, this is definitely something people study in school.",
    "There's a lot of debate around topics like this depending on who you ask.",
    "This is the kind of question that comes up a lot in trivia games.",
]

def make_variant(kind, question, ref, wrong, idx):
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

rows = []
rid = 1
for i, (q, ref, wrong) in enumerate(FACTS):
    start = i % len(VARIANT_TYPES)
    chosen = [VARIANT_TYPES[(start + k) % len(VARIANT_TYPES)] for k in range(5)]
    for kind in chosen:
        pred = make_variant(kind, q, ref, wrong, i)
        rows.append({
            "id": rid,
            "input": q,
            "prediction": pred,
            "reference": ref,
            "category": kind,
            "correct": None
        })
        rid += 1

with open("data/gold/gold_v1_unlabeled.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

print(f"wrote {len(rows)} rows to data/gold/gold_v1_unlabeled.jsonl")