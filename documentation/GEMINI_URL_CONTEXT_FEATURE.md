# 🌐 Google Gemini URL Context Integration

## Overview

Nodeflow now supports **Google's URL Context** feature, allowing you to extract data from any webpage, PDF, or image directly in your prompts - **no scraping tools needed!**

## 🎯 What is URL Context?

URL Context is a built-in Gemini capability that:
- ✅ Fetches live data from up to **20 URLs per request**
- ✅ Works with **webpages, PDFs, and images**
- ✅ **No tools or scraper setup** required
- ✅ You only pay for tokens (not per URL fetch)
- ✅ Automatically extracts and processes content

## 🚀 How to Use

### **Option 1: Enable URL Context in Chat Node**

1. **Add a Chat Node** to your workflow
2. **Select Gemini** as the provider
3. **Enable "Enable URL Context"** toggle
4. **Add URLs** to the "URLs to Analyze" field (or include them in your prompt)
5. **Include URLs in your prompt** - Gemini will automatically fetch them!

### **Example Workflow:**

```
Text Input → Chat (Gemini with URL Context) → Output
```

**Prompt Example:**
```
Compare the ingredients and cooking times from the recipes at:
https://www.allrecipes.com/recipe/21151/simple-whole-roast-chicken/
```

**Result:** Gemini automatically fetches the webpage, extracts the recipe data, and compares it!

---

## 📋 Configuration Options

### **Chat Node Settings:**

- **Enable URL Context**: Toggle to enable URL Context tool
- **URLs to Analyze**: List of URLs (up to 20) - optional, can also include URLs directly in prompt
- **Gemini Model**: Select model (gemini-2.5-flash recommended)

---

## 💡 Use Cases

### **1. Recipe Comparison**
```
Prompt: "Compare the ingredients and cooking times from:
https://recipe-site-1.com/chicken
https://recipe-site-2.com/chicken"
```

### **2. Research & Analysis**
```
Prompt: "Summarize the key findings from:
https://research-paper-1.pdf
https://research-paper-2.pdf"
```

### **3. Price Comparison**
```
Prompt: "Compare prices for iPhone 15 from:
https://store-1.com/iphone-15
https://store-2.com/iphone-15"
```

### **4. Document Analysis**
```
Prompt: "Extract the main points from:
https://company.com/annual-report.pdf"
```

### **5. GitHub Repo Analysis**
```
Prompt: "Analyze the documentation and code structure from:
https://github.com/user/repo"
```

---

## 🔧 Technical Details

### **How It Works:**

1. **Enable URL Context**: Adds `{"url_context": {}}` tool to Gemini request
2. **Include URLs**: URLs can be:
   - Added to "URLs to Analyze" field
   - Included directly in the prompt text
3. **Automatic Fetching**: Gemini automatically fetches and processes URLs
4. **Content Extraction**: Extracts text, images, PDFs, etc.
5. **Response**: Returns analyzed content based on your prompt

### **API Integration:**

```python
# In Chat Node with Gemini
config = {
    "provider": "gemini",
    "gemini_model": "gemini-2.5-flash",
    "gemini_use_url_context": True,
    "gemini_url_context_urls": [
        "https://example.com/page1",
        "https://example.com/page2"
    ]
}

# Or include URLs directly in prompt:
prompt = "Analyze: https://example.com/page"
```

---

## ⚠️ Limitations

- **Max 20 URLs** per request
- **Only works with Gemini** provider
- **Requires Gemini API key**
- **Rate limits** apply (based on Gemini API limits)
- **Token costs** - you pay for tokens used, not per URL

---

## 🆚 URL Context vs Web Scraping Tool

| Feature | URL Context | Web Scraping Tool |
|---------|-------------|-------------------|
| **Setup** | No setup needed | Requires BeautifulSoup, httpx |
| **Provider** | Gemini only | Any provider |
| **URLs** | Up to 20 per request | 1 at a time |
| **Cost** | Token-based | Free (your server) |
| **PDFs/Images** | ✅ Supported | ❌ Not supported |
| **Ease of Use** | ✅ Very easy | ⚠️ Requires configuration |

**Recommendation**: Use **URL Context** for quick research and analysis. Use **Web Scraping Tool** for custom extraction or when not using Gemini.

---

## 📝 Example Workflows

### **Workflow 1: Multi-Source Research**

```
Text Input (research topic)
    ↓
Chat (Gemini + URL Context)
    - URLs: [research-paper-1.pdf, research-paper-2.pdf, article-1.com]
    - Prompt: "Summarize key findings from these sources"
    ↓
Output (consolidated summary)
```

### **Workflow 2: Competitive Analysis**

```
Text Input (product name)
    ↓
Chat (Gemini + URL Context)
    - URLs: [competitor-1.com/product, competitor-2.com/product]
    - Prompt: "Compare features and prices"
    ↓
Output (comparison report)
```

### **Workflow 3: Document Q&A**

```
Text Input (question)
    ↓
Chat (Gemini + URL Context)
    - URLs: [document.pdf]
    - Prompt: "{question} - Answer based on the document"
    ↓
Output (answer)
```

---

## 🎯 Best Practices

1. **Include URLs in prompt** for better context
2. **Limit to 20 URLs** per request
3. **Use descriptive prompts** - tell Gemini what to extract
4. **Combine with other tools** - URL Context + File Search for comprehensive analysis
5. **Monitor token usage** - URL Context increases token consumption

---

## 🔗 Related Features

- **Gemini File Search**: For RAG with uploaded files
- **Web Scraping Tool**: For custom web scraping (non-Gemini)
- **Vector Search**: For semantic search across documents

---

## 📚 Resources

- [Google Gemini URL Context Documentation](https://ai.google.dev/gemini-api/docs/url-context)
- [Gemini API Reference](https://ai.google.dev/api)
- [Nodeflow Chat Node Documentation](./NODE_DOCUMENTATION.md)

---

**Last Updated**: January 2025

