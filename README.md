# ProjectPulse

ProjectPulse is a Python-based project management dashboard that models task dependencies, workload risk, and confidence levels for delivery. It follows the ProjectPulse specification and provides a Streamlit-based cockpit with task validation, scheduling, and planning analytics.

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Run the dashboard:
   streamlit run projectpulse/app/streamlit_app.py

## Package layout

- projectpulse/core: domain models, scheduling, and exceptions
- projectpulse/analytics: workload, Monte Carlo, burnout, scenario, and insight analysis
- projectpulse/io: parser, storage, exports, and holiday API integration
- projectpulse/app: Streamlit UI entrypoint
- tests: pytest coverage for key domain behavior

## Notes

This implementation focuses on the seeded domain model, parser, schedule validation, and dashboard scaffolding described in the master spec, while keeping the code modular and testable.
