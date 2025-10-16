"""
Metrics and monitoring utilities
"""
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, date
from .sheets import GoogleSheetsClient

logger = structlog.get_logger()


class MetricsCollector:
    """
    Metrics collector for monitoring system performance
    """

    def __init__(self):
        """Initialize metrics collector"""
        self.sheets_client = GoogleSheetsClient()
        logger.info("metrics_collector_initialized")

    def get_success_rate(self, days: int = 1) -> float:
        """
        Calculate success rate for recent jobs

        Args:
            days: Number of days to look back (default 1)

        Returns:
            Success rate (0.0 to 1.0)
        """
        try:
            today = date.today().isoformat()
            metrics = self.sheets_client.get_daily_metrics(today)

            if not metrics or metrics['total_jobs'] == 0:
                logger.warning("no_metrics_found", date=today)
                return 0.0

            success_rate = metrics['successful_jobs'] / metrics['total_jobs']
            logger.info("success_rate_calculated", success_rate=success_rate, date=today)

            return round(success_rate, 4)

        except Exception as e:
            logger.error("get_success_rate_failed", error=str(e))
            return 0.0

    def get_average_latency(self, days: int = 1) -> float:
        """
        Get average latency in milliseconds

        Args:
            days: Number of days to look back (default 1)

        Returns:
            Average latency in milliseconds
        """
        try:
            today = date.today().isoformat()
            metrics = self.sheets_client.get_daily_metrics(today)

            if not metrics:
                logger.warning("no_metrics_found", date=today)
                return 0.0

            avg_latency = metrics['avg_latency_ms']
            logger.info("avg_latency_retrieved", latency_ms=avg_latency, date=today)

            return round(avg_latency, 2)

        except Exception as e:
            logger.error("get_average_latency_failed", error=str(e))
            return 0.0

    def get_daily_generation_count(self, target_date: Optional[str] = None) -> int:
        """
        Get total generation count for a specific date

        Args:
            target_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Total generation count
        """
        try:
            if not target_date:
                target_date = date.today().isoformat()

            metrics = self.sheets_client.get_daily_metrics(target_date)

            if not metrics:
                logger.warning("no_metrics_found", date=target_date)
                return 0

            count = metrics['total_jobs']
            logger.info("daily_count_retrieved", count=count, date=target_date)

            return count

        except Exception as e:
            logger.error("get_daily_generation_count_failed", error=str(e))
            return 0

    def write_audit_log(
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
        Write audit log entry

        Args:
            user_id: User ID
            action: Action performed
            entity_type: Type of entity
            entity_id: Entity ID
            ip_address: Client IP address
            latency_ms: Request latency
            tokens_used: Tokens used
            metadata: Additional metadata
        """
        try:
            self.sheets_client.create_audit_log(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=ip_address,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                metadata=metadata
            )

            logger.info(
                "audit_log_written",
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id
            )

        except Exception as e:
            logger.error("write_audit_log_failed", error=str(e))
            # Don't raise - audit log failure shouldn't break main flow

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get audit logs with pagination

        Args:
            user_id: Filter by user ID
            from_date: Start date filter
            to_date: End date filter
            limit: Page size
            offset: Pagination offset

        Returns:
            Dictionary with logs and pagination info
        """
        try:
            logs = self.sheets_client.get_audit_logs(
                user_id=user_id,
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                offset=offset
            )

            logger.info("audit_logs_retrieved", count=len(logs))

            return {
                'logs': logs,
                'total': len(logs),  # Approximate
                'page': offset // limit + 1,
                'size': limit
            }

        except Exception as e:
            logger.error("get_audit_logs_failed", error=str(e))
            return {
                'logs': [],
                'total': 0,
                'page': 1,
                'size': limit
            }

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics for monitoring dashboard

        Returns:
            Dictionary with all metrics
        """
        try:
            today = date.today().isoformat()
            metrics = self.sheets_client.get_daily_metrics(today)

            if not metrics:
                return {
                    'success_rate': 0.0,
                    'average_latency_ms': 0.0,
                    'daily_generation_count': 0,
                    'total_jobs_today': 0,
                    'failed_jobs_today': 0,
                    'total_tokens_today': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }

            success_rate = (
                metrics['successful_jobs'] / metrics['total_jobs']
                if metrics['total_jobs'] > 0
                else 0.0
            )

            return {
                'success_rate': round(success_rate, 4),
                'average_latency_ms': round(metrics['avg_latency_ms'], 2),
                'daily_generation_count': metrics['total_jobs'],
                'total_jobs_today': metrics['total_jobs'],
                'failed_jobs_today': metrics['failed_jobs'],
                'total_tokens_today': metrics['total_tokens'],
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("get_comprehensive_metrics_failed", error=str(e))
            return {
                'success_rate': 0.0,
                'average_latency_ms': 0.0,
                'daily_generation_count': 0,
                'total_jobs_today': 0,
                'failed_jobs_today': 0,
                'total_tokens_today': 0,
                'timestamp': datetime.utcnow().isoformat()
            }


# Global metrics collector instance
metrics_collector = MetricsCollector()
