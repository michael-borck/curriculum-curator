import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LLMProviderFields } from './LLMProviderFields';
import { LLMProvider } from '../../types/llm';
import type { LLMConfigFormData } from '../../types/llm';

const renderWithProvider = (provider: LLMProvider) => {
  const formData: Partial<LLMConfigFormData> = { provider };
  return render(
    <LLMProviderFields
      formData={formData}
      onChange={vi.fn()}
      availableModels={[]}
      onRefreshModels={vi.fn()}
      onProviderChange={vi.fn()}
    />
  );
};

describe('LLMProviderFields data notice', () => {
  it('tells layperson users a cloud provider receives their text', () => {
    renderWithProvider(LLMProvider.OPENAI);
    expect(
      screen.getByText(/sent over the internet to OpenAI/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/An API key is like a password/i)
    ).toBeInTheDocument();
  });

  it('describes Ollama as not sending text to an online AI company', () => {
    renderWithProvider(LLMProvider.OLLAMA);
    expect(
      screen.getByText(/not to an online AI company/i)
    ).toBeInTheDocument();
  });

  it('describes a custom provider as the service at the entered address', () => {
    renderWithProvider(LLMProvider.CUSTOM);
    expect(
      screen.getByText(/sent to the service at the address you enter/i)
    ).toBeInTheDocument();
  });
});
