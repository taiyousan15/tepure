"""
Migration: Jobs Status Vocabulary Update
Date: 2025-10-16
Purpose: Convert old status vocabulary to new vocabulary

Old → New:
- queued → pending
- running → processing
- succeeded → completed
- failed → failed (no change)
"""

import logging
from typing import Dict, List, Any
from ..sheets import SheetsService

logger = logging.getLogger(__name__)

# Status mapping
STATUS_MAP = {
    "queued": "pending",
    "running": "processing",
    "succeeded": "completed",
    "failed": "failed"  # No change
}


class JobsStatusMigration:
    """Migration to update Jobs status vocabulary"""

    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.migration_name = "20251016_jobs_status_map"

    def up(self) -> Dict[str, Any]:
        """
        Apply migration: Update all job statuses from old to new vocabulary

        Returns:
            Dict with migration results (total_rows, updated_rows, errors)
        """
        logger.info(f"Starting migration: {self.migration_name}")

        try:
            # Get all jobs from Google Sheets
            jobs_data = self.sheets_service.get_all_jobs()

            total_rows = len(jobs_data)
            updated_rows = 0
            errors: List[str] = []

            # Process each job row
            for idx, job in enumerate(jobs_data, start=2):  # Row 2+ (row 1 is header)
                old_status = job.get("status", "")

                if old_status in STATUS_MAP:
                    new_status = STATUS_MAP[old_status]

                    # Update only if status changed
                    if old_status != new_status:
                        try:
                            # Update status in Google Sheets
                            # Assuming Jobs sheet structure: A=id, B=user_id, C=template_id, D=status, E=inputs, F=result, G=cost, H=created_at, I=completed_at
                            range_name = f"Jobs!D{idx}"

                            self.sheets_service.service.spreadsheets().values().update(
                                spreadsheetId=self.sheets_service.sheets_jobs_id,
                                range=range_name,
                                valueInputOption="RAW",
                                body={"values": [[new_status]]}
                            ).execute()

                            updated_rows += 1
                            logger.info(f"Row {idx}: Updated status from '{old_status}' to '{new_status}'")

                        except Exception as e:
                            error_msg = f"Row {idx}: Failed to update status - {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                else:
                    # Unknown status - log warning
                    if old_status:
                        logger.warning(f"Row {idx}: Unknown status '{old_status}', skipping")

            result = {
                "migration": self.migration_name,
                "status": "completed",
                "total_rows": total_rows,
                "updated_rows": updated_rows,
                "errors": errors,
                "error_count": len(errors)
            }

            logger.info(f"Migration completed: {updated_rows}/{total_rows} rows updated")

            return result

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {
                "migration": self.migration_name,
                "status": "failed",
                "error": str(e)
            }

    def down(self) -> Dict[str, Any]:
        """
        Rollback migration: Revert all job statuses to old vocabulary

        Returns:
            Dict with rollback results
        """
        logger.info(f"Rolling back migration: {self.migration_name}")

        # Reverse mapping
        REVERSE_MAP = {v: k for k, v in STATUS_MAP.items()}

        try:
            jobs_data = self.sheets_service.get_all_jobs()

            total_rows = len(jobs_data)
            reverted_rows = 0
            errors: List[str] = []

            for idx, job in enumerate(jobs_data, start=2):
                current_status = job.get("status", "")

                if current_status in REVERSE_MAP:
                    old_status = REVERSE_MAP[current_status]

                    if current_status != old_status:
                        try:
                            range_name = f"Jobs!D{idx}"

                            self.sheets_service.service.spreadsheets().values().update(
                                spreadsheetId=self.sheets_service.sheets_jobs_id,
                                range=range_name,
                                valueInputOption="RAW",
                                body={"values": [[old_status]]}
                            ).execute()

                            reverted_rows += 1
                            logger.info(f"Row {idx}: Reverted status from '{current_status}' to '{old_status}'")

                        except Exception as e:
                            error_msg = f"Row {idx}: Failed to revert status - {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)

            result = {
                "migration": self.migration_name,
                "status": "rolled_back",
                "total_rows": total_rows,
                "reverted_rows": reverted_rows,
                "errors": errors,
                "error_count": len(errors)
            }

            logger.info(f"Rollback completed: {reverted_rows}/{total_rows} rows reverted")

            return result

        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return {
                "migration": self.migration_name,
                "status": "rollback_failed",
                "error": str(e)
            }


def run_migration(sheets_service: SheetsService) -> Dict[str, Any]:
    """
    Execute the migration

    Args:
        sheets_service: Initialized SheetsService instance

    Returns:
        Migration result dictionary
    """
    migration = JobsStatusMigration(sheets_service)
    return migration.up()


def rollback_migration(sheets_service: SheetsService) -> Dict[str, Any]:
    """
    Rollback the migration

    Args:
        sheets_service: Initialized SheetsService instance

    Returns:
        Rollback result dictionary
    """
    migration = JobsStatusMigration(sheets_service)
    return migration.down()


if __name__ == "__main__":
    # CLI execution
    import sys
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize sheets service
    sheets_service = SheetsService(
        service_account_json_base64=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64"),
        sheets_users_id=os.getenv("SHEETS_USERS_ID"),
        sheets_templates_id=os.getenv("SHEETS_TEMPLATES_ID"),
        sheets_jobs_id=os.getenv("SHEETS_JOBS_ID"),
        sheets_auditlogs_id=os.getenv("SHEETS_AUDITLOGS_ID")
    )

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        result = rollback_migration(sheets_service)
        print(f"Rollback result: {result}")
    else:
        result = run_migration(sheets_service)
        print(f"Migration result: {result}")
