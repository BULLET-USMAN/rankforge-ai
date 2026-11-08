from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from app.schemas.worker import SmokeTaskRequest, SmokeTaskResponse
from services.worker.celery_app import celery_app

router = APIRouter()


@router.post("/smoke-task", response_model=SmokeTaskResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_smoke_task(payload: SmokeTaskRequest):
    """
    Dispatches a harmless smoke test task to the Celery/Redis queue.
    Returns the task ID to poll for execution result.
    """
    try:
        task = celery_app.send_task("tasks.smoke.smoke_task", args=[payload.x, payload.y])
        return SmokeTaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Dispatched smoke task calculating {payload.x} + {payload.y} to Celery worker queue.",
            result=None,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to dispatch task to Celery/Redis broker: {str(exc)}",
        )


@router.get("/task-status/{task_id}", response_model=SmokeTaskResponse)
def get_task_status(task_id: str):
    """Check status and retrieve result of a previously dispatched Celery task."""
    result = AsyncResult(task_id, app=celery_app)
    task_status = result.status

    if task_status == "SUCCESS":
        return SmokeTaskResponse(
            task_id=task_id,
            status=task_status,
            message="Task executed successfully.",
            result=result.result,
        )
    elif task_status == "FAILURE":
        return SmokeTaskResponse(
            task_id=task_id,
            status=task_status,
            message="Task execution failed.",
            result=str(result.result),
        )
    else:
        return SmokeTaskResponse(
            task_id=task_id,
            status=task_status,
            message=f"Task is currently {task_status.lower()}.",
            result=None,
        )
