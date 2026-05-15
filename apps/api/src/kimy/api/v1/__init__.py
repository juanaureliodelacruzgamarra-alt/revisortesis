from fastapi import APIRouter

from kimy.api.v1.audit import router as audit_router
from kimy.api.v1.auth import router as auth_router
from kimy.api.v1.bulk import router as bulk_router
from kimy.api.v1.citations import router as citations_router
from kimy.api.v1.evaluations import router as evaluations_router
from kimy.api.v1.fine_tuning import router as fine_tuning_router
from kimy.api.v1.orcid import router as orcid_router
from kimy.api.v1.plagiarism import router as plagiarism_router
from kimy.api.v1.programs import router as programs_router
from kimy.api.v1.push import router as push_router
from kimy.api.v1.stats import router as stats_router
from kimy.api.v1.submissions import router as submissions_router
from kimy.api.v1.templates import router as templates_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(programs_router)
router.include_router(bulk_router)
router.include_router(submissions_router)
router.include_router(templates_router)
router.include_router(evaluations_router)
router.include_router(plagiarism_router)
router.include_router(citations_router)
router.include_router(orcid_router)
router.include_router(stats_router)
router.include_router(fine_tuning_router)
router.include_router(push_router)
router.include_router(audit_router)
