/**
 * Enhanced S3 Node Form Component
 * Provides a better UX than the generic SchemaForm for S3 operations
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { APIKeyInput } from './APIKeyInput';
import { testS3Connection } from '@/services/nodes';
import { ProviderIcon } from '@/components/common/ProviderIcon';

interface S3NodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema: Record<string, any>;
}

const S3_OPERATIONS = [
  { value: 'list', label: 'List Files', icon: 'database' },
  { value: 'upload', label: 'Upload File', icon: 'api' },
  { value: 'download', label: 'Download File', icon: 'api' },
  { value: 'delete', label: 'Delete File', icon: 'api' },
  { value: 'copy', label: 'Copy File', icon: 'api' },
  { value: 'move', label: 'Move File', icon: 'api' },
  { value: 'get_url', label: 'Get Presigned URL', icon: 'api' },
];

const AWS_REGIONS = [
  { value: 'us-east-1', label: 'US East (N. Virginia)', icon: 'api' },
  { value: 'us-east-2', label: 'US East (Ohio)', icon: 'api' },
  { value: 'us-west-1', label: 'US West (N. California)', icon: 'api' },
  { value: 'us-west-2', label: 'US West (Oregon)', icon: 'api' },
  { value: 'eu-west-1', label: 'Europe (Ireland)', icon: 'api' },
  { value: 'eu-central-1', label: 'Europe (Frankfurt)', icon: 'api' },
  { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)', icon: 'api' },
  { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)', icon: 'api' },
  { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)', icon: 'api' },
];

export function S3NodeForm({ initialData, onChange, schema }: S3NodeFormProps) {
  const [operation, setOperation] = useState(initialData.s3_operation || 'list');
  const [accessKeyId, setAccessKeyId] = useState(initialData.s3_access_key_id || '');
  const [secretAccessKey, setSecretAccessKey] = useState(initialData.s3_secret_access_key || '');
  const [bucket, setBucket] = useState(initialData.s3_bucket || '');
  const [region, setRegion] = useState(initialData.s3_region || 'us-east-1');
  const [key, setKey] = useState(initialData.s3_key || '');
  const [prefix, setPrefix] = useState(initialData.s3_prefix || '');
  const [maxKeys, setMaxKeys] = useState(initialData.s3_max_keys || 100);
  const [sourceKey, setSourceKey] = useState(initialData.s3_source_key || '');
  const [destKey, setDestKey] = useState(initialData.s3_dest_key || '');
  const [contentType, setContentType] = useState(initialData.s3_content_type || '');
  const [isPublic, setIsPublic] = useState(initialData.s3_public || false);
  const [urlExpiration, setUrlExpiration] = useState(initialData.s3_url_expiration || 3600);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionError, setConnectionError] = useState<string>('');
  
  const onChangeRef = useRef(onChange);
  
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent when form changes
  useEffect(() => {
    const config: Record<string, any> = {
      s3_operation: operation,
      s3_access_key_id: accessKeyId,
      s3_secret_access_key: secretAccessKey,
      s3_bucket: bucket,
      s3_region: region,
    };

    // Add operation-specific fields
    if (operation === 'list') {
      if (prefix) config.s3_prefix = prefix;
      if (maxKeys) config.s3_max_keys = maxKeys;
    } else if (operation === 'upload' || operation === 'download' || operation === 'delete' || operation === 'get_url') {
      if (key) config.s3_key = key;
      if (operation === 'upload') {
        if (contentType) config.s3_content_type = contentType;
        config.s3_public = isPublic;
      }
      if (operation === 'get_url') {
        config.s3_url_expiration = urlExpiration;
      }
    } else if (operation === 'copy' || operation === 'move') {
      if (sourceKey) config.s3_source_key = sourceKey;
      if (destKey) config.s3_dest_key = destKey;
    }

    onChangeRef.current(config);
  }, [operation, accessKeyId, secretAccessKey, bucket, region, key, prefix, maxKeys, sourceKey, destKey, contentType, isPublic, urlExpiration, onChange]);

  const handleTestConnection = async () => {
    if (!accessKeyId || !secretAccessKey || !bucket) {
      setConnectionError('Please fill in Access Key ID, Secret Access Key, and Bucket');
      setConnectionStatus('error');
      return;
    }

    setConnectionStatus('testing');
    setConnectionError('');

    try {
      // Test connection by attempting to list bucket (with limit 1)
      const result = await testS3Connection(accessKeyId, secretAccessKey, bucket, region);
      if (result.success) {
        setConnectionStatus('success');
        setConnectionError('');
      } else {
        setConnectionStatus('error');
        setConnectionError(result.error || 'Connection test failed');
      }
    } catch (error: any) {
      setConnectionStatus('error');
      setConnectionError(error.message || 'Connection test failed');
    }
  };

  return (
    <div className="space-y-4">
      {/* Operation Selector */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Operation <span className="text-red-400">*</span>
        </label>
        <p className="text-xs text-slate-400 -mt-1">
          Select the S3 operation to perform
        </p>
        <SelectWithIcons
          value={operation}
          onChange={setOperation}
          options={S3_OPERATIONS}
          placeholder="Select operation..."
        />
      </div>

      {/* AWS Credentials */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="s3" size="sm" />
          <h3 className="text-sm font-semibold text-white">AWS Credentials</h3>
        </div>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Access Key ID <span className="text-red-400">*</span>
          </label>
          <APIKeyInput
            value={accessKeyId}
            onChange={setAccessKeyId}
            placeholder="Enter AWS Access Key ID..."
            label=""
            description=""
            serviceName="AWS"
            testConnection={undefined}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Secret Access Key <span className="text-red-400">*</span>
          </label>
          <APIKeyInput
            value={secretAccessKey}
            onChange={setSecretAccessKey}
            placeholder="Enter AWS Secret Access Key..."
            label=""
            description=""
            serviceName="AWS"
            testConnection={undefined}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Bucket Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={bucket}
            onChange={(e) => setBucket(e.target.value)}
            placeholder="my-bucket-name"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Region <span className="text-red-400">*</span>
          </label>
          <SelectWithIcons
            value={region}
            onChange={setRegion}
            options={AWS_REGIONS}
            placeholder="Select region..."
          />
        </div>

        {/* Test Connection Button */}
        <button
          type="button"
          onClick={handleTestConnection}
          disabled={connectionStatus === 'testing' || !accessKeyId || !secretAccessKey || !bucket}
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

      {/* Operation-Specific Fields */}
      {operation === 'list' && (
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Prefix (Optional)
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Filter files by prefix (e.g., "folder/subfolder/")
            </p>
            <input
              type="text"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              placeholder="folder/subfolder/"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Max Keys
            </label>
            <input
              type="number"
              value={maxKeys}
              onChange={(e) => setMaxKeys(parseInt(e.target.value) || 100)}
              min={1}
              max={1000}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}

      {(operation === 'upload' || operation === 'download' || operation === 'delete' || operation === 'get_url') && (
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            File Key/Path <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            S3 object key (file path), e.g., "documents/file.pdf"
          </p>
          <input
            type="text"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="documents/file.pdf"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>
      )}

      {operation === 'upload' && (
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Content Type (Optional)
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              MIME type (auto-detected if not provided)
            </p>
            <input
              type="text"
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              placeholder="application/pdf, image/png, etc."
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="s3_public"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="w-4 h-4 rounded bg-white/5 border-white/10 text-amber-600 focus:ring-amber-500"
            />
            <label htmlFor="s3_public" className="text-sm text-slate-300">
              Make file publicly accessible
            </label>
          </div>
        </div>
      )}

      {operation === 'get_url' && (
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            URL Expiration (seconds)
          </label>
          <input
            type="number"
            value={urlExpiration}
            onChange={(e) => setUrlExpiration(parseInt(e.target.value) || 3600)}
            min={1}
            max={604800}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
          <p className="text-xs text-slate-400">
            Default: 3600 seconds (1 hour). Max: 604800 seconds (7 days)
          </p>
        </div>
      )}

      {(operation === 'copy' || operation === 'move') && (
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Source Key <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={sourceKey}
              onChange={(e) => setSourceKey(e.target.value)}
              placeholder="source/file.pdf"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Destination Key <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={destKey}
              onChange={(e) => setDestKey(e.target.value)}
              placeholder="destination/file.pdf"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}
    </div>
  );
}

