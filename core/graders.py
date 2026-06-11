import re
import os
import httpx


def exact_match(prediction: str, reference: str) -> dict:
    prediction_clean = prediction.strip().lower()
    reference_clean = reference.strip().lower()
    passed = prediction_clean == reference_clean
    return {
        "grader": "exact_match",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "prediction": prediction,
        "reference": reference,
    }


def contains_match(prediction: str, reference: str) -> dict:
    prediction_clean = prediction.strip().lower()
    reference_clean = reference.strip().lower()
    passed = reference_clean in prediction_clean
    return {
        "grader": "contains_match",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "prediction": prediction,
        "reference": reference,
    }


def regex_match(prediction: str, pattern: str) -> dict:
    try:
        passed = bool(re.search(pattern, prediction, re.DOTALL | re.IGNORECASE))
    except re.error:
        passed = False
    return {
        "grader": "regex_match",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "prediction": prediction,
        "reference": pattern,
    }


def llm_judge_gemini(prediction: str, reference: str, criteria: str = "accuracy") -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
    prompt = f"""You are an evaluator. Score the prediction against the reference.

Criteria: {criteria}
Reference: {reference}
Prediction: {prediction}

Respond in this exact format:
SCORE: <number between 0.0 and 1.0>
REASONING: <one sentence explanation>"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = httpx.post(url, json=payload, timeout=30)
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        lines = text.strip().split("\n")
        score = float(lines[0].replace("SCORE:", "").strip())
        reasoning = lines[1].replace("REASONING:", "").strip()
        passed = score >= 0.5
        return {"score": score, "passed": passed, "grader": "llm_judge", "reasoning": reasoning}
    except Exception as e:
        raise RuntimeError(str(e))


def llm_judge_groq(prediction: str, reference: str, criteria: str = "accuracy") -> dict:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""You are an evaluator. Score the prediction against the reference.

Criteria: {criteria}
Reference: {reference}
Prediction: {prediction}

Respond in this exact format:
SCORE: <number between 0.0 and 1.0>
REASONING: <one sentence explanation>"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        timeout=30
    )
    text = response.choices[0].message.content.strip()
    lines = text.split("\n")
    score = float(lines[0].replace("SCORE:", "").strip())
    reasoning = lines[1].replace("REASONING:", "").strip()
    passed = score >= 0.5
    return {"score": score, "passed": passed, "grader": "llm_judge", "reasoning": reasoning}


def llm_judge(prediction: str, reference: str, criteria: str = "accuracy") -> dict:
    try:
        return llm_judge_gemini(prediction, reference, criteria)
    except Exception:
        pass
    try:
        return llm_judge_groq(prediction, reference, criteria)
    except Exception:
        pass
    result = contains_match(prediction, reference)
    result["grader"] = "llm_judge"
    result["reasoning"] = "Fallback to contains_match after Gemini and Groq failed"
    return result