# Integration Data Flow & Data Structures

## 📊 Overview

This document explains how integrations (tools) receive inputs, process data, and return outputs in NodAI workflows. It covers both **agent usage** (where agents call tools) and **direct node usage** (where tools are used as workflow nodes).

---

## 🔄 Data Flow Architecture

### **Two Usage Patterns:**

1. **Agent Usage** (Tools called by AI agents)
   ```
   Agent Node → Calls Tool → Tool executes → Returns string → Agent processes
   ```

2. **Direct Node Usage** (Tools as workflow nodes)
   ```
   Previous Node → Tool Node (inputs) → Tool executes → Returns structured data → Next Node
   ```

---

## 🛠️ Tool Input/Output Structure

### **1. Tool Registration (Tool Node)**

When a Tool Node executes, it registers the tool definition:

```python
# Tool Node Output
{
    "tool_id": "web_search_123",
    "tool_name": "Web Search",
    "tool_type": "web_search",
    "tool_description": "Search the web for information",
    "registered": True,
    "config": {
        "web_search_provider": "serper",
        "serper_api_key": "..."
    }
}
```

### **2. Agent Tool Call (LangChain Format)**

When an agent calls a tool, it passes a **string input**:

```python
# Agent calls tool with string
tool.run("What is the weather in San Francisco?")
```

The tool function receives this string and processes it.

### **3. Tool Output (String Format for Agents)**

Tools return **strings** that agents can understand:

```python
# Web Search Output (String)
"""
1. Weather in San Francisco - Current Conditions
   Current temperature: 65°F, Partly cloudy
   https://weather.com/san-francisco

2. San Francisco Weather Forecast
   5-day forecast with detailed conditions
   https://forecast.com/sf
"""
```

### **4. Direct Node Usage (Structured Input/Output)**

When tools are used as workflow nodes (not by agents), they can accept **structured inputs** from previous nodes:

