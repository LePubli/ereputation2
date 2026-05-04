"""
Routes API pour le plugin Automation Engine
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/v1/automation", tags=["Automation"])

class StartSequenceRequest(BaseModel):
    prospect_id: str
    contact_first_name: str
    contact_email: str
    company_name: str
    top_pain_point: str
    workflow_name: str = "standard_b2b"
    sender_name: str = "Notre équipe"
    sender_company: str = "Notre société"

class SequenceActionRequest(BaseModel):
    sequence_id: str

@router.post("/sequences/start")
async def start_sequence(request: StartSequenceRequest) -> Dict[str, Any]:
    """Démarrer une séquence d'automatisation pour un prospect"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        prospect_data = {
            "id": request.prospect_id,
            "contact_first_name": request.contact_first_name,
            "contact_email": request.contact_email,
            "company_name": request.company_name,
            "top_pain_point": request.top_pain_point,
            "sender_name": request.sender_name,
            "sender_company": request.sender_company
        }
        
        result = await engine.start_sequence(
            prospect_data=prospect_data,
            workflow_name=request.workflow_name
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sequences/{sequence_id}")
async def get_sequence_status(sequence_id: str) -> Dict[str, Any]:
    """Obtenir le statut d'une séquence"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        result = engine.get_sequence_status(sequence_id)
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/pause")
async def pause_sequence(request: SequenceActionRequest) -> Dict[str, Any]:
    """Mettre en pause une séquence"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        result = await engine.pause_sequence(request.sequence_id)
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/resume")
async def resume_sequence(request: SequenceActionRequest) -> Dict[str, Any]:
    """Reprendre une séquence en pause"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        result = await engine.resume_sequence(request.sequence_id)
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/stop")
async def stop_sequence(request: SequenceActionRequest) -> Dict[str, Any]:
    """Arrêter définitivement une séquence"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        result = await engine.stop_sequence(request.sequence_id)
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows")
async def list_workflows() -> Dict[str, Any]:
    """Lister les workflows de séquences disponibles"""
    from plugins.automation_engine.engine import SEQUENCE_WORKFLOWS
    
    return {
        "success": True,
        "data": {
            name: {
                "display_name": workflow["name"],
                "steps_count": len(workflow["steps"]),
                "duration_days": max(s["day"] for s in workflow["steps"]) + 1,
                "channels": list(set(s["channel"] for s in workflow["steps"]))
            }
            for name, workflow in SEQUENCE_WORKFLOWS.items()
        }
    }

@router.get("/templates/{channel}")
async def get_templates(channel: str) -> Dict[str, Any]:
    """Obtenir les templates de messages pour un canal"""
    from plugins.automation_engine.engine import MESSAGE_TEMPLATES
    
    if channel not in MESSAGE_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Canal non trouvé: {channel}")
    
    return {
        "success": True,
        "data": {
            template_name: list(template.keys())
            for template_name, template in MESSAGE_TEMPLATES[channel].items()
        }
    }

@router.post("/execute-scheduled")
async def execute_scheduled_steps(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Exécuter les steps planifiés (à appeler via cron/scheduler)"""
    try:
        from plugins.automation_engine.engine import create_plugin
        engine = create_plugin()
        
        # Exécution en background
        background_tasks.add_task(engine.execute_scheduled_steps)
        
        return {
            "success": True,
            "message": "Exécution des steps planifiés démarrée en background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/daily")
async def get_daily_stats() -> Dict[str, Any]:
    """Statistiques d'automatisation du jour"""
    from plugins.automation_engine.engine import create_plugin
    engine = create_plugin()
    
    active_count = sum(1 for seq in engine.active_sequences.values() if seq["status"] == "active")
    completed_count = sum(1 for seq in engine.active_sequences.values() if seq["status"] == "completed")
    
    return {
        "success": True,
        "data": {
            "active_sequences": active_count,
            "completed_today": completed_count,
            "max_per_day": engine.config["max_sequences_per_day"],
            "remaining_capacity": engine.config["max_sequences_per_day"] - active_count
        }
    }
