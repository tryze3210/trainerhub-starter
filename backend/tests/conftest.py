import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

from tests.factories import build_account_context, build_access_snapshot, build_tenant_context


@pytest.fixture()
def request_context():
    return build_account_context()


@pytest.fixture()
def tenant_context():
    return build_tenant_context()


@pytest.fixture()
def access_snapshot():
    return build_access_snapshot()
