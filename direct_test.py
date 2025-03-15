"""
Script to directly test the auth_router and test_router.
"""
import logging
from routers.auth_router import router as auth_router
from routers.test_router import router as test_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Print auth_router routes
logger.info("Auth router routes:")
for route in auth_router.routes:
    logger.info(f"  {route.path} [{route.methods}]")

# Print test_router routes
logger.info("Test router routes:")
for route in test_router.routes:
    logger.info(f"  {route.path} [{route.methods}]") 