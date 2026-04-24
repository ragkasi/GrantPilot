"""Shared ownership-check helpers used across routers.

Keeps route handlers thin: they call these helpers instead of repeating
the fetch + user_id comparison pattern in every endpoint.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User


def require_org_access(db: Session, org_id: str, current_user: User) -> Organization:
    """Fetch an organization and verify the caller owns it."""
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    if org.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )
    return org


def require_project_access(db: Session, project_id: str, current_user: User) -> Project:
    """Fetch a project and verify the caller owns the parent organization."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    require_org_access(db, project.organization_id, current_user)
    return project
