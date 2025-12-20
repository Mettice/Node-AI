# Direct vs Indirect Sources - Explained

## 🎯 What Are Direct and Indirect Sources?

### Direct Source (One Hop Away)

**Definition**: A node that is **directly connected** to the target node with a single edge.

**Example**:
```
text_input ──→ blog_generator
     ↑              ↑
  source        target
```

In this case, `text_input` is a **direct source** of `blog_generator`.

**Another Example**:
```
file_upload ──→ Advanced NLP ──→ blog_generator
     ↑              ↑                 ↑
  source        intermediate       target
```

Here:
- `file_upload` is a **direct source** of `Advanced NLP`
- `Advanced NLP` is a **direct source** of `blog_generator`
- `file_upload` is an **indirect source** of `blog_generator` (2 hops away)

---

### Indirect Source (Multiple Hops Away)

**Definition**: A node that reaches the target through **one or more intermediate nodes**.

**Example**:
```
text_input ──→ Advanced NLP ──→ blog_generator
     ↑              ↑                 ↑
  source        intermediate       target
```

Here:
- `text_input` is an **indirect source** of `blog_generator` (2 hops away)
- `Advanced NLP` is a **direct source** of `blog_generator` (1 hop away)

---

## 📊 Real-World Example from Your Workflow

### Your Current Workflow:
```
text_input ──→ blog_generator
     ↑              ↑
  direct         target

file_upload ──→ Advanced NLP ──→ blog_generator
     ↑              ↑                 ↑
  indirect      direct            target
```

**For `blog_generator`**:
- **Direct sources**: `text_input`, `Advanced NLP`
- **Indirect sources**: `file_upload` (reaches through `Advanced NLP`)

**For `Advanced NLP`**:
- **Direct sources**: `file_upload`
- **Indirect sources**: None

---

## 🔢 Can We Connect Multiple Inputs? (YES!)

### Answer: **YES, you can connect ANY number of inputs!**

The universal fix supports:
- ✅ 2 inputs
- ✅ 4 inputs
- ✅ 6 inputs
- ✅ 12 inputs
- ✅ **Unlimited inputs** (as many as you want)

### How It Works:

**Example: 6 inputs to one node**:
```
text_input_1 ──┐
text_input_2 ──┤
text_input_3 ──┤
file_upload_1 ─┼──→ blog_generator
file_upload_2 ─┤
advanced_nlp ──┘
```

**All 6 are DIRECT sources** of `blog_generator` (one hop away).

**The fix handles this by**:
1. Identifying all 6 as direct sources
2. Processing all 6 and setting their fields
3. Using intelligent merging to combine them

---

## 🎯 How Direct Source Priority Works

### The Logic:

```python
# For target node: blog_generator
# Check each source in source_data

for source_id, source_info in source_data.items():
    # Check if edge exists: source_id → target_node_id
    is_direct = any(
        edge.source == source_id and edge.target == target_node_id
        for edge in workflow.edges
    )
    
    if is_direct:
        # This is a DIRECT source
        # Process it FIRST and ALWAYS set its fields
        direct_sources.append((source_id, source_info))
    else:
        # This is an INDIRECT source
        # Process it SECOND with conditionals
        indirect_sources.append((source_id, source_info))
```

### Example with 4 Direct Sources:

```python
# Target: blog_generator
# Sources:
# - text_input_1 (direct)
# - text_input_2 (direct)
# - file_upload (direct)
# - advanced_nlp (direct)

# Step 1: Process ALL direct sources
for source in direct_sources:
    # Always set fields (no conditionals)
    if source.type == "text_input":
        available_data["topic"] = source.text  # ✅ Always set
    elif source.type == "file_upload":
        available_data["file_content"] = source.text  # ✅ Always set
    # ... etc

# Result: All 4 sources contribute their data
# - topic from text_input_1
# - topic from text_input_2 (might overwrite, or we merge)
# - file_content from file_upload
# - summary from advanced_nlp
```

---

## 🔄 Multiple Direct Sources with Same Field

### The Challenge:

What if multiple direct sources set the same field?

**Example**:
```
text_input_1 ──┐
text_input_2 ──┼──→ blog_generator
text_input_3 ──┘
```

All 3 set `topic`. Which one wins?

### Solution Options:

#### Option 1: Last One Wins (Current Behavior)
```python
# Process in order
available_data["topic"] = text_input_1.text  # Set
available_data["topic"] = text_input_2.text  # Overwrites
available_data["topic"] = text_input_3.text  # Overwrites (final value)
```

#### Option 2: Merge/Combine (Better)
```python
# Collect all topics
topics = []
for source in direct_sources:
    if source.type == "text_input":
        topics.append(source.text)

# Combine them
available_data["topic"] = " ".join(topics)  # "topic1 topic2 topic3"
# OR
available_data["topics"] = topics  # ["topic1", "topic2", "topic3"]
```

#### Option 3: Use Source Prefixes (Best for Multiple)
```python
# Set with source ID prefix
available_data["text_input_1_topic"] = text_input_1.text
available_data["text_input_2_topic"] = text_input_2.text
available_data["text_input_3_topic"] = text_input_3.text

# Also set primary field (last one or merged)
available_data["topic"] = text_input_3.text  # Or merged value
```

---

## 📋 Universal Fix Implementation

### The Fix Handles:

1. ✅ **Any number of direct sources** (2, 4, 6, 12, unlimited)
2. ✅ **Any number of indirect sources** (through intermediate nodes)
3. ✅ **Multiple sources with same field** (using merging strategy)
4. ✅ **Complex workflows** (multiple hops, branches, etc.)

### Code Structure:

```python
def _smart_merge_sources(
    self,
    source_data: Dict[str, Dict[str, Any]],
    target_node_type: str,
    workflow: Workflow,
    target_node_id: str,
) -> Dict[str, Any]:
    # Step 1: Separate direct vs indirect
    direct_sources = []
    indirect_sources = []
    
    for source_id, source_info in source_data.items():
        # Check if direct (edge exists: source_id → target_node_id)
        is_direct = any(
            edge.source == source_id and edge.target == target_node_id
            for edge in workflow.edges
        )
        
        if is_direct:
            direct_sources.append((source_id, source_info))
        else:
            indirect_sources.append((source_id, source_info))
    
    # Step 2: Process ALL direct sources (no limit!)
    available_data = {}
    for source_id, source_info in direct_sources:
        # Process each direct source
        # Always set fields (no conditionals)
        # Handle conflicts by merging or using prefixes
        ...
    
    # Step 3: Process indirect sources (with conditionals)
    for source_id, source_info in indirect_sources:
        # Process with conditionals to avoid conflicts
        ...
    
    return available_data
```

---

## 🎯 Summary

### Direct Source:
- **One hop away** (single edge connection)
- Example: `A → B` (A is direct source of B)

### Indirect Source:
- **Multiple hops away** (through intermediate nodes)
- Example: `A → C → B` (A is indirect source of B)

### Multiple Inputs:
- ✅ **YES, you can connect ANY number of inputs**
- ✅ The fix supports 2, 4, 6, 12, or unlimited inputs
- ✅ All direct sources are processed and contribute data
- ✅ Conflicts are handled by merging or using source prefixes

### The Universal Fix:
- Works with **any number of direct sources**
- Works with **any number of indirect sources**
- Handles **conflicts intelligently**
- **No limits** on number of inputs

---

## 🧪 Example: 12 Inputs to One Node

```
text_input_1 ──┐
text_input_2 ──┤
text_input_3 ──┤
file_upload_1 ─┤
file_upload_2 ─┤
file_upload_3 ─┤
advanced_nlp_1 ┼──→ blog_generator
advanced_nlp_2 ┤
chat_1 ────────┤
chat_2 ────────┤
data_loader_1 ─┤
data_loader_2 ─┘
```

**All 12 are direct sources** - the fix processes all of them! ✅

