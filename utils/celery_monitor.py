"""
Celery Task Monitoring Service
Provides monitoring and management of Celery tasks
"""
from celery.result import AsyncResult
from celery import current_app
from django.core.cache import cache
from datetime import datetime, timedelta


class CeleryMonitorService:
    """Service for monitoring Celery tasks"""
    
    @staticmethod
    def get_task_status(task_id):
        """Get status of a specific task"""
        result = AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.successful() else None,
            'error': str(result.result) if result.failed() else None,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None,
        }
    
    @staticmethod
    def get_active_tasks():
        """Get list of active tasks"""
        inspect = current_app.control.inspect()
        active = inspect.active()
        
        if not active:
            return []
        
        tasks = []
        for worker, task_list in active.items():
            for task in task_list:
                tasks.append({
                    'worker': worker,
                    'task_id': task['id'],
                    'name': task['name'],
                    'args': task['args'],
                    'kwargs': task['kwargs'],
                    'time_start': task.get('time_start'),
                })
        
        return tasks
    
    @staticmethod
    def get_scheduled_tasks():
        """Get list of scheduled tasks"""
        inspect = current_app.control.inspect()
        scheduled = inspect.scheduled()
        
        if not scheduled:
            return []
        
        tasks = []
        for worker, task_list in scheduled.items():
            for task in task_list:
                tasks.append({
                    'worker': worker,
                    'task_id': task['request']['id'],
                    'name': task['request']['name'],
                    'eta': task.get('eta'),
                })
        
        return tasks
    
    @staticmethod
    def get_registered_tasks():
        """Get list of all registered tasks"""
        inspect = current_app.control.inspect()
        registered = inspect.registered()
        
        if not registered:
            return []
        
        all_tasks = set()
        for worker, task_list in registered.items():
            all_tasks.update(task_list)
        
        return sorted(list(all_tasks))
    
    @staticmethod
    def get_worker_stats():
        """Get statistics about workers"""
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return []
        
        worker_info = []
        for worker, info in stats.items():
            worker_info.append({
                'worker': worker,
                'pool': info.get('pool', {}).get('implementation'),
                'max_concurrency': info.get('pool', {}).get('max-concurrency'),
                'total_tasks': info.get('total', {}),
            })
        
        return worker_info
    
    @staticmethod
    def cancel_task(task_id):
        """Cancel a task"""
        result = AsyncResult(task_id)
        result.revoke(terminate=True)
        return {'status': 'cancelled', 'task_id': task_id}
    
    @staticmethod
    def retry_task(task_id):
        """Retry a failed task"""
        result = AsyncResult(task_id)
        if result.failed():
            # Get task name and args
            task_name = result.name
            task_args = result.args
            task_kwargs = result.kwargs
            
            # Re-execute the task
            task = current_app.tasks.get(task_name)
            if task:
                new_result = task.apply_async(args=task_args, kwargs=task_kwargs)
                return {'status': 'retried', 'new_task_id': new_result.id}
        
        return {'status': 'not_retried', 'reason': 'Task not failed or not found'}
    
    @staticmethod
    def purge_queue(queue_name='celery'):
        """Purge all messages from a queue"""
        result = current_app.control.purge()
        return {'purged': result}
    
    @staticmethod
    def get_task_history(hours=24):
        """Get task execution history from cache"""
        # This would require custom task tracking
        # For now, return a placeholder
        return {
            'message': 'Task history tracking requires custom implementation',
            'hours': hours
        }


class TaskLogger:
    """Utility to log task executions"""
    
    @staticmethod
    def log_task_start(task_id, task_name, args, kwargs):
        """Log task start"""
        cache_key = f'task_log_{task_id}'
        cache.set(cache_key, {
            'task_id': task_id,
            'task_name': task_name,
            'args': args,
            'kwargs': kwargs,
            'status': 'started',
            'start_time': datetime.now().isoformat(),
        }, timeout=86400)  # 24 hours
    
    @staticmethod
    def log_task_success(task_id, result):
        """Log task success"""
        cache_key = f'task_log_{task_id}'
        data = cache.get(cache_key, {})
        data.update({
            'status': 'success',
            'result': str(result)[:500],
            'end_time': datetime.now().isoformat(),
        })
        cache.set(cache_key, data, timeout=86400)
    
    @staticmethod
    def log_task_failure(task_id, error):
        """Log task failure"""
        cache_key = f'task_log_{task_id}'
        data = cache.get(cache_key, {})
        data.update({
            'status': 'failed',
            'error': str(error)[:500],
            'end_time': datetime.now().isoformat(),
        })
        cache.set(cache_key, data, timeout=86400)
