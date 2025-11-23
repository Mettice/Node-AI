# NodAI Widget Usage

## Quick Start

The NodAI Widget is a React component that can be embedded in external websites to query deployed workflows.

## Installation

If using in a React project:

```tsx
import { NodAIWidget } from '@nodai/widget';
```

Or copy the component file directly into your project.

## Basic Usage

```tsx
<NodAIWidget
  apiKey="nk_your_api_key_here"
  workflowId="your-workflow-id"
  apiUrl="https://api.nodai.io"  // Optional: defaults to current origin
/>
```

## Props

- `apiKey` (required): Your NodAI API key
- `workflowId` (required): The ID of the deployed workflow
- `apiUrl` (optional): Base URL of the NodAI API (defaults to `window.location.origin`)
- `placeholder` (optional): Input placeholder text (default: "Ask a question...")
- `buttonText` (optional): Submit button text (default: "Send")
- `className` (optional): Additional CSS classes

## Example

```tsx
function MyApp() {
  return (
    <div>
      <h1>Ask our AI assistant</h1>
      <NodAIWidget
        apiKey="nk_a1b2c3d4..."
        workflowId="workflow-123"
        apiUrl="https://api.nodai.io"
        placeholder="What would you like to know?"
        buttonText="Ask"
      />
    </div>
  );
}
```

## Standalone HTML Usage

For non-React websites, you can build a standalone version or use an iframe wrapper.

## Styling

The widget includes basic styling but can be customized with the `className` prop or by overriding CSS classes.

