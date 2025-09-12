from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.agent_registry import AgentRegistry, AgentRequest
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution

router = APIRouter()

# Initialize agent registry
agent_registry = AgentRegistry()

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition: Dict[str, Any]
    schedule_cron: Optional[str] = None

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    schedule_cron: Optional[str] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    definition: Dict[str, Any]
    is_active: bool
    schedule_cron: Optional[str]
    created_at: str
    updated_at: str

class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]

class WorkflowExecuteRequest(BaseModel):
    params: Optional[Dict[str, Any]] = {}

@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workflows for the current user"""
    result = await db.execute(
        select(Workflow).where(Workflow.user_id == current_user.id)
    )
    workflows = result.scalars().all()
    
    return [
        WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            definition=workflow.definition,
            is_active=workflow.is_active,
            schedule_cron=workflow.schedule_cron,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        for workflow in workflows
    ]

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow"""
    workflow = Workflow(
        user_id=current_user.id,
        name=workflow_data.name,
        description=workflow_data.description,
        definition=workflow_data.definition,
        schedule_cron=workflow_data.schedule_cron
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        definition=workflow.definition,
        is_active=workflow.is_active,
        schedule_cron=workflow.schedule_cron,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow details"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        definition=workflow.definition,
        is_active=workflow.is_active,
        schedule_cron=workflow.schedule_cron,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update workflow"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Update fields
    update_data = workflow_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        definition=workflow.definition,
        is_active=workflow.is_active,
        schedule_cron=workflow.schedule_cron,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )

@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete workflow"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    await db.delete(workflow)
    await db.commit()
    
    return {"message": "Workflow deleted successfully"}

async def execute_workflow_steps(workflow: Workflow, execution: WorkflowExecution, db: AsyncSession, params: Dict[str, Any] = {}):
    """Execute workflow steps"""
    try:
        steps = workflow.definition.get("steps", [])
        context = {"params": params, "steps": {}}
        execution_log = []
        
        for step in steps:
            step_name = step.get("name")
            step_type = step.get("type")
            
            execution_log.append({
                "step": step_name,
                "type": step_type,
                "started_at": datetime.utcnow().isoformat(),
                "status": "running"
            })
            
            try:
                if step_type == "ai_agent":
                    # Execute AI agent step
                    agent_name = step.get("agent")
                    prompt = step.get("prompt", "")
                    
                    # Replace variables in prompt
                    for key, value in context.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                prompt = prompt.replace(f"{{{key}.{sub_key}}}", str(sub_value))
                        else:
                            prompt = prompt.replace(f"{{{key}}}", str(value))
                    
                    # Execute agent request
                    agent_request = AgentRequest(
                        capability=step.get("capability", "text_analysis"),
                        input_data={"prompt": prompt},
                        context=context,
                        user_id=str(workflow.user_id),
                        workflow_id=str(workflow.id)
                    )
                    
                    response = await agent_registry.execute_agent_request(agent_name, agent_request)
                    
                    if response.success:
                        context["steps"][step_name] = {"output": response.output_data}
                        execution_log[-1]["status"] = "completed"
                        execution_log[-1]["result"] = response.output_data
                    else:
                        raise Exception(f"Agent execution failed: {response.error_message}")
                
                elif step_type == "plugin_action":
                    # Execute plugin action step
                    plugin_name = step.get("plugin")
                    action = step.get("action")
                    step_params = step.get("params", {})
                    
                    # Replace variables in params
                    for key, value in step_params.items():
                        if isinstance(value, str):
                            for ctx_key, ctx_value in context.items():
                                if isinstance(ctx_value, dict):
                                    for sub_key, sub_value in ctx_value.items():
                                        value = value.replace(f"{{{ctx_key}.{sub_key}}}", str(sub_value))
                                else:
                                    value = value.replace(f"{{{ctx_key}}}", str(ctx_value))
                            step_params[key] = value
                    
                    # Simulate plugin execution (would use plugin_loader in real implementation)
                    result = {"message": f"Executed {action} on {plugin_name}", "params": step_params}
                    
                    context["steps"][step_name] = {"output": result}
                    execution_log[-1]["status"] = "completed"
                    execution_log[-1]["result"] = result
                
                elif step_type == "system_action":
                    # Execute system action step
                    action = step.get("action")
                    step_params = step.get("params", {})
                    
                    if action == "create_notification":
                        result = {
                            "notification_id": "notif_123",
                            "title": step_params.get("title", "Workflow Notification"),
                            "content": step_params.get("content", "Workflow completed successfully")
                        }
                    else:
                        result = {"message": f"Executed system action: {action}"}
                    
                    context["steps"][step_name] = {"output": result}
                    execution_log[-1]["status"] = "completed"
                    execution_log[-1]["result"] = result
                
                execution_log[-1]["completed_at"] = datetime.utcnow().isoformat()
                
            except Exception as step_error:
                execution_log[-1]["status"] = "failed"
                execution_log[-1]["error"] = str(step_error)
                execution_log[-1]["completed_at"] = datetime.utcnow().isoformat()
                raise step_error
        
        # Update execution with success
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.execution_log = execution_log
        execution.result = context["steps"]
        
    except Exception as e:
        # Update execution with failure
        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error_message = str(e)
        execution.execution_log = execution_log
    
    await db.commit()

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execute_data: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute workflow"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id,
            Workflow.is_active == True
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or inactive"
        )
    
    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status="running"
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # Execute workflow in background
    background_tasks.add_task(
        execute_workflow_steps,
        workflow,
        execution,
        db,
        execute_data.params
    )
    
    return {
        "execution_id": str(execution.id),
        "status": execution.status,
        "message": "Workflow execution started"
    }

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def get_workflow_executions(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow execution history"""
    # Verify workflow belongs to user
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Get executions
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.started_at.desc())
    )
    executions = result.scalars().all()
    
    return [
        WorkflowExecutionResponse(
            id=str(execution.id),
            workflow_id=str(execution.workflow_id),
            status=execution.status,
            started_at=execution.started_at.isoformat(),
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            error_message=execution.error_message,
            result=execution.result
        )
        for execution in executions
    ]

@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow execution details"""
    result = await db.execute(
        select(WorkflowExecution)
        .join(Workflow)
        .where(
            WorkflowExecution.id == execution_id,
            Workflow.user_id == current_user.id
        )
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found"
        )
    
    return WorkflowExecutionResponse(
        id=str(execution.id),
        workflow_id=str(execution.workflow_id),
        status=execution.status,
        started_at=execution.started_at.isoformat(),
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        error_message=execution.error_message,
        result=execution.result
    )