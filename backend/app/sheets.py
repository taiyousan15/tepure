"""
Google Sheets service extension with user management and audit logging
"""
import os
import json
import base64
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class GoogleSheetsClient:
    """
    Extended Google Sheets client with user management, quota tracking, and audit logging

    Sheet structure:
    - Users: id, email, password_hash, role, monthly_quota, created_at
    - Templates: id, name, figma_file_key, figma_node_id, category, tags, thumbnail_url, version, created_at
    - Jobs: id, user_id, template_id, status, inputs, result, usage, idempotency_key, created_at, updated_at
    - AuditLogs: id, timestamp, user_id, action, entity_type, entity_id, ip, latency_ms, tokens, metadata
    - Metrics: date, total_jobs, successful_jobs, failed_jobs, avg_latency_ms, total_tokens
    """

    def __init__(self):
        """Initialize Google Sheets client"""
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable not set")

        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.service = None
        self._initialize_service()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _initialize_service(self):
        """Initialize Google Sheets API service with retry logic"""
        try:
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")

            service_account_info = json.loads(base64.b64decode(service_account_json))
            creds = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=self.scopes
            )

            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("sheets_service_initialized")

        except Exception as e:
            logger.error("sheets_service_init_failed", error=str(e))
            raise

    # ========== User Management ==========

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address

        Args:
            email: User email

        Returns:
            User dictionary or None if not found
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Users!A:F'
            ).execute()

            values = result.get('values', [])
            if not values:
                return None

            # Skip header row
            for row in values[1:]:
                if len(row) >= 2 and row[1].lower() == email.lower():
                    return {
                        'id': row[0],
                        'email': row[1],
                        'password_hash': row[2] if len(row) > 2 else None,
                        'role': row[3] if len(row) > 3 else 'user',
                        'monthly_quota': int(row[4]) if len(row) > 4 and row[4] else 100,
                        'created_at': row[5] if len(row) > 5 else None
                    }

            return None

        except HttpError as e:
            logger.error("get_user_by_email_failed", email=email, error=str(e))
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_user(self, email: str, password_hash: str, role: str = 'user') -> str:
        """
        Create a new user

        Args:
            email: User email
            password_hash: Hashed password
            role: User role (user or admin)

        Returns:
            Created user ID
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            user_id = f"usr_{timestamp.replace(':', '').replace('.', '').replace('-', '')[:17]}"

            values = [[
                user_id,
                email,
                password_hash,
                role,
                100,  # default monthly_quota
                timestamp
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Users!A:F',
                valueInputOption='RAW',
                body=body
            ).execute()

            logger.info("user_created", user_id=user_id, email=email, role=role)
            return user_id

        except HttpError as e:
            logger.error("create_user_failed", email=email, error=str(e))
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_user_monthly_usage(self, user_id: str) -> int:
        """
        Get user's job count for current month

        Args:
            user_id: User ID

        Returns:
            Number of jobs created this month
        """
        try:
            # Get current month start
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A:H'
            ).execute()

            values = result.get('values', [])
            if not values:
                return 0

            # Count jobs for this user in current month
            count = 0
            for row in values[1:]:
                if len(row) >= 2 and row[1] == user_id:
                    created_at = row[7] if len(row) > 7 else ''
                    if created_at >= month_start:
                        count += 1

            logger.info("user_monthly_usage_retrieved", user_id=user_id, count=count)
            return count

        except HttpError as e:
            logger.error("get_user_monthly_usage_failed", user_id=user_id, error=str(e))
            return 0

    # ========== Audit Logging ==========

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        ip_address: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create audit log entry

        Args:
            user_id: User who performed action
            action: Action performed
            entity_type: Type of entity (job, template, user)
            entity_id: Entity ID
            ip_address: Client IP address
            latency_ms: Request latency in milliseconds
            tokens_used: LLM tokens used
            metadata: Additional metadata
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            log_id = f"log_{timestamp.replace(':', '').replace('.', '').replace('-', '')[:17]}"

            values = [[
                log_id,
                timestamp,
                user_id,
                action,
                entity_type,
                entity_id,
                ip_address or '',
                latency_ms or '',
                tokens_used or '',
                json.dumps(metadata) if metadata else ''
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='AuditLogs!A:J',
                valueInputOption='RAW',
                body=body
            ).execute()

            logger.info(
                "audit_log_created",
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id
            )

        except HttpError as e:
            logger.error("create_audit_log_failed", error=str(e))
            # Don't raise - audit log failure shouldn't break main flow

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs with filtering

        Args:
            user_id: Filter by user ID
            from_date: Filter by start date (ISO format)
            to_date: Filter by end date (ISO format)
            limit: Maximum number of logs
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='AuditLogs!A:J'
            ).execute()

            values = result.get('values', [])
            if not values:
                return []

            logs = []
            for row in values[1:]:  # Skip header
                if len(row) < 6:
                    continue

                # Apply filters
                if user_id and row[2] != user_id:
                    continue

                timestamp = row[1] if len(row) > 1 else ''
                if from_date and timestamp < from_date:
                    continue
                if to_date and timestamp > to_date:
                    continue

                logs.append({
                    'id': row[0],
                    'timestamp': timestamp,
                    'user_id': row[2],
                    'action': row[3],
                    'entity_type': row[4],
                    'entity_id': row[5],
                    'ip_address': row[6] if len(row) > 6 else None,
                    'latency_ms': int(row[7]) if len(row) > 7 and row[7] else None,
                    'tokens_used': int(row[8]) if len(row) > 8 and row[8] else None,
                    'metadata': json.loads(row[9]) if len(row) > 9 and row[9] else None
                })

            # Sort by timestamp descending
            logs.sort(key=lambda x: x['timestamp'], reverse=True)

            # Apply pagination
            return logs[offset:offset + limit]

        except HttpError as e:
            logger.error("get_audit_logs_failed", error=str(e))
            return []

    # ========== Metrics ==========

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def record_daily_metrics(
        self,
        date: str,
        total_jobs: int,
        successful_jobs: int,
        failed_jobs: int,
        avg_latency_ms: float,
        total_tokens: int
    ):
        """
        Record daily metrics

        Args:
            date: Date in YYYY-MM-DD format
            total_jobs: Total jobs run
            successful_jobs: Successful jobs
            failed_jobs: Failed jobs
            avg_latency_ms: Average latency
            total_tokens: Total tokens used
        """
        try:
            values = [[
                date,
                total_jobs,
                successful_jobs,
                failed_jobs,
                round(avg_latency_ms, 2),
                total_tokens,
                datetime.utcnow().isoformat()
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Metrics!A:G',
                valueInputOption='RAW',
                body=body
            ).execute()

            logger.info("daily_metrics_recorded", date=date, total_jobs=total_jobs)

        except HttpError as e:
            logger.error("record_daily_metrics_failed", error=str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_daily_metrics(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for specific date

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Metrics dictionary or None
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Metrics!A:G'
            ).execute()

            values = result.get('values', [])
            if not values:
                return None

            for row in values[1:]:  # Skip header
                if len(row) >= 1 and row[0] == date:
                    return {
                        'date': row[0],
                        'total_jobs': int(row[1]) if len(row) > 1 else 0,
                        'successful_jobs': int(row[2]) if len(row) > 2 else 0,
                        'failed_jobs': int(row[3]) if len(row) > 3 else 0,
                        'avg_latency_ms': float(row[4]) if len(row) > 4 else 0.0,
                        'total_tokens': int(row[5]) if len(row) > 5 else 0
                    }

            return None

        except HttpError as e:
            logger.error("get_daily_metrics_failed", date=date, error=str(e))
            return None
