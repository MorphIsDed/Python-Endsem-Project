from datetime import date

from projectpulse.core.exceptions import CircularDependencyError
from projectpulse.core.models import Dependency, StandardTask
from projectpulse.core.scheduler import Scheduler
from projectpulse.io.parser import parse_task_lines


def test_parse_task_lines_accepts_valid_line():
    content = "T01 | Design | 2026-04-08 | 2026-04-15 | Bob | 4 | T02,T03+2 | 30\n"
    result = parse_task_lines(content)
    assert len(result.accepted) == 1
    assert result.accepted[0].id == "T01"
    assert result.rejected == []


def test_parse_task_lines_rejects_invalid_line():
    content = "T02 | Bad | 2026-04-08 | 2026-04-05 | Bob | 4\n"
    result = parse_task_lines(content)
    assert len(result.accepted) == 0
    assert len(result.rejected) == 1


def test_scheduler_detects_cycle():
    tasks = [
        StandardTask("A", "Alpha", date(2026, 4, 1), date(2026, 4, 3), "Alice", 3, [Dependency("B")]),
        StandardTask("B", "Beta", date(2026, 4, 4), date(2026, 4, 6), "Bob", 2, [Dependency("A")]),
    ]
    try:
        Scheduler(type("P", (), {"tasks": tasks, "deadline": None, "holidays": set()})()).topo_sort()
    except CircularDependencyError:
        assert True
    else:
        assert False, "Expected CircularDependencyError"


def test_scheduler_accepts_linear_dependency():
    tasks = [
        StandardTask("A", "Alpha", date(2026, 4, 1), date(2026, 4, 3), "Alice", 3),
        StandardTask("B", "Beta", date(2026, 4, 4), date(2026, 4, 6), "Bob", 2, [Dependency("A")]),
    ]
    project = type("P", (), {"tasks": tasks, "deadline": None, "holidays": set()})()
    order = Scheduler(project).topo_sort()
    assert order[0] == "A"
    assert order[1] == "B"
