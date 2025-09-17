"""
AI Provider Service - Integrates with OpenAI, Anthropic Claude, and other AI providers

This service handles the actual AI model interactions, using personalized context
from the AI Context service to provide more relevant responses.
"""

import asyncio
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured",
                "response": "I'm sorry, but the OpenAI integration is not properly configured. Please add your OpenAI API key to use this feature."
            }
        
        try:
            # For now, return a structured mock response
            # In production, this would make actual API calls to OpenAI
            return {
                "success": True,
                "response": f"[OpenAI {model} Response]\n\nBased on your personalized context, here's my response to your query.\n\nThis is currently a demo response. To enable full OpenAI integration:\n1. Add your OpenAI API key to the environment\n2. Install the openai Python package\n3. The system will automatically use your context for personalized responses",
                "model": model,
                "usage": {
                    "prompt_tokens": len(str(messages)),
                    "completion_tokens": 150,
                    "total_tokens": len(str(messages)) + 150
                },
                "provider": "openai"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Please try again later."
            }
    
    def get_available_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Anthropic Claude API"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "Anthropic API key not configured",
                "response": "I'm sorry, but the Anthropic Claude integration is not properly configured. Please add your Anthropic API key to use this feature."
            }
        
        try:
            # For now, return a structured mock response
            # In production, this would make actual API calls to Anthropic
            return {
                "success": True,
                "response": f"[Claude {model} Response]\n\nHello! I'm Claude, and I've been provided with your personalized context to give you more relevant assistance.\n\nThis is currently a demo response. To enable full Claude integration:\n1. Add your Anthropic API key to the environment\n2. Install the anthropic Python package\n3. The system will automatically use your learning style and background for better responses",
                "model": model,
                "usage": {
                    "input_tokens": len(str(messages)),
                    "output_tokens": 160,
                    "total_tokens": len(str(messages)) + 160
                },
                "provider": "anthropic"
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Please try again later."
            }
    
    def get_available_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]

class AIProviderService:
    """Service for managing AI providers and generating responses"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        self.logger = logging.getLogger(__name__)
    
    def get_provider(self, provider_name: str) -> Optional[AIProvider]:
        """Get AI provider by name"""
        return self.providers.get(provider_name.lower())
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_available_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider"""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_available_models()
        return []
    
    async def generate_contextual_response(
        self,
        provider_name: str,
        model: str,
        user_message: str,
        personalized_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using the specified AI provider with personalized context
        
        Args:
            provider_name: AI provider to use ('openai', 'anthropic')
            model: Specific model to use
            user_message: User's current message
            personalized_prompt: Context-aware system prompt
            conversation_history: Previous conversation messages
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Dict containing the AI response and metadata
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return {
                "success": False,
                "error": f"Provider '{provider_name}' not available",
                "response": f"The {provider_name} provider is not available. Please try a different provider."
            }
        
        try:
            # Build the messages array for the AI model
            messages = []
            
            # Add system prompt with personalized context
            messages.append({
                "role": "system",
                "content": personalized_prompt
            })
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages to stay within limits
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg.get("content", "")
                        })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            result = await provider.generate_response(
                messages=messages,
                model=model,
                **kwargs
            )
            
            self.logger.info(f"Generated response using {provider_name} {model}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating response with {provider_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while generating a response. Please try again later."
            }
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all providers"""
        status = {}
        
        for name, provider in self.providers.items():
            has_api_key = False
            
            if name == "openai":
                has_api_key = bool(os.getenv("OPENAI_API_KEY"))
            elif name == "anthropic":
                has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
            
            status[name] = {
                "available": True,
                "configured": has_api_key,
                "models": provider.get_available_models(),
                "status": "ready" if has_api_key else "needs_api_key"
            }
        
        return status

# Global service instance
ai_provider_service = AIProviderService()