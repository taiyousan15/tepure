"""
Migration: Templates Schema Extension
Date: 2025-10-16
Purpose: Add new columns to Templates sheet

New columns:
- category (LP/Banner/SNS/WebApp)
- fields[] (JSON array of Field objects)
- figma_node_id (string)
- preview_url (string URL)

Field structure:
{
  "type": "text" | "color" | "border",
  "label": "string",
  "default_value": "any"
}
"""

import logging
import json
from typing import Dict, List, Any
from ..sheets import SheetsService

logger = logging.getLogger(__name__)


class TemplatesExtensionMigration:
    """Migration to extend Templates schema with new columns"""

    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.migration_name = "20251016_templates_extend"

    def up(self) -> Dict[str, Any]:
        """
        Apply migration: Add new columns to Templates sheet

        Old schema:
        A=id, B=name, C=figma_file_key, D=tags, E=version, F=created_at

        New schema:
        A=id, B=name, C=figma_file_key, D=category, E=tags, F=version,
        G=preview_url, H=fields, I=figma_node_id, J=created_at

        Returns:
            Dict with migration results
        """
        logger.info(f"Starting migration: {self.migration_name}")

        try:
            # Step 1: Read current header row
            header_result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A1:Z1"
            ).execute()

            current_headers = header_result.get("values", [[]])[0] if header_result.get("values") else []

            logger.info(f"Current headers: {current_headers}")

            # Step 2: Define new header structure
            new_headers = [
                "id",
                "name",
                "figma_file_key",
                "category",           # NEW
                "tags",
                "version",
                "preview_url",        # NEW
                "fields",             # NEW (JSON string)
                "figma_node_id",      # NEW
                "created_at"
            ]

            # Step 3: Update header row
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A1:J1",
                valueInputOption="RAW",
                body={"values": [new_headers]}
            ).execute()

            logger.info(f"Updated header row with new columns")

            # Step 4: Read all existing template data
            data_result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A2:F"  # Old schema columns
            ).execute()

            existing_rows = data_result.get("values", [])
            total_rows = len(existing_rows)

            logger.info(f"Found {total_rows} existing template rows")

            # Step 5: Transform and write updated rows
            updated_rows = []

            for row in existing_rows:
                # Pad row to 6 columns if needed
                while len(row) < 6:
                    row.append("")

                # Old: [id, name, figma_file_key, tags, version, created_at]
                # New: [id, name, figma_file_key, category, tags, version, preview_url, fields, figma_node_id, created_at]

                transformed_row = [
                    row[0],  # id
                    row[1],  # name
                    row[2],  # figma_file_key
                    "LP",    # category - default to LP (user should update manually)
                    row[3],  # tags
                    row[4],  # version
                    "",      # preview_url - empty (user should add)
                    json.dumps([]),  # fields - empty array (user should add)
                    "",      # figma_node_id - empty (user should add)
                    row[5]   # created_at
                ]

                updated_rows.append(transformed_row)

            # Step 6: Write transformed data
            if updated_rows:
                self.sheets_service.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_service.sheets_templates_id,
                    range="Templates!A2:J",
                    valueInputOption="RAW",
                    body={"values": updated_rows}
                ).execute()

                logger.info(f"Updated {len(updated_rows)} rows with new schema")

            result = {
                "migration": self.migration_name,
                "status": "completed",
                "total_rows": total_rows,
                "updated_rows": len(updated_rows),
                "new_columns": ["category", "preview_url", "fields", "figma_node_id"],
                "message": "Migration completed. Please update category, preview_url, fields, and figma_node_id manually."
            }

            logger.info(f"Migration completed successfully")

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
        Rollback migration: Remove new columns and restore old schema

        WARNING: This will lose data in the new columns!

        Returns:
            Dict with rollback results
        """
        logger.info(f"Rolling back migration: {self.migration_name}")

        try:
            # Step 1: Read current data
            data_result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A1:J"  # New schema
            ).execute()

            all_rows = data_result.get("values", [])

            if not all_rows:
                return {
                    "migration": self.migration_name,
                    "status": "rolled_back",
                    "message": "No data to rollback"
                }

            # Step 2: Transform back to old schema
            old_headers = ["id", "name", "figma_file_key", "tags", "version", "created_at"]

            rollback_rows = [old_headers]  # Header row

            for row in all_rows[1:]:  # Skip header
                # Pad to 10 columns if needed
                while len(row) < 10:
                    row.append("")

                # New: [id, name, figma_file_key, category, tags, version, preview_url, fields, figma_node_id, created_at]
                # Old: [id, name, figma_file_key, tags, version, created_at]

                old_row = [
                    row[0],  # id
                    row[1],  # name
                    row[2],  # figma_file_key
                    row[4],  # tags
                    row[5],  # version
                    row[9]   # created_at
                ]

                rollback_rows.append(old_row)

            # Step 3: Clear sheet and write old schema
            # Clear entire sheet first
            self.sheets_service.service.spreadsheets().values().clear(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A1:J"
            ).execute()

            # Write old schema data
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.sheets_service.sheets_templates_id,
                range="Templates!A1:F",
                valueInputOption="RAW",
                body={"values": rollback_rows}
            ).execute()

            result = {
                "migration": self.migration_name,
                "status": "rolled_back",
                "total_rows": len(rollback_rows) - 1,
                "message": "Rollback completed. New columns (category, preview_url, fields, figma_node_id) have been removed."
            }

            logger.info(f"Rollback completed successfully")

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
    migration = TemplatesExtensionMigration(sheets_service)
    return migration.up()


def rollback_migration(sheets_service: SheetsService) -> Dict[str, Any]:
    """
    Rollback the migration

    Args:
        sheets_service: Initialized SheetsService instance

    Returns:
        Rollback result dictionary
    """
    migration = TemplatesExtensionMigration(sheets_service)
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
