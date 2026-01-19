"""
Cleanup Service for Intelligent Coding Agent.

Provides scheduled cleanup functionality for:
- Expired artifacts
- Old executions (based on user tier)
- Orphaned files
"""

import structlog
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.database.models import Artifact, CodeExecution, ExecutionAttempt
from src.services.artifact_service import ArtifactService, get_artifact_service

logger = structlog.get_logger(__name__)


class CleanupService:
    """
    Service for cleaning up expired and old data.

    Can be run as:
    - Manual cleanup via API endpoint
    - Scheduled cron job
    - Background task on app startup
    """

    def __init__(
        self,
        artifact_service: Optional[ArtifactService] = None,
    ):
        self.artifact_service = artifact_service or get_artifact_service()

    def cleanup_expired_artifacts(self) -> dict:
        """
        Delete artifacts that have passed their expiration date.

        Returns:
            Dict with cleanup statistics
        """
        logger.info("Starting expired artifacts cleanup")

        deleted_count = 0
        failed_count = 0
        deleted_ids = []

        with get_db_session() as db:
            # Find expired artifacts
            now = datetime.now(timezone.utc)
            query = select(Artifact).where(
                Artifact.expires_at.isnot(None),
                Artifact.expires_at < now,
            )
            expired_artifacts = db.execute(query).scalars().all()

            logger.info(
                "Found expired artifacts",
                count=len(expired_artifacts),
            )

            for artifact in expired_artifacts:
                try:
                    # Delete from storage
                    self.artifact_service.delete_artifact(artifact.file_path)

                    # Delete from database
                    db.delete(artifact)
                    deleted_count += 1
                    deleted_ids.append(artifact.id)

                    logger.debug(
                        "Deleted expired artifact",
                        artifact_id=artifact.id,
                        name=artifact.name,
                        expired_at=artifact.expires_at.isoformat() if artifact.expires_at else None,
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        "Failed to delete artifact",
                        artifact_id=artifact.id,
                        error=str(e),
                    )

            db.commit()

        result = {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "deleted_ids": deleted_ids,
        }

        logger.info("Expired artifacts cleanup complete", **result)
        return result

    def cleanup_old_executions(
        self,
        max_age_days: int = 90,
        max_per_user: int = 50,
    ) -> dict:
        """
        Delete old code executions based on age and count limits.

        Args:
            max_age_days: Maximum age of executions to keep
            max_per_user: Maximum number of executions to keep per user

        Returns:
            Dict with cleanup statistics
        """
        logger.info(
            "Starting old executions cleanup",
            max_age_days=max_age_days,
            max_per_user=max_per_user,
        )

        deleted_count = 0

        with get_db_session() as db:
            # Delete executions older than max_age_days
            cutoff_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(
                day=cutoff_date.day - max_age_days
            ) if cutoff_date.day > max_age_days else cutoff_date.replace(
                month=cutoff_date.month - 1,
                day=cutoff_date.day + 30 - max_age_days
            )

            # This is a simplified approach - in production, use proper date arithmetic
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

            old_query = delete(CodeExecution).where(
                CodeExecution.created_at < cutoff_date
            )
            result = db.execute(old_query)
            deleted_count += result.rowcount

            # Get unique user IDs
            user_query = select(CodeExecution.user_id).distinct().where(
                CodeExecution.user_id.isnot(None)
            )
            user_ids = [row[0] for row in db.execute(user_query).all()]

            # For each user, keep only the most recent max_per_user executions
            for user_id in user_ids:
                # Get execution count for user
                count_query = select(CodeExecution).where(
                    CodeExecution.user_id == user_id
                ).order_by(CodeExecution.created_at.desc())
                user_executions = db.execute(count_query).scalars().all()

                if len(user_executions) > max_per_user:
                    # Delete older executions
                    to_delete = user_executions[max_per_user:]
                    for execution in to_delete:
                        db.delete(execution)
                        deleted_count += 1

            db.commit()

        result = {
            "deleted_count": deleted_count,
            "max_age_days": max_age_days,
            "max_per_user": max_per_user,
        }

        logger.info("Old executions cleanup complete", **result)
        return result

    def cleanup_orphaned_files(self) -> dict:
        """
        Find and delete files in storage that have no database record.

        Returns:
            Dict with cleanup statistics
        """
        logger.info("Starting orphaned files cleanup")

        # This is a placeholder - actual implementation would scan the storage
        # and compare against database records

        # For local storage, we'd scan the artifact directory
        # For GCS, we'd list bucket objects

        # Currently just return empty result
        result = {
            "scanned_files": 0,
            "orphaned_files": 0,
            "deleted_count": 0,
        }

        logger.info("Orphaned files cleanup complete (not implemented)", **result)
        return result

    def run_full_cleanup(self) -> dict:
        """
        Run all cleanup tasks.

        Returns:
            Dict with results from all cleanup tasks
        """
        logger.info("Starting full cleanup")

        results = {
            "artifacts": self.cleanup_expired_artifacts(),
            "executions": self.cleanup_old_executions(),
            "orphaned": self.cleanup_orphaned_files(),
        }

        logger.info("Full cleanup complete", results=results)
        return results


# Singleton instance
_cleanup_service: Optional[CleanupService] = None


def get_cleanup_service() -> CleanupService:
    """Get the global cleanup service instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service


# CLI entry point for cron jobs
def run_cleanup():
    """Run cleanup from command line."""
    service = get_cleanup_service()
    results = service.run_full_cleanup()
    print(f"Cleanup complete: {results}")


if __name__ == "__main__":
    run_cleanup()
