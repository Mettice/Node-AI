# Nodes Implementation Guide & Answers

## 1. Auto Chart Generator

### Current Issue
- **Problem**: Chart types show as "add item" array input instead of dropdown
- **Solution**: The schema is correct (array of enums), but frontend needs to render it as a multi-select dropdown

### How It Works
- Accepts data input (CSV, JSON, DataFrame, or text)
- Analyzes data structure (numerical, categorical, datetime columns)
- Automatically suggests appropriate chart types based on data
- Generates chart configurations and data for visualization
- Supports: scatter, line, bar, histogram, pie, box, heatmap, area, donut, violin, bubble

### Data Flow
- **Input**: Data from previous nodes (text_input, data_loader, etc.)
- **Output**: Chart configurations with data ready for visualization

---

## 2. Content Moderator

### Current Issues
1. **Categories**: Shows as "add item" instead of multi-select dropdown
2. **Image/Vision Support**: Currently placeholder - needs implementation
3. **HuggingFace Models**: Not integrated - should use HF models for better detection

### How It Works
- **Text Moderation**: Uses regex patterns for basic detection (needs improvement)
- **Image Moderation**: Placeholder - needs AI vision integration
- **Categories**: 
  - inappropriate_language
  - hate_speech (needs HF model)
  - spam
  - pii (Personal Identifiable Information)
  - violence (needs HF model)
  - harassment
  - adult_content (needs vision model)

### Custom Rules
- Users can define keyword or regex-based rules
- Each rule has: name, type (keyword/regex), pattern, action (warn/block)
- Rules are applied after category checks

### Recommended Improvements
1. **Integrate HuggingFace Models**:
   - `unitary/toxic-bert` for toxicity detection
   - `facebook/roberta-hate-speech-dynabench-r4-target` for hate speech
   - `martin-ha/toxic-comment-model` for general toxicity
2. **Add Vision Support**:
   - Use OpenAI Vision API or Google Vision API for image moderation
   - Or use HuggingFace image classification models
3. **Fix Frontend**: Make categories a multi-select dropdown

---

## 3. Meeting Summarizer

### Current Implementation
- **Uses LLM** (via LLMConfigMixin) for high-quality summarization
- **Falls back to pattern matching** if LLM is not available or fails
- **Hybrid approach**: LLM for summaries, pattern matching for structure extraction

### How It Works
- **LLM-Powered Summarization** (when API key configured):
  - Generates executive summaries using LLM (brief/standard/detailed styles)
  - Context-aware and high-quality summaries
  - Adapts to meeting content and style
- **Pattern Matching** (always used for structure):
  - Parses transcript by speaker segments
  - Extracts topics using keyword matching
  - Extracts action items using pattern matching (e.g., "TODO:", "Action:", "Will do")
  - Extracts decisions using keywords ("decided", "agreed", "approved")
  - Analyzes participant contributions
- **Output**:
  - Executive summary (LLM-generated or pattern-based)
  - Main topics discussed
  - Action items with owners and deadlines
  - Decisions made
  - Participant analysis
  - Follow-up recommendations

### LLM Configuration
- Uses LLMConfigMixin - supports OpenAI, Anthropic, Gemini
- Configure provider and API key in node settings
- If no API key: automatically falls back to pattern matching
- Temperature: Default 0.1 for consistent summaries

### Difference from Advanced NLP
- **Meeting Summarizer**: Specialized for meeting transcripts
  - Extracts action items with owners and deadlines
  - Identifies decisions with context
  - Tracks attendees and their contributions
  - Meeting-specific structure and formatting
  - Follow-up recommendations
- **Advanced NLP**: General-purpose NLP tasks
  - Sentiment analysis
  - Named entity recognition
  - Text classification
  - General summarization (not meeting-specific)

---

## 4. Stripe Analytics

### How It Works
- **API Connection**: Requires Stripe API key in config (uses vault integration)
- **Data Fetching**: 
  - **Automatic**: When API key is configured, node automatically fetches data from Stripe API on execution
  - **Manual Input**: Can also accept `stripe_data` input from previous nodes
  - **Analysis Period**: Configurable (7_days, 30_days, 90_days, 1_year)
- **What Gets Analyzed**:
  - Revenue trends and growth rates
  - Customer lifetime value (LTV)
  - Customer segments (high/medium/low value)
  - Subscription metrics (MRR, retention rate)
  - Churn patterns and at-risk customers
  - Revenue forecasting (30/60/90 day projections)
  - Business insights and recommendations

### Data Flow
1. **Input**: Stripe API key (from vault or direct entry)
2. **Execution**: 
   - Connects to Stripe API
   - Fetches transactions, customers, subscriptions for selected period
   - Analyzes data using statistical methods
   - Generates insights using AI (if LLM configured)
3. **Output**: Structured JSON with all analysis results

### Data Display/Preview
- **Current**: Returns structured JSON data
- **Recommended Frontend Display**:
  - Revenue trend charts (line/area charts)
  - Customer segment pie charts
  - Churn risk dashboard with customer list
  - Forecast graphs with confidence intervals
  - Business insights cards

### Implementation Status
- **Backend**: Structure in place, needs actual Stripe Python SDK integration
- **Frontend**: Needs data visualization components for charts and dashboards

---

## 5. Cost Optimizer

### How It Works
- **Platform Selection**: User selects cloud platform (AWS, GCP, Azure, Multi-Cloud) via dropdown
- **Data Input**: 
  - **Option 1**: Provide `cost_data` input from previous node (e.g., from cloud export file)
  - **Option 2**: Connect directly to cloud platform APIs (needs implementation)
- **What Gets Analyzed**:
  - Cost trends and patterns
  - Unused/underutilized resources
  - Right-sizing opportunities (over-provisioned instances)
  - Potential savings estimates
  - Cost allocation by service/resource

### Cloud Platform Connection
- **Current**: Expects `cost_data` input (doesn't connect directly yet)
- **Data Format Expected**:
  ```json
  {
    "services": {
      "EC2": 500.00,
      "S3": 100.00,
      "RDS": 300.00
    },
    "resources": [...],
    "period": {...}
  }
  ```
- **Future Implementation Needed**: 
  - AWS Cost Explorer API integration
  - GCP Billing API integration  
  - Azure Cost Management API integration
  - Cloud cost export file parser (CSV/JSON)

### Data Viewing/Preview
- **Current**: Returns optimization opportunities and recommendations as JSON
- **Recommended Frontend Display**:
  - Cost breakdown pie/bar chart by service
  - Optimization opportunities list with savings amounts
  - Cost trend line chart
  - Resource utilization heatmap
  - Savings potential summary card

### How Users Add Data
- **Method 1**: Connect previous node that exports cloud cost data
- **Method 2**: Upload cost export file (CSV/JSON) via file_loader node
- **Method 3**: (Future) Direct API connection with cloud credentials

---

## 6. Social Media Analyzer

### How It Works
- **Purpose**: **ANALYZES** social media posts (does NOT post - that's Social Scheduler)
- **Platform Selection**: User selects platforms to analyze (Twitter, LinkedIn, Facebook, Instagram) via multi-select dropdown
- **Analysis Types**: User selects what to analyze (sentiment, engagement, trends) via multi-select dropdown
- **Input**: Requires `social_data` array with post objects

### What Gets Analyzed
- **Sentiment Analysis**: Classifies posts as positive/negative/neutral
- **Engagement Metrics**: Analyzes likes, shares, comments, total engagement
- **Trend Identification**: Identifies trending topics and patterns
- **Top Performing Posts**: Ranks posts by engagement

### Data Input Format
- **Required Format**: Array of post objects:
  ```json
  [
    {
      "content": "Post text content",
      "likes": 100,
      "shares": 20,
      "comments": 15,
      "platform": "twitter",
      "author": "@username",
      "timestamp": "2024-01-15T10:00:00Z"
    }
  ]
  ```

### How Users Add Data
- **Method 1**: From Social Media API nodes (Twitter API, LinkedIn API, etc.)
- **Method 2**: From data collection nodes that fetch social media data
- **Method 3**: Manual input via JSON/text_input node
- **Method 4**: Import from CSV/JSON file via file_loader node

### Difference from Social Scheduler
- **Social Analyzer**: 
  - **Analyzes** existing posts
  - Reads data, performs sentiment/engagement analysis
  - Does NOT post or schedule content
- **Social Scheduler**: 
  - **Posts** new content
  - Schedules posts for future publication
  - Manages content calendar

---

## 7. AB Test Analyzer

### How It Works
- **Input**: Requires `test_data` object with control and treatment groups
- **Test Type Selection**: User selects test type (conversion, revenue, engagement) via dropdown
- **Confidence Level**: Configurable (default 95%)
- **Analysis**:
  - Statistical significance testing (z-test for proportions)
  - P-value calculation
  - Confidence intervals
  - Effect size analysis (absolute/relative lift)
  - Practical significance assessment
  - Winner determination
  - Actionable recommendations

### Data Input Format
- **Required Format**:
  ```json
  {
    "control": {
      "conversions": 100,
      "visitors": 1000
    },
    "treatment": {
      "conversions": 120,
      "visitors": 1000
    }
  }
  ```
- **For Revenue Tests**: Include revenue amounts instead of just conversions
- **For Engagement Tests**: Include engagement metrics

### How It Receives Data
- **Method 1**: From Analytics/Data Collection Nodes
  - Connect from nodes that track website/app analytics
  - Connect from experiment tracking systems
- **Method 2**: From Manual Input
  - Use text_input or JSON node to provide test results
- **Method 3**: From File Import
  - Import CSV/JSON export from analytics tools (Google Analytics, Mixpanel, etc.)
  - Use file_loader node to import test data

### Output
- **Statistical Analysis**:
  - Control vs Treatment rates
  - Lift percentage
  - Z-score and p-value
  - Confidence intervals
- **Winner Determination**: control / treatment / inconclusive
- **Recommendations**: 
  - Implement winner (if significant)
  - Continue test (if not significant)
  - Consider practical significance

### Use Cases
- Website conversion rate tests
- Email campaign A/B tests
- Feature flag experiments
- Pricing experiments
- UI/UX tests

---

## Summary of Required Fixes

### Frontend Fixes Needed
1. **Auto Chart Generator**: Render `chart_types` as multi-select dropdown
2. **Content Moderator**: Render `check_categories` as multi-select dropdown
3. **All Analytics Nodes**: Add data visualization/preview components

### Backend Improvements Needed
1. **Content Moderator**: 
   - Integrate HuggingFace models for hate speech/violence detection
   - Add image/vision moderation support
2. **Meeting Summarizer**: Add LLM support via LLMConfigMixin
3. **Stripe Analytics**: Implement actual Stripe API integration
4. **Cost Optimizer**: Add cloud platform API integrations

### Documentation Needed
- User guides for each node
- Data format specifications
- Integration examples

