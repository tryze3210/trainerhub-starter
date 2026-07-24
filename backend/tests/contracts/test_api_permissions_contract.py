import ast
from pathlib import Path

from django.conf import settings


API_VIEW_BASES = {
    'APIView',
    'GenericAPIView',
    'ViewSet',
    'GenericViewSet',
    'ModelViewSet',
    'ReadOnlyModelViewSet',
    'ListAPIView',
    'RetrieveAPIView',
    'ListCreateAPIView',
    'CreateAPIView',
    'UpdateAPIView',
    'DestroyAPIView',
}

APPROVED_PERMISSION_MIXINS = {
    'TrainerCMSAccessMixin',
    'TrainerOwnedMixin',
}


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ''


def test_drf_default_permission_requires_authentication():
    assert settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] == (
        'rest_framework.permissions.IsAuthenticated',
    )


def test_api_views_do_not_depend_on_implicit_allow_any():
    repo_root = Path(__file__).resolve().parents[3]
    offenders = []

    for path in (repo_root / 'backend' / 'apps').rglob('*.py'):
        if '/migrations/' in str(path):
            continue
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {_base_name(base) for base in node.bases}
            if not bases.intersection(API_VIEW_BASES):
                continue
            has_permission_classes = any(
                isinstance(statement, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'permission_classes' for target in statement.targets)
                for statement in node.body
            )
            has_get_permissions = any(
                isinstance(statement, ast.FunctionDef) and statement.name == 'get_permissions'
                for statement in node.body
            )
            has_approved_permission_mixin = bool(bases.intersection(APPROVED_PERMISSION_MIXINS))
            if not (has_permission_classes or has_get_permissions or has_approved_permission_mixin):
                offenders.append(f'{path.relative_to(repo_root)}:{node.lineno}:{node.name}')

    assert offenders == []
