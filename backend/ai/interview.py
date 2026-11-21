"""
AI Mock Interview: question generation + answer evaluation.

Rule engine (always available):
  * questions picked from a curated bank for the role's / job's skills + HR questions
  * answers scored on: key-point coverage, depth (length), structure (STAR for HR),
    concrete examples / numbers
Gemini (optional) gives richer questions and feedback.
"""
import random
import re

from resumes.ml.skill_extractor import technical_only

from .llm import ask_json

# skill -> [(question, [key points an ideal answer should mention])]
BANK = {
    "Python": [
        ("What is the difference between a list and a tuple in Python?", ["mutable", "immutable", "performance", "hashable"]),
        ("Explain decorators in Python with an example.", ["function", "wrapper", "@", "reuse", "logging"]),
        ("How does memory management and garbage collection work in Python?", ["reference counting", "garbage collector", "cycles", "heap"]),
        ("What are generators and why are they useful?", ["yield", "lazy", "memory", "iterator"]),
    ],
    "Django": [
        ("Explain the request-response cycle in Django.", ["url", "view", "middleware", "template", "response"]),
        ("What is the Django ORM and how do migrations work?", ["model", "query", "makemigrations", "migrate", "database"]),
        ("How do you prevent N+1 query problems in Django?", ["select_related", "prefetch_related", "join", "queries"]),
    ],
    "Django REST Framework": [
        ("What are serializers in DRF and why do we need them?", ["validation", "json", "model", "convert"]),
        ("How do you secure a DRF API?", ["authentication", "permission", "jwt", "token", "throttling"]),
    ],
    "JavaScript": [
        ("What is the difference between let, const and var?", ["scope", "block", "hoisting", "reassign"]),
        ("Explain closures in JavaScript.", ["function", "scope", "outer", "variable", "private"]),
        ("What is the event loop and how do promises work?", ["call stack", "queue", "async", "await", "non-blocking"]),
    ],
    "React": [
        ("What are React hooks? Explain useState and useEffect.", ["state", "side effect", "dependency", "render", "functional"]),
        ("What is the virtual DOM and how does reconciliation work?", ["diff", "real dom", "update", "performance", "key"]),
        ("How do you manage state in a large React application?", ["context", "redux", "props", "lifting state", "store"]),
    ],
    "SQL": [
        ("What is the difference between INNER JOIN and LEFT JOIN?", ["matching", "all rows", "null", "left table"]),
        ("What are indexes and when should you use them?", ["faster", "search", "b-tree", "write", "columns"]),
        ("Explain normalization and its normal forms.", ["redundancy", "1nf", "2nf", "3nf", "dependency"]),
    ],
    "PostgreSQL": [
        ("What are transactions and ACID properties?", ["atomicity", "consistency", "isolation", "durability", "commit", "rollback"]),
    ],
    "Java": [
        ("Explain the four pillars of OOP with Java examples.", ["encapsulation", "inheritance", "polymorphism", "abstraction"]),
        ("What is the difference between an interface and an abstract class?", ["multiple", "implementation", "default", "extends", "implements"]),
        ("How does HashMap work internally?", ["hash", "bucket", "equals", "collision", "linked list", "tree"]),
    ],
    "Spring Boot": [
        ("What is dependency injection in Spring?", ["bean", "container", "autowired", "loose coupling"]),
    ],
    "Machine Learning": [
        ("What is overfitting and how do you prevent it?", ["training", "validation", "regularization", "cross-validation", "more data"]),
        ("Explain the bias-variance trade-off.", ["bias", "variance", "underfitting", "overfitting", "complexity"]),
        ("How do you evaluate a classification model?", ["accuracy", "precision", "recall", "f1", "confusion matrix"]),
    ],
    "Data Analysis": [
        ("How do you handle missing values in a dataset?", ["drop", "impute", "mean", "median", "analysis"]),
    ],
    "Docker": [
        ("What is the difference between a Docker image and a container?", ["template", "running", "instance", "layers"]),
    ],
    "AWS": [
        ("Explain EC2, S3 and RDS and when you would use each.", ["compute", "storage", "database", "scalable"]),
    ],
    "REST API": [
        ("What are REST principles and the common HTTP methods?", ["stateless", "get", "post", "put", "delete", "resource"]),
    ],
    "Git": [
        ("What is the difference between git merge and git rebase?", ["history", "commit", "linear", "branch"]),
    ],
    "DSA": [
        ("How would you find if a linked list has a cycle?", ["two pointers", "slow", "fast", "floyd", "o(n)"]),
    ],
}

HR = [
    ("Tell me about yourself.", ["education", "skills", "project", "experience", "goal"]),
    ("Describe a challenging project you worked on and how you handled it.", ["situation", "task", "action", "result", "learned"]),
    ("Why should we hire you for this role?", ["skills", "match", "project", "value", "learn"]),
    ("Where do you see yourself in 5 years?", ["growth", "skills", "role", "company", "learn"]),
    ("Tell me about a time you worked in a team and faced a conflict.", ["situation", "team", "action", "communication", "result"]),
]

STAR = ["situation", "task", "action", "result"]


def _rule_questions(role, skills, n):
    tech = [s for s in technical_only(skills) if s in BANK] or ["Python", "SQL", "REST API"]
    random.shuffle(tech)
    qs = []
    for skill in tech:
        q, pts = random.choice(BANK[skill])
        qs.append({"question": q, "type": "technical", "skill": skill, "points": pts})
        if len(qs) >= n - 2:
            break
    hr = random.sample(HR, 2)
    qs.insert(0, {"question": hr[0][0], "type": "hr", "skill": "Communication", "points": hr[0][1]})
    qs.append({"question": hr[1][0], "type": "hr", "skill": "Behavioural", "points": hr[1][1]})
    return qs[:n]


def generate_questions(role, skills, job_text="", n=6):
    data = ask_json(
        f"You are a technical interviewer in India hiring a fresher/junior for the role '{role}'.\n"
        f"Candidate skills: {', '.join(skills[:20])}.\n"
        f"Job description (may be empty): {job_text[:1500]}\n"
        f"Write {n} interview questions: 1 opening HR question, {n - 2} technical questions on the most relevant "
        "skills, and 1 behavioural question at the end. For each give 4-6 short key points an ideal answer covers.\n"
        'Return JSON: {"questions":[{"question":"...","type":"hr|technical","skill":"...","points":["..."]}]}'
    )
    try:
        qs = [q for q in data["questions"] if q.get("question")][:n]
        if len(qs) >= 3:
            return [{"question": q["question"], "type": q.get("type", "technical"),
                     "skill": q.get("skill", ""), "points": [str(p) for p in q.get("points", [])][:6]} for q in qs]
    except Exception:
        pass
    return _rule_questions(role, skills, n)


def _stem_hit(point, text):
    """'projects' matches 'project', 'optimization' matches 'optimiz…' (simple stemming)."""
    for w in point.lower().split():
        w = re.sub(r"[^a-z0-9+#.]", "", w)
        if len(w) <= 3:
            if re.search(rf"\b{re.escape(w)}\b", text):
                return True
        elif w[: max(4, len(w) - 3)] in text:
            return True
    return False


HR_SIGNALS = [
    r"\b(when|during|while|in my|at my|last year|in college|internship)\b",                      # situation
    r"\b(i (built|developed|led|created|designed|used|worked|solved|learned|handled|took)|we )",   # action
    r"(improv|reduc|increas|deliver|achiev|result|success|award|won|\d+\s?%)",                    # result
]


def _rule_evaluate(q, answer):
    text = answer.lower()
    words = len(re.findall(r"\w+", text))
    pts = [p.lower() for p in q.get("points", [])]
    covered = [p for p in q.get("points", []) if _stem_hit(p, text)]
    missed = [p for p in q.get("points", []) if p not in covered]
    coverage = len(covered) / len(pts) if pts else 0.5

    depth = min(1.0, words / 70)                     # ~70+ words = detailed answer
    has_example = bool(re.search(r"\b(for example|e\.g\.|such as|in my (project|internship)|i built|i developed|i used|\d+)", text))
    if q.get("type") == "hr":
        structure = sum(bool(re.search(sig, text)) for sig in HR_SIGNALS) / len(HR_SIGNALS)
        weights = (0.30, 0.25, 0.25, 0.20)
    else:
        structure = 1.0 if words > 25 else 0.3
        weights = (0.50, 0.20, 0.15, 0.15)
    wc, wd, ws, we = weights
    score = round(10 * (wc * coverage + wd * depth + ws * structure + we * has_example), 1)
    if words < 8:
        score = min(score, 2.0)

    strengths, tips = [], []
    if covered:
        strengths.append("You covered: " + ", ".join(covered[:4]) + ".")
    if has_example:
        strengths.append("Good use of a real example.")
    if words >= 60:
        strengths.append("Detailed and complete answer.")
    if missed:
        tips.append("Also mention: " + ", ".join(missed[:4]) + ".")
    if words < 40:
        tips.append("Your answer is short. Explain in 4-6 sentences.")
    if not has_example:
        tips.append("Add an example from your project or internship.")
    if q.get("type") == "hr" and structure < 0.67:
        tips.append("Use the STAR method: Situation, Task, Action, Result.")
    return {"score": score, "strengths": strengths or ["You attempted the question."], "improvements": tips,
            "ideal_points": q.get("points", [])}


def evaluate_answer(q, answer):
    data = ask_json(
        f"You are an interviewer. Question: {q['question']}\n"
        f"Key points of an ideal answer: {', '.join(q.get('points', []))}\n"
        f"Candidate answer: {answer[:3000]}\n"
        "Score the answer from 0 to 10 (be fair for a fresher), list up to 3 strengths and up to 3 specific "
        "improvements, and write a short model answer (3-4 sentences).\n"
        'Return JSON: {"score":7.5,"strengths":["..."],"improvements":["..."],"model_answer":"..."}', 900)
    try:
        result = {"score": max(0.0, min(10.0, float(data["score"]))),
                  "strengths": [str(s) for s in data.get("strengths", [])][:3],
                  "improvements": [str(s) for s in data.get("improvements", [])][:3],
                  "model_answer": str(data.get("model_answer", "")),
                  "ideal_points": q.get("points", [])}
        return result
    except Exception:
        return _rule_evaluate(q, answer)


def verdict(avg):
    if avg >= 8:
        return "Interview ready 🎉"
    if avg >= 6:
        return "Almost there 👍"
    if avg >= 4:
        return "Needs more practice"
    return "Keep practising 💪"
