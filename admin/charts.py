import io
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no GUI needed, safe for a web server
import matplotlib.pyplot as plt
from admin.quiz import TOPICS


def _fig_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def student_skill_chart(skills):
    """
    Horizontal bar chart of a single student's last score (%) per topic.
    skills: dict {topic: {"last_pct": float, ...}}
    """
    values = np.array([skills.get(t, {}).get("last_pct", 0) for t in TOPICS], dtype=float)
    colors = ["#4a47a3" if v >= 50 else "#d9534f" for v in values]

    fig, ax = plt.subplots(figsize=(7, 5))
    y_pos = np.arange(len(TOPICS))
    ax.barh(y_pos, values, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(TOPICS)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Skill Level (%)")
    ax.set_title("Your Skill Level by Topic")
    for i, v in enumerate(values):
        ax.text(v + 1.5, i, f"{v:.0f}%", va="center", fontsize=9)
    fig.tight_layout()
    return _fig_to_png(fig)


def admin_overview_chart(all_students):
    """
    Bar chart of the AVERAGE last-score (%) per topic, across all registered students.
    all_students: dict {reg_no: {..., "skills": {...}}}
    """
    averages = []
    for topic in TOPICS:
        vals = [
            s["skills"].get(topic, {}).get("last_pct", 0)
            for s in all_students.values()
            if s["skills"].get(topic, {}).get("attempts", 0) > 0
        ]
        averages.append(np.mean(vals) if vals else 0)

    fig, ax = plt.subplots(figsize=(9, 5))
    x_pos = np.arange(len(TOPICS))
    ax.bar(x_pos, averages, color="#4a47a3")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(TOPICS, rotation=35, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Average Skill Level (%)")
    ax.set_title(f"Average Skill Level Across {len(all_students)} Registered Students")
    for i, v in enumerate(averages):
        ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=9)
    fig.tight_layout()
    return _fig_to_png(fig)
