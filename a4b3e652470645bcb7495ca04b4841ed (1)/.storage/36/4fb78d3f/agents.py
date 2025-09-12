from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.agent_registry import AgentRegistry, AgentRequest, AgentCapability
from app.models.user import User

router = APIRouter()

# Initialize agent registry
agent_registry = AgentRegistry()

class AgentInteractRequest(BaseModel):
    capability: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    agent_name: str
    capability: str
    success: bool
    output_data: Dict[str, Any]
    error_message: Optional[str]
    tokens_used: Optional[int]
    cost: Optional[float]
    duration_ms: int

class AgentCapabilityResponse(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    cost_per_request: Optional[float]
    max_tokens: Optional[int]

class AgentInfoResponse(BaseModel):
    name: str
    type: str
    capabilities: List[AgentCapabilityResponse]
    is_healthy: bool

@router.get("/", response_model=List[AgentInfoResponse])
async def get_agents(current_user: User = Depends(get_current_user)):
    """Get all available AI agents"""
    agents = []
    
    for agent_name in agent_registry.list_agents():
        agent = agent_registry.get_agent(agent_name)
        if agent:
            capabilities = await agent_registry.get_agent_capabilities(agent_name)
            is_healthy = await agent.health_check()
            
            agents.append(AgentInfoResponse(
                name=agent_name,
                type=agent.agent_type,
                capabilities=[
                    AgentCapabilityResponse(
                        name=cap.name,
                        description=cap.description,
                        input_schema=cap.input_schema,
                        output_schema=cap.output_schema,
                        cost_per_request=cap.cost_per_request,
                        max_tokens=cap.max_tokens
                    )
                    for cap in capabilities
                ],
                is_healthy=is_healthy
            ))
    
    return agents

@router.get("/{agent_name}", response_model=AgentInfoResponse)
async def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific agent information"""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    capabilities = await agent_registry.get_agent_capabilities(agent_name)
    is_healthy = await agent.health_check()
    
    return AgentInfoResponse(
        name=agent_name,
        type=agent.agent_type,
        capabilities=[
            AgentCapabilityResponse(
                name=cap.name,
                description=cap.description,
                input_schema=cap.input_schema,
                output_schema=cap.output_schema,
                cost_per_request=cap.cost_per_request,
                max_tokens=cap.max_tokens
            )
            for cap in capabilities
        ],
        is_healthy=is_healthy
    )

@router.post("/{agent_name}/interact", response_model=AgentResponse)
async def interact_with_agent(
    agent_name: str,
    request_data: AgentInteractRequest,
    current_user: User = Depends(get_current_user)
):
    """Interact with a specific AI agent"""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if agent is healthy
    is_healthy = await agent.health_check()
    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent is currently unavailable"
        )
    
    # Verify capability exists
    capabilities = await agent_registry.get_agent_capabilities(agent_name)
    capability_names = [cap.name for cap in capabilities]
    
    if request_data.capability not in capability_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capability '{request_data.capability}' not supported by agent '{agent_name}'"
        )
    
    # Create agent request
    agent_request = AgentRequest(
        capability=request_data.capability,
        input_data=request_data.input_data,
        context=request_data.context,
        user_id=str(current_user.id)
    )
    
    # Execute request
    response = await agent_registry.execute_agent_request(agent_name, agent_request)
    
    return AgentResponse(
        agent_name=agent_name,
        capability=request_data.capability,
        success=response.success,
        output_data=response.output_data,
        error_message=response.error_message,
        tokens_used=response.tokens_used,
        cost=response.cost,
        duration_ms=response.duration_ms
    )

@router.get("/{agent_name}/capabilities", response_model=List[AgentCapabilityResponse])
async def get_agent_capabilities(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get capabilities for a specific agent"""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    capabilities = await agent_registry.get_agent_capabilities(agent_name)
    
    return [
        AgentCapabilityResponse(
            name=cap.name,
            description=cap.description,
            input_schema=cap.input_schema,
            output_schema=cap.output_schema,
            cost_per_request=cap.cost_per_request,
            max_tokens=cap.max_tokens
        )
        for cap in capabilities
    ]

@router.post("/batch-interact")
async def batch_interact(
    requests: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """Execute multiple agent interactions in batch"""
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10 requests"
        )
    
    results = []
    
    for req in requests:
        agent_name = req.get("agent_name")
        capability = req.get("capability")
        input_data = req.get("input_data", {})
        context = req.get("context")
        
        if not agent_name or not capability:
            results.append({
                "success": False,
                "error": "Missing agent_name or capability"
            })
            continue
        
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            results.append({
                "success": False,
                "error": f"Agent '{agent_name}' not found"
            })
            continue
        
        # Create and execute request
        agent_request = AgentRequest(
            capability=capability,
            input_data=input_data,
            context=context,
            user_id=str(current_user.id)
        )
        
        response = await agent_registry.execute_agent_request(agent_name, agent_request)
        
        results.append({
            "agent_name": agent_name,
            "capability": capability,
            "success": response.success,
            "output_data": response.output_data,
            "error_message": response.error_message,
            "tokens_used": response.tokens_used,
            "cost": response.cost,
            "duration_ms": response.duration_ms
        })
    
    return {"results": results}

@router.get("/{agent_name}/health")
async def check_agent_health(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Check agent health status"""
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    is_healthy = await agent.health_check()
    
    return {
        "agent_name": agent_name,
        "is_healthy": is_healthy,
        "status": "healthy" if is_healthy else "unhealthy"
    }