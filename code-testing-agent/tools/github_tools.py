from claude_agent_sdk import tool
from github import Github, GithubException
from typing import Any, Dict
import os

@tool(
    "create_pull_request",
    "Create a GitHub pull request with detailed description",
    {
        "title": str,
        "body": str,
        "head_branch": str,
        "base_branch": str,
        "owner": str,
        "repo": str
    }
)
async def create_pull_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create GitHub PR with comprehensive description"""
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return {
                "content": [{
                    "type": "text",
                    "text": "ERROR: GITHUB_TOKEN not set in environment"
                }],
                "is_error": True
            }

        g = Github(token)
        repo = g.get_repo(f"{args['owner']}/{args['repo']}")

        pr = repo.create_pull(
            title=args["title"],
            body=args["body"],
            head=args["head_branch"],
            base=args.get("base_branch", "main")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Pull Request created successfully!\nURL: {pr.html_url}\nNumber: #{pr.number}"
            }]
        }
    except GithubException as e:
        return {
            "content": [{
                "type": "text",
                "text": f"GitHub API Error: {e.data.get('message', str(e))}"
            }],
            "is_error": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }

@tool(
    "list_pull_requests",
    "List pull requests for a repository",
    {"owner": str, "repo": str, "state": str}
)
async def list_pull_requests(args: Dict[str, Any]) -> Dict[str, Any]:
    """List PRs with their status"""
    try:
        token = os.environ.get("GITHUB_TOKEN")
        g = Github(token)
        repo = g.get_repo(f"{args['owner']}/{args['repo']}")

        prs = repo.get_pulls(state=args.get("state", "open"))
        pr_list = [f"#{pr.number}: {pr.title} ({pr.state})" for pr in prs[:10]]

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(pr_list) if pr_list else "No pull requests found"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }
