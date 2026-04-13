from django.urls import path

from apps.ops.api.views import DiagnosticsSnapshotView, RunDiagnosticsView

urlpatterns = [
    path('diagnostics/', DiagnosticsSnapshotView.as_view(), name='ops-diagnostics'),
    path('diagnostics/run/', RunDiagnosticsView.as_view(), name='ops-diagnostics-run'),
]
