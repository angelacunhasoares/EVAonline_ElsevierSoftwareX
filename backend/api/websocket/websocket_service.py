from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from celery.result import AsyncResult
from loguru import logger
import asyncio
from typing import Dict, Set
from datetime import datetime

# Criar roteador para integrar no app principal
router = APIRouter()

# Armazenar conexões ativas
active_connections: Dict[str, Set[WebSocket]] = {}

async def broadcast_to_task_subscribers(task_id: str, message: dict):
    """
    Envia mensagem para todos os clientes monitorando uma tarefa específica.
    """
    if task_id in active_connections:
        disconnected = set()
        for connection in active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Remover conexões desconectadas
        active_connections[task_id] -= disconnected

async def monitor_task_timeout(task_id: str, websocket: WebSocket, timeout_minutes: int = 30):
    """
    Monitora o timeout da tarefa e fecha a conexão se exceder o limite.
    """
    try:
        await asyncio.sleep(timeout_minutes * 60)
        if websocket in active_connections.get(task_id, set()):
            await websocket.send_json({
                "status": "TIMEOUT",
                "error": f"Monitoramento excedeu {timeout_minutes} minutos"
            })
            await websocket.close()
    except Exception as e:
        logger.error(f"Erro no monitor de timeout: {str(e)}")

@router.websocket("/task_status/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    Endpoint WebSocket para monitorar status de tarefas Celery.
    
    Args:
        websocket: Conexão WebSocket
        task_id: ID da tarefa Celery a ser monitorada
    """
    await websocket.accept()
    
    # Registrar nova conexão
    if task_id not in active_connections:
        active_connections[task_id] = set()
    active_connections[task_id].add(websocket)
    
    # Iniciar monitor de timeout
    timeout_task = asyncio.create_task(
        monitor_task_timeout(task_id, websocket)
    )
    
    try:
        task = AsyncResult(task_id)
        
        # Enviar estado inicial
        current_state = {
            "status": task.state,
            "info": task.info or {},
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(current_state)
        
        while not task.ready():
            if task.state == 'PROGRESS':
                current_state = {
                    "status": "PROGRESS",
                    "info": task.info or {},
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(current_state)
            
            await asyncio.sleep(1)
        
        if task.failed():
            error_info = {
                "status": "FAILURE",
                "error": str(task.info),
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_to_task_subscribers(task_id, error_info)
        else:
            task_result = task.get()
            result, warnings = task_result if task_result else (None, None)
            success_info = {
                "status": "SUCCESS",
                "result": result.to_dict() if hasattr(result, 'to_dict') else result,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_to_task_subscribers(task_id, success_info)
            
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado do monitoramento da tarefa {task_id}")
    except Exception as e:
        error_message = {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        try:
            await websocket.send_json(error_message)
        except Exception:
            logger.error(f"Erro ao enviar mensagem de erro para o cliente: {str(e)}")
    finally:
        # Limpar recursos
        timeout_task.cancel()
        if task_id in active_connections and websocket in active_connections[task_id]:
            active_connections[task_id].remove(websocket)
            if not active_connections[task_id]:
                del active_connections[task_id]
    await websocket.close()