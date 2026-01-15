"""
Human-in-the-Loop System

Provides confirmation prompts and approval workflows for critical agent actions.
"""
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()

class ApprovalType(Enum):
    """Types of actions that require human approval"""
    FILE_MODIFICATION = "file_modification"
    PR_CREATION = "pr_creation"
    CODE_EXECUTION = "code_execution"
    DESTRUCTIVE_ACTION = "destructive_action"
    SECURITY_SENSITIVE = "security_sensitive"
    EXTERNAL_REQUEST = "external_request"
    FINDING_CONFIRMATION = "finding_confirmation"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    approval_type: ApprovalType
    title: str
    description: str
    details: Dict[str, Any]
    options: List[str] = None  # e.g., ["approve", "reject", "modify"]
    default_option: str = "approve"
    timeout_seconds: int = 300  # 5 minutes default


@dataclass
class ApprovalResponse:
    """Human response to approval request"""
    request_id: str
    approved: bool
    option_selected: str
    user_message: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class HumanInTheLoop:
    """
    Manages human-in-the-loop interactions for the Code Testing Agent.

    Features:
    - Confirmation prompts before critical actions
    - Approval workflows for PRs, file changes, code execution
    - Ability to modify agent proposals before execution
    - Emergency stop capability
    """

    def __init__(self, web_publisher=None, auto_approve_safe: bool = False):
        """
        Initialize human-in-the-loop system.

        Args:
            web_publisher: Function to publish events to web interface
            auto_approve_safe: If True, auto-approve low-risk actions
        """
        self.web_publisher = web_publisher
        self.auto_approve_safe = auto_approve_safe
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_responses: Dict[str, ApprovalResponse] = {}
        self._approval_callback: Optional[Callable] = None

        # Actions that are always safe (auto-approved)
        self.safe_actions = {
            "read_file",
            "list_directory",
            "search_code",
            "analyze_code",
            "run_tests_readonly",
        }

        # Actions that always require approval
        self.require_approval = {
            ApprovalType.PR_CREATION,
            ApprovalType.DESTRUCTIVE_ACTION,
            ApprovalType.SECURITY_SENSITIVE,
        }

    def set_approval_callback(self, callback: Callable):
        """Set callback for handling approval requests"""
        self._approval_callback = callback

    async def request_approval(
        self,
        approval_type: ApprovalType,
        title: str,
        description: str,
        details: Dict[str, Any] = None,
        options: List[str] = None
    ) -> ApprovalResponse:
        """
        Request human approval for an action.

        Args:
            approval_type: Type of approval needed
            title: Short title for the approval request
            description: Detailed description of what will happen
            details: Additional details (code changes, etc.)
            options: Available options (default: approve/reject)

        Returns:
            ApprovalResponse with human's decision
        """
        import uuid
        import asyncio

        request_id = str(uuid.uuid4())[:8]

        if options is None:
            options = ["approve", "reject", "modify"]

        request = ApprovalRequest(
            request_id=request_id,
            approval_type=approval_type,
            title=title,
            description=description,
            details=details or {},
            options=options
        )

        self.pending_approvals[request_id] = request

        # Check for auto-approval
        if self.auto_approve_safe and approval_type not in self.require_approval:
            logger.info("Auto-approving safe action", type=approval_type.value)
            return ApprovalResponse(
                request_id=request_id,
                approved=True,
                option_selected="approve"
            )

        # Publish approval request to web interface
        if self.web_publisher:
            self.web_publisher('approval-request', {
                'request_id': request_id,
                'type': approval_type.value,
                'title': title,
                'description': description,
                'details': details,
                'options': options,
                'text': f"🔔 APPROVAL NEEDED: {title}\n\n{description}"
            })

        logger.info("Waiting for human approval", request_id=request_id, title=title)

        # Wait for response
        timeout = request.timeout_seconds
        for _ in range(timeout):
            if request_id in self.approval_responses:
                response = self.approval_responses.pop(request_id)
                del self.pending_approvals[request_id]
                return response
            await asyncio.sleep(1)

        # Timeout - return rejection
        logger.warning("Approval request timed out", request_id=request_id)
        return ApprovalResponse(
            request_id=request_id,
            approved=False,
            option_selected="timeout"
        )

    def submit_approval(
        self,
        request_id: str,
        approved: bool,
        option_selected: str = None,
        user_message: str = None,
        modifications: Dict[str, Any] = None
    ) -> bool:
        """
        Submit human approval response.

        Returns True if request was found and response recorded.
        """
        if request_id not in self.pending_approvals:
            logger.warning("Unknown approval request", request_id=request_id)
            return False

        self.approval_responses[request_id] = ApprovalResponse(
            request_id=request_id,
            approved=approved,
            option_selected=option_selected or ("approve" if approved else "reject"),
            user_message=user_message,
            modifications=modifications
        )

        logger.info(
            "Approval response received",
            request_id=request_id,
            approved=approved,
            option=option_selected
        )
        return True

    async def confirm_file_modification(
        self,
        file_path: str,
        change_type: str,
        old_content: str = None,
        new_content: str = None,
        description: str = None
    ) -> ApprovalResponse:
        """Request approval for file modification"""
        details = {
            "file_path": file_path,
            "change_type": change_type,
        }

        if old_content and new_content:
            # Show diff
            details["old_content"] = old_content[:500] + "..." if len(old_content) > 500 else old_content
            details["new_content"] = new_content[:500] + "..." if len(new_content) > 500 else new_content

        return await self.request_approval(
            ApprovalType.FILE_MODIFICATION,
            f"Modify file: {file_path}",
            description or f"The agent wants to {change_type} the file {file_path}",
            details
        )

    async def confirm_pr_creation(
        self,
        title: str,
        body: str,
        branch: str,
        files_changed: List[str]
    ) -> ApprovalResponse:
        """Request approval for PR creation"""
        return await self.request_approval(
            ApprovalType.PR_CREATION,
            f"Create PR: {title}",
            f"The agent wants to create a pull request with {len(files_changed)} file(s) changed.",
            {
                "pr_title": title,
                "pr_body": body[:1000],
                "branch": branch,
                "files_changed": files_changed
            },
            options=["approve", "reject", "edit_description"]
        )

    async def confirm_code_execution(
        self,
        code: str,
        language: str,
        purpose: str
    ) -> ApprovalResponse:
        """Request approval for code execution"""
        return await self.request_approval(
            ApprovalType.CODE_EXECUTION,
            f"Execute {language} code",
            f"The agent wants to execute code for: {purpose}",
            {
                "language": language,
                "code": code[:1000] + "..." if len(code) > 1000 else code,
                "purpose": purpose
            },
            options=["approve", "reject", "view_full_code"]
        )

    async def confirm_finding(
        self,
        finding_type: str,
        severity: str,
        description: str,
        evidence: str,
        proposed_fix: str = None
    ) -> ApprovalResponse:
        """Request confirmation of a finding before proceeding"""
        return await self.request_approval(
            ApprovalType.FINDING_CONFIRMATION,
            f"Finding: {finding_type} ({severity})",
            description,
            {
                "severity": severity,
                "evidence": evidence,
                "proposed_fix": proposed_fix
            },
            options=["confirm_and_fix", "confirm_skip_fix", "false_positive", "need_more_info"]
        )

    async def confirm_destructive_action(
        self,
        action: str,
        target: str,
        warning: str
    ) -> ApprovalResponse:
        """Request approval for destructive action"""
        return await self.request_approval(
            ApprovalType.DESTRUCTIVE_ACTION,
            f"⚠️ Destructive Action: {action}",
            f"WARNING: {warning}",
            {
                "action": action,
                "target": target,
                "warning": warning
            },
            options=["approve", "reject"]
        )

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.pending_approvals.values())

    def cancel_approval(self, request_id: str) -> bool:
        """Cancel a pending approval request"""
        if request_id in self.pending_approvals:
            del self.pending_approvals[request_id]
            self.approval_responses[request_id] = ApprovalResponse(
                request_id=request_id,
                approved=False,
                option_selected="cancelled"
            )
            return True
        return False
