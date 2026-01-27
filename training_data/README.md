# NodeAI Documentation Fine-Tuning Dataset

## File: `nodeai_docs_finetune.jsonl`

This file contains 20 training examples for fine-tuning a model on NodeAI documentation. Each example is in the chat format required for GPT-3.5-turbo and GPT-4 fine-tuning.

## How to Use

### Step 1: Upload the File

1. Open NodeAI and add a **Fine-Tune** node to your canvas
2. Click on the Fine-Tune node to open its properties
3. In the "Training File ID" field, click the **Upload** button
4. Select `nodeai_docs_finetune.jsonl` from the `training_data` folder
5. The file ID will be automatically filled in

### Step 2: Configure Fine-Tuning

- **Provider**: OpenAI
- **Base Model**: `gpt-3.5-turbo` (recommended for cost) or `gpt-4` (better quality)
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
   - The model will now answer questions about NodeAI using the training data

2. **In RAG Systems**:
   - Fine-tuned models work great in the **generation step** of RAG
   - Build your RAG workflow: File Loader → Chunk → Embed → Vector Store → Vector Search → **Chat (with fine-tuned model)**
   - The fine-tuned model will generate responses using both:
     - Retrieved context from your knowledge base
     - Its training on NodeAI documentation

## Example RAG Workflow with Fine-Tuned Model

```
File Loader (NodeAI docs) 
  → Chunk 
  → Embed 
  → Vector Store 
  → Vector Search 
  → Chat (with fine-tuned NodeAI model)
```

This gives you:
- **Retrieval**: Finds relevant docs from your knowledge base
- **Generation**: Uses fine-tuned model that understands NodeAI terminology and features

## Training Data Format

Each line in the JSONL file is a JSON object with this format:

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant specialized in NodeAI..."},
    {"role": "user", "content": "What is NodeAI?"},
    {"role": "assistant", "content": "NodeAI is a visual, no-code platform..."}
  ]
}
```

## Topics Covered

The training data includes questions and answers about:
- What NodeAI is and its key features
- How to build RAG systems
- Available node types
- Data flow between nodes
- Fine-tuning models
- LLM providers supported
- Multi-agent workflows
- Hybrid retrieval
- Cost tracking
- File formats
- RAG evaluation
- Vector databases
- External integrations
- Deployment options
- Embedding providers
- Document analysis
- Agent Lightning
- Performance monitoring
- And more!

## Next Steps

After fine-tuning:
1. Test your model with various NodeAI questions
2. Use it in Chat nodes for NodeAI-specific support
3. Integrate it into RAG workflows for enhanced generation
4. Consider adding more training examples for better coverage

## Cost Estimate

- 20 examples × ~500 tokens × 3 epochs ≈ **$0.24** (very affordable!)
- Training time: 1-3 hours depending on OpenAI queue
