from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

class AgentCapability(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    cost_per_request: Optional[float] = None
    max_tokens: Optional[int] = None

class AgentRequest(BaseModel):
    capability: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    user_id: str
    workflow_id: Optional[str] = None

class AgentResponse(BaseModel):
    success: bool
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    duration_ms: int

class BaseAIAgent(ABC):
    """Base class for all AI agents in the system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.agent_type = config.get("type", "generic")
    
    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return list of capabilities this agent supports"""
        pass
    
    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute a request using this agent"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and available"""
        pass

class MetaGPTAgent(BaseAIAgent):
    """MetaGPT agent implementation"""
    
    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="code_generation",
                description="Generate code based on requirements",
                input_schema={"requirements": "string", "language": "string"},
                output_schema={"code": "string", "explanation": "string"},
                cost_per_request=0.05
            ),
            AgentCapability(
                name="architecture_design",
                description="Design system architecture",
                input_schema={"requirements": "string", "constraints": "array"},
                output_schema={"design": "object", "diagrams": "array"},
                cost_per_request=0.08
            )
        ]
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            # Simulate MetaGPT API call
            await asyncio.sleep(1)  # Simulate processing time
            
            if request.capability == "code_generation":
                result = {
                    "code": f"# Generated code for: {request.input_data.get('requirements', 'Unknown')}\nprint('Hello World')",
                    "explanation": "This is a simple implementation based on your requirements."
                }
            elif request.capability == "architecture_design":
                result = {
                    "design": {"components": ["frontend", "backend", "database"], "patterns": ["MVC"]},
                    "diagrams": ["system_diagram.png"]
                }
            else:
                raise ValueError(f"Unsupported capability: {request.capability}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                success=True,
                output_data=result,
                tokens_used=150,
                cost=0.05,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                success=False,
                output_data={},
                error_message=str(e),
                duration_ms=duration_ms
            )
    
    async def health_check(self) -> bool:
        return True  # Simulate healthy status

class ClaudeAgent(BaseAIAgent):
    """Claude agent implementation"""
    
    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="text_analysis",
                description="Analyze and summarize text content",
                input_schema={"text": "string", "analysis_type": "string"},
                output_schema={"summary": "string", "key_points": "array"},
                cost_per_request=0.03
            ),
            AgentCapability(
                name="question_answering",
                description="Answer questions based on context",
                input_schema={"question": "string", "context": "string"},
                output_schema={"answer": "string", "confidence": "number"},
                cost_per_request=0.02
            )
        ]
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            await asyncio.sleep(0.5)  # Simulate processing time
            
            if request.capability == "text_analysis":
                result = {
                    "summary": f"Analysis of: {request.input_data.get('text', 'No text')[:50]}...",
                    "key_points": ["Point 1", "Point 2", "Point 3"]
                }
            elif request.capability == "question_answering":
                result = {
                    "answer": f"Based on the context, the answer to '{request.input_data.get('question', 'No question')}' is...",
                    "confidence": 0.85
                }
            else:
                raise ValueError(f"Unsupported capability: {request.capability}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                success=True,
                output_data=result,
                tokens_used=100,
                cost=0.03,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                success=False,
                output_data={},
                error_message=str(e),
                duration_ms=duration_ms
            )
    
    async def health_check(self) -> bool:
        return True

class AgentRegistry:
    """Registry for managing AI agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAIAgent] = {}
    
    async def initialize_agents(self):
        """Initialize default agents"""
        # Initialize MetaGPT agent
        metagpt_config = {
            "name": "metagpt",
            "type": "code_generation",
            "api_key": "demo_key"
        }
        self.agents["metagpt"] = MetaGPTAgent(metagpt_config)
        
        # Initialize Claude agent
        claude_config = {
            "name": "claude",
            "type": "text_analysis", 
            "api_key": "demo_key"
        }
        self.agents["claude"] = ClaudeAgent(claude_config)
        
        logger.info(f"Initialized {len(self.agents)} AI agents")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAIAgent]:
        """Get an agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all available agents"""
        return list(self.agents.keys())
    
    async def execute_agent_request(self, agent_name: str, request: AgentRequest) -> AgentResponse:
        """Execute a request on a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentResponse(
                success=False,
                output_data={},
                error_message=f"Agent {agent_name} not found",
                duration_ms=0
            )
        
        return await agent.execute(request)
    
    async def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Get capabilities for a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        
        return await agent.get_capabilities()