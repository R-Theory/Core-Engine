#!/usr/bin/env python3
"""
Core Engine MVP System Test Script
Tests all major components and integrations
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class CoreEngineSystemTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results = []
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Core Engine MVP System Tests...")
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
        
        # Print test results
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        print(f"\n📈 Total: {len(self.test_results)} | Passed: {passed} | Failed: {failed}")
        
        if failed > 0:
            print("❌ Some tests failed. Check the logs above.")
            exit(1)
        else:
            print("🎉 All tests passed!")
    
    def log_test(self, test_name: str, status: str, message: str):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
    
    async def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        self.log_test("Health Check", "PASS", "API is healthy")
                        return True
                    else:
                        self.log_test("Health Check", "FAIL", f"Unhealthy status: {data}")
                        return False
                else:
                    self.log_test("Health Check", "FAIL", f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Connection error: {e}")
            return False
    
    async def test_user_registration(self):
        """Test user registration"""
        try:
            user_data = {
                "email": "test@coreengine.dev",
                "username": "testuser",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.log_test("User Registration", "PASS", "User registered successfully")
                    return True
                else:
                    error_data = await response.json()
                    self.log_test("User Registration", "FAIL", f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Error: {e}")
            return False
    
    async def test_user_login(self):
        """Test user login"""
        try:
            login_data = {
                "username": "test@coreengine.dev",
                "password": "testpass123"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data  # OAuth2PasswordRequestForm expects form data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.log_test("User Login", "PASS", "Login successful")
                    return True
                else:
                    error_data = await response.json()
                    self.log_test("User Login", "FAIL", f"HTTP {response.status}: {error_data}")
                    return False
        except Exception as e:
            self.log_test("User Login", "FAIL", f"Error: {e}")
            return False
    
    async def test_course_management(self):
        """Test course CRUD operations"""
        if not self.auth_token:
            self.log_test("Course Management", "FAIL", "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Create course
            course_data = {
                "name": "Test Course",
                "code": "TEST101",
                "semester": "Fall 2024",
                "instructor": "Dr. Test",
                "description": "A test course for system validation"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/courses",
                json=course_data,
                headers=headers
            ) as response:
                if response.status == 201:
                    course = await response.json()
                    course_id = course["id"]
                    
                    # Get courses
                    async with self.session.get(
                        f"{self.base_url}/api/v1/courses",
                        headers=headers
                    ) as get_response:
                        if get_response.status == 200:
                            courses = await get_response.json()
                            if len(courses) > 0:
                                self.log_test("Course Management", "PASS", f"Created and retrieved course: {course_id}")
                                return True
                            else:
                                self.log_test("Course Management", "FAIL", "No courses returned")
                                return False
                        else:
                            self.log_test("Course Management", "FAIL", f"Failed to get courses: {get_response.status}")
                            return False
                else:
                    error_data = await response.json()
                    self.log_test("Course Management", "FAIL", f"Failed to create course: {error_data}")
                    return False
        except Exception as e:
            self.log_test("Course Management", "FAIL", f"Error: {e}")
            return False
    
    async def test_ai_agents(self):
        """Test AI agent functionality"""
        if not self.auth_token:
            self.log_test("AI Agents", "FAIL", "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Get available agents
            async with self.session.get(
                f"{self.base_url}/api/v1/agents",
                headers=headers
            ) as response:
                if response.status == 200:
                    agents = await response.json()
                    if len(agents) > 0:
                        # Test interaction with first agent
                        agent = agents[0]
                        agent_name = agent["name"]
                        
                        if agent["capabilities"]:
                            capability = agent["capabilities"][0]["name"]
                            
                            interaction_data = {
                                "capability": capability,
                                "input_data": {
                                    "text": "This is a test input for AI analysis",
                                    "analysis_type": "summary"
                                }
                            }
                            
                            async with self.session.post(
                                f"{self.base_url}/api/v1/agents/{agent_name}/interact",
                                json=interaction_data,
                                headers=headers
                            ) as interact_response:
                                if interact_response.status == 200:
                                    result = await interact_response.json()
                                    if result.get("success"):
                                        self.log_test("AI Agents", "PASS", f"Successfully interacted with {agent_name}")
                                        return True
                                    else:
                                        self.log_test("AI Agents", "FAIL", f"Agent interaction failed: {result.get('error_message')}")
                                        return False
                                else:
                                    self.log_test("AI Agents", "FAIL", f"Agent interaction HTTP {interact_response.status}")
                                    return False
                        else:
                            self.log_test("AI Agents", "FAIL", f"Agent {agent_name} has no capabilities")
                            return False
                    else:
                        self.log_test("AI Agents", "FAIL", "No agents available")
                        return False
                else:
                    self.log_test("AI Agents", "FAIL", f"Failed to get agents: {response.status}")
                    return False
        except Exception as e:
            self.log_test("AI Agents", "FAIL", f"Error: {e}")
            return False
    
    async def test_plugins(self):
        """Test plugin system"""
        if not self.auth_token:
            self.log_test("Plugin System", "FAIL", "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Get available plugins
            async with self.session.get(
                f"{self.base_url}/api/v1/plugins",
                headers=headers
            ) as response:
                if response.status == 200:
                    plugins = await response.json()
                    if len(plugins) > 0:
                        self.log_test("Plugin System", "PASS", f"Found {len(plugins)} plugins")
                        return True
                    else:
                        self.log_test("Plugin System", "FAIL", "No plugins available")
                        return False
                else:
                    self.log_test("Plugin System", "FAIL", f"Failed to get plugins: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Plugin System", "FAIL", f"Error: {e}")
            return False
    
    async def test_workflows(self):
        """Test workflow system"""
        if not self.auth_token:
            self.log_test("Workflow System", "FAIL", "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Create a simple workflow
            workflow_data = {
                "name": "Test Workflow",
                "description": "A simple test workflow",
                "definition": {
                    "steps": [
                        {
                            "name": "test_step",
                            "type": "ai_agent",
                            "agent": "claude",
                            "capability": "text_analysis",
                            "prompt": "Analyze this test input"
                        }
                    ]
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/workflows",
                json=workflow_data,
                headers=headers
            ) as response:
                if response.status == 201:
                    workflow = await response.json()
                    workflow_id = workflow["id"]
                    
                    # Execute the workflow
                    async with self.session.post(
                        f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                        json={"params": {}},
                        headers=headers
                    ) as execute_response:
                        if execute_response.status == 202:
                            result = await execute_response.json()
                            self.log_test("Workflow System", "PASS", f"Created and executed workflow: {workflow_id}")
                            return True
                        else:
                            self.log_test("Workflow System", "FAIL", f"Failed to execute workflow: {execute_response.status}")
                            return False
                else:
                    error_data = await response.json()
                    self.log_test("Workflow System", "FAIL", f"Failed to create workflow: {error_data}")
                    return False
        except Exception as e:
            self.log_test("Workflow System", "FAIL", f"Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        await self.setup()
        
        try:
            # Test basic connectivity
            if not await self.test_health_check():
                print("❌ Health check failed - aborting tests")
                return
            
            # Test authentication
            if not await self.test_user_registration():
                # Try login with existing user
                await self.test_user_login()
            
            # Test core functionality
            await self.test_course_management()
            await self.test_ai_agents()
            await self.test_plugins()
            await self.test_workflows()
            
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    tester = CoreEngineSystemTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())