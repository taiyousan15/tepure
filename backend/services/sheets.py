"""
Google Sheets service for metadata management
"""
import os
import json
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsClient:
    """
    Google Sheets client for managing template metadata

    Sheet structure:
    - Users: id, email, password_hash, created_at
    - Templates: id, name, figma_file_id, figma_node_id, category, thumbnail_url, created_at
    - TemplateFields: id, template_id, field_name, field_type, default_value, layer_name
    - FillJobs: id, user_id, template_id, status, input_data, result_urls, created_at, updated_at
    - AuditLogs: id, timestamp, actor, action, target_id, metadata
    """

    def __init__(self):
        """Initialize Google Sheets client"""
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Sheets API service"""
        try:
            # Load service account credentials from base64-encoded JSON in environment
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

            if not service_account_json:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")

            # Decode base64 service account JSON
            service_account_info = json.loads(base64.b64decode(service_account_json))

            creds = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=self.scopes
            )

            self.service = build('sheets', 'v4', credentials=creds)
            print("Google Sheets service initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Google Sheets service: {e}")
            raise

    def get_templates(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get templates from Google Sheets

        Args:
            limit: Maximum number of templates to return
            offset: Number of templates to skip

        Returns:
            List of template dictionaries
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Templates!A:G'
            ).execute()

            values = result.get('values', [])

            if not values or len(values) < 2:  # No data or only header
                return []

            # Skip header row and apply offset/limit
            templates = []
            for row in values[1 + offset:1 + offset + limit]:
                if len(row) >= 3:
                    templates.append({
                        'id': row[0],
                        'name': row[1],
                        'figma_file_id': row[2],
                        'figma_node_id': row[3] if len(row) > 3 else None,
                        'category': row[4] if len(row) > 4 else 'uncategorized',
                        'thumbnail_url': row[5] if len(row) > 5 else None,
                        'created_at': row[6] if len(row) > 6 else None
                    })

            return templates

        except HttpError as e:
            print(f"Failed to get templates: {e}")
            return []

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single template by ID

        Args:
            template_id: Template ID

        Returns:
            Template dictionary or None if not found
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Templates!A:G'
            ).execute()

            values = result.get('values', [])

            if not values:
                return None

            # Skip header row
            for row in values[1:]:
                if len(row) >= 1 and row[0] == template_id:
                    return {
                        'id': row[0],
                        'name': row[1] if len(row) > 1 else None,
                        'figma_file_id': row[2] if len(row) > 2 else None,
                        'figma_node_id': row[3] if len(row) > 3 else None,
                        'category': row[4] if len(row) > 4 else 'uncategorized',
                        'thumbnail_url': row[5] if len(row) > 5 else None,
                        'created_at': row[6] if len(row) > 6 else None
                    }

            return None

        except HttpError as e:
            print(f"Failed to get template: {e}")
            return None

    def create_template(self, template_data: Dict[str, Any]) -> str:
        """
        Create a new template in Google Sheets

        Args:
            template_data: Template data with keys: name, figma_file_id, figma_node_id, category, thumbnail_url

        Returns:
            Created template ID
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            template_id = f"tpl_{timestamp.replace(':', '').replace('.', '').replace('-', '')}"

            values = [[
                template_id,
                template_data.get('name', 'Untitled'),
                template_data.get('figma_file_id', ''),
                template_data.get('figma_node_id', ''),
                template_data.get('category', 'uncategorized'),
                template_data.get('thumbnail_url', ''),
                timestamp
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Templates!A:G',
                valueInputOption='RAW',
                body=body
            ).execute()

            return template_id

        except HttpError as e:
            print(f"Failed to create template: {e}")
            raise

    def get_template_fields(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Get template fields from Google Sheets

        Args:
            template_id: Template ID

        Returns:
            List of field dictionaries
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='TemplateFields!A:F'
            ).execute()

            values = result.get('values', [])

            if not values:
                return []

            # Skip header row and filter by template_id
            fields = []
            for row in values[1:]:
                if len(row) >= 2 and row[1] == template_id:
                    fields.append({
                        'id': row[0],
                        'template_id': row[1],
                        'field_name': row[2] if len(row) > 2 else None,
                        'field_type': row[3] if len(row) > 3 else 'text',
                        'default_value': row[4] if len(row) > 4 else None,
                        'layer_name': row[5] if len(row) > 5 else None
                    })

            return fields

        except HttpError as e:
            print(f"Failed to get template fields: {e}")
            return []

    def create_fill_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a new fill job record

        Args:
            job_data: Job data with keys: user_id, template_id, input_data

        Returns:
            Created job ID
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            job_id = f"job_{timestamp.replace(':', '').replace('.', '').replace('-', '')}"

            values = [[
                job_id,
                job_data.get('user_id', ''),
                job_data.get('template_id', ''),
                'pending',
                json.dumps(job_data.get('input_data', {})),
                '',  # result_urls (empty initially)
                timestamp,
                timestamp
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='FillJobs!A:H',
                valueInputOption='RAW',
                body=body
            ).execute()

            return job_id

        except HttpError as e:
            print(f"Failed to create fill job: {e}")
            raise

    def update_fill_job(self, job_id: str, status: str, result_urls: Optional[List[str]] = None):
        """
        Update fill job status

        Args:
            job_id: Job ID
            status: New status
            result_urls: Result file URLs
        """
        try:
            # First, find the row index for this job_id
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='FillJobs!A:H'
            ).execute()

            values = result.get('values', [])
            row_index = None

            for i, row in enumerate(values):
                if len(row) >= 1 and row[0] == job_id:
                    row_index = i + 1  # 1-indexed
                    break

            if row_index is None:
                print(f"Job {job_id} not found")
                return

            # Update status and result_urls
            timestamp = datetime.utcnow().isoformat()
            update_range = f'FillJobs!D{row_index}:H{row_index}'

            result_urls_str = json.dumps(result_urls) if result_urls else ''

            values = [[
                status,
                values[row_index - 1][4] if len(values[row_index - 1]) > 4 else '',  # Keep input_data
                result_urls_str,
                values[row_index - 1][6] if len(values[row_index - 1]) > 6 else '',  # Keep created_at
                timestamp  # updated_at
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=body
            ).execute()

        except HttpError as e:
            print(f"Failed to update fill job: {e}")

    def get_fill_jobs(self, user_id: str, limit: int = 20, offset: int = 0, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get fill jobs for a user

        Args:
            user_id: User ID
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            status_filter: Optional status filter

        Returns:
            List of job dictionaries
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='FillJobs!A:H'
            ).execute()

            values = result.get('values', [])

            if not values:
                return []

            # Skip header row and filter by user_id
            jobs = []
            for row in values[1:]:
                if len(row) >= 3 and row[1] == user_id:
                    # Apply status filter if provided
                    status = row[3] if len(row) > 3 else 'pending'
                    if status_filter and status != status_filter:
                        continue

                    jobs.append({
                        'job_id': row[0],
                        'user_id': row[1],
                        'template_id': row[2],
                        'status': status,
                        'input_data': json.loads(row[4]) if len(row) > 4 and row[4] else {},
                        'result_urls': json.loads(row[5]) if len(row) > 5 and row[5] else [],
                        'created_at': row[6] if len(row) > 6 else None,
                        'updated_at': row[7] if len(row) > 7 else None
                    })

            # Sort by created_at descending (most recent first)
            jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            # Apply pagination
            paginated_jobs = jobs[offset:offset + limit]

            return paginated_jobs

        except HttpError as e:
            print(f"Failed to get fill jobs: {e}")
            return []

    def log_audit(self, actor: str, action: str, target_id: str, metadata: Dict[str, Any]):
        """
        Log an action to audit log

        Args:
            actor: User who performed the action
            action: Action performed
            target_id: Target resource ID
            metadata: Additional metadata
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            log_id = f"log_{timestamp.replace(':', '').replace('.', '').replace('-', '')}"

            values = [[
                log_id,
                timestamp,
                actor,
                action,
                target_id,
                json.dumps(metadata)
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='AuditLogs!A:F',
                valueInputOption='RAW',
                body=body
            ).execute()

        except HttpError as e:
            print(f"Failed to log audit: {e}")

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
                range='Users!A:D'
            ).execute()

            values = result.get('values', [])

            if not values:
                return None

            # Skip header row
            for row in values[1:]:
                if len(row) >= 2 and row[1] == email:
                    return {
                        'id': row[0],
                        'email': row[1],
                        'password_hash': row[2] if len(row) > 2 else None,
                        'created_at': row[3] if len(row) > 3 else None
                    }

            return None

        except HttpError as e:
            print(f"Failed to get user: {e}")
            return None

    def create_user(self, email: str, password_hash: str) -> str:
        """
        Create a new user in Google Sheets

        Args:
            email: User email
            password_hash: Hashed password

        Returns:
            Created user ID
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            user_id = f"usr_{timestamp.replace(':', '').replace('.', '').replace('-', '')}"

            values = [[
                user_id,
                email,
                password_hash,
                timestamp
            ]]

            body = {'values': values}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Users!A:D',
                valueInputOption='RAW',
                body=body
            ).execute()

            # Log user creation
            self.log_audit(
                actor=email,
                action='user.created',
                target_id=user_id,
                metadata={'email': email}
            )

            return user_id

        except HttpError as e:
            print(f"Failed to create user: {e}")
            raise
