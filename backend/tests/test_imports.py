MODULES = [
    'apps.authn.services',
    'apps.accounts.services',
    'apps.access_control.policies',
    'apps.runtime.services',
    'apps.ops.services',
    'apps.events.services',
    'apps.workflows.services',
]


def test_imports():
    for module_path in MODULES:
        __import__(module_path)
