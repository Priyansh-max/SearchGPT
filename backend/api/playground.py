"""Anonymous public playground demo lane."""

from fastapi import APIRouter

from api.v1 import QueryRequest
from services.playground import execute_playground_query

router = APIRouter(prefix="/api/playground", tags=["playground"])


@router.post("/query")
async def demo_playground_query(body: QueryRequest):
    return await execute_playground_query(body, tier="demo", user=None)
