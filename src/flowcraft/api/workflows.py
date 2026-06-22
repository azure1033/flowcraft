"""Workflow CRUD API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from .schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
)
from .store import store
from .deps import verify_api_key

router = APIRouter(
    prefix="/api/workflows",
    tags=["workflows"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(body: WorkflowCreate):
    """Create a new workflow template."""
    # Basic validation: check nodes and edges exist
    definition = body.definition
    if "nodes" not in definition or "edges" not in definition:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workflow definition must contain 'nodes' and 'edges' arrays.",
        )
    if not definition["nodes"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workflow must contain at least one node.",
        )

    wf = store.create_workflow(body.name, body.description, definition)
    return WorkflowResponse(**wf)


@router.get("", response_model=WorkflowListResponse)
async def list_workflows():
    """List all workflow templates."""
    workflows = store.list_workflows()
    return WorkflowListResponse(
        workflows=[WorkflowResponse(**w) for w in workflows],
        total=len(workflows),
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a workflow template by ID."""
    wf = store.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found."
        )
    return WorkflowResponse(**wf)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, body: WorkflowUpdate):
    """Update a workflow template. Version auto-increments."""
    wf = store.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found."
        )

    update_data = body.model_dump(exclude_unset=True)
    updated = store.update_workflow(workflow_id, **update_data)
    return WorkflowResponse(**updated)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str):
    """Delete a workflow template."""
    if not store.delete_workflow(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found."
        )
