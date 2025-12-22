# Intelligent Routing Fix - Email/Slack Data Flow

## Issues Fixed

### 1. **Email Node - Missing email_body**
**Problem:** Email node was checking for `email_body` but fallback routing only set `body`.

**Fix:**
- ✅ Email node now checks multiple input sources: `output`, `text`, `content`, `body`, `email_body`
- ✅ Fallback routing now maps `output` → both `body` AND `email_body`
- ✅ Also maps `text` → `body` and `email_body`
- ✅ Also maps `content` → `body` and `email_body`

### 2. **Slack Node - Missing message**
**Problem:** Similar issue - fallback routing wasn't mapping `output` to `message`.

**Fix:**
- ✅ Slack node now checks: `output`, `text`, `content`, `body`, `message`
- ✅ Fallback routing maps `output` → `message` and `text`

### 3. **Output Extraction**
**Problem:** Nested output structures like `{ "output": { "output": "text" } }` weren't being extracted.

**Fix:**
- ✅ Engine now properly extracts nested output structures
- ✅ Maps `output.output` → `output`, `body`, `content`, `text`
- ✅ Also extracts `summary` field for advanced_nlp nodes

### 4. **ExecutionOutputs - Expansion & Markdown**
**Problem:** Not all nodes were expandable, markdown wasn't rendering properly.

**Fix:**
- ✅ Better output detection for all node types (including `summary` field)
- ✅ Auto-expands nodes with substantial outputs (>200 chars)
- ✅ Proper markdown rendering (removes ##, **, etc. and formats correctly)

## How It Works Now

### Example: CrewAI → Email

**Before (Broken):**
```
CrewAI outputs: { "output": "Blog post content..." }
Email receives: { "output": "Blog post content..." }
Email checks: email_body? ❌ No
Error: "Missing required fields: email_body"
```

**After (Fixed):**
```
CrewAI outputs: { "output": "Blog post content..." }
Engine extracts: { "output": "...", "text": "...", "body": "...", "content": "..." }
Email receives: { "output": "...", "text": "...", "body": "...", "content": "..." }
Email checks: email_body? ✅ Found in body!
Email sends successfully ✅
```

### Data Flow Paths

1. **Source Node Output:**
   ```python
   { "output": "Hello world" }
   ```

2. **Engine Extraction (engine.py):**
   ```python
   available_data = {
       "output": "Hello world",
       "text": "Hello world",      # Auto-extracted
       "body": "Hello world",      # Auto-extracted for communication nodes
       "content": "Hello world"    # Auto-extracted
   }
   ```

3. **Intelligent Routing (if enabled):**
   - AI maps: `output` → `email_body` ✅
   - Or falls back to rule-based: `output` → `body` → `email_body` ✅

4. **Email Node Receives:**
   ```python
   inputs = {
       "output": "Hello world",
       "text": "Hello world",
       "body": "Hello world",      # ✅ Email finds this!
       "email_body": "Hello world" # ✅ Or this!
   }
   ```

5. **Email Node Checks (in order):**
   ```python
   body = (
       config.get("email_body") or      # From UI config
       inputs.get("email_body") or      # From intelligent routing
       inputs.get("body") or            # From fallback routing ✅
       inputs.get("content") or         # Alternative
       inputs.get("text") or            # Alternative
       inputs.get("output") or          # Direct ✅
       inputs.get("message")            # Alternative
   )
   ```

## Testing

### Test 1: CrewAI → Email
1. Create workflow: CrewAI Agent → Email
2. Configure Email: Set `email_from` and `resend_api_key` only
3. Leave `email_to`, `email_subject`, `email_body` empty
4. Run with intelligent routing ON
5. **Expected:** Email should send with CrewAI output as body ✅

### Test 2: Chat → Slack
1. Create workflow: Chat → Slack
2. Configure Slack: Set `slack_token_id` only
3. Leave `slack_channel` and `slack_message` empty
4. Run with intelligent routing ON
5. **Expected:** Slack should send with Chat output as message ✅

### Test 3: Advanced NLP → Email
1. Create workflow: Advanced NLP (summarization) → Email
2. Configure Email: Set `email_from` and `resend_api_key` only
3. Run with intelligent routing ON
4. **Expected:** Email should send with summary as body ✅

## Debugging

### Check Backend Logs

**If intelligent routing is working:**
```
✅ Intelligent routing for email-123 (email): Available=['output', 'text', 'body'], Routed=['email_body', 'body']
```

**If falling back to rule-based:**
```
📋 Rule-based routing for email-123: Available data keys: ['output', 'text', 'body', 'content']
```

**If intelligent routing failed:**
```
⚠️ Intelligent routing failed for node email-123, using rule-based: [error message]
```

### Check Frontend Console

When you click Run, you should see:
```javascript
[ExecutionControls] Workflow execution started {
  execution_id: "...",
  intelligent_routing: true,  // ✅ Should be true
  ...
}
```

## Common Issues

### Issue: "Missing required fields: email_body"
**Cause:** Output not being extracted or mapped correctly.

**Solution:**
1. Check backend logs to see what data is available
2. Verify source node is outputting data
3. Check if intelligent routing is enabled (should see ✅ in logs)
4. Verify email node checks multiple fields (already fixed)

### Issue: Intelligent routing not working
**Possible causes:**
1. **Missing API key:** Intelligent routing needs an LLM API key (OpenAI, Anthropic, or Gemini)
2. **Router not initialized:** Check logs for "Initialized intelligent router"
3. **Routing failed:** Check logs for ⚠️ warnings

**Solution:**
- Fallback routing should still work even if intelligent routing fails
- The fixes ensure fallback routing maps `output` → `body` → `email_body`

## Summary

✅ **Email node** now checks 7 different input sources for body content
✅ **Slack node** now checks 6 different input sources for message content  
✅ **Fallback routing** properly maps `output` → `body`/`email_body`/`message`
✅ **Engine extraction** properly handles nested output structures
✅ **Better logging** to debug routing issues

**Even if intelligent routing fails, the fallback routing should now work!** 🎉

