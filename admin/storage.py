"""
Lightweight storage layer.
- data/students.json  -> master record for ALL students (profile + latest skill % per topic)
- data/scores/<reg>.csv -> full question-by-question history for ONE student, written/read with numpy
No database, no ORM -- just numpy + json + the filesystem, as requested.
"""
import os
import json
import numpy as np
from datetime import datetime
from admin.quiz import TOPICS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCORES_DIR = os.path.join(DATA_DIR, "scores")
STUDENTS_JSON = os.path.join(DATA_DIR, "students.json")

CSV_HEADER = ["attempt_id", "topic", "q_no", "question", "selected_option", "correct_option", "is_correct", "timestamp"]

os.makedirs(SCORES_DIR, exist_ok=True)
if not os.path.exists(STUDENTS_JSON):
    with open(STUDENTS_JSON, "w", encoding="utf-8") as f:
        json.dump({}, f)


# -------------------------
# students.json (master file)
# -------------------------
def load_students():
    with open(STUDENTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_students(data):
    with open(STUDENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_student(reg_no, name, dob):
    """dob format expected: YYYY-MM-DD, used as the password."""
    students = load_students()
    if reg_no in students:
        return False, "Register number already exists."
    students[reg_no] = {
        "reg_no": reg_no,
        "name": name,
        "dob": dob,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "skills": {topic: {"attempts": 0, "best_pct": 0, "last_pct": 0} for topic in TOPICS},
    }
    save_students(students)
    return True, "Registered successfully."


def verify_login(reg_no, dob):
    students = load_students()
    student = students.get(reg_no)
    if not student:
        return False, None
    if student.get("dob") == dob:
        return True, student
    return False, None


def get_student(reg_no):
    return load_students().get(reg_no)


def update_skill(reg_no, topic, pct):
    students = load_students()
    if reg_no not in students:
        return
    entry = students[reg_no]["skills"].setdefault(topic, {"attempts": 0, "best_pct": 0, "last_pct": 0})
    entry["attempts"] += 1
    entry["last_pct"] = pct
    entry["best_pct"] = max(entry["best_pct"], pct)
    save_students(students)


# -------------------------
# per-student CSV (numpy)
# -------------------------
def csv_path(reg_no):
    return os.path.join(SCORES_DIR, f"{reg_no}.csv")


def save_attempt(reg_no, topic, attempt_id, records):
    """
    records: list of dicts, each with keys
        q_no, question, selected_option, correct_option, is_correct
    Appended to the student's personal CSV using numpy.savetxt.
    """
    path = csv_path(reg_no)
    file_exists = os.path.exists(path)
    timestamp = datetime.now().isoformat(timespec="seconds")

    rows = []
    if not file_exists:
        rows.append(CSV_HEADER)
    for r in records:
        rows.append([
            str(attempt_id),
            topic,
            str(r["q_no"]),
            r["question"].replace("|", "/"),
            r["selected_option"].replace("|", "/"),
            r["correct_option"].replace("|", "/"),
            str(r["is_correct"]),
            timestamp,
        ])

    arr = np.array(rows, dtype="<U1000")
    with open(path, "a", encoding="utf-8") as f:
        np.savetxt(f, arr, delimiter="|", fmt="%s")


def read_all_attempts(reg_no):
    """Returns a list of dict rows (all attempts, all topics) for this student."""
    path = csv_path(reg_no)
    if not os.path.exists(path):
        return []
    raw = np.genfromtxt(path, delimiter="|", dtype=str, encoding="utf-8")
    if raw.size == 0:
        return []
    if raw.ndim == 1:
        raw = raw.reshape(1, -1)
    header, body = raw[0], raw[1:]
    return [dict(zip(header, row)) for row in body]


def read_latest_attempt(reg_no, topic):
    """Returns the rows (question-by-question) belonging to the most recent attempt for a topic."""
    all_rows = [r for r in read_all_attempts(reg_no) if r["topic"] == topic]
    if not all_rows:
        return []
    latest_id = max(all_rows, key=lambda r: int(r["attempt_id"]))["attempt_id"]
    rows = [r for r in all_rows if r["attempt_id"] == latest_id]
    rows.sort(key=lambda r: int(r["q_no"]))
    return rows


def next_attempt_id(reg_no):
    rows = read_all_attempts(reg_no)
    if not rows:
        return 1
    return max(int(r["attempt_id"]) for r in rows) + 1


# -------------------------
# Flat export for Power BI
# -------------------------
POWERBI_CSV = os.path.join(DATA_DIR, "powerbi_students.csv")


def export_flat_csv_for_powerbi():
    """
    Flattens students.json into one row per (student, topic) so Power BI Desktop
    can load it directly via Get Data -> Text/CSV.
    Columns: reg_no,name,topic,attempts,best_pct,last_pct
    """
    students = load_students()
    header = ["reg_no", "name", "topic", "attempts", "best_pct", "last_pct"]
    rows = [header]
    for reg_no, s in students.items():
        for topic in TOPICS:
            skill = s["skills"].get(topic, {"attempts": 0, "best_pct": 0, "last_pct": 0})
            rows.append([
                reg_no,
                s["name"],
                topic,
                str(skill["attempts"]),
                str(skill["best_pct"]),
                str(skill["last_pct"]),
            ])
    arr = np.array(rows, dtype="<U500")
    np.savetxt(POWERBI_CSV, arr, delimiter=",", fmt="%s")
    return POWERBI_CSV
