/**
 * Selecting a provider in a node's settings shows that provider's model dropdown,
 * and only providers the node's backend supports are offered.
 */

import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen, userEvent } from '@/test/utils';
import { SchemaForm } from '@/components/Properties/SchemaForm';

// Mirrors the schema LLMConfigMixin nodes (blog_generator, lead_scorer, ...) serve
const llmNodeSchema = {
  type: 'object',
  properties: {
    provider: { type: 'string', enum: ['openai', 'anthropic', 'gemini'], default: 'openai', title: 'Provider' },
    model: { type: 'string', default: 'gpt-4o-mini', title: 'Model' },
    openai_model: { type: 'string', enum: ['gpt-4o-mini', 'gpt-5.6-sol'], default: 'gpt-4o-mini', title: 'OpenAI Model' },
    anthropic_model: { type: 'string', enum: ['claude-sonnet-5', 'claude-haiku-4-5-20251001'], default: 'claude-sonnet-5', title: 'Anthropic Model' },
    gemini_model: { type: 'string', enum: ['gemini-2.5-flash', 'gemini-3.8-flash'], default: 'gemini-2.5-flash', title: 'Gemini Model' },
  },
};

// Mirrors the Transcribe node schema
const transcribeSchema = {
  type: 'object',
  properties: {
    provider: { type: 'string', enum: ['openai', 'local'], default: 'openai', title: 'Provider' },
    openai_model: { type: 'string', enum: ['whisper-1', 'gpt-transcribe'], default: 'whisper-1', title: 'OpenAI Model' },
    local_model: { type: 'string', enum: ['base', 'tiny', 'large'], default: 'base', title: 'Local Whisper Model' },
  },
};

function renderForm(schema: Record<string, unknown>, nodeType: string) {
  const onChange = vi.fn();
  renderWithProviders(<SchemaForm schema={schema} nodeType={nodeType} initialData={{}} onChange={onChange} />);
  return onChange;
}

async function chooseProvider(currentLabel: string, nextLabel: string) {
  const user = userEvent.setup();
  await user.click(screen.getByText(currentLabel, { selector: 'span' }).closest('button')!);
  await user.click(screen.getByText(nextLabel, { selector: 'span' }).closest('button')!);
}

describe('SchemaForm provider and model fields', () => {
  it("shows the default provider's model dropdown and hides the others", () => {
    renderForm(llmNodeSchema, 'blog_generator');
    expect(screen.getByText('OpenAI Model')).toBeInTheDocument();
    expect(screen.queryByText('Anthropic Model')).not.toBeInTheDocument();
    expect(screen.queryByText('Gemini Model')).not.toBeInTheDocument();
    // The generic free-text "model" field is hidden once a provider-specific one applies
    expect(screen.queryByText('Model', { selector: 'label' })).not.toBeInTheDocument();
  });

  it("offers only the providers in the node's schema", async () => {
    renderForm(llmNodeSchema, 'blog_generator');
    const user = userEvent.setup();
    await user.click(screen.getByText('OpenAI', { selector: 'span' }).closest('button')!);
    expect(screen.getByText('Anthropic', { selector: 'span' })).toBeInTheDocument();
    expect(screen.getByText('Google Gemini', { selector: 'span' })).toBeInTheDocument();
    expect(screen.queryByText('Azure OpenAI')).not.toBeInTheDocument();
  });

  it("switching provider shows that provider's models", async () => {
    renderForm(llmNodeSchema, 'blog_generator');
    await chooseProvider('OpenAI', 'Anthropic');
    expect(screen.getByText('Anthropic Model')).toBeInTheDocument();
    expect(screen.queryByText('OpenAI Model')).not.toBeInTheDocument();

    // Open the Anthropic model dropdown: it lists Anthropic's models only
    const user = userEvent.setup();
    const modelField = screen.getByText('Anthropic Model').parentElement!;
    await user.click(modelField.querySelector('button')!);
    const listed = Array.from(modelField.querySelectorAll('button span.flex-1')).map((el) => el.textContent);
    expect(listed).toHaveLength(2);
    expect(listed.join(' ')).toMatch(/Sonnet 5/i);
    expect(listed.join(' ')).not.toMatch(/gpt|gemini/i);
  });

  it('transcribe: choosing Local shows the local Whisper model sizes', async () => {
    renderForm(transcribeSchema, 'transcribe');
    expect(screen.getByText('OpenAI Model')).toBeInTheDocument();
    expect(screen.queryByText('Local Whisper Model')).not.toBeInTheDocument();

    await chooseProvider('OpenAI', 'Local');
    expect(screen.getByText('Local Whisper Model')).toBeInTheDocument();
    expect(screen.queryByText('OpenAI Model')).not.toBeInTheDocument();
  });
});
