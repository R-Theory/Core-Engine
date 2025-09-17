import asyncio
import aiohttp
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import base64

logger = logging.getLogger(__name__)

class PluginClass:
    """GitHub Integration Plugin"""
    
    def __init__(self):
        self.name = "github-integration"
        self.version = "1.0.0"
        self.session = None
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the plugin with configuration"""
        self.config = config
        self.access_token = config.get("access_token")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"token {self.access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CoreEngine/1.0"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Check if GitHub API is accessible"""
        try:
            if not self.session:
                return False
                
            async with self.session.get("https://api.github.com/user") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"GitHub health check failed: {e}")
            return False
    
    async def sync_repositories(self, user_id: str, include_private: bool = False) -> Dict[str, Any]:
        """Synchronize repositories from GitHub"""
        try:
            repositories = []
            url = "https://api.github.com/user/repos"
            
            params = {
                "visibility": "all" if include_private else "public",
                "sort": "updated",
                "per_page": 100
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    github_repos = await response.json()
                    
                    for repo_data in github_repos:
                        # Skip forks unless they have commits
                        if repo_data.get("fork") and not await self._has_original_commits(repo_data["full_name"]):
                            continue
                        
                        repo = {
                            "external_id": str(repo_data.get("id")),
                            "name": repo_data.get("name", ""),
                            "full_name": repo_data.get("full_name", ""),
                            "description": repo_data.get("description", ""),
                            "language": repo_data.get("language"),
                            "private": repo_data.get("private", False),
                            "clone_url": repo_data.get("clone_url"),
                            "html_url": repo_data.get("html_url"),
                            "created_at": repo_data.get("created_at"),
                            "updated_at": repo_data.get("updated_at"),
                            "pushed_at": repo_data.get("pushed_at"),
                            "size": repo_data.get("size", 0),
                            "stargazers_count": repo_data.get("stargazers_count", 0),
                            "forks_count": repo_data.get("forks_count", 0),
                            "open_issues_count": repo_data.get("open_issues_count", 0),
                            "default_branch": repo_data.get("default_branch", "main"),
                            "topics": repo_data.get("topics", [])
                        }
                        repositories.append(repo)
                    
                    logger.info(f"Synced {len(repositories)} repositories from GitHub")
                    return {
                        "success": True,
                        "repositories": repositories,
                        "sync_count": len(repositories)
                    }
                else:
                    logger.error(f"Failed to fetch repositories: {response.status}")
                    return {
                        "success": False,
                        "error": f"GitHub API error: {response.status}",
                        "repositories": [],
                        "sync_count": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "repositories": [],
                "sync_count": 0
            }
    
    async def analyze_commits(self, repository_id: str, since_date: str = None) -> Dict[str, Any]:
        """Analyze commit activity for a repository"""
        try:
            # Get repository info first
            repo_info = await self._get_repository_info(repository_id)
            if not repo_info:
                return {
                    "success": False,
                    "error": "Repository not found",
                    "commits": [],
                    "analysis": {}
                }
            
            full_name = repo_info["full_name"]
            
            # Calculate since date (default to 30 days ago)
            if not since_date:
                since = datetime.now() - timedelta(days=30)
                since_date = since.isoformat()
            
            commits = []
            url = f"https://api.github.com/repos/{full_name}/commits"
            
            params = {
                "since": since_date,
                "per_page": 100
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    github_commits = await response.json()
                    
                    for commit_data in github_commits:
                        commit = {
                            "sha": commit_data.get("sha"),
                            "message": commit_data["commit"]["message"],
                            "author": {
                                "name": commit_data["commit"]["author"]["name"],
                                "email": commit_data["commit"]["author"]["email"],
                                "date": commit_data["commit"]["author"]["date"]
                            },
                            "committer": {
                                "name": commit_data["commit"]["committer"]["name"],
                                "email": commit_data["commit"]["committer"]["email"],
                                "date": commit_data["commit"]["committer"]["date"]
                            },
                            "url": commit_data.get("html_url"),
                            "stats": await self._get_commit_stats(full_name, commit_data.get("sha"))
                        }
                        commits.append(commit)
                    
                    # Generate analysis
                    analysis = self._analyze_commit_data(commits)
                    
                    logger.info(f"Analyzed {len(commits)} commits for repository {full_name}")
                    return {
                        "success": True,
                        "commits": commits,
                        "analysis": analysis
                    }
                else:
                    return {
                        "success": False,
                        "error": f"GitHub API error: {response.status}",
                        "commits": [],
                        "analysis": {}
                    }
                    
        except Exception as e:
            logger.error(f"Error analyzing commits: {e}")
            return {
                "success": False,
                "error": str(e),
                "commits": [],
                "analysis": {}
            }
    
    async def track_issues(self, repository_id: str) -> Dict[str, Any]:
        """Track issues and pull requests for a repository"""
        try:
            repo_info = await self._get_repository_info(repository_id)
            if not repo_info:
                return {
                    "success": False,
                    "error": "Repository not found",
                    "issues": [],
                    "pull_requests": []
                }
            
            full_name = repo_info["full_name"]
            
            # Get issues (excluding pull requests)
            issues = await self._get_issues(full_name, is_pr=False)
            
            # Get pull requests
            pull_requests = await self._get_issues(full_name, is_pr=True)
            
            return {
                "success": True,
                "issues": issues,
                "pull_requests": pull_requests
            }
            
        except Exception as e:
            logger.error(f"Error tracking issues: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "pull_requests": []
            }
    
    async def _has_original_commits(self, full_name: str) -> bool:
        """Check if a forked repository has original commits"""
        try:
            url = f"https://api.github.com/repos/{full_name}/commits"
            params = {"per_page": 1}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    commits = await response.json()
                    return len(commits) > 0
        except Exception:
            pass
        
        return False
    
    async def _get_repository_info(self, repository_id: str) -> Dict[str, Any]:
        """Get repository information by ID"""
        try:
            url = f"https://api.github.com/repositories/{repository_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error fetching repository info: {e}")
        
        return None
    
    async def _get_commit_stats(self, full_name: str, sha: str) -> Dict[str, Any]:
        """Get statistics for a specific commit"""
        try:
            url = f"https://api.github.com/repos/{full_name}/commits/{sha}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    commit_data = await response.json()
                    stats = commit_data.get("stats", {})
                    return {
                        "additions": stats.get("additions", 0),
                        "deletions": stats.get("deletions", 0),
                        "total": stats.get("total", 0)
                    }
        except Exception as e:
            logger.error(f"Error fetching commit stats: {e}")
        
        return {"additions": 0, "deletions": 0, "total": 0}
    
    async def _get_issues(self, full_name: str, is_pr: bool = False) -> List[Dict[str, Any]]:
        """Get issues or pull requests for a repository"""
        try:
            url = f"https://api.github.com/repos/{full_name}/issues"
            params = {
                "state": "all",
                "sort": "updated",
                "per_page": 50
            }
            
            if is_pr:
                params["pulls"] = "true"
            else:
                params["pulls"] = "false"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    github_issues = await response.json()
                    
                    issues = []
                    for issue_data in github_issues:
                        # Skip pull requests when fetching issues
                        if not is_pr and "pull_request" in issue_data:
                            continue
                        
                        # Skip issues when fetching pull requests
                        if is_pr and "pull_request" not in issue_data:
                            continue
                        
                        issue = {
                            "id": issue_data.get("id"),
                            "number": issue_data.get("number"),
                            "title": issue_data.get("title"),
                            "body": issue_data.get("body", ""),
                            "state": issue_data.get("state"),
                            "created_at": issue_data.get("created_at"),
                            "updated_at": issue_data.get("updated_at"),
                            "closed_at": issue_data.get("closed_at"),
                            "author": issue_data["user"]["login"] if issue_data.get("user") else None,
                            "labels": [label["name"] for label in issue_data.get("labels", [])],
                            "assignees": [assignee["login"] for assignee in issue_data.get("assignees", [])],
                            "html_url": issue_data.get("html_url")
                        }
                        issues.append(issue)
                    
                    return issues
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
        
        return []
    
    def _analyze_commit_data(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze commit data and generate insights"""
        if not commits:
            return {}
        
        total_commits = len(commits)
        total_additions = sum(commit["stats"]["additions"] for commit in commits)
        total_deletions = sum(commit["stats"]["deletions"] for commit in commits)
        
        # Analyze commit frequency by day
        commit_dates = [commit["author"]["date"][:10] for commit in commits]
        date_counts = {}
        for date in commit_dates:
            date_counts[date] = date_counts.get(date, 0) + 1
        
        # Analyze contributors
        contributors = {}
        for commit in commits:
            author = commit["author"]["name"]
            contributors[author] = contributors.get(author, 0) + 1
        
        # Calculate average changes per commit
        avg_additions = total_additions / total_commits if total_commits > 0 else 0
        avg_deletions = total_deletions / total_commits if total_commits > 0 else 0
        
        return {
            "total_commits": total_commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "avg_additions_per_commit": round(avg_additions, 2),
            "avg_deletions_per_commit": round(avg_deletions, 2),
            "commit_frequency": date_counts,
            "contributors": contributors,
            "most_active_day": max(date_counts.items(), key=lambda x: x[1])[0] if date_counts else None,
            "most_active_contributor": max(contributors.items(), key=lambda x: x[1])[0] if contributors else None
        }