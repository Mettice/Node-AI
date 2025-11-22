# Frontend Phase 3: Properties & Configuration

**Duration:** 2-3 days  
**Status:** 📋 Not Started  
**Prerequisites:** [Frontend Phase 2: Canvas & Nodes](./FRONTEND_PHASE_2_CANVAS.md)

---

## 🎯 Goals

- Create properties panel for node configuration
- Build dynamic form generator from node schemas
- Implement provider selection for generic nodes
- Add node testing functionality
- Real-time form validation

---

## 📋 Tasks

### 1. Properties Panel Component

#### 1.1 Properties Panel (`src/components/Properties/PropertiesPanel.tsx`)

- [ ] Panel layout
  - Show when node is selected
  - Hide when no node selected
  - Show "Select a node" message when empty
  - Collapsible (optional)

- [ ] Panel header
  - Node name and icon
  - Node type
  - Close button (optional)

- [ ] Panel body
  - Dynamic form based on schema
  - Provider selector (for generic nodes)
  - Test node button
  - Output preview section

- [ ] Connect to store
  - Read selected node from store
  - Update node data on form change
  - Auto-save (debounced)

#### 1.2 Empty State (`src/components/Properties/EmptyState.tsx`)

- [ ] Empty state component
  - Icon
  - Message: "Select a node to configure"
  - Helpful hint

---

### 2. Schema Form Generator

#### 2.1 Schema Form Component (`src/components/Properties/SchemaForm.tsx`)

- [ ] Fetch node schema
  - Call `/api/v1/nodes/{node_type}` API
  - Parse JSON schema
  - Handle loading/error states

- [ ] Generate form fields
  - Parse schema properties
  - Create appropriate input components
  - Handle nested objects
  - Handle arrays

- [ ] Form state management
  - Use React Hook Form
  - Initialize with node data
  - Update node data on change
  - Debounce updates

#### 2.2 Form Field Component (`src/components/Properties/FormField.tsx`)

- [ ] Support different field types:
  - `string` → Text input
  - `number` / `integer` → Number input
  - `boolean` → Checkbox
  - `enum` → Select dropdown
  - `array` → Array input (add/remove items)
  - `object` → Nested form (collapsible)

- [ ] Field features
  - Label
  - Description/help text
  - Required indicator
  - Validation errors
  - Placeholder text
  - Default values

#### 2.3 Provider Selector (`src/components/Properties/ProviderSelector.tsx`)

- [ ] Provider dropdown
  - Show available providers for generic nodes
  - Update form fields based on provider
  - Clear provider-specific fields on change

- [ ] Provider-specific configs
  - Show/hide fields based on provider
  - Load provider-specific schema
  - Validate provider-specific fields

- [ ] Provider mapping
  - `embed` node: OpenAI, HuggingFace, Cohere
  - `vector_store` node: FAISS, Pinecone
  - `vector_search` node: FAISS, Pinecone
  - `chat` node: OpenAI, Anthropic

---

### 3. Form Validation

#### 3.1 Schema Validation (`src/utils/validation.ts`)

- [ ] Convert JSON Schema to Zod schema
  - Parse JSON Schema
  - Generate Zod schema
  - Handle all field types
  - Handle nested schemas

- [ ] Validation rules
  - Required fields
  - Type validation
  - Enum validation
  - Min/max values
  - String patterns (regex)

#### 3.2 Real-time Validation

- [ ] Form validation
  - Validate on input change
  - Show validation errors
  - Highlight invalid fields
  - Prevent submission if invalid

- [ ] Error display
  - Show error message below field
  - Red border on invalid fields
  - Error icon
  - Clear errors on fix

---

### 4. Node Testing

#### 4.1 Node Test Panel (`src/components/Properties/NodeTestPanel.tsx`)

- [ ] Test button
  - "Test Node" button in properties panel
  - Disabled if node not configured
  - Loading state during test

- [ ] Sample input generator
  - Generate sample inputs based on node type
  - Allow manual input override
  - Show input preview

- [ ] Test execution
  - Call test endpoint (if available)
  - Or: Execute single node with sample inputs
  - Show loading state
  - Handle errors

- [ ] Results display
  - Show output preview
  - Show execution time
  - Show cost (if applicable)
  - Expandable JSON viewer
  - Copy to clipboard

#### 4.2 Test Input Form (`src/components/Properties/TestInputForm.tsx`)

- [ ] Input form
  - Generate inputs based on node input schema
  - Allow manual editing
  - Save test inputs (localStorage)

- [ ] Input types
  - Text input
  - Number input
  - File upload (if applicable)
  - JSON input (for complex types)

---

### 5. Output Preview

#### 5.1 Output Preview Component (`src/components/Properties/OutputPreview.tsx`)

- [ ] Preview display
  - Show node output structure
  - Format based on output type
  - Expandable sections

- [ ] Output types
  - Text → Plain text display
  - JSON → JSON viewer with syntax highlighting
  - Array → List display
  - Object → Key-value display

- [ ] Output actions
  - Copy to clipboard
  - Download as JSON
  - Expand/collapse sections

#### 5.2 JSON Viewer (`src/components/Properties/JSONViewer.tsx`)

- [ ] JSON display
  - Syntax highlighting
  - Expandable/collapsible nodes
  - Search functionality (optional)
  - Copy value on click

---

### 6. Form Field Components

#### 6.1 Text Input (`src/components/Properties/fields/TextInput.tsx`)

- [ ] Text input field
  - Standard text input
  - Textarea for long text
  - Character count (if maxLength)
  - Placeholder

#### 6.2 Number Input (`src/components/Properties/fields/NumberInput.tsx`)

- [ ] Number input field
  - Number input with validation
  - Min/max constraints
  - Step increment
  - Unit display (if applicable)

#### 6.3 Select Input (`src/components/Properties/fields/SelectInput.tsx`)

- [ ] Select dropdown
  - Options from enum
  - Searchable (if many options)
  - Clear selection
  - Placeholder

#### 6.4 Checkbox Input (`src/components/Properties/fields/CheckboxInput.tsx`)

- [ ] Checkbox field
  - Toggle checkbox
  - Label
  - Description

#### 6.5 Array Input (`src/components/Properties/fields/ArrayInput.tsx`)

- [ ] Array field
  - Add/remove items
  - Reorder items (drag-drop optional)
  - Item validation
  - Empty state

#### 6.6 Object Input (`src/components/Properties/fields/ObjectInput.tsx`)

- [ ] Nested object field
  - Collapsible section
  - Nested form fields
  - Indentation
  - Add/remove nested properties (if dynamic)

---

### 7. Provider-Specific Forms

#### 7.1 Embed Node Forms

- [ ] OpenAI form
  - Model dropdown
  - Dimensions (if applicable)
  - Other OpenAI-specific fields

- [ ] HuggingFace form
  - Model name input
  - Device selection
  - Other HuggingFace-specific fields

- [ ] Cohere form
  - Model dropdown
  - Other Cohere-specific fields

#### 7.2 Vector Store Node Forms

- [ ] FAISS form
  - Index type dropdown
  - Persist toggle
  - File path (if persist)

- [ ] Pinecone form
  - Index name
  - Environment
  - Region
  - Other Pinecone-specific fields

#### 7.3 Chat Node Forms

- [ ] OpenAI form
  - Model dropdown
  - Temperature slider
  - Max tokens
  - System prompt
  - User prompt template

- [ ] Anthropic form
  - Model dropdown
  - Temperature slider
  - Max tokens
  - System prompt
  - User prompt template

---

### 8. Form State Management

#### 8.1 Update Workflow Store

- [ ] Add form actions
  - `updateNodeConfig(nodeId, config)` - Update node config
  - `updateNodeData(nodeId, data)` - Update node data
  - Auto-save on change (debounced)

- [ ] Form synchronization
  - Load node data into form
  - Update store on form change
  - Sync with canvas node

---

### 9. Advanced Features (Optional)

#### 9.1 Form Templates

- [ ] Save form templates
  - Save common configurations
  - Load templates
  - Share templates

#### 9.2 Form History

- [ ] Undo/redo
  - Track form changes
  - Undo last change
  - Redo change

#### 9.3 Form Validation Rules

- [ ] Custom validation
  - Cross-field validation
  - Conditional validation
  - Custom error messages

---

## ✅ Deliverables Checklist

- [ ] Properties panel displays when node selected
- [ ] Dynamic form generated from schema
- [ ] All field types supported
- [ ] Provider selection works for generic nodes
- [ ] Form validation works
- [ ] Node data updates on form change
- [ ] Node testing works
- [ ] Output preview displays correctly
- [ ] Form errors display correctly
- [ ] Auto-save works

---

## 🧪 Testing Checklist

- [ ] Can configure text input node
- [ ] Can configure chunk node (all strategies)
- [ ] Can configure embed node (all providers)
- [ ] Can configure vector store node (all providers)
- [ ] Can configure chat node (all providers)
- [ ] Form validation works
- [ ] Invalid inputs show errors
- [ ] Node testing works
- [ ] Output preview shows results
- [ ] Config changes reflect on canvas node

---

## 📝 Notes

- Start with simple nodes (text_input)
- Add complex nodes incrementally
- Test each provider separately
- Keep forms simple and intuitive
- Add advanced features later

---

## 🔗 Related Files

- `frontend/src/components/Properties/PropertiesPanel.tsx` - Main panel
- `frontend/src/components/Properties/SchemaForm.tsx` - Form generator
- `frontend/src/components/Properties/FormField.tsx` - Field component
- `frontend/src/components/Properties/ProviderSelector.tsx` - Provider selector
- `frontend/src/components/Properties/NodeTestPanel.tsx` - Test panel
- `frontend/src/utils/validation.ts` - Validation utilities

---

## ➡️ Next Phase

Once Phase 3 is complete, proceed to [Frontend Phase 4: Execution & Real-time](./FRONTEND_PHASE_4_EXECUTION.md)

