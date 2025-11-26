#!/usr/bin/env python3
"""
Index Performance Testing Script

This script tests the performance impact of the new database indexes
by running common queries before and after index creation.
"""

import time
import psycopg2
from typing import Dict, List, Tuple
import statistics
from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def time_query(query: str, params: Tuple = None, runs: int = 3) -> Dict:
    """Execute a query multiple times and measure performance."""
    times = []
    
    if not is_database_configured():
        logger.warning("Database not configured, skipping performance test")
        return {"error": "Database not configured"}
    
    try:
        for _ in range(runs):
            start_time = time.perf_counter()
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    results = cur.fetchall()
                    result_count = len(results)
            
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds
        
        return {
            "avg_time_ms": round(statistics.mean(times), 2),
            "min_time_ms": round(min(times), 2),
            "max_time_ms": round(max(times), 2),
            "std_dev_ms": round(statistics.stdev(times) if len(times) > 1 else 0, 2),
            "result_count": result_count,
            "runs": runs
        }
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"error": str(e)}


def test_workflow_queries() -> Dict:
    """Test common workflow query performance."""
    queries = {
        "list_user_workflows": (
            """
            SELECT id, name, description, is_template, is_deployed, created_at, updated_at
            FROM workflows 
            WHERE user_id = %s 
            ORDER BY updated_at DESC 
            LIMIT 20
            """,
            ("test-user-id",)
        ),
        
        "list_templates": (
            """
            SELECT id, name, description, created_at
            FROM workflows 
            WHERE is_template = true 
            ORDER BY created_at DESC 
            LIMIT 10
            """,
            ()
        ),
        
        "list_deployed_workflows": (
            """
            SELECT id, name, deployed_at
            FROM workflows 
            WHERE user_id = %s AND is_deployed = true 
            ORDER BY deployed_at DESC
            """,
            ("test-user-id",)
        ),
        
        "search_workflows_by_tag": (
            """
            SELECT id, name, tags
            FROM workflows 
            WHERE tags && %s
            ORDER BY updated_at DESC
            LIMIT 10
            """,
            (["ai", "automation"],)
        ),
        
        "search_workflows_by_name": (
            """
            SELECT id, name
            FROM workflows 
            WHERE name ILIKE %s
            ORDER BY name
            """,
            ("%chat%",)
        )
    }
    
    results = {}
    
    for query_name, (query, params) in queries.items():
        logger.info(f"Testing query: {query_name}")
        results[query_name] = time_query(query, params)
    
    return results


def test_secrets_queries() -> Dict:
    """Test common secrets query performance."""
    queries = {
        "list_active_secrets": (
            """
            SELECT id, name, provider, secret_type, last_used_at
            FROM secrets_vault 
            WHERE user_id = %s AND is_active = true 
            ORDER BY updated_at DESC
            """,
            ("test-user-id",)
        ),
        
        "find_secret_by_provider": (
            """
            SELECT id, name, encrypted_value
            FROM secrets_vault 
            WHERE user_id = %s AND provider = %s AND secret_type = %s AND is_active = true
            """,
            ("test-user-id", "openai", "api_key")
        ),
        
        "list_expiring_secrets": (
            """
            SELECT id, name, expires_at
            FROM secrets_vault 
            WHERE expires_at < NOW() + INTERVAL '30 days' AND is_active = true
            ORDER BY expires_at
            """,
            ()
        ),
        
        "search_secrets_by_tags": (
            """
            SELECT id, name, tags
            FROM secrets_vault 
            WHERE user_id = %s AND tags && %s AND is_active = true
            """,
            ("test-user-id", ["production", "api"])
        )
    }
    
    results = {}
    
    for query_name, (query, params) in queries.items():
        logger.info(f"Testing query: {query_name}")
        results[query_name] = time_query(query, params)
    
    return results


def test_traces_queries() -> Dict:
    """Test common traces query performance."""
    queries = {
        "list_recent_traces": (
            """
            SELECT trace_id, workflow_id, execution_id, status, started_at, total_duration_ms
            FROM traces 
            WHERE user_id = %s 
            ORDER BY started_at DESC 
            LIMIT 50
            """,
            ("test-user-id",)
        ),
        
        "list_workflow_traces": (
            """
            SELECT trace_id, execution_id, status, total_cost, total_duration_ms
            FROM traces 
            WHERE workflow_id = %s 
            ORDER BY started_at DESC 
            LIMIT 20
            """,
            ("test-workflow-id",)
        ),
        
        "find_failed_traces": (
            """
            SELECT trace_id, workflow_id, error, started_at
            FROM traces 
            WHERE status = 'failed' AND started_at > NOW() - INTERVAL '7 days'
            ORDER BY started_at DESC
            """,
            ()
        ),
        
        "cost_analysis": (
            """
            SELECT workflow_id, COUNT(*) as executions, AVG(total_cost) as avg_cost, SUM(total_cost) as total_cost
            FROM traces 
            WHERE total_cost > 0 AND started_at > NOW() - INTERVAL '30 days'
            GROUP BY workflow_id 
            ORDER BY total_cost DESC
            """,
            ()
        )
    }
    
    results = {}
    
    for query_name, (query, params) in queries.items():
        logger.info(f"Testing query: {query_name}")
        results[query_name] = time_query(query, params)
    
    return results


def check_index_usage() -> Dict:
    """Check if indexes are being used by analyzing query plans."""
    if not is_database_configured():
        return {"error": "Database not configured"}
    
    test_queries = [
        ("workflow_by_user", "SELECT id FROM workflows WHERE user_id = 'test' ORDER BY updated_at DESC LIMIT 10"),
        ("active_secrets", "SELECT id FROM secrets_vault WHERE user_id = 'test' AND is_active = true"),
        ("workflow_tags", "SELECT id FROM workflows WHERE tags && ARRAY['ai']"),
        ("traces_by_status", "SELECT trace_id FROM traces WHERE status = 'completed' ORDER BY started_at DESC LIMIT 10")
    ]
    
    index_usage = {}
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for query_name, query in test_queries:
                    # Get query execution plan
                    cur.execute(f"EXPLAIN (FORMAT JSON) {query}")
                    plan = cur.fetchone()[0]
                    
                    # Check if index scan is used
                    plan_str = str(plan)
                    uses_index = "Index Scan" in plan_str or "Index Only Scan" in plan_str
                    uses_bitmap = "Bitmap" in plan_str
                    uses_seq_scan = "Seq Scan" in plan_str
                    
                    index_usage[query_name] = {
                        "uses_index": uses_index,
                        "uses_bitmap": uses_bitmap,
                        "uses_seq_scan": uses_seq_scan,
                        "efficient": uses_index or uses_bitmap
                    }
        
        return index_usage
    
    except Exception as e:
        logger.error(f"Error checking index usage: {e}")
        return {"error": str(e)}


def generate_performance_report() -> Dict:
    """Generate a complete performance report."""
    logger.info("Starting database performance analysis...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "workflow_queries": test_workflow_queries(),
        "secrets_queries": test_secrets_queries(),
        "traces_queries": test_traces_queries(),
        "index_usage": check_index_usage()
    }
    
    return report


def print_performance_report(report: Dict):
    """Print a formatted performance report."""
    print("\n" + "="*60)
    print("DATABASE PERFORMANCE REPORT")
    print("="*60)
    print(f"Generated: {report['timestamp']}")
    print()
    
    # Print query performance
    for category, queries in report.items():
        if category in ["workflow_queries", "secrets_queries", "traces_queries"]:
            print(f"\n{category.replace('_', ' ').title()}:")
            print("-" * 40)
            
            if isinstance(queries, dict):
                for query_name, stats in queries.items():
                    if "error" in stats:
                        print(f"  {query_name}: ERROR - {stats['error']}")
                    else:
                        print(f"  {query_name}:")
                        print(f"    Average time: {stats['avg_time_ms']:.2f}ms")
                        print(f"    Results: {stats['result_count']} rows")
                        print(f"    Consistency: ±{stats['std_dev_ms']:.2f}ms")
    
    # Print index usage
    if "index_usage" in report:
        print(f"\nIndex Usage Analysis:")
        print("-" * 40)
        
        index_usage = report["index_usage"]
        if isinstance(index_usage, dict) and "error" not in index_usage:
            efficient_queries = sum(1 for stats in index_usage.values() 
                                  if isinstance(stats, dict) and stats.get("efficient", False))
            total_queries = len([k for k, v in index_usage.items() 
                               if isinstance(v, dict) and "efficient" in v])
            
            print(f"  Efficient queries: {efficient_queries}/{total_queries}")
            
            for query_name, stats in index_usage.items():
                if isinstance(stats, dict) and "efficient" in stats:
                    status = "✓ EFFICIENT" if stats["efficient"] else "✗ NEEDS OPTIMIZATION"
                    scan_type = []
                    if stats.get("uses_index"):
                        scan_type.append("Index Scan")
                    if stats.get("uses_bitmap"):
                        scan_type.append("Bitmap Scan")
                    if stats.get("uses_seq_scan"):
                        scan_type.append("Sequential Scan")
                    
                    print(f"  {query_name}: {status} ({', '.join(scan_type)})")
        else:
            print(f"  Error analyzing index usage: {index_usage.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    """Run the performance test when script is executed directly."""
    try:
        report = generate_performance_report()
        print_performance_report(report)
        
        # Save report to file
        import json
        with open("database_performance_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: database_performance_report.json")
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        print(f"Performance test failed: {e}")