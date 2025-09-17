"""
GitHub Integration
Syncs repositories, issues, pull requests, and commits
Supports knowledge graph connections between code and academic work
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.integration_engine import (
    BaseIntegration, IntegrationType, IntegrationCapability, 
    SyncResult, SyncStatus, IntegrationMetadata, register_integration
)

class GitHubConfig(BaseModel):
    """GitHub API configuration"""
    access_token: str
    api_url: str = "https://api.github.com"
    username: Optional[str] = None

class GitHubRepository(BaseModel):
    """GitHub repository data"""
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    html_url: str
    clone_url: str
    language: Optional[str]
    topics: List[str] = []
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime]
    stargazers_count: int = 0
    forks_count: int = 0

class GitHubIssue(BaseModel):
    """GitHub issue/pull request data"""
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    labels: List[str] = []
    assignees: List[str] = []
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    html_url: str
    repository_id: int
    is_pull_request: bool = False

class GitHubCommit(BaseModel):
    """GitHub commit data"""
    sha: str
    message: str
    author_name: str
    author_email: str
    committed_at: datetime
    html_url: str
    repository_id: int
    files_changed: List[str] = []

@register_integration
class GitHubIntegration(BaseIntegration[GitHubRepository]):
    """
    GitHub integration for code repository and project management
    Perfect for tracking coding assignments and personal projects
    """
    
    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.CODE_REPO
    
    @property
    def supported_capabilities(self) -> List[IntegrationCapability]:
        return [
            IntegrationCapability.READ,
            IntegrationCapability.WRITE,
            IntegrationCapability.WEBHOOK,
            IntegrationCapability.SEARCH,
            IntegrationCapability.GRAPH,  # Repos -> Issues -> Commits relationships
        ]
    
    @property
    def service_name(self) -> str:
        return "GitHub"
    
    def __init__(self, integration_id: str, config: Dict[str, Any]):
        super().__init__(integration_id, config)
        if config:  # Only validate config if it's provided
            self.github_config = GitHubConfig(**config)
        else:
            self.github_config = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"token {self.github_config.access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CoreEngine-Integration/1.0"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make GitHub API request"""
        session = await self._get_session()
        url = f"{self.github_config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with session.get(url, params=params or {}) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"GitHub API request failed: {str(e)}")
            raise
    
    async def _get_paginated_data(self, endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all pages of data from GitHub API"""
        all_data = []
        page_params = (params or {}).copy()
        page_params.update({"per_page": 100, "page": 1})
        
        while True:
            try:
                data = await self._make_request(endpoint, page_params)
                if isinstance(data, list):
                    all_data.extend(data)
                    if len(data) < 100:  # Last page
                        break
                    page_params["page"] += 1
                else:
                    all_data.append(data)
                    break
            except Exception as e:
                self.logger.error(f"Error fetching paginated data: {str(e)}")
                break
        
        return all_data
    
    async def authenticate(self) -> bool:
        """Test GitHub API authentication"""
        try:
            user_data = await self._make_request("/user")
            self.github_config.username = user_data.get("login")
            return True
        except Exception as e:
            self.logger.error(f"GitHub authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test GitHub connection"""
        return await self.authenticate()
    
    async def get_repositories(self, include_private: bool = True) -> List[GitHubRepository]:
        """Get all repositories for the authenticated user"""
        try:
            # Get user's repositories
            repos_data = await self._get_paginated_data(
                "/user/repos",
                {
                    "sort": "updated",
                    "direction": "desc",
                    "type": "all" if include_private else "public"
                }
            )
            
            repositories = []
            for repo_data in repos_data:
                try:
                    # Parse dates
                    created_at = datetime.fromisoformat(repo_data["created_at"].replace('Z', '+00:00'))
                    updated_at = datetime.fromisoformat(repo_data["updated_at"].replace('Z', '+00:00'))
                    pushed_at = None
                    if repo_data.get("pushed_at"):
                        pushed_at = datetime.fromisoformat(repo_data["pushed_at"].replace('Z', '+00:00'))
                    
                    repository = GitHubRepository(
                        id=repo_data["id"],
                        name=repo_data["name"],
                        full_name=repo_data["full_name"],
                        description=repo_data.get("description"),
                        private=repo_data["private"],
                        html_url=repo_data["html_url"],
                        clone_url=repo_data["clone_url"],
                        language=repo_data.get("language"),
                        topics=repo_data.get("topics", []),
                        created_at=created_at,
                        updated_at=updated_at,
                        pushed_at=pushed_at,
                        stargazers_count=repo_data.get("stargazers_count", 0),
                        forks_count=repo_data.get("forks_count", 0)
                    )
                    repositories.append(repository)
                except Exception as e:
                    self.logger.warning(f"Failed to parse repository {repo_data.get('id', 'unknown')}: {str(e)}")
            
            return repositories
        except Exception as e:
            self.logger.error(f"Failed to fetch repositories: {str(e)}")
            return []
    
    async def get_repository_issues(self, repo_full_name: str, repository_id: int) -> List[GitHubIssue]:
        """Get issues and pull requests for a repository"""
        try:
            # Get issues (includes pull requests)
            issues_data = await self._get_paginated_data(
                f"/repos/{repo_full_name}/issues",
                {"state": "all", "sort": "updated"}
            )
            
            issues = []
            for issue_data in issues_data:
                try:
                    created_at = datetime.fromisoformat(issue_data["created_at"].replace('Z', '+00:00'))
                    updated_at = datetime.fromisoformat(issue_data["updated_at"].replace('Z', '+00:00'))
                    closed_at = None
                    if issue_data.get("closed_at"):
                        closed_at = datetime.fromisoformat(issue_data["closed_at"].replace('Z', '+00:00'))
                    
                    # Extract labels and assignees
                    labels = [label["name"] for label in issue_data.get("labels", [])]
                    assignees = [assignee["login"] for assignee in issue_data.get("assignees", [])]
                    
                    issue = GitHubIssue(
                        id=issue_data["id"],
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data.get("body"),
                        state=issue_data["state"],
                        labels=labels,
                        assignees=assignees,
                        created_at=created_at,
                        updated_at=updated_at,
                        closed_at=closed_at,
                        html_url=issue_data["html_url"],
                        repository_id=repository_id,
                        is_pull_request="pull_request" in issue_data
                    )
                    issues.append(issue)
                except Exception as e:
                    self.logger.warning(f"Failed to parse issue {issue_data.get('id', 'unknown')}: {str(e)}")
            
            return issues
        except Exception as e:
            self.logger.error(f"Failed to fetch issues for {repo_full_name}: {str(e)}")
            return []
    
    async def get_repository_commits(self, repo_full_name: str, repository_id: int, limit: int = 50) -> List[GitHubCommit]:
        """Get recent commits for a repository"""
        try:
            commits_data = await self._make_request(
                f"/repos/{repo_full_name}/commits",
                {"per_page": limit}
            )
            
            commits = []
            for commit_data in commits_data:
                try:
                    commit_info = commit_data["commit"]
                    author_info = commit_info.get("author", {})
                    
                    committed_at = datetime.fromisoformat(
                        author_info.get("date", "").replace('Z', '+00:00')
                    )
                    
                    commit = GitHubCommit(
                        sha=commit_data["sha"],
                        message=commit_info.get("message", ""),
                        author_name=author_info.get("name", ""),
                        author_email=author_info.get("email", ""),
                        committed_at=committed_at,
                        html_url=commit_data["html_url"],
                        repository_id=repository_id,
                        files_changed=[]  # Would need separate API call for detailed file info
                    )
                    commits.append(commit)
                except Exception as e:
                    self.logger.warning(f"Failed to parse commit {commit_data.get('sha', 'unknown')}: {str(e)}")
            
            return commits
        except Exception as e:
            self.logger.error(f"Failed to fetch commits for {repo_full_name}: {str(e)}")
            return []
    
    async def sync_data(self, db: Session, user_id: str, full_sync: bool = False) -> SyncResult:
        """Sync GitHub data to local database"""
        try:
            result = SyncResult(status=SyncStatus.IN_PROGRESS)
            
            # Note: For now, we'll store in the existing Course/Assignment models
            # TODO: Create dedicated GitHub models (Repository, Issue, Commit) later
            
            self.logger.info(f"Syncing GitHub repositories for user {user_id}")
            github_repos = await self.get_repositories()
            
            for github_repo in github_repos:
                try:
                    # For now, treat repositories as "courses" in the system
                    # This allows integration with existing UI while we build dedicated models
                    from app.models import Course
                    
                    existing_course = db.query(Course).filter(
                        Course.user_id == user_id,
                        Course.external_id == str(github_repo.id),
                        Course.external_source == "github"
                    ).first()
                    
                    if existing_course:
                        # Update existing
                        existing_course.name = github_repo.name
                        existing_course.description = github_repo.description or ""
                        existing_course.course_code = github_repo.language or "CODE"
                        result.items_updated += 1
                    else:
                        # Create new
                        new_course = Course(
                            user_id=user_id,
                            name=github_repo.name,
                            course_code=github_repo.language or "CODE",
                            description=github_repo.description or f"GitHub Repository: {github_repo.full_name}",
                            is_active=True,
                            external_id=str(github_repo.id),
                            external_source="github",
                            external_url=github_repo.html_url
                        )
                        db.add(new_course)
                        result.items_created += 1
                    
                    db.flush()
                    course_obj = existing_course or new_course
                    
                    # Sync issues as assignments
                    if full_sync:
                        self.logger.info(f"Syncing issues for repository {github_repo.name}")
                        github_issues = await self.get_repository_issues(github_repo.full_name, github_repo.id)
                        
                        for github_issue in github_issues[:20]:  # Limit to recent issues
                            try:
                                from app.models import Assignment
                                
                                existing_assignment = db.query(Assignment).filter(
                                    Assignment.course_id == course_obj.id,
                                    Assignment.external_id == str(github_issue.id),
                                    Assignment.external_source == "github"
                                ).first()
                                
                                if existing_assignment:
                                    # Update existing
                                    existing_assignment.title = github_issue.title
                                    existing_assignment.description = github_issue.body or ""
                                    existing_assignment.is_active = github_issue.state == "open"
                                    result.items_updated += 1
                                else:
                                    # Create new
                                    new_assignment = Assignment(
                                        course_id=course_obj.id,
                                        title=f"#{github_issue.number}: {github_issue.title}",
                                        description=github_issue.body or "",
                                        is_active=github_issue.state == "open",
                                        external_id=str(github_issue.id),
                                        external_source="github",
                                        external_url=github_issue.html_url
                                    )
                                    db.add(new_assignment)
                                    result.items_created += 1
                                
                                result.items_processed += 1
                                
                            except Exception as e:
                                self.logger.error(f"Failed to sync issue {github_issue.id}: {str(e)}")
                                result.items_failed += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to sync repository {github_repo.id}: {str(e)}")
                    result.items_failed += 1
            
            db.commit()
            
            if result.items_failed > 0:
                result.status = SyncStatus.PARTIAL
            else:
                result.status = SyncStatus.SUCCESS
            
            self.logger.info(f"GitHub sync completed: {result.items_created} created, {result.items_updated} updated, {result.items_failed} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"GitHub sync failed: {str(e)}")
            db.rollback()
            return SyncResult(
                status=SyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_relationships(self, item_id: str) -> List[str]:
        """Get related items for knowledge graph"""
        relationships = []
        
        try:
            # Repositories relate to issues, issues relate to commits
            if item_id.startswith("repo_"):
                repo_id = item_id.replace("repo_", "")
                # Would fetch issues and commits for this repo
                # For now, return placeholder
                relationships.append(f"issues_{repo_id}")
                relationships.append(f"commits_{repo_id}")
        except Exception as e:
            self.logger.error(f"Failed to get relationships for {item_id}: {str(e)}")
        
        return relationships
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[GitHubRepository]:
        """Search GitHub repositories"""
        try:
            repositories = await self.get_repositories()
            
            # Simple text search
            query_lower = query.lower()
            matching_repos = [
                repo for repo in repositories 
                if query_lower in repo.name.lower() or 
                   query_lower in (repo.description or "").lower() or
                   query_lower in (repo.language or "").lower()
            ]
            
            return matching_repos
        except Exception as e:
            self.logger.error(f"GitHub search failed: {str(e)}")
            return []
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle GitHub webhook events"""
        try:
            event_type = payload.get("action", "")
            
            # Handle different GitHub events
            if "repository" in payload:
                self.logger.info(f"Received GitHub webhook: {event_type} for repository {payload['repository']['name']}")
                # TODO: Trigger incremental sync for this repository
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to handle GitHub webhook: {str(e)}")
            return False
    
    def extract_metadata(self, item: Any) -> IntegrationMetadata:
        """Extract metadata for knowledge graph"""
        if isinstance(item, GitHubRepository):
            return IntegrationMetadata(
                source_id=f"repo_{item.id}",
                source_type="repository",
                source_url=item.html_url,
                last_modified=item.updated_at,
                relationships=[],  # Will be populated by get_relationships
                tags=["github", "repository", item.language or "unknown"] + item.topics,
                additional_data={
                    "language": item.language,
                    "private": item.private,
                    "stars": item.stargazers_count,
                    "forks": item.forks_count,
                    "topics": item.topics
                }
            )
        elif isinstance(item, GitHubIssue):
            return IntegrationMetadata(
                source_id=f"issue_{item.id}",
                source_type="issue" if not item.is_pull_request else "pull_request",
                source_url=item.html_url,
                last_modified=item.updated_at,
                relationships=[f"repo_{item.repository_id}"],
                tags=["github", "issue" if not item.is_pull_request else "pull_request", item.state] + item.labels,
                additional_data={
                    "number": item.number,
                    "state": item.state,
                    "labels": item.labels,
                    "assignees": item.assignees,
                    "is_pull_request": item.is_pull_request
                }
            )
        
        return super().extract_metadata(item)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()