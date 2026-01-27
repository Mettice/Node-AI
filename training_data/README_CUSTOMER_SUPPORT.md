# Customer Support Fine-Tuning Dataset

## File: `customer_support_finetune.jsonl`

This file contains 20 training examples for fine-tuning a model on customer support and troubleshooting. Each example is in the chat format required for GPT-3.5-turbo and GPT-4 fine-tuning.

## How to Use

### Step 1: Upload the File

1. Open NodeAI and add a **Fine-Tune** node to your canvas
2. Click on the Fine-Tune node to open its properties
3. In the "Training File ID" field, click the **Upload** button
4. Select `customer_support_finetune.jsonl` from the `training_data` folder
5. The file ID will be automatically filled in

### Step 2: Configure Fine-Tuning

- **Provider**: OpenAI
- **Base Model**: `gpt-3.5-turbo` (recommended for cost) or `gpt-4` (better quality)
- **Model Name (Optional)**: "Customer Support Assistant" or your custom name
- **Validation Split**: 0.2 (20% for validation)
- **Epochs**: 3-5 (start with 3)
- **Batch Size**: Leave empty (auto)
- **Learning Rate**: Leave empty (auto)

### Step 3: Start Training

1. Click "Run" on your workflow
2. The fine-tuning job will start (this can take hours)
3. You'll get a `job_id` to track progress
4. Check OpenAI dashboard for training status

### Step 4: Use Your Fine-Tuned Model

Once training completes:

1. **In Chat Nodes**: 
   - Enable "Use Fine-Tuned Model"
   - Select your fine-tuned model from the dropdown
   - The model will now provide customer support responses using the training data

2. **In Support Workflows**:
   - Use the fine-tuned model in Chat nodes for customer support
   - Combine with RAG for knowledge base integration
   - Use in multi-agent workflows for complex support scenarios

## Example Support Workflow

```
Text Input (Customer Question)
  → Vector Search (Search Knowledge Base)
  → Chat (with fine-tuned Customer Support model)
  → Output (Helpful Response)
```

This gives you:
- **Retrieval**: Finds relevant information from your knowledge base
- **Generation**: Uses fine-tuned model that understands customer support best practices

## Training Data Format

Each line in the JSONL file is a JSON object with this format:

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful and empathetic customer support assistant..."},
    {"role": "user", "content": "I can't log into my account. What should I do?"},
    {"role": "assistant", "content": "I'm sorry you're having trouble logging in. Let's try these steps..."}
  ]
}
```

## Topics Covered

The training data includes questions and answers about:
- Account login and password issues
- Payment and billing problems
- Subscription management
- Technical troubleshooting
- Security and account recovery
- File management and recovery
- Account settings and preferences
- Service availability issues
- Data export and privacy
- Mobile app support
- Email notifications
- File sharing
- System requirements
- And more common support scenarios!

## Use Cases

This fine-tuned model is perfect for:
- **Customer Support Chatbots**: Automated support that's empathetic and helpful
- **Help Desk Systems**: First-line support that can handle common issues
- **FAQ Systems**: Intelligent responses to frequently asked questions
- **Self-Service Portals**: Help customers resolve issues independently
- **Support Ticket Routing**: Understand customer issues and route appropriately

## Next Steps

After fine-tuning:
1. Test your model with various customer support questions
2. Use it in Chat nodes for automated support
3. Integrate it into RAG workflows for enhanced knowledge base support
4. Consider adding more training examples specific to your business
5. Combine with your company's knowledge base for domain-specific support

## Cost Estimate

- 20 examples × ~600 tokens × 3 epochs ≈ **$0.30** (very affordable!)
- Training time: 1-3 hours depending on OpenAI queue

## Customization Tips

To make this model even better for your business:
1. Add examples specific to your product/service
2. Include your company's support policies and procedures
3. Add examples with your brand voice and tone
4. Include common issues specific to your industry
5. Add examples for your specific product features
