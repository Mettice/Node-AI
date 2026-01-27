# Fine-Tuning Guide

## Overview

The Fine-Tune node allows you to customize LLM models (like GPT-3.5-turbo or GPT-4) with your own training data. This is useful for:
- **Domain-specific knowledge**: Train models on legal, medical, or technical documents
- **Custom behavior**: Teach models to respond in specific formats or styles
- **Brand voice**: Make models match your company's communication style

## How Fine-Tuning Works

### 1. **Training Data Format**

Your training data must be in one of two formats:

#### Chat Format (Recommended for GPT-3.5-turbo/GPT-4)
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is NodeAI?"},
    {"role": "assistant", "content": "NodeAI is a visual workflow platform..."}
  ]
}
```

#### Completion Format (Legacy)
```json
{
  "prompt": "What is NodeAI?",
  "completion": "NodeAI is a visual workflow platform..."
}
```

### 2. **Adding Training Data**

You have **two ways** to provide training data:

#### Option A: From Previous Node (Recommended)
1. Connect a node that outputs an array of training examples (e.g., data_loader, file_loader)
2. The finetune node will automatically receive the data via the `data` input
3. The data will be validated and converted to the correct format

**Example Workflow:**
```
File Loader (JSONL) → Fine-Tune Node
```

#### Option B: Upload Training File
1. Upload a JSONL file (one JSON object per line) to your server
2. Enter the file ID in the "Training File ID" field
3. The node will load the file automatically

**File Format Example (JSONL):**
```
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]}
{"messages": [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI is..."}]}
```

### 3. **Configuration Options**

- **Provider**: Currently supports OpenAI (Anthropic coming soon)
- **Base Model**: Choose `gpt-3.5-turbo` or `gpt-4` (gpt-3.5-turbo is cheaper and faster)
- **Validation Split**: Percentage of data to use for validation (0.0 to 1.0, default: 0.2 = 20%)
- **Epochs**: Number of training passes (1-50, default: 3)
  - More epochs = better training but higher cost
  - Start with 3-5 epochs
- **Batch Size**: (Optional) Leave empty for auto
- **Learning Rate**: (Optional) Leave empty for auto

### 4. **Training Process**

1. **Data Validation**: The node validates your training data format
2. **Data Split**: If validation_split > 0, data is split into training and validation sets
3. **File Upload**: Training data is uploaded to OpenAI
4. **Job Creation**: Fine-tuning job is created and returns a `job_id`
5. **Async Training**: Training happens on OpenAI's servers (can take hours)

### 5. **Using Fine-Tuned Models**

After training completes:
1. The fine-tuned model ID will be available in the job output
2. Use the model in Chat nodes by:
   - Enabling "Use Fine-Tuned Model"
   - Selecting your fine-tuned model from the dropdown
3. The model will behave according to your training data

## Example Workflows

### Workflow 1: Customer Support Bot
```
1. Data Loader → Load customer support conversations (JSONL)
2. Fine-Tune → Train on support style and knowledge
3. Chat → Use fine-tuned model for support
```

### Workflow 2: Legal Document Analysis
```
1. File Loader → Load legal Q&A pairs
2. Fine-Tune → Train on legal terminology
3. Chat → Use for legal document analysis
```

## Best Practices

1. **Data Quality**: Use high-quality, consistent training examples
2. **Data Quantity**: Minimum 10 examples, recommended 50-100+ for good results
3. **Validation Split**: Use 10-20% for validation to monitor training quality
4. **Epochs**: Start with 3 epochs, increase if needed (but watch costs)
5. **Cost**: Fine-tuning costs ~$0.008 per 1K tokens. A 100-example dataset might cost $5-20

## Troubleshooting

**Error: "No training data provided"**
- Make sure you either:
  - Connected a node with data output, OR
  - Provided a training_file_id

**Error: "Training example must have 'messages' or 'prompt'/'completion'"**
- Check your data format matches one of the supported formats
- For chat models, use the `messages` format

**Error: "OpenAI API key not found"**
- Add your OpenAI API key in the node settings or Secrets Vault

## Cost Estimation

The node estimates training costs based on:
- Number of training examples
- Base model selected
- Number of epochs

Example: 100 examples × 500 tokens × 3 epochs ≈ $1.20

## Next Steps

After training starts:
1. Monitor job status using the `job_id`
2. Wait for training to complete (check OpenAI dashboard)
3. Use the fine-tuned model in your Chat nodes
