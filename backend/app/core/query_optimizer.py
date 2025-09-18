"""
Database query optimization utilities for Core Engine.
Provides query analysis, optimization suggestions, and performance monitoring.
"""

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing import Dict, List, Any, Optional, Tuple
import time
import logging
from functools import wraps
from dataclasses import dataclass
from app.core.database import engine, AsyncSessionLocal

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Query execution statistics"""
    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    using_index: bool
    suggested_indexes: List[str]


class QueryOptimizer:
    """Database query optimizer and analyzer"""

    def __init__(self):
        self.slow_queries = []
        self.query_cache = {}

    async def analyze_query(self, session: AsyncSession, query: str, params: Dict = None) -> QueryStats:
        """Analyze query performance and suggest optimizations"""
        start_time = time.time()

        # Execute EXPLAIN to get query plan
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

        try:
            if params:
                result = await session.execute(text(explain_query), params)
            else:
                result = await session.execute(text(explain_query))

            execution_time = time.time() - start_time
            explain_result = result.fetchone()[0]

            # Parse the explain output
            plan = explain_result[0]['Plan']
            stats = self._parse_explain_output(plan, query, execution_time)

            # Log slow queries
            if execution_time > 1.0:  # Queries slower than 1 second
                self.slow_queries.append(stats)
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")

            return stats

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return QueryStats(
                query=query,
                execution_time=time.time() - start_time,
                rows_examined=0,
                rows_returned=0,
                using_index=False,
                suggested_indexes=[]
            )

    def _parse_explain_output(self, plan: Dict, query: str, execution_time: float) -> QueryStats:
        """Parse PostgreSQL EXPLAIN output"""
        rows_examined = plan.get('Actual Rows', 0)
        rows_returned = plan.get('Actual Rows', 0)

        # Check if indexes are being used
        using_index = self._check_index_usage(plan)

        # Generate index suggestions
        suggested_indexes = self._suggest_indexes(plan, query)

        return QueryStats(
            query=query,
            execution_time=execution_time,
            rows_examined=rows_examined,
            rows_returned=rows_returned,
            using_index=using_index,
            suggested_indexes=suggested_indexes
        )

    def _check_index_usage(self, plan: Dict) -> bool:
        """Check if the query is using indexes effectively"""
        node_type = plan.get('Node Type', '')

        # Good index usage indicators
        good_types = ['Index Scan', 'Index Only Scan', 'Bitmap Index Scan']

        if node_type in good_types:
            return True

        # Check child plans recursively
        if 'Plans' in plan:
            for child_plan in plan['Plans']:
                if self._check_index_usage(child_plan):
                    return True

        return False

    def _suggest_indexes(self, plan: Dict, query: str) -> List[str]:
        """Suggest indexes based on query plan"""
        suggestions = []

        # Look for sequential scans on large tables
        if plan.get('Node Type') == 'Seq Scan':
            table_name = plan.get('Relation Name')
            filter_condition = plan.get('Filter')

            if table_name and filter_condition:
                # Simple heuristic: suggest index on filtered columns
                # In practice, this would be more sophisticated
                suggestions.append(f"CREATE INDEX idx_{table_name}_filter ON {table_name} (column_name);")

        # Look for sorts that could benefit from indexes
        if plan.get('Node Type') == 'Sort':
            sort_key = plan.get('Sort Key')
            if sort_key:
                suggestions.append(f"Consider index on sort columns: {sort_key}")

        # Check child plans
        if 'Plans' in plan:
            for child_plan in plan['Plans']:
                suggestions.extend(self._suggest_indexes(child_plan, query))

        return suggestions

    async def get_table_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """Get database table statistics for optimization"""
        try:
            # Get table sizes
            size_query = """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """

            result = await session.execute(text(size_query))
            table_sizes = [dict(row._mapping) for row in result]

            # Get index usage statistics
            index_query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC;
            """

            result = await session.execute(text(index_query))
            index_stats = [dict(row._mapping) for row in result]

            # Get slow query statistics if pg_stat_statements is available
            slow_query_stats = await self._get_slow_query_stats(session)

            return {
                "table_sizes": table_sizes,
                "index_usage": index_stats,
                "slow_queries": slow_query_stats,
                "optimization_suggestions": self._generate_optimization_suggestions(table_sizes, index_stats)
            }

        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}

    async def _get_slow_query_stats(self, session: AsyncSession) -> List[Dict]:
        """Get slow query statistics from pg_stat_statements"""
        try:
            query = """
            SELECT
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements
            WHERE mean_time > 100  -- Queries with mean time > 100ms
            ORDER BY mean_time DESC
            LIMIT 20;
            """

            result = await session.execute(text(query))
            return [dict(row._mapping) for row in result]

        except Exception as e:
            # pg_stat_statements might not be installed
            logger.info("pg_stat_statements not available for query analysis")
            return []

    def _generate_optimization_suggestions(self, table_sizes: List[Dict], index_stats: List[Dict]) -> List[str]:
        """Generate optimization suggestions based on statistics"""
        suggestions = []

        # Suggest indexes for large tables without good index usage
        large_tables = [t for t in table_sizes if t['size_bytes'] > 100 * 1024 * 1024]  # > 100MB

        for table in large_tables:
            table_name = table['tablename']

            # Check if table has good index usage
            table_indexes = [i for i in index_stats if i['tablename'] == table_name]

            if not table_indexes or all(i['idx_scan'] < 100 for i in table_indexes):
                suggestions.append(f"Table '{table_name}' is large ({table['size']}) but has low index usage. Consider adding appropriate indexes.")

        # Suggest removing unused indexes
        unused_indexes = [i for i in index_stats if i['idx_scan'] == 0]
        for index in unused_indexes:
            suggestions.append(f"Index '{index['indexname']}' on table '{index['tablename']}' is unused and could be dropped.")

        return suggestions


