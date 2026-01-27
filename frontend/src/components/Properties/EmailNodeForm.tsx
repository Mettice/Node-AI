/**
 * Enhanced Email Node Form Component
 * Provides a better UX than the generic SchemaForm for email operations
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { APIKeyInput } from './APIKeyInput';
import { testEmailConnection } from '@/services/nodes';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { Mail, Send } from 'lucide-react';

interface EmailNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema: Record<string, any>;
}

const EMAIL_PROVIDERS = [
  { value: 'resend', label: 'Resend', icon: 'resend' },
];

const EMAIL_TYPES = [
  { value: 'text', label: 'Plain Text', icon: 'api' },
  { value: 'html', label: 'HTML', icon: 'api' },
];

export function EmailNodeForm({ initialData, onChange, schema }: EmailNodeFormProps) {
  const [provider, setProvider] = useState(initialData.email_provider || 'resend');
  const [apiKey, setApiKey] = useState(initialData.resend_api_key || '');
  const [fromEmail, setFromEmail] = useState(initialData.email_from || '');
  const [fromName, setFromName] = useState(initialData.email_from_name || '');
  const [replyTo, setReplyTo] = useState(initialData.email_reply_to || '');
  const [toEmail, setToEmail] = useState(initialData.email_to || '');
  const [cc, setCc] = useState(initialData.email_cc || '');
  const [bcc, setBcc] = useState(initialData.email_bcc || '');
  const [subject, setSubject] = useState(initialData.email_subject || '');
  const [emailType, setEmailType] = useState(initialData.email_type || 'text');
  const [body, setBody] = useState(initialData.email_body || '');
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionError, setConnectionError] = useState<string>('');
  
  const onChangeRef = useRef(onChange);
  
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent when form changes
  useEffect(() => {
    const config: Record<string, any> = {
      email_provider: provider,
      resend_api_key: apiKey,
      email_from: fromEmail,
      email_type: emailType,
    };

    if (fromName) config.email_from_name = fromName;
    if (replyTo) config.email_reply_to = replyTo;
    if (toEmail) config.email_to = toEmail;
    if (cc) config.email_cc = cc;
    if (bcc) config.email_bcc = bcc;
    if (subject) config.email_subject = subject;
    if (body) config.email_body = body;

    onChangeRef.current(config);
  }, [provider, apiKey, fromEmail, fromName, replyTo, toEmail, cc, bcc, subject, emailType, body]); // Removed onChange from dependencies

  const handleTestConnection = async () => {
    if (!apiKey) {
      setConnectionError('Please enter Resend API key');
      setConnectionStatus('error');
      return;
    }

    setConnectionStatus('testing');
    setConnectionError('');

    try {
      const result = await testEmailConnection(provider, apiKey);
      if (result) {
        setConnectionStatus('success');
        setConnectionError('');
      } else {
        setConnectionStatus('error');
        setConnectionError('Connection test failed');
      }
    } catch (error: any) {
      setConnectionStatus('error');
      setConnectionError(error.message || 'Connection test failed');
    }
  };

  return (
    <div className="space-y-4">
      {/* Provider Selector */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Email Provider <span className="text-red-400">*</span>
        </label>
        <SelectWithIcons
          value={provider}
          onChange={setProvider}
          options={EMAIL_PROVIDERS}
          placeholder="Select provider..."
        />
      </div>

      {/* API Key and Connection */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="resend" size="sm" />
          <h3 className="text-sm font-semibold text-white">Resend Configuration</h3>
        </div>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            API Key <span className="text-red-400">*</span>
          </label>
          <APIKeyInput
            value={apiKey}
            onChange={setApiKey}
            placeholder="Enter Resend API key..."
            label=""
            description=""
            serviceName="Resend"
            testConnection={undefined}
          />
        </div>

        {/* Test Connection Button */}
        <button
          type="button"
          onClick={handleTestConnection}
          disabled={connectionStatus === 'testing' || !apiKey}
          className="w-full px-3 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-all text-sm font-medium"
        >
          {connectionStatus === 'testing' ? 'Testing...' : 'Test Connection'}
        </button>

        {/* Connection Status */}
        {connectionStatus === 'success' && (
          <div className="text-xs text-green-400 flex items-center gap-1">
            <span>✓</span> Connection successful
          </div>
        )}
        {connectionStatus === 'error' && connectionError && (
          <div className="text-xs text-red-400 flex items-center gap-1">
            <span>✗</span> {connectionError}
          </div>
        )}
      </div>

      {/* From Email Configuration */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Mail className="w-4 h-4" />
          Sender Configuration
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            From Email <span className="text-red-400">*</span>
          </label>
          <input
            type="email"
            value={fromEmail}
            onChange={(e) => setFromEmail(e.target.value)}
            placeholder="noreply@example.com"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            From Name (Optional)
          </label>
          <input
            type="text"
            value={fromName}
            onChange={(e) => setFromName(e.target.value)}
            placeholder="NodAI Team"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Reply-To Email (Optional)
          </label>
          <input
            type="email"
            value={replyTo}
            onChange={(e) => setReplyTo(e.target.value)}
            placeholder="support@example.com"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Email Content */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Send className="w-4 h-4" />
          Email Content
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            To Email <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Recipient email (can also come from previous node)
          </p>
          <input
            type="email"
            value={toEmail}
            onChange={(e) => setToEmail(e.target.value)}
            placeholder="recipient@example.com"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              CC (Optional)
            </label>
            <input
              type="text"
              value={cc}
              onChange={(e) => setCc(e.target.value)}
              placeholder="cc@example.com"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              BCC (Optional)
            </label>
            <input
              type="text"
              value={bcc}
              onChange={(e) => setBcc(e.target.value)}
              placeholder="bcc@example.com"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Subject <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Email subject (can also come from previous node)
          </p>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Email subject"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Email Type
          </label>
          <SelectWithIcons
            value={emailType}
            onChange={setEmailType}
            options={EMAIL_TYPES}
            placeholder="Select email type..."
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Body <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Email body content (can also come from previous node)
          </p>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={emailType === 'html' ? '<p>Your HTML email content here...</p>' : 'Your email message here...'}
            rows={emailType === 'html' ? 12 : 8}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-mono text-sm"
          />
          {emailType === 'html' && (
            <p className="text-xs text-slate-400">
              HTML format supported. Use HTML tags for formatting.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

