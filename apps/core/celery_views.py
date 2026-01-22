"""
API Views for Celery Task Monitoring
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from utils.celery_monitor import CeleryMonitorService, TaskLogger


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def celery_status(request):
    """Get overall Celery status"""
    active_tasks = CeleryMonitorService.get_active_tasks()
    scheduled_tasks = CeleryMonitorService.get_scheduled_tasks()
    worker_stats = CeleryMonitorService.get_worker_stats()
    registered_tasks = CeleryMonitorService.get_registered_tasks()
    
    return Response({
        'active_tasks': active_tasks,
        'active_count': len(active_tasks),
        'scheduled_tasks': scheduled_tasks,
        'scheduled_count': len(scheduled_tasks),
        'workers': worker_stats,
        'registered_tasks': registered_tasks,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status(request, task_id):
    """Get status of a specific task"""
    task_info = CeleryMonitorService.get_task_status(task_id)
    return Response(task_info)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def cancel_task(request, task_id):
    """Cancel a task"""
    result = CeleryMonitorService.cancel_task(task_id)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def retry_task(request, task_id):
    """Retry a failed task"""
    result = CeleryMonitorService.retry_task(task_id)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def purge_queue(request):
    """Purge Celery queue"""
    queue_name = request.data.get('queue', 'celery')
    result = CeleryMonitorService.purge_queue(queue_name)
    return Response(result)
