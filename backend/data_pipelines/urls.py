from django.urls import path

from . import views

app_name = 'data_pipelines'

urlpatterns = [
    path('pipelines/', views.DataPipelineListCreateView.as_view(), name='pipelines'),
    path('pipelines/<uuid:pk>/', views.DataPipelineDetailView.as_view(), name='pipeline_detail'),
    path('pipelines/<uuid:pk>/execute/', views.execute_pipeline_view, name='execute_pipeline'),
    path('pipelines/<uuid:pk>/status/', views.pipeline_status_view, name='pipeline_status'),
    path('pipelines/<uuid:pk>/stop/', views.stop_pipeline_view, name='stop_pipeline'),
    path('sources/', views.DataSourceListCreateView.as_view(), name='sources'),
    path('sources/<uuid:pk>/', views.DataSourceDetailView.as_view(), name='source_detail'),
    path('sources/<uuid:pk>/test/', views.test_data_source_view, name='test_source'),
    path('quality-rules/', views.DataQualityRuleListCreateView.as_view(), name='quality_rules'),
]