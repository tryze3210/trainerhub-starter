from django.urls import path

from apps.workflows.api.views import WorkflowDefinitionListView, WorkflowRunListView, WorkflowStartView

urlpatterns = [
    path('definitions/', WorkflowDefinitionListView.as_view(), name='workflow-definitions'),
    path('runs/', WorkflowRunListView.as_view(), name='workflow-runs'),
    path('start/', WorkflowStartView.as_view(), name='workflow-start'),
]
