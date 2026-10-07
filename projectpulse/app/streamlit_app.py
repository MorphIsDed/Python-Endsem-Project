"""Streamlit dashboard entrypoint for ProjectPulse."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from projectpulse.analytics.insights import InsightEngine
from projectpulse.core.models import Project, TeamMember
from projectpulse.io.parser import parse_project_file


def build_sample_project() -> Project:
    from projectpulse.core.models import StandardTask, MilestoneTask, BufferTask
    from datetime import date

    tasks = [
        StandardTask("T01", "Kickoff", date(2026, 4, 1), date(2026, 4, 2), "Alice", 3, [], 0.0, 8.0),
        StandardTask("T02", "Requirements", date(2026, 4, 3), date(2026, 4, 8), "Bob", 4, [], 10.0, 8.0),
        StandardTask("T03", "Design", date(2026, 4, 9), date(2026, 4, 15), "Alice", 3, [], 20.0, 8.0),
        MilestoneTask("M01", "Approval", date(2026, 4, 16), date(2026, 4, 16), "Bob", 5, [], 0.0),
        BufferTask("B01", "Risk Buffer", date(2026, 4, 17), date(2026, 4, 20), None, 2, [], 0.0, 8.0),
    ]
    return Project(name="Sample Project", tasks=tasks, team=[TeamMember("Alice"), TeamMember("Bob")])


st.title("ProjectPulse")

if "project" not in st.session_state:
    st.session_state.project = build_sample_project()

project = st.session_state.project
st.sidebar.header("Project Settings")
st.sidebar.text_input("Project name", value=project.name)

if st.button("Load Sample Project"):
    st.session_state.project = build_sample_project()

if st.sidebar.button("Validate project"):
    st.write("Project ready:", len(project.tasks), "tasks")

insights = InsightEngine().summarise(0.72, 18.5, [task.id for task in project.tasks[:2]], ["Bob"])
for item in insights:
    st.info(item)

st.subheader("Tasks")
for task in project.tasks:
    st.write(f"- {task.id}: {task.name} | {task.assignee_name} | {task.planned_start} to {task.planned_end}")

st.caption("ProjectPulse: other tools draw the plan. This tool stress-tests it.")
