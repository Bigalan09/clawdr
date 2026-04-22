"""Unit tests for domain types and invariants."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from clawdr.domain.models import (
    InvalidStateTransitionError,
    Project,
    ProjectId,
    Session,
    SessionState,
    SessionUrl,
)


class TestProjectId:
    def test_valid_slug(self) -> None:
        pid = ProjectId("ledger-sync")
        assert pid.value == "ledger-sync"

    def test_single_char(self) -> None:
        pid = ProjectId("x")
        assert pid.value == "x"

    def test_digits_allowed(self) -> None:
        pid = ProjectId("project-42")
        assert pid.value == "project-42"

    def test_rejects_uppercase(self) -> None:
        with pytest.raises(ValueError, match="lowercase slug"):
            ProjectId("Ledger-Sync")

    def test_rejects_leading_hyphen(self) -> None:
        with pytest.raises(ValueError, match="lowercase slug"):
            ProjectId("-bad")

    def test_rejects_trailing_hyphen(self) -> None:
        with pytest.raises(ValueError, match="lowercase slug"):
            ProjectId("bad-")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="lowercase slug"):
            ProjectId("")

    def test_rejects_spaces(self) -> None:
        with pytest.raises(ValueError, match="lowercase slug"):
            ProjectId("has space")

    def test_frozen(self) -> None:
        pid = ProjectId("abc")
        with pytest.raises(AttributeError):
            pid.value = "xyz"  # type: ignore[misc]

    def test_equality(self) -> None:
        assert ProjectId("abc") == ProjectId("abc")
        assert ProjectId("abc") != ProjectId("xyz")


class TestProject:
    def test_creation(self) -> None:
        p = Project(
            id=ProjectId("my-proj"),
            name="My Project",
            path=Path("/home/alan/projects/my-proj"),
            source="config",
        )
        assert p.name == "My Project"
        assert p.source == "config"

    def test_frozen(self) -> None:
        p = Project(
            id=ProjectId("my-proj"),
            name="My Project",
            path=Path("/home/alan/my-proj"),
            source="ui",
        )
        with pytest.raises(AttributeError):
            p.name = "Other"  # type: ignore[misc]


class TestSessionUrl:
    def test_repr_redacted(self) -> None:
        url = SessionUrl("https://claude.ai/code/session_abc123")
        assert "abc123" not in repr(url)
        assert repr(url) == "SessionUrl(<redacted>)"

    def test_str_redacted(self) -> None:
        url = SessionUrl("https://claude.ai/code/session_abc123")
        assert "abc123" not in str(url)
        assert str(url) == "SessionUrl(<redacted>)"

    def test_value_accessible(self) -> None:
        url = SessionUrl("https://claude.ai/code/session_abc123")
        assert url.value == "https://claude.ai/code/session_abc123"

    def test_frozen(self) -> None:
        url = SessionUrl("https://claude.ai/code/session_abc123")
        with pytest.raises(AttributeError):
            url.value = "other"  # type: ignore[misc]


class TestSessionState:
    def test_values(self) -> None:
        assert SessionState.STOPPED.value == "stopped"
        assert SessionState.STARTING.value == "starting"
        assert SessionState.RUNNING.value == "running"
        assert SessionState.CRASHED.value == "crashed"


class TestSession:
    @staticmethod
    def _make_session() -> Session:
        return Session(project_id=ProjectId("test-proj"))

    def test_default_state(self) -> None:
        s = self._make_session()
        assert s.state == SessionState.STOPPED
        assert s.url is None
        assert s.started_at is None

    def test_start_from_stopped(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        assert s.state == SessionState.STARTING
        assert s.started_at == now

    def test_start_from_crashed(self) -> None:
        s = self._make_session()
        s.state = SessionState.CRASHED
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        assert s.state == SessionState.STARTING

    def test_start_from_starting_raises(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        with pytest.raises(InvalidStateTransitionError):
            s.start(now)

    def test_start_from_running_raises(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        s.mark_running(SessionUrl("https://claude.ai/code/session_abc"))
        with pytest.raises(InvalidStateTransitionError):
            s.start(now)

    def test_mark_running(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        url = SessionUrl("https://claude.ai/code/session_abc")
        s.mark_running(url)
        assert s.state == SessionState.RUNNING
        assert s.url is url

    def test_mark_running_from_stopped_raises(self) -> None:
        s = self._make_session()
        url = SessionUrl("https://claude.ai/code/session_abc")
        with pytest.raises(InvalidStateTransitionError):
            s.mark_running(url)

    def test_stop_clears_state(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        s.mark_running(SessionUrl("https://claude.ai/code/session_abc"))
        s.stop()
        assert s.state == SessionState.STOPPED
        assert s.url is None
        assert s.started_at is None

    def test_crash_clears_url(self) -> None:
        s = self._make_session()
        now = datetime(2026, 4, 22, tzinfo=UTC)
        s.start(now)
        s.mark_running(SessionUrl("https://claude.ai/code/session_abc"))
        s.crash()
        assert s.state == SessionState.CRASHED
        assert s.url is None
