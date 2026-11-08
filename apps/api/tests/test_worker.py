from services.worker.tasks.smoke import ping_task, smoke_task


def test_smoke_task_execution():
    """Verify smoke_task runs mathematical logic and returns formatted dictionary."""
    async_result = smoke_task.apply(args=[15, 27])
    result = async_result.result

    assert result["status"] == "success"
    assert result["sum"] == 42
    assert result["x"] == 15
    assert result["y"] == 27
    assert "task_id" in result
    assert "executed_at" in result


def test_ping_task_execution():
    """Verify worker ping_task responds with status='pong'."""
    result = ping_task()
    assert result["status"] == "pong"
    assert "timestamp" in result