```python
# Input from previous node
{
    "query": "What is the weather?",
    "location": "San Francisco",
    "format": "json"
}

# Tool processes and returns structured output
{
    "results": [
        {
            "title": "Weather in San Francisco",
            "snippet": "Current temperature: 65°F",
            "url": "https://weather.com/sf"
        }
    ],
    "query": "What is the weather?",
    "provider": "serper",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📧 Email Integration Data Structure

### **Input Format (From Previous Nodes or Agent)**

#### **Option 1: Agent Usage (String Input)**
```python
# Agent calls email tool with string
tool.run("Send email to john@example.com with subject 'Hello' and body 'This is a test'")
```

**Tool parses the string** to extract:
- `to`: "john@example.com"
- `subject`: "Hello"
- `body`: "This is a test"

#### **Option 2: Direct Node Usage (Structured Input)**
```python
# Input from previous node (e.g., Chat node, Text Input)
{
    "to": "john@example.com",
    "subject": "Hello",
    "body": "This is a test email",
    "from": "sender@example.com",  # Optional, uses config default
    "cc": ["cc@example.com"],      # Optional
    "bcc": ["bcc@example.com"],    # Optional
    "reply_to": "reply@example.com", # Optional
    "attachments": [                # Optional
        {
            "filename": "report.pdf",
            "content": "base64_encoded_content",
            "content_type": "application/pdf"
        }
    ]
}
```

### **Output Format**

#### **For Agents (String)**
```python
"""
Email sent successfully
Message ID: msg_abc123
To: john@example.com
Subject: Hello
Status: queued
"""
```

#### **For Direct Node Usage (Structured)**
```python
{
    "success": True,
    "message_id": "msg_abc123",
    "to": "john@example.com",
    "subject": "Hello",
    "status": "queued",  # queued, sent, delivered, failed
    "timestamp": "2024-01-15T10:30:00Z",
    "error": None
}
```

### **Configuration (Tool Node Config)**
```python
{
    "tool_type": "email",
    "email_provider": "resend",
    "resend_api_key": "re_abc123...",
    "email_from": "noreply@example.com",  # Default from address
    "email_from_name": "NodAI",            # Optional
    "reply_to": "support@example.com"      # Optional
}
```

---

## 🔍 Web Search Integration Data Structure

### **Input Format**

#### **Agent Usage (String)**
```python
tool.run("What is the latest news about AI?")
```

#### **Direct Node Usage (Structured)**
```python
{
    "query": "What is the latest news about AI?",
    "num_results": 10,  # Optional, defaults to 10
    "language": "en",   # Optional
    "region": "us"      # Optional
}
```

### **Output Format**

#### **Agent Usage (String)**
```python
"""
1. Latest AI News - TechCrunch
   OpenAI releases GPT-5 with new capabilities...
   https://techcrunch.com/ai-news

2. AI Developments - The Verge
   Google announces new AI model...
   https://theverge.com/ai
"""
```

#### **Direct Node Usage (Structured)**
```python
{
    "query": "What is the latest news about AI?",
    "provider": "serper",
    "results": [
        {
            "title": "Latest AI News - TechCrunch",
            "snippet": "OpenAI releases GPT-5...",
            "url": "https://techcrunch.com/ai-news",
            "position": 1
        },
        {
            "title": "AI Developments - The Verge",
            "snippet": "Google announces new AI model...",
            "url": "https://theverge.com/ai",
            "position": 2
        }
    ],
    "total_results": 2,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🗄️ Database Integration Data Structure

### **Input Format**

#### **Agent Usage (String)**
```python
tool.run("SELECT * FROM users WHERE age > 25")
```

#### **Direct Node Usage (Structured)**
```python
{
    "query": "SELECT * FROM users WHERE age > ?",
    "parameters": [25],  # For parameterized queries
    "query_type": "SELECT"  # SELECT, INSERT, UPDATE, DELETE
}
```

### **Output Format**

#### **Agent Usage (String)**
```python
"""
Query executed successfully
Columns: id, name, age, email
Rows: 5

1. (1, 'John', 30, 'john@example.com')
2. (2, 'Jane', 28, 'jane@example.com')
...
"""
```

#### **Direct Node Usage (Structured)**
```python
{
    "success": True,
    "query": "SELECT * FROM users WHERE age > 25",
    "columns": ["id", "name", "age", "email"],
    "rows": [
        {"id": 1, "name": "John", "age": 30, "email": "john@example.com"},
        {"id": 2, "name": "Jane", "age": 28, "email": "jane@example.com"}
    ],
    "row_count": 2,
    "execution_time_ms": 45,
    "error": None
}
```

---

## ☁️ S3 Integration Data Structure

### **Input Format**

#### **Agent Usage (String)**
```python
# Upload
tool.run("Upload file report.pdf to s3://my-bucket/reports/")

# Download
tool.run("Download file s3://my-bucket/reports/report.pdf")
```

#### **Direct Node Usage (Structured)**
```python
# Upload
{
    "operation": "upload",
    "bucket": "my-bucket",
    "key": "reports/report.pdf",
    "content": "base64_encoded_file_content",
    "content_type": "application/pdf",
    "metadata": {  # Optional
        "author": "John Doe",
        "version": "1.0"
    }
}

# Download
{
    "operation": "download",
    "bucket": "my-bucket",
    "key": "reports/report.pdf"
}

# List
{
    "operation": "list",
    "bucket": "my-bucket",
    "prefix": "reports/",  # Optional
    "max_keys": 100  # Optional
}
```

### **Output Format**

#### **Agent Usage (String)**
```python
# Upload
"""
File uploaded successfully
URL: https://my-bucket.s3.amazonaws.com/reports/report.pdf
Size: 1.5 MB
"""

# Download
"""
File downloaded successfully
Size: 1.5 MB
Content-Type: application/pdf
"""
```

#### **Direct Node Usage (Structured)**
```python
# Upload
{
    "success": True,
    "operation": "upload",
    "bucket": "my-bucket",
    "key": "reports/report.pdf",
    "url": "https://my-bucket.s3.amazonaws.com/reports/report.pdf",
    "size_bytes": 1572864,
    "etag": "abc123...",
    "timestamp": "2024-01-15T10:30:00Z"
}

# Download
{
    "success": True,
    "operation": "download",
    "bucket": "my-bucket",
    "key": "reports/report.pdf",
    "content": "base64_encoded_content",
    "content_type": "application/pdf",
    "size_bytes": 1572864,
    "last_modified": "2024-01-15T09:00:00Z"
}

# List
{
    "success": True,
    "operation": "list",
    "bucket": "my-bucket",
    "prefix": "reports/",
    "files": [
        {
            "key": "reports/report.pdf",
            "size_bytes": 1572864,
            "last_modified": "2024-01-15T09:00:00Z",
            "etag": "abc123..."
        }
    ],
    "count": 1
}
```

---

## 📱 Slack Integration Data Structure

### **Input Format**

#### **Agent Usage (String)**
```python
tool.run("Send message 'Hello team!' to channel #general")
```

#### **Direct Node Usage (Structured)**
```python
{
    "channel": "#general",  # or channel ID
    "text": "Hello team!",
    "blocks": [  # Optional, for rich formatting
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hello team!"
            }
        }
    ],
    "thread_ts": "1234567890.123456",  # Optional, for threading
    "attachments": []  # Optional
}
```

### **Output Format**

#### **Agent Usage (String)**
```python
"""
Message sent successfully
Channel: #general
Timestamp: 1234567890.123456
Message ID: C1234567890
"""
```

#### **Direct Node Usage (Structured)**
```python
{
    "success": True,
    "channel": "#general",
    "ts": "1234567890.123456",
    "message": {
        "text": "Hello team!",
        "user": "U1234567890",
        "type": "message"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔄 How Agents Use Tools

### **Step 1: Tool Registration**

```python
# Tool Node executes and registers tool
tool_def = {
    "type": "email",
    "name": "Send Email",
    "description": "Send an email using Resend",
    "config": {...}
}
```

### **Step 2: Agent Discovers Tools**

```python
# Agent node receives tool outputs from connected Tool nodes
inputs = {
    "tool_email_123": {
        "tool_id": "email_123",
        "tool_name": "Send Email",
        "tool_type": "email",
        ...
    }
}

# Agent converts to LangChain Tool
tools = [
    Tool(
        name="Send Email",
        func=email_tool_func,
        description="Send an email using Resend. Input format: 'to: email@example.com, subject: Hello, body: Message text'"
    )
]
```

### **Step 3: Agent Calls Tool**

```python
# Agent decides to use tool
agent_action = AgentAction(
    tool="Send Email",
    tool_input="to: john@example.com, subject: Hello, body: This is a test"
)

# Tool executes
result = tool.run(agent_action.tool_input)
# Returns: "Email sent successfully. Message ID: msg_abc123"
```

### **Step 4: Agent Processes Result**

```python
# Agent receives tool result as string
observation = "Email sent successfully. Message ID: msg_abc123"

# Agent continues reasoning with this information
agent_final_answer = "I've sent the email to john@example.com. The message ID is msg_abc123."
```

---

## 🎯 Standard Data Structure Pattern

### **For All Integrations:**

#### **Input (Direct Node Usage)**
```python
{
    # Operation-specific fields
    "operation": "send|upload|query|fetch|...",
    "data": {...},  # Operation-specific data
    
    # Optional metadata
    "metadata": {...},
    "options": {...}
}
```

#### **Output (Direct Node Usage)**
```python
{
    "success": bool,
    "data": {...},  # Operation-specific result data
    "metadata": {
        "operation": str,
        "timestamp": str,
        "duration_ms": int,
        "provider": str
    },
    "error": {
        "code": str,
        "message": str,
        "details": {...}
    } | None
}
```

#### **Output (Agent Usage - String)**
```python
"""
[Success/Failure] message
Key details: value1, value2
Additional information...
"""
```

---

## 📋 Implementation Guidelines

### **1. Tool Functions Must:**

- **Accept string input** (for agent usage)
- **Parse string intelligently** (extract structured data)
- **Accept structured input** (for direct node usage)
- **Return string** (for agent usage)
- **Return structured dict** (for direct node usage)

### **2. Input Parsing (String → Structured)**

```python
def parse_email_input(input_str: str) -> dict:
    """Parse email input from agent string."""
    # Try to extract: to, subject, body, etc.
    # Use regex or simple parsing
    # Fallback to defaults if not found
    pass
```

### **3. Output Formatting (Structured → String)**

```python
def format_email_output(result: dict) -> str:
    """Format email result as string for agent."""
    if result["success"]:
        return f"Email sent successfully\nMessage ID: {result['message_id']}\nTo: {result['to']}"
    else:
        return f"Email failed: {result['error']['message']}"
```

### **4. Dual Mode Support**

```python
async def execute_tool(input_data: Any, config: dict) -> dict:
    """Execute tool with flexible input."""
    # Check if input is string (agent) or dict (direct)
    if isinstance(input_data, str):
        # Parse string input
        structured_input = parse_string_input(input_data)
    else:
        # Use structured input directly
        structured_input = input_data
    
    # Execute with structured input
    result = await perform_operation(structured_input, config)
    
    return result
```

---

## 🚀 Example: Email Tool Implementation

```python
# In tool_node.py

elif tool_type == "email":
    async def email_func_async(input_data: str) -> str:
        """Send an email."""
        # Parse input (string from agent or structured from node)
        if isinstance(input_data, str):
            # Parse: "to: email@example.com, subject: Hello, body: Message"
            email_data = parse_email_string(input_data)
        else:
            email_data = input_data
        
        # Get config
        provider = config.get("email_provider", "resend")
        api_key = config.get("resend_api_key", "")
        from_email = config.get("email_from", "")
        
        # Send email
        result = await send_email_via_resend(
            to=email_data.get("to"),
            subject=email_data.get("subject"),
            body=email_data.get("body"),
            from_email=from_email,
            api_key=api_key
        )
        
        # Format output for agent (string)
        if result["success"]:
            return f"Email sent successfully\nMessage ID: {result['message_id']}\nTo: {result['to']}"
        else:
            return f"Email failed: {result['error']}"
    
    # Wrapper for LangChain
    def email_func(input_data: str) -> str:
        return asyncio.run(email_func_async(input_data))
    
    return Tool(
        name=tool_name,
        func=email_func,
        description="Send an email. Input format: 'to: email@example.com, subject: Subject, body: Message body'"
    )
```

---

## 📝 Summary

1. **Tools accept both string (agent) and structured (direct) inputs**
2. **Tools return strings for agents, structured dicts for direct usage**
3. **All integrations follow the same pattern**
4. **Error handling is consistent across all tools**
5. **Metadata (timestamps, providers, etc.) is always included**

This design ensures:
- ✅ Agents can use tools naturally (string I/O)
- ✅ Workflows can use tools with structured data
- ✅ Consistent error handling
- ✅ Easy to add new integrations
- ✅ Clear data contracts

