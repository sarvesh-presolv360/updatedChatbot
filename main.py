import uvicorn
import logging
import sys
import os

# Configure logging - only stdout for Render (ephemeral filesystem)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from watchfiles
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def main():
    """Run the FastAPI application."""
    logger.info("=" * 80)
    logger.info("STARTING ARBITRATION API SERVER")
    logger.info("=" * 80)

    # Get port from environment variable (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))

    # Detect if running in production (Render)
    is_production = os.getenv("RENDER") is not None

    try:
        uvicorn.run(
            "api_v2:app",
            host="0.0.0.0",
            port=port,
            reload=not is_production,  # Only reload in development
            log_level="info",
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
