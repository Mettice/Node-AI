/**
 * Settings Panel - User settings, API keys, preferences
 */

import { useState } from 'react';
import { User, Key, Bell, Palette, Shield, Save, Activity, Plug } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';
import { SecretsVault } from './SecretsVault';
import { ObservabilitySettings } from './ObservabilitySettings';
import { MCPSettings } from './MCPSettings';

type SettingsTab = 'profile' | 'api-keys' | 'mcp' | 'observability' | 'notifications' | 'appearance' | 'security';

export function SettingsPanel() {
  const { user, updateProfile } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [name, setName] = useState(user?.user_metadata?.name || '');
  const [isSaving, setIsSaving] = useState(false);

  const tabs: { id: SettingsTab; label: string; icon: typeof User }[] = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'api-keys', label: 'Secrets Vault', icon: Key },
    { id: 'mcp', label: 'MCP Tools', icon: Plug },
    { id: 'observability', label: 'Observability', icon: Activity },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      const { error } = await updateProfile({ name });
      if (error) {
        toast.error(error.message || 'Failed to update profile');
      } else {
        toast.success('Profile updated successfully');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Profile Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
                    placeholder="Enter your name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-slate-500">Email cannot be changed</p>
                </div>
                <button
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600',
                    'text-white rounded-lg transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  <Save className="w-4 h-4" />
                  <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </div>
          </div>
        );

      case 'api-keys':
        return <SecretsVault />;

      case 'mcp':
        return <MCPSettings />;

      case 'observability':
        return <ObservabilitySettings />;

      case 'notifications':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Notification Preferences</h3>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <p className="text-sm text-slate-400">
                  Notification settings coming soon.
                </p>
              </div>
            </div>
          </div>
        );

      case 'appearance':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Appearance</h3>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <p className="text-sm text-slate-400">
                  Appearance settings coming soon.
                </p>
              </div>
            </div>
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Security</h3>
              <div className="space-y-4">
                <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-white mb-2">Password</h4>
                  <p className="text-sm text-slate-400 mb-3">
                    Change your password to keep your account secure.
                  </p>
                  <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-slate-300 transition-colors">
                    Change Password
                  </button>
                </div>
                <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-white mb-2">Two-Factor Authentication</h4>
                  <p className="text-sm text-slate-400 mb-3">
                    Add an extra layer of security to your account.
                  </p>
                  <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-slate-300 transition-colors">
                    Enable 2FA
                  </button>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex border-b border-white/10">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                'border-b-2',
                isActive
                  ? 'text-amber-400 border-amber-500'
                  : 'text-slate-400 border-transparent hover:text-slate-300 hover:border-white/10'
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {renderContent()}
      </div>
    </div>
  );
}

