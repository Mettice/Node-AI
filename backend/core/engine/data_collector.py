"""
Data collection and merging module.

This module handles:
- Collecting source data from nodes
- Merging multiple inputs intelligently
- Handling direct vs indirect source priority
- Supporting intelligent routing
"""

from typing import Any, Dict, List, Optional

from backend.core.models import Node, Workflow
from backend.core.node_registry import NodeRegistry
from backend.core.engine.workflow_validator import WorkflowValidator
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataCollector:
    """Collects and merges data from source nodes."""

    @staticmethod
    def collect_source_data(
        workflow: Workflow,
        node_id: str,
        node_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect source data from all source nodes WITHOUT merging.
        Preserves all source data separately to avoid data loss.
        
        Returns:
            Dictionary mapping source_id -> {
                "outputs": {...},
                "node_type": "...",
                "node_label": "...",
                "node": Node object
            }
        """
        source_data: Dict[str, Dict[str, Any]] = {}
        
        # Find all edges that target this node
        for edge in workflow.edges:
            if edge.target == node_id:
                source_outputs = node_outputs.get(edge.source, {})
                source_node = WorkflowValidator.get_node_by_id(workflow, edge.source)
                
                source_data[edge.source] = {
                    "outputs": source_outputs.copy(),  # Preserve original outputs
                    "node_type": source_node.type if source_node else "unknown",
                    "node_label": source_node.data.get("label", "").lower() if (source_node and source_node.data) else "",
                    "node": source_node,
                }
        
        return source_data
    
    @staticmethod
    def smart_merge_sources(
        source_data: Dict[str, Dict[str, Any]],
        target_node_type: str,
        workflow: Workflow,
        target_node_id: str,
    ) -> Dict[str, Any]:
        """
        Smart merging of source data when intelligent routing is OFF.
        Uses pattern-based mapping based on source node types.
        
        FIXED: Now implements direct source priority - direct sources (one hop away)
        are processed first and always set their fields, while indirect sources
        use conditionals to avoid conflicts.
        
        Args:
            source_data: Collected source data from collect_source_data
            target_node_type: Type of target node (e.g., "blog_generator", "email")
            workflow: The workflow (to check edge connections)
            target_node_id: ID of the target node (to identify direct sources)
            
        Returns:
            Merged inputs dictionary
        """
        available_data: Dict[str, Any] = {}
        all_attachments: List[Dict[str, Any]] = []
        
        # STEP 1: Separate direct vs indirect sources
        # Direct source = one hop away (edge directly connects to target)
        # Indirect source = multiple hops away or conflicting
        direct_sources: List[tuple] = []
        indirect_sources: List[tuple] = []
        
        for source_id, source_info in source_data.items():
            # Check if this is a direct source (edge directly to target)
            is_direct = any(
                edge.source == source_id and edge.target == target_node_id
                for edge in workflow.edges
            )
            
            if is_direct:
                direct_sources.append((source_id, source_info))
            else:
                indirect_sources.append((source_id, source_info))
        
        logger.info(f"📋 Source separation for {target_node_id} ({target_node_type}): Direct={len(direct_sources)}, Indirect={len(indirect_sources)}")
        if direct_sources:
            logger.info(f"   Direct sources: {[s[0] for s in direct_sources]} (types: {[s[1]['node_type'] for s in direct_sources]})")
        if indirect_sources:
            logger.info(f"   Indirect sources: {[s[0] for s in indirect_sources]} (types: {[s[1]['node_type'] for s in indirect_sources]})")
        
        # STEP 2: Process DIRECT sources FIRST (always set fields, no conditionals)
        for source_id, source_info in direct_sources:
            outputs = source_info["outputs"]
            node_type = source_info["node_type"]
            node_label = source_info["node_label"]
            source_node = source_info["node"]
            
            # NOTE: Formatters are for display/communication only, NOT for data flow
            # Data should flow as original structured data between nodes
            all_attachments = []  # Initialize attachments (can be populated later if needed)
            
            # Pattern-based mapping based on source node type
            # DIRECT SOURCES: Always set fields (no conditionals)
            if node_type == "text_input":
                # text_input → primary data (topic, brand, tone, etc.)
                # DIRECT SOURCE: Merge text instead of overwrite
                if "text" in outputs:
                    text_value = outputs["text"]
                    
                    # PATCH: Check if text already exists and merge instead of overwrite
                    if "text" in available_data:
                        existing_text = available_data["text"]
                        if isinstance(existing_text, str) and isinstance(text_value, str):
                            # Concatenate with clear separator
                            available_data["text"] = f"{existing_text}\n\n--- Text Input from {source_id} ---\n{text_value}"
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) MERGED text field (new length: {len(available_data['text'])})")
                        else:
                            # Convert to list if mixed types
                            available_data["text"] = [existing_text, text_value]
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) CONVERTED text to list")
                    else:
                        available_data["text"] = text_value  # First source sets it normally
                        logger.info(f"   ✅ Direct source {source_id} ({node_type}) set text field (length: {len(text_value) if isinstance(text_value, str) else 'N/A'})")
                    
                    available_data[source_id] = text_value  # Also by node ID
                    
                    # Semantic mapping based on label
                    if "topic" in node_label or "subject" in node_label:
                        available_data["topic"] = text_value  # ✅ Always set
                    elif "brand" in node_label or "product" in node_label:
                        available_data["brand_info"] = text_value
                        available_data["brand"] = text_value
                    elif "tone" in node_label or "style" in node_label:
                        available_data["tone"] = text_value
                        available_data["style"] = text_value
                    elif "content" in node_label and "type" in node_label:
                        available_data["content_type"] = text_value
                    else:
                        # Default: ALWAYS map to topic for text_input (direct source)
                        available_data["topic"] = text_value  # ✅ Always set
                        logger.info(f"   ✅ Direct source {source_id} ({node_type}) set topic field (default mapping)")
                    
                    # Also map to query for search nodes
                    available_data["query"] = text_value  # ✅ Always set
                    logger.info(f"   ✅ Direct source {source_id} ({node_type}) set text and topic fields")
                        
            elif node_type == "file_loader" or node_type == "file_upload":
                # file_loader → context/content
                # DIRECT SOURCE: Merge text instead of overwrite
                if "text" in outputs:
                    file_content = outputs["text"]
                    
                    # PATCH: Check if text already exists and merge instead of overwrite
                    if "text" in available_data:
                        existing_text = available_data["text"]
                        if isinstance(existing_text, str) and isinstance(file_content, str):
                            # Concatenate with clear separator
                            available_data["text"] = f"{existing_text}\n\n--- File Content from {source_id} ---\n{file_content}"
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) MERGED text field (new length: {len(available_data['text'])})")
                        else:
                            # Convert to list if mixed types
                            available_data["text"] = [existing_text, file_content]
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) CONVERTED text to list")
                    else:
                        available_data["text"] = file_content  # First source sets it normally
                        logger.info(f"   ✅ Direct source {source_id} ({node_type}) set text field (length: {len(file_content) if isinstance(file_content, str) else 'N/A'})")
                    
                    available_data["file_content"] = file_content
                    available_data["context"] = file_content
                    available_data["content"] = file_content
                    available_data[f"{source_id}_content"] = file_content  # Preserve with source prefix
                else:
                    logger.warning(f"   ⚠️ Direct source {source_id} ({node_type}) has no 'text' field in outputs: {list(outputs.keys())}")
                        
            elif node_type == "advanced_nlp":
                # advanced_nlp → summary/content/analysis
                # DIRECT SOURCE: Merge fields instead of overwrite
                if "output" in outputs:
                    nlp_output = outputs["output"]
                    
                    # PATCH: Merge text instead of overwrite
                    if "text" in available_data:
                        existing_text = available_data["text"]
                        if isinstance(existing_text, str) and isinstance(nlp_output, str):
                            available_data["text"] = f"{existing_text}\n\n--- NLP Analysis from {source_id} ---\n{nlp_output}"
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) MERGED text field")
                        else:
                            available_data["text"] = [existing_text, nlp_output]
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) CONVERTED text to list")
                    else:
                        available_data["text"] = nlp_output
                        logger.info(f"   ✅ Direct source {source_id} ({node_type}) set text field")
                    
                    available_data["summary"] = nlp_output  # ✅ Always set
                    available_data["content"] = nlp_output  # ✅ Always set
                    available_data["analysis"] = nlp_output  # ✅ Always set
                elif "summary" in outputs:
                    available_data["summary"] = outputs["summary"]  # ✅ Always set
                    available_data["content"] = outputs["summary"]  # ✅ Always set
                    
            elif node_type in ["blog_generator", "proposal_generator", "brand_generator"]:
                # Content generators → structured output for downstream nodes
                if "output" in outputs:
                    generator_output = outputs["output"]
                    
                    # PATCH: Merge text instead of overwrite
                    if "text" in available_data:
                        existing_text = available_data["text"]
                        if isinstance(existing_text, str) and isinstance(generator_output, str):
                            available_data["text"] = f"{existing_text}\n\n--- Generated Content from {source_id} ---\n{generator_output}"
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) MERGED text field")
                        else:
                            available_data["text"] = [existing_text, generator_output]
                            logger.info(f"   🔄 Direct source {source_id} ({node_type}) CONVERTED text to list")
                    else:
                        available_data["text"] = generator_output
                        logger.info(f"   ✅ Direct source {source_id} ({node_type}) set text field")
                    
                    available_data["content"] = generator_output
                    available_data["topic"] = generator_output  # For blog chaining
                elif "blog_post" in outputs:
                    # Extract text content from blog post structure
                    blog_post = outputs["blog_post"]
                    if isinstance(blog_post, dict):
                        content_parts = []
                        for part in ["title", "introduction", "content", "conclusion"]:
                            if blog_post.get(part):
                                content_parts.append(str(blog_post[part]))
                        content = "\n\n".join(content_parts) if content_parts else str(blog_post)
                    else:
                        content = str(blog_post)
                    available_data["text"] = content
                    available_data["content"] = content
                            
            elif node_type == "auto_chart_generator":
                # Chart generator → structured output for downstream nodes
                if "charts" in outputs:
                    # Extract text summaries from chart data for downstream processing
                    chart_summaries = []
                    for chart in outputs.get("charts", []):
                        if chart.get("title"):
                            chart_summaries.append(chart["title"])
                        if chart.get("description"):
                            chart_summaries.append(chart["description"])
                    
                    chart_text = "\n".join(chart_summaries) if chart_summaries else "Chart analysis generated"
                    available_data["text"] = chart_text
                    available_data["content"] = chart_text
                    
                if "data_summary" in outputs:
                    summary = outputs["data_summary"]
                    if isinstance(summary, dict) and summary.get("data_overview"):
                        available_data["summary"] = summary["data_overview"]
                        available_data["analysis"] = summary["data_overview"]
                    
            elif node_type in ["embed", "embedding"]:
                # Embedding nodes → embeddings for vector search
                if "embeddings" in outputs:
                    available_data["query_embedding"] = outputs["embeddings"]
                    available_data["embeddings"] = outputs["embeddings"]
                if "embedding" in outputs:
                    available_data["query_embedding"] = outputs["embedding"]  
                    available_data["embeddings"] = outputs["embedding"]
                # Pass through query/text that was embedded
                if "query" in outputs:
                    available_data["query"] = outputs["query"]
                    available_data["text"] = outputs["query"]
                    
            elif node_type in ["email", "slack"]:
                # Communication nodes → pass through
                if "body" in outputs:
                    available_data["body"] = outputs["body"]
                if "message" in outputs:
                    available_data["message"] = outputs["message"]
                    
            # Common field extraction for all node types (direct sources)
            if "output" in outputs:
                output_value = outputs["output"]
                if isinstance(output_value, str):
                    # PATCH: Merge text instead of overwrite
                    if "text" in available_data:
                        existing_text = available_data["text"]
                        if isinstance(existing_text, str):
                            available_data["text"] = f"{existing_text}\n\n--- Output from {source_id} ---\n{output_value}"
                            logger.info(f"   🔄 Direct source {source_id} MERGED common text field")
                        else:
                            available_data["text"] = [existing_text, output_value]
                            logger.info(f"   🔄 Direct source {source_id} CONVERTED common text to list")
                    else:
                        available_data["text"] = output_value  # First source sets it normally
                        logger.info(f"   ✅ Direct source {source_id} set common text field")
                elif isinstance(output_value, dict):
                    # Extract nested output string if it exists
                    if "output" in output_value and isinstance(output_value["output"], str):
                        nested_output = output_value["output"]
                        # PATCH: Merge nested text too
                        if "text" in available_data:
                            existing_text = available_data["text"]
                            if isinstance(existing_text, str):
                                available_data["text"] = f"{existing_text}\n\n--- Nested Output from {source_id} ---\n{nested_output}"
                            else:
                                available_data["text"] = [existing_text, nested_output]
                        else:
                            available_data["text"] = nested_output
                    # Extract other string fields
                    for nested_key, nested_value in output_value.items():
                        if isinstance(nested_value, str):
                            available_data[nested_key] = nested_value  # ✅ Always set (direct source)
                            
            # Preserve all original fields with source prefix (for debugging/fallback)
            for key, value in outputs.items():
                if key not in ["output", "text", "metadata"]:  # Avoid duplicates
                    prefixed_key = f"{source_id}_{key}"
                    available_data[prefixed_key] = value  # ✅ Always set (direct source)
                    
            # Pass through common fields
            if "index_id" in outputs:
                available_data["index_id"] = outputs["index_id"]
            if "query" in outputs:
                available_data["query"] = outputs["query"]
        
        # STEP 3: Process INDIRECT sources SECOND (use conditionals to avoid conflicts)
        for source_id, source_info in indirect_sources:
            outputs = source_info["outputs"]
            node_type = source_info["node_type"]
            node_label = source_info["node_label"]
            source_node = source_info["node"]
            
            # Note: Formatters not needed for data flow between nodes
            
            # Pattern-based mapping for INDIRECT sources (with conditionals)
            if node_type == "text_input":
                # text_input → primary data (only if not already set)
                if "text" in outputs:
                    text_value = outputs["text"]
                    if "text" not in available_data:  # ✅ Conditional
                        available_data["text"] = text_value
                    available_data[source_id] = text_value  # Always set by node ID
                    
                    # Semantic mapping (only if not already set)
                    if "topic" not in available_data:  # ✅ Conditional
                        if "topic" in node_label or "subject" in node_label:
                            available_data["topic"] = text_value
                        elif "brand" in node_label or "product" in node_label:
                            available_data["brand_info"] = text_value
                            available_data["brand"] = text_value
                        elif "tone" in node_label or "style" in node_label:
                            available_data["tone"] = text_value
                            available_data["style"] = text_value
                        elif "content" in node_label and "type" in node_label:
                            available_data["content_type"] = text_value
                        else:
                            available_data["topic"] = text_value
                    
                    if "query" not in available_data:  # ✅ Conditional
                        available_data["query"] = text_value
                        
            elif node_type == "file_loader" or node_type == "file_upload":
                # file_loader → context/content (only if not already set)
                if "text" in outputs:
                    file_content = outputs["text"]
                    available_data["file_content"] = file_content  # ✅ Always set (different field)
                    available_data["context"] = file_content  # ✅ Always set (different field)
                    available_data["content"] = file_content  # ✅ Always set (different field)
                    available_data[f"{source_id}_content"] = file_content
                    
                    if "text" not in available_data:  # ✅ Conditional
                        available_data["text"] = file_content
                        
            elif node_type == "advanced_nlp":
                # advanced_nlp → summary/content/analysis (only if not already set)
                if "output" in outputs:
                    nlp_output = outputs["output"]
                    if "summary" not in available_data:  # ✅ Conditional
                        available_data["summary"] = nlp_output
                    if "content" not in available_data:  # ✅ Conditional
                        available_data["content"] = nlp_output
                    if "analysis" not in available_data:  # ✅ Conditional
                        available_data["analysis"] = nlp_output
                    if "text" not in available_data:  # ✅ Conditional
                        available_data["text"] = nlp_output
                elif "summary" in outputs:
                    if "summary" not in available_data:  # ✅ Conditional
                        available_data["summary"] = outputs["summary"]
                    if "content" not in available_data:  # ✅ Conditional
                        available_data["content"] = outputs["summary"]
                    
            elif node_type in ["blog_generator", "proposal_generator", "brand_generator"]:
                # Content generators → structured output (conditional)
                if "output" in outputs and "text" not in available_data:
                    available_data["text"] = outputs["output"]
                    available_data["content"] = outputs["output"]
                            
            elif node_type == "auto_chart_generator":
                # Chart generator → structured output (conditional)
                if "charts" in outputs and "text" not in available_data:
                    # Extract chart summaries for text processing
                    chart_summaries = []
                    for chart in outputs.get("charts", []):
                        if chart.get("title"):
                            chart_summaries.append(chart["title"])
                    chart_text = "\n".join(chart_summaries) if chart_summaries else "Chart analysis"
                    available_data["text"] = chart_text
                    available_data["content"] = chart_text
                    
            elif node_type in ["embed", "embedding"]:
                # Embedding nodes → embeddings (conditional)
                if "embeddings" in outputs and "query_embedding" not in available_data:
                    available_data["query_embedding"] = outputs["embeddings"]
                    available_data["embeddings"] = outputs["embeddings"]
                if "embedding" in outputs and "query_embedding" not in available_data:
                    available_data["query_embedding"] = outputs["embedding"]  
                    available_data["embeddings"] = outputs["embedding"]
                if "query" in outputs and "query" not in available_data:
                    available_data["query"] = outputs["query"]
                    
            elif node_type in ["email", "slack"]:
                # Communication nodes → pass through
                if "body" in outputs and "body" not in available_data:  # ✅ Conditional
                    available_data["body"] = outputs["body"]
                if "message" in outputs and "message" not in available_data:  # ✅ Conditional
                    available_data["message"] = outputs["message"]
                    
            # Common field extraction for indirect sources (with conditionals)
            if "output" in outputs:
                output_value = outputs["output"]
                if isinstance(output_value, str):
                    if "text" not in available_data:  # ✅ Conditional
                        available_data["text"] = output_value
                elif isinstance(output_value, dict):
                    if "output" in output_value and isinstance(output_value["output"], str):
                        if "text" not in available_data:  # ✅ Conditional
                            available_data["text"] = output_value["output"]
                    for nested_key, nested_value in output_value.items():
                        if isinstance(nested_value, str) and nested_key not in available_data:  # ✅ Conditional
                            available_data[nested_key] = nested_value
                            
            # Preserve all original fields with source prefix
            for key, value in outputs.items():
                if key not in ["output", "text", "metadata"]:
                    prefixed_key = f"{source_id}_{key}"
                    if prefixed_key not in available_data:  # ✅ Conditional
                        available_data[prefixed_key] = value
                    
            # Pass through common fields
            if "index_id" in outputs and "index_id" not in available_data:  # ✅ Conditional
                available_data["index_id"] = outputs["index_id"]
            if "query" in outputs and "query" not in available_data:  # ✅ Conditional
                available_data["query"] = outputs["query"]
                
        # Add attachments if any
        if all_attachments:
            available_data["_email_attachments"] = all_attachments
            
        logger.info(f"📋 Merged data for {target_node_id} ({target_node_type}): Direct={len(direct_sources)}, Indirect={len(indirect_sources)}, Final keys={list(available_data.keys())}")
        # Log important fields for debugging
        if "text" in available_data:
            text_val = available_data["text"]
            logger.info(f"   ✅ 'text' field present: {type(text_val).__name__} (length: {len(text_val) if isinstance(text_val, str) else 'N/A'})")
        if "topic" in available_data:
            topic_val = available_data["topic"]
            logger.info(f"   ✅ 'topic' field present: {type(topic_val).__name__} (length: {len(topic_val) if isinstance(topic_val, str) else 'N/A'})")
        return available_data
    
    @staticmethod
    def collect_all_source_data(
        source_data: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Collect all source data into a flat dictionary for intelligent routing.
        Preserves all data without merging conflicts.
        
        Returns:
            Flat dictionary with all source data (may have duplicate keys with source prefixes)
        """
        available_data: Dict[str, Any] = {}
        source_node_types: List[str] = []
        
        for source_id, source_info in source_data.items():
            outputs = source_info["outputs"]
            node_type = source_info["node_type"]
            source_node_types.append(node_type)
            
            # Add all outputs with source prefix to avoid conflicts
            # Use namespace collision detection to prevent data loss
            for key, value in outputs.items():
                prefixed_key = f"{source_id}_{key}"
                
                # Check for namespace collisions and resolve them
                if prefixed_key in available_data:
                    logger.warning(f"Intelligent routing: Namespace collision detected for key '{prefixed_key}'. "
                                 f"Existing: {available_data[prefixed_key]}, "
                                 f"New: {value}")
                    # Create numbered variants to preserve all data
                    counter = 1
                    while f"{prefixed_key}_v{counter}" in available_data:
                        counter += 1
                    final_key = f"{prefixed_key}_v{counter}"
                    available_data[final_key] = value
                    logger.info(f"Intelligent routing: Stored conflicting data as '{final_key}'")
                else:
                    available_data[prefixed_key] = value
                
            # Also add common fields without prefix (for intelligent routing to understand)
            if "text" in outputs:
                available_data[f"text_{source_id}"] = outputs["text"]  # Prefixed version
            if "output" in outputs:
                available_data[f"output_{source_id}"] = outputs["output"]
                
            # Note: Formatters removed - data flows as structured data between nodes
            # Formatted output is only generated when specifically needed for communication nodes
        
        # Add metadata for intelligent routing
        available_data["_source_node_types"] = list(set(source_node_types))
        available_data["_source_ids"] = list(source_data.keys())
        
        return available_data

    @staticmethod
    async def collect_node_inputs(
        workflow: Workflow,
        node_id: str,
        node_outputs: Dict[str, Dict[str, Any]],
        use_intelligent_routing: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Collect inputs for a node from its source nodes.
        
        FIXED: Now collects source data FIRST, then applies intelligent routing or smart merging.
        This prevents data loss from premature merging.
        
        Args:
            workflow: The workflow
            node_id: The target node ID
            node_outputs: Outputs from previously executed nodes
            use_intelligent_routing: Whether to use intelligent routing (None = auto-detect from settings)
            
        Returns:
            Combined inputs dictionary
        """
        # STRATEGIC DECISION: Disable intelligent routing to eliminate complexity
        # Focus on Universal Data Envelope instead
        use_intelligent_routing = False
        logger.debug(f"Intelligent routing DISABLED - using enhanced smart merge instead")
        
        # STEP 1: Collect source data WITHOUT merging (preserve all sources)
        source_data = DataCollector.collect_source_data(workflow, node_id, node_outputs)
        
        # STEP 2: Apply routing strategy
        target_node = WorkflowValidator.get_node_by_id(workflow, node_id)
        target_node_type = target_node.type if target_node else "unknown"
        
        # STEP 2.5: For vector_search nodes, ensure query from config is available in inputs
        # This handles cases where query is injected by frontend into node config
        if target_node_type == "vector_search" and target_node and target_node.data:
            query_from_config = target_node.data.get("query")
            if query_from_config and not source_data:
                # If there are no source nodes but query is in config, create a minimal source_data
                # so the query can be passed through
                logger.info(f"   📋 Vector search node {node_id} has query in config: {query_from_config[:50] if isinstance(query_from_config, str) else query_from_config}")
        
        if not source_data:
            # No source nodes, but check if we need to pass config values
            if target_node_type == "vector_search" and target_node and target_node.data:
                query_from_config = target_node.data.get("query")
                if query_from_config:
                    logger.info(f"   📋 No source nodes for {node_id}, but query found in config")
                    return {"query": query_from_config}
            logger.debug(f"📋 No source nodes for {node_id}")
            return {}
        
        logger.info(f"🔀 Collecting inputs for {node_id} ({target_node_type}): Intelligent routing={use_intelligent_routing}, Sources={list(source_data.keys())}")
        for source_id, source_info in source_data.items():
            logger.info(f"   Source {source_id}: type={source_info['node_type']}, has_text={'text' in source_info['outputs']}, output_keys={list(source_info['outputs'].keys())}")
        
        if use_intelligent_routing:
            # STEP 2A: Use intelligent routing
            try:
                # Collect all source data for intelligent routing
                available_data = DataCollector.collect_all_source_data(source_data)
                
                # Get node schema for intelligent routing
                try:
                    node_class = NodeRegistry.get(target_node_type)
                    node_instance = node_class()
                    node_schema = node_instance.get_schema()
                except Exception as e:
                    schema_error_context = {
                        "target_node_type": target_node_type,
                        "node_id": node_id,
                        "available_source_types": list(set([info["node_type"] for info in source_data.values()])),
                        "error": str(e)
                    }
                    logger.warning(f"⚠️ Could not get schema for {target_node_type}, using smart fallback. Context: {schema_error_context}")
                    # Fall through to smart fallback merging
                    inputs = DataCollector.smart_merge_sources(source_data, target_node_type, workflow, node_id)
                    logger.debug(f"📋 Smart fallback for {node_id} ({target_node_type}): Merged keys: {list(inputs.keys())}")
                    return inputs
                
                # Get workflow context for better routing decisions
                workflow_context = f"{workflow.name}: {workflow.description or 'No description'}"
                
                # Get source node types
                source_node_types = list(set([info["node_type"] for info in source_data.values()]))
                
                # Use intelligent router
                from backend.core.intelligent_router import route_data_intelligently
                intelligent_inputs = await route_data_intelligently(
                    target_node_type=target_node_type,
                    target_node_schema=node_schema,
                    available_data=available_data,
                    source_node_types=source_node_types,
                    workflow_context=workflow_context,
                    use_intelligent=True,
                )
                
                # Merge intelligent routing results with source data
                # CRITICAL FIX: Merge multiple text sources instead of letting LLM pick just one
                
                # Start with available data (all prefixed keys)
                inputs = dict(available_data)
                
                # For each field in intelligent_inputs, check if we should merge or overwrite
                logger.info(f"   🔍 Intelligent routing merging: available_data keys={list(available_data.keys())}")
                logger.info(f"   🔍 Intelligent routing merging: intelligent_inputs keys={list(intelligent_inputs.keys())}")
                
                for key, value in intelligent_inputs.items():
                    logger.info(f"   🔍 Processing intelligent field: {key} = {type(value).__name__}")
                    
                    if key == "text":
                        # ALWAYS merge multiple text sources for text field
                        logger.info(f"   🔍 Found text field in intelligent_inputs")
                        
                        # Find all text sources in available_data
                        text_sources = []
                        for source_key, source_value in available_data.items():
                            if "_text" in source_key and isinstance(source_value, str):
                                source_id = source_key.replace("_text", "")
                                text_sources.append(f"--- Content from {source_id} ---\n{source_value}")
                                logger.info(f"   🔍 Found text source: {source_key} (length: {len(source_value)})")
                        
                        if len(text_sources) > 1:
                            # Combine all sources when multiple exist
                            inputs[key] = "\n\n".join(text_sources)
                            logger.info(f"   🔄 Intelligent routing MERGED {len(text_sources)} text sources for {node_id}")
                        else:
                            # Single source or no sources found, use LLM's choice
                            inputs[key] = value
                            logger.info(f"   ✅ Intelligent routing used LLM choice for text (sources: {len(text_sources)})")
                    else:
                        # For non-text fields, use LLM's mapping
                        inputs[key] = value
                
                # Extract attachments if any
                if "_email_attachments" in available_data:
                    inputs["_email_attachments"] = available_data["_email_attachments"]
                
                # Post-process: Extract formatted output for communication / display nodes if not already mapped
                # This handles cases where intelligent routing succeeded but didn't map formatted_* keys
                formatted_value = None
                formatted_keys = [k for k in available_data.keys() if k.startswith("formatted_")]
                if formatted_keys:
                    formatted_value = available_data[formatted_keys[0]]  # Use first formatted output
                
                if formatted_value:
                    # Email nodes need body/email_body
                    if target_node_type == "email" or "send_email" in target_node_type:
                        if not inputs.get("body") and not inputs.get("email_body"):
                            inputs["body"] = formatted_value
                            inputs["email_body"] = formatted_value
                            inputs["_email_type"] = "html"
                            logger.info(f"   📧 Extracted formatted output for email body from {formatted_keys}")
                    
                    # Slack nodes need message
                    elif target_node_type == "slack":
                        if not inputs.get("message"):
                            inputs["message"] = formatted_value
                            inputs["text"] = formatted_value
                            logger.info(f"   💬 Extracted formatted output for Slack message from {formatted_keys}")
                    
                    # Other nodes that might need text/content.
                    # IMPORTANT: Skip embedding / vector nodes to avoid sending huge formatted blobs
                    # directly into embeddings or vector ops (can exceed model context limits).
                    # Also skip chat nodes - they need 'results' and 'query' from vector_search, not formatted text
                    elif (
                        target_node_type
                        not in {
                            "embed",
                            "vector_store",
                            "vector_search",
                            "faiss_vector_store",
                            "chat",  # Chat nodes need 'results' and 'query', not formatted text
                        }
                        and not inputs.get("text")
                        and not inputs.get("content")
                        and not inputs.get("output")
                    ):
                        inputs["text"] = formatted_value
                        inputs["content"] = formatted_value
                        logger.info(f"   📝 Extracted formatted output for {target_node_type} from {formatted_keys}")

                # Special handling for embedding / vector nodes
                # 1) Embedding nodes: reconstruct 'chunks' from prefixed keys if needed
                if target_node_type == "embed":
                    if "chunks" not in inputs:
                        chunk_lists = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_chunks")
                        ]
                        if chunk_lists:
                            # Use the first chunk list (typical case: single chunk node)
                            inputs["chunks"] = chunk_lists[0]
                            logger.info(
                                "   📦 Reconstructed 'chunks' for embed node from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_chunks')]}"
                            )

                # 2) Vector store nodes: reconstruct 'embeddings' (and optionally 'chunks')
                if target_node_type in {"vector_store", "faiss_vector_store"}:
                    if "embeddings" not in inputs:
                        embedding_lists = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_embeddings")
                        ]
                        if embedding_lists:
                            inputs["embeddings"] = embedding_lists[0]
                            logger.info(
                                "   📊 Reconstructed 'embeddings' for vector_store from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_embeddings')]}"
                            )
                    # Also pass through chunks if available from embed node
                    if "chunks" not in inputs:
                        chunk_lists = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_chunks")
                        ]
                        if chunk_lists:
                            inputs["chunks"] = chunk_lists[0]
                            logger.info(
                                "   📦 Passed through 'chunks' for vector_store from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_chunks')]}"
                            )

                # 3) Vector search nodes: reconstruct 'index_id' and 'query' from prefixed keys
                if target_node_type == "vector_search":
                    if "index_id" not in inputs:
                        index_ids = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_index_id")
                        ]
                        if index_ids:
                            inputs["index_id"] = index_ids[0]
                            logger.info(
                                "   🔍 Reconstructed 'index_id' for vector_search from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_index_id')]}"
                            )
                    
                    # Reconstruct 'query' from text_input nodes or other sources
                    if "query" not in inputs:
                        # Try to get query from text_input nodes
                        query_values = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_text") or key.endswith("_query") or key == "text" or key == "query"
                        ]
                        if query_values:
                            # Use the first query value found
                            inputs["query"] = query_values[0]
                            logger.info(
                                "   ❓ Reconstructed 'query' for vector_search from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_text') or k.endswith('_query') or k == 'text' or k == 'query']}"
                            )
                    
                    # Also check node config for query (in case frontend injected it)
                    if "query" not in inputs and target_node and target_node.data:
                        query_from_config = target_node.data.get("query")
                        if query_from_config:
                            inputs["query"] = query_from_config
                            logger.info(f"   ❓ Added 'query' for vector_search from node config")
                
                # 4) Chat nodes: reconstruct 'results' and 'query' from prefixed keys (from vector_search)
                if target_node_type == "chat":
                    # Reconstruct 'results' from vector_search output
                    if "results" not in inputs:
                        results_lists = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_results")
                        ]
                        if results_lists:
                            inputs["results"] = results_lists[0]
                            logger.info(
                                "   💬 Reconstructed 'results' for chat node from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_results')]}"
                            )
                    
                    # Reconstruct 'query' from vector_search output
                    if "query" not in inputs:
                        queries = [
                            value
                            for key, value in available_data.items()
                            if key.endswith("_query")
                        ]
                        if queries:
                            inputs["query"] = queries[0]
                            logger.info(
                                "   ❓ Reconstructed 'query' for chat node from keys "
                                f"{[k for k in available_data.keys() if k.endswith('_query')]}"
                            )
                
                # Log what was routed
                logger.info(f"✅ Intelligent routing for {node_id} ({target_node_type}): Sources={list(source_data.keys())}, Routed={list(intelligent_inputs.keys())}")
                logger.info(f"   Final inputs keys: {list(inputs.keys())}")
                if "topic" in inputs:
                    logger.info(f"   ✅ 'topic' field present: {type(inputs['topic']).__name__} (length: {len(inputs['topic']) if isinstance(inputs['topic'], str) else 'N/A'})")
                if "text" in inputs:
                    logger.info(f"   ✅ 'text' field present: {type(inputs['text']).__name__} (length: {len(inputs['text']) if isinstance(inputs['text'], str) else 'N/A'})")
                if "body" in inputs or "email_body" in inputs:
                    body_value = inputs.get("body") or inputs.get("email_body")
                    logger.info(f"   ✅ 'body' field present: {type(body_value).__name__} (length: {len(body_value) if isinstance(body_value, str) else 'N/A'})")
                return inputs
                
            except Exception as e:
                routing_error_context = {
                    "target_node_type": target_node_type,
                    "node_id": node_id,
                    "source_data_keys": list(source_data.keys()),
                    "available_data_keys": list(available_data.keys()) if 'available_data' in locals() else [],
                    "workflow_name": workflow.name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.warning(f"⚠️ Intelligent routing failed for node {node_id}, using smart fallback. Context: {routing_error_context}")
                # Fall through to smart fallback merging
        else:
            logger.info(f"📋 Intelligent routing OFF for {node_id}, using smart fallback merging")
        
        # STEP 2B: Use smart fallback merging (when intelligent routing is OFF or failed)
        inputs = DataCollector.smart_merge_sources(source_data, target_node_type, workflow, node_id)
        
        # STEP 2C: Extract critical fields from prefixed keys (same as intelligent routing does)
        # This ensures nodes receive properly named inputs even when routing is OFF
        
        # 1) Embedding nodes: extract 'chunks' from prefixed keys
        if target_node_type == "embed":
            if "chunks" not in inputs:
                chunk_lists = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_chunks")
                ]
                if chunk_lists:
                    inputs["chunks"] = chunk_lists[0]
                    logger.info(f"   📦 Extracted 'chunks' for embed node from prefixed keys")
        
        # 2) Vector store nodes: extract 'embeddings' and 'chunks' from prefixed keys
        if target_node_type in {"vector_store", "faiss_vector_store"}:
            if "embeddings" not in inputs:
                embedding_lists = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_embeddings")
                ]
                if embedding_lists:
                    inputs["embeddings"] = embedding_lists[0]
                    logger.info(f"   📊 Extracted 'embeddings' for vector_store from prefixed keys")
            if "chunks" not in inputs:
                chunk_lists = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_chunks")
                ]
                if chunk_lists:
                    inputs["chunks"] = chunk_lists[0]
                    logger.info(f"   📦 Extracted 'chunks' for vector_store from prefixed keys")
        
        # 3) Vector search nodes: extract 'index_id' from prefixed keys
        if target_node_type == "vector_search":
            if "index_id" not in inputs:
                index_ids = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_index_id")
                ]
                if index_ids:
                    inputs["index_id"] = index_ids[0]
                    logger.info(f"   🔍 Extracted 'index_id' for vector_search from prefixed keys")
        
        # 4) Chat nodes: extract 'results' and 'query' from prefixed keys
        if target_node_type == "chat":
            if "results" not in inputs:
                results_lists = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_results")
                ]
                if results_lists:
                    inputs["results"] = results_lists[0]
                    logger.info(f"   💬 Extracted 'results' for chat node from prefixed keys")
            if "query" not in inputs:
                query_values = [
                    value
                    for key, value in inputs.items()
                    if key.endswith("_query")
                ]
                if query_values:
                    inputs["query"] = query_values[0]
                    logger.info(f"   ❓ Extracted 'query' for chat node from prefixed keys")
        
        # STEP 2.5: For vector_search nodes, ensure query from config is merged into inputs
        # This handles cases where query is injected by frontend into node config
        if target_node_type == "vector_search" and target_node and target_node.data:
            query_from_config = target_node.data.get("query")
            if query_from_config and "query" not in inputs:
                inputs["query"] = query_from_config
                logger.info(f"   ❓ Added 'query' for vector_search from node config (smart fallback)")
        
        logger.info(f"📋 Smart fallback result for {node_id} ({target_node_type}): Merged keys: {list(inputs.keys())}")
        return inputs

