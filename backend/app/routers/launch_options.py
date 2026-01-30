"""Launch options endpoints."""

from fastapi import APIRouter

from app.data import get_all_launch_options
from app.models import LaunchOption

router = APIRouter(prefix="/launch-options", tags=["launch-options"])


@router.get("", response_model=list[LaunchOption])
async def list_launch_options() -> list[LaunchOption]:
    """Get all available launch vehicle options.

    These are editable placeholder values representing various
    launch vehicle and injection configurations.
    """
    return get_all_launch_options()
