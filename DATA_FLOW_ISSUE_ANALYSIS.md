# Data Flow Issue Analysis

## 🔍 Problem Summary

After implementing the data flow fix, nodes are not receiving data correctly:

1. **Advanced NLP Error**: "No text provided in inputs"
   - `File Upload` → `Advanced NLP` connection failing
   - Advanced NLP expects `text` field but not receiving it

2. **Blog Generator Error**: "Topic is required"
   - `text_input` → `blog_generator` connection failing
   - Blog generator expects `topic` field but not receiving it

---

## 🐛 Root Causes Identified

### Issue 1: Conditional Text Mapping in `_smart_merge_sources`

**Location**: `backend/core/engine.py` lines 651-662

**Problem**:
```python
elif node_type == "file_loader" or node_type == "file_upload":
    if "text" in outputs:
        file_content = outputs["text"]
        available_data["file_content"] = file_content
        available_data["context"] = file_content
        available_data["content"] = file_content
        # ...
        # ❌ PROBLEM: Only sets "text" if it doesn't already exist
        if "text" not in available_data:
            available_data["text"] = file_content
```

**Why it fails**:
- If `text_input` is processed BEFORE `file_upload` (based on edge order)
- `text_input` sets `available_data["text"]` = "Building RAG application with"
- When `file_upload` is processed, condition `if "text" not in available_data` is FALSE
- So `file_upload` text is NOT set to `available_data["text"]`
- `Advanced NLP` receives `text` from `text_input` instead of `file_upload` ❌

**Expected behavior**:
- `Advanced NLP` should receive `text` from `file_upload` (its direct source)
- `text_input` text should NOT overwrite `file_upload` text for `Advanced NLP`

---

### Issue 2: Topic Mapping Logic Too Restrictive

**Location**: `backend/core/engine.py` lines 624-649

**Problem**:
```python
if node_type == "text_input":
    if "text" in outputs:
        text_value = outputs["text"]
        available_data["text"] = text_value
        # ...
        # Semantic mapping based on label
        if "topic" in node_label or "subject" in node_label:
            available_data["topic"] = text_value
        # ...
        else:
            # Default: map to topic if not specified
            if "topic" not in available_data:  # ❌ PROBLEM: Only if not already set
                available_data["topic"] = text_value
```

**Why it might fail**:
- If `Advanced NLP` output is processed BEFORE `text_input` (unlikely but possible)
- Or if `Advanced NLP` sets something that maps to `topic` (it doesn't, but the logic is fragile)
- The condition `if "topic" not in available_data` prevents setting topic if already exists

**However**, the more likely issue is:
- `text_input` sets `text` and `topic` correctly
- But when `blog_generator` receives inputs, it might not be getting the merged data correctly
- OR the order of processing causes `text_input` data to be overwritten

---

### Issue 3: Processing Order Dependency

**Location**: `backend/core/engine.py` line 609

**Problem**:
```python
# Process each source
for source_id, source_info in source_data.items():
    # ... process in order
```

**Why it fails**:
- `source_data` is a dictionary, and dictionaries in Python 3.7+ maintain insertion order
- But the order depends on edge order in the workflow
- If edges are: `[text_input→blog, file_upload→advanced_nlp, advanced_nlp→blog]`
- Processing order might be: `text_input`, `file_upload`, `advanced_nlp`
- This causes `text_input` to set `text` first, preventing `file_upload` from setting it

---

## 🔧 Proposed Fixes

### Fix 1: Always Set Text for Direct Sources (Priority: HIGH)

**Problem**: When a node has a direct source, that source's data should take priority.

**Solution**: Track which source is "primary" for each target node, and always set fields from primary sources.

```python
def _smart_merge_sources(self, source_data, target_node_type):
    available_data = {}
    
    # Group sources by their relationship to target
    # Direct sources (single hop) should take priority
    for source_id, source_info in source_data.items():
        outputs = source_info["outputs"]
        node_type = source_info["node_type"]
        
        # For file_upload → advanced_nlp: file_upload is direct source
        # Always set text from file_upload, not from text_input
        if node_type == "file_loader" or node_type == "file_upload":
            if "text" in outputs:
                # ALWAYS set text for file_upload (it's the direct source)
                # But also set other fields
                available_data["text"] = outputs["text"]  # ✅ Always set
                available_data["file_content"] = outputs["text"]
                available_data["context"] = outputs["text"]
                available_data["content"] = outputs["text"]
```

**Better Solution**: Process sources in a way that respects direct connections:
- For each target node, identify its direct sources
- Process direct sources FIRST and set their fields
- Then process indirect sources and only set fields that don't conflict

---

### Fix 2: Always Set Topic for text_input (Priority: HIGH)

**Problem**: `text_input` should always map to `topic` for content generators.

**Solution**: Remove the conditional check for `topic`:

```python
if node_type == "text_input":
    if "text" in outputs:
        text_value = outputs["text"]
        available_data["text"] = text_value
        available_data[source_id] = text_value
        
        # Semantic mapping based on label
        if "topic" in node_label or "subject" in node_label:
            available_data["topic"] = text_value
        elif "brand" in node_label or "product" in node_label:
            available_data["brand_info"] = text_value
            available_data["brand"] = text_value
        # ...
        else:
            # ✅ ALWAYS set topic as default for text_input
            # (unless explicitly mapped to something else)
            available_data["topic"] = text_value  # Remove conditional
```

---

### Fix 3: Process Sources by Dependency Order (Priority: MEDIUM)

**Problem**: Processing order matters when multiple sources set the same field.

**Solution**: Process sources in topological order (direct sources first):

```python
def _smart_merge_sources(self, source_data, target_node_type, workflow, target_node_id):
    # Get direct sources (one hop away)
    direct_sources = []
    indirect_sources = []
    
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
    
    # Process direct sources FIRST (they take priority)
    available_data = {}
    for source_id, source_info in direct_sources:
        # Process and set fields (always set, no conditionals)
        ...
    
    # Then process indirect sources (only set if not already set)
    for source_id, source_info in indirect_sources:
        # Process and set fields (with conditionals)
        ...
```

---

## 📊 Current Workflow Structure

From the screenshot:
```
text_input → blog_generator
File Upload → Advanced NLP → blog_generator
```

**Expected data flow**:
1. `text_input` → `blog_generator`: `topic` = "Building RAG application with"
2. `File Upload` → `Advanced NLP`: `text` = file content
3. `Advanced NLP` → `blog_generator`: `content` or `summary` = processed content

**Actual data flow (broken)**:
1. `text_input` sets `text` and `topic` ✅
2. `File Upload` tries to set `text` but condition fails ❌
3. `Advanced NLP` receives `text` from `text_input` instead of `file_upload` ❌
4. `blog_generator` might not receive `topic` correctly ❌

---

## 🎯 Recommended Fix Strategy

### Priority 1: Fix Direct Source Priority
- Always set fields from direct sources (no conditionals)
- Only use conditionals for indirect/conflicting sources

### Priority 2: Fix Topic Mapping
- Always set `topic` for `text_input` (remove conditional)
- Ensure `blog_generator` receives `topic` correctly

### Priority 3: Add Source Priority Logic
- Track which sources are direct vs indirect
- Process direct sources first

---

## 🧪 Testing Plan

After fixes, test:
1. ✅ `File Upload` → `Advanced NLP`: Should receive file content as `text`
2. ✅ `text_input` → `blog_generator`: Should receive text as `topic`
3. ✅ `Advanced NLP` → `blog_generator`: Should receive processed content
4. ✅ Multiple inputs to same node: Should merge correctly

---

## 📝 Code Changes Required

1. **`_smart_merge_sources` method** (lines 589-757):
   - Remove conditional `if "text" not in available_data` for file_upload
   - Always set `topic` for text_input
   - Add source priority logic

2. **Consider**: Add `workflow` and `target_node_id` parameters to `_smart_merge_sources` to determine direct sources

---

## ⚠️ Important Notes

- The fix should NOT break existing single-input workflows
- The fix should work with intelligent routing ON and OFF
- The fix should preserve backward compatibility

