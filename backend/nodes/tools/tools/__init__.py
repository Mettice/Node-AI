"""
Tool implementations for the Tool Node.

Each tool type has its own module with:
- Schema definition (get_schema_fields)
- Tool function (create_tool_function)
"""

from .calculator import get_calculator_schema, create_calculator_tool
from .web_search import get_web_search_schema, create_web_search_tool
from .web_scraping import get_web_scraping_schema, create_web_scraping_tool
from .rss_feed import get_rss_feed_schema, create_rss_feed_tool
from .s3_storage import get_s3_storage_schema, create_s3_storage_tool
from .email import get_email_schema, create_email_tool
from .code_execution import get_code_execution_schema, create_code_execution_tool
from .database_query import get_database_query_schema, create_database_query_tool
from .api_call import get_api_call_schema, create_api_call_tool
from .custom import get_custom_schema, create_custom_tool

__all__ = [
    "get_calculator_schema",
    "create_calculator_tool",
    "get_web_search_schema",
    "create_web_search_tool",
    "get_web_scraping_schema",
    "create_web_scraping_tool",
    "get_rss_feed_schema",
    "create_rss_feed_tool",
    "get_s3_storage_schema",
    "create_s3_storage_tool",
    "get_email_schema",
    "create_email_tool",
    "get_code_execution_schema",
    "create_code_execution_tool",
    "get_database_query_schema",
    "create_database_query_tool",
    "get_api_call_schema",
    "create_api_call_tool",
    "get_custom_schema",
    "create_custom_tool",
]

