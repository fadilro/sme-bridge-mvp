from fastapi import APIRouter
from app.api.routes import health, email_webhook, dashboard, bills, exports, smes

router = APIRouter()
router.include_router(health.router)
router.include_router(email_webhook.router)
router.include_router(dashboard.router)
router.include_router(bills.router)
router.include_router(exports.router)
router.include_router(smes.router)
