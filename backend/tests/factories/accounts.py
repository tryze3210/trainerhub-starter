from dataclasses import dataclass, field
from typing import Any


@dataclass
class DummyUser:
    id: int = 1
    email: str = 'user@example.com'
    is_authenticated: bool = True
    profile: Any = None


@dataclass
class DummyProfile:
    trainer_id: int | None = 101
    display_name: str = 'Trainer Demo'


@dataclass
class DummyRequest:
    user: DummyUser = field(default_factory=DummyUser)
    headers: dict[str, str] = field(default_factory=dict)


def build_account_context() -> DummyRequest:
    user = DummyUser()
    user.profile = DummyProfile()
    return DummyRequest(user=user, headers={'X-Correlation-ID': 'corr-test-001'})
