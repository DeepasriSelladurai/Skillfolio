from flask import Flask, render_template, request, redirect, url_for, session, Response, flash
import numpy as np
from admin import *
from admin import quiz, storage, charts

QUESTIONS = quiz.QUESTIONS
TOPICS = quiz.TOPICS
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-if-needed"  # fine for local-only, no-security use

# Hardcoded admin login (explicitly no security required, local machine only)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# Helpers
# =========================================================
def current_student():
    reg_no = session.get("reg_no")
    if not reg_no:
        return None
    return storage.get_student(reg_no)


def build_quiz(topic):
    """Randomize question order AND option order for this session (numpy)."""
    bank = QUESTIONS[topic]
    order = np.arange(len(bank))
    np.random.shuffle(order)

    quiz = []
    for q_no, idx in enumerate(order, start=1):
        item = bank[int(idx)]
        opt_order = np.arange(len(item["options"]))
        np.random.shuffle(opt_order)
        shuffled_options = [item["options"][int(i)] for i in opt_order]
        correct_new_index = int(np.where(opt_order == item["answer"])[0][0])
        quiz.append({
            "q_no": q_no,
            "question": item["q"],
            "options": shuffled_options,
            "correct_index": correct_new_index,
        })
    return quiz


# =========================================================
# Public / Home
# =========================================================
@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# Student registration & login
# =========================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip()
        name = request.form.get("name", "").strip()
        dob = request.form.get("dob", "").strip()  # YYYY-MM-DD, used as password

        if not reg_no or not name or not dob:
            flash("All fields are required.")
            return redirect(url_for("register"))

        ok, message = storage.register_student(reg_no, name, dob)
        if not ok:
            flash(message)
            return redirect(url_for("register"))

        flash("Registration successful. Please log in with your register number and date of birth.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip()
        dob = request.form.get("dob", "").strip()

        ok, student = storage.verify_login(reg_no, dob)
        if not ok:
            flash("Invalid register number or date of birth.")
            return redirect(url_for("login"))

        session["reg_no"] = reg_no
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =========================================================
# Student dashboard, quiz, review, profile
# =========================================================
@app.route("/dashboard")
def dashboard():
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    return render_template("dashboard.html", student=student, topics=TOPICS)


@app.route("/quiz/<topic>", methods=["GET", "POST"])
def quiz(topic):
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    if topic not in TOPICS:
        return "Unknown topic", 404

    if request.method == "POST":
        quiz_data = session.get("quiz")
        if not quiz_data or quiz_data.get("topic") != topic:
            flash("Your quiz session expired. Please start again.")
            return redirect(url_for("quiz", topic=topic))

        questions = quiz_data["questions"]
        records = []
        correct_count = 0
        for q in questions:
            selected_raw = request.form.get(f"q_{q['q_no']}")
            selected_index = int(selected_raw) if selected_raw is not None else -1
            is_correct = selected_index == q["correct_index"]
            if is_correct:
                correct_count += 1
            records.append({
                "q_no": q["q_no"],
                "question": q["question"],
                "selected_option": q["options"][selected_index] if 0 <= selected_index < len(q["options"]) else "No answer",
                "correct_option": q["options"][q["correct_index"]],
                "is_correct": is_correct,
            })

        pct = round((correct_count / len(questions)) * 100, 1)
        attempt_id = storage.next_attempt_id(student["reg_no"])
        storage.save_attempt(student["reg_no"], topic, attempt_id, records)
        storage.update_skill(student["reg_no"], topic, pct)
        session.pop("quiz", None)

        return redirect(url_for("result", topic=topic, score=correct_count, total=len(questions), pct=pct))

    # GET: build a fresh randomized quiz for this session
    quiz_questions = build_quiz(topic)
    session["quiz"] = {"topic": topic, "questions": quiz_questions}
    return render_template("quiz.html", topic=topic, questions=quiz_questions)


@app.route("/result/<topic>")
def result(topic):
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    score = request.args.get("score", type=int)
    total = request.args.get("total", type=int)
    pct = request.args.get("pct", type=float)
    return render_template("result.html", topic=topic, score=score, total=total, pct=pct)


@app.route("/review/<topic>")
def review(topic):
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    rows = storage.read_latest_attempt(student["reg_no"], topic)
    if not rows:
        flash("No attempt found for this topic yet.")
        return redirect(url_for("dashboard"))
    return render_template("review.html", topic=topic, rows=rows)


@app.route("/profile")
def profile():
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    return render_template("profile.html", student=student, topics=TOPICS)


@app.route("/profile/chart.png")
def profile_chart():
    student = current_student()
    if not student:
        return redirect(url_for("login"))
    png_bytes = charts.student_skill_chart(student["skills"])
    return Response(png_bytes, mimetype="image/png")


# =========================================================
# Admin
# =========================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    students = storage.load_students()
    storage.export_flat_csv_for_powerbi()  # keep the Power BI source file fresh
    # Placeholder embed URL -- replace with your published Power BI report's embed URL
    powerbi_url = "https://app.powerbi.com/view?r=REPLACE_WITH_YOUR_PUBLISHED_REPORT_ID"
    return render_template(
        "admin_dashboard.html",
        students=students,
        topics=TOPICS,
        powerbi_url=powerbi_url,
    )


@app.route("/admin/chart.png")
def admin_chart():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    students = storage.load_students()
    png_bytes = charts.admin_overview_chart(students)
    return Response(png_bytes, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)