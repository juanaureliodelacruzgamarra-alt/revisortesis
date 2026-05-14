from fastapi import APIRouter

from kimy.api.v1.auth import router as auth_router
from kimy.api.v1.evaluations import router as evaluations_router
from kimy.api.v1.programs import router as programs_router
from kimy.api.v1.submissions import router as submissions_router
from kimy.api.v1.templates import router as templates_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(programs_router)
router.include_router(submissions_router)
router.include_router(templates_router)
router.include_router(evaluations_router)
