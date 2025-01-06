from fastapi import APIRouter
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.user import router as user_router
from app.api.endpoints.predictions import router as predictions_router
from app.api.endpoints.mlmodels import router as mlmodels_router

router = APIRouter()

# Add auth endpoints
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(predictions_router, prefix="/predictions", tags=["Predictions"])
router.include_router(mlmodels_router, prefix="/mlmodels", tags=["ML Models"])

@router.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Heart Disease Prediction API"}

# Export router
api_router = router