# Global optimizer instance
query_optimizer = QueryOptimizer()


def optimize_query(func):
    """Decorator to automatically optimize and analyze queries"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log slow operations
            if execution_time > 0.5:  # Log operations slower than 500ms
                logger.warning(f"Slow database operation: {func.__name__} took {execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Database operation failed: {func.__name__} after {execution_time:.2f}s - {e}")
            raise

    return wrapper


class OptimizedQueries:
    """Collection of optimized query patterns"""

    @staticmethod
    async def get_user_with_relations(session: AsyncSession, user_id: int):
        """Optimized query to get user with related data"""
        from app.models.user import User

        # Use selectinload for one-to-many relationships to avoid N+1 queries
        query = (
            session.query(User)
            .options(
                selectinload(User.courses),
                selectinload(User.assignments),
                joinedload(User.profile)  # Use joinedload for one-to-one
            )
            .filter(User.id == user_id)
        )

        return await query.first()

    @staticmethod
    async def get_courses_with_assignments(session: AsyncSession, user_id: int):
        """Optimized query to get courses with assignments"""
        from app.models.course import Course
        from app.models.assignment import Assignment

        # Use subquery to avoid cartesian product
        query = """
        SELECT c.*, a.id as assignment_id, a.title as assignment_title
        FROM courses c
        LEFT JOIN assignments a ON c.id = a.course_id
        WHERE c.user_id = :user_id
        ORDER BY c.id, a.due_date
        """

        result = await session.execute(text(query), {"user_id": user_id})
        return result.fetchall()

    @staticmethod
    async def get_dashboard_data(session: AsyncSession, user_id: int):
        """Optimized query for dashboard data with minimal database hits"""
        # Single query to get all dashboard data
        query = """
        WITH user_stats AS (
            SELECT
                COUNT(DISTINCT c.id) as course_count,
                COUNT(DISTINCT a.id) as assignment_count,
                COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed_assignments
            FROM users u
            LEFT JOIN courses c ON u.id = c.user_id
            LEFT JOIN assignments a ON c.id = a.course_id
            WHERE u.id = :user_id
        ),
        recent_activity AS (
            SELECT
                'assignment' as type,
                a.title as title,
                a.updated_at as timestamp
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            WHERE c.user_id = :user_id
            ORDER BY a.updated_at DESC
            LIMIT 5
        )
        SELECT * FROM user_stats, recent_activity;
        """

        result = await session.execute(text(query), {"user_id": user_id})
        return result.fetchall()


# Database maintenance utilities
class DatabaseMaintenance:
    """Database maintenance and optimization utilities"""

    @staticmethod
    async def analyze_tables(session: AsyncSession, table_names: List[str] = None):
        """Run ANALYZE on specified tables or all tables"""
        if table_names:
            for table in table_names:
                await session.execute(text(f"ANALYZE {table};"))
        else:
            await session.execute(text("ANALYZE;"))

        logger.info(f"ANALYZE completed for tables: {table_names or 'all'}")

    @staticmethod
    async def vacuum_tables(session: AsyncSession, table_names: List[str] = None):
        """Run VACUUM on specified tables"""
        if table_names:
            for table in table_names:
                await session.execute(text(f"VACUUM {table};"))
        else:
            await session.execute(text("VACUUM;"))

        logger.info(f"VACUUM completed for tables: {table_names or 'all'}")

    @staticmethod
    async def reindex_tables(session: AsyncSession, table_names: List[str] = None):
        """Reindex specified tables or all tables"""
        if table_names:
            for table in table_names:
                await session.execute(text(f"REINDEX TABLE {table};"))
        else:
            await session.execute(text("REINDEX DATABASE core_engine;"))

        logger.info(f"REINDEX completed for tables: {table_names or 'all'}")

    @staticmethod
    async def get_database_size(session: AsyncSession) -> Dict[str, Any]:
        """Get database size information"""
        query = """
        SELECT
            pg_size_pretty(pg_database_size(current_database())) as database_size,
            pg_database_size(current_database()) as database_size_bytes
        """

        result = await session.execute(text(query))
        return dict(result.fetchone()._mapping)


# Connection to monitoring system
async def update_database_metrics():
    """Update database metrics for monitoring"""
    try:
        async with AsyncSessionLocal() as session:
            stats = await query_optimizer.get_table_statistics(session)
            db_size = await DatabaseMaintenance.get_database_size(session)

            # Update Prometheus metrics
            from app.core.monitoring import DATABASE_CONNECTIONS
            DATABASE_CONNECTIONS.set(len(engine.pool.checkedout()))

            logger.debug("Database metrics updated successfully")

    except Exception as e:
        logger.error(f"Failed to update database metrics: {e}")