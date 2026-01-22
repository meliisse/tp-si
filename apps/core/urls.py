
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ClientViewSet, ChauffeurViewSet, VehiculeViewSet, DestinationViewSet, TypeServiceViewSet, TarificationViewSet
from .celery_views import celery_status, task_status, cancel_task, retry_task, purge_queue

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'chauffeurs', ChauffeurViewSet)
router.register(r'vehicules', VehiculeViewSet)
router.register(r'destinations', DestinationViewSet)
router.register(r'typeservices', TypeServiceViewSet)
router.register(r'tarifications', TarificationViewSet)

urlpatterns = [
	path('api/', include(router.urls)),
	path('api/celery/status/', celery_status, name='celery-status'),
	path('api/celery/task/<str:task_id>/', task_status, name='task-status'),
	path('api/celery/task/<str:task_id>/cancel/', cancel_task, name='cancel-task'),
	path('api/celery/task/<str:task_id>/retry/', retry_task, name='retry-task'),
	path('api/celery/purge/', purge_queue, name='purge-queue'),
]