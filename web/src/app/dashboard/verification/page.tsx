"use client";

import { useEffect, useState } from "react";
import api, {
  SheerIDType,
  SheerIDVerification,
  SheerIDSettings,
  IPLookupResult,
  ProxyCheckResult,
  UserProxy,
} from "@/lib/api";

export default function VerificationPage() {
  // State
  const [types, setTypes] = useState<SheerIDType[]>([]);
  const [verifications, setVerifications] = useState<SheerIDVerification[]>([]);
  const [settings, setSettings] = useState<SheerIDSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Form state
  const [selectedType, setSelectedType] = useState("");
  const [verifyUrl, setVerifyUrl] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkResult, setCheckResult] = useState<{
    valid?: boolean;
    error?: string;
    step?: string;
  } | null>(null);
  const [submitResult, setSubmitResult] = useState<{
    success?: boolean;
    message?: string;
    error?: string;
  } | null>(null);

  // Multi-proxy state
  const [proxies, setProxies] = useState<UserProxy[]>([]);
  const [showProxyManager, setShowProxyManager] = useState(false);
  const [showAddProxy, setShowAddProxy] = useState(false);
  const [editingProxy, setEditingProxy] = useState<UserProxy | null>(null);
  const [newProxyName, setNewProxyName] = useState("");
  const [newProxyHost, setNewProxyHost] = useState("");
  const [newProxyPort, setNewProxyPort] = useState("");
  const [newProxyUsername, setNewProxyUsername] = useState("");
  const [newProxyPassword, setNewProxyPassword] = useState("");
  const [isAddingProxy, setIsAddingProxy] = useState(false);
  const [testingProxyId, setTestingProxyId] = useState<number | null>(null);
  const [proxyTestResults, setProxyTestResults] = useState<
    Record<number, ProxyCheckResult>
  >({});

  // IP Lookup state
  const [currentIP, setCurrentIP] = useState<IPLookupResult | null>(null);
  const [isLoadingIP, setIsLoadingIP] = useState(false);

  // Detail modal
  const [selectedVerification, setSelectedVerification] =
    useState<SheerIDVerification | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [typesResult, verificationsResult, settingsResult, proxiesResult] =
        await Promise.all([
          api.getSheerIDTypes(),
          api.getSheerIDVerifications(),
          api.getSheerIDSettings(),
          api.getProxies(),
        ]);

      if (typesResult.data?.types) {
        setTypes(typesResult.data.types);
        if (typesResult.data.types.length > 0 && !selectedType) {
          setSelectedType(typesResult.data.types[0].id);
        }
      }
      if (verificationsResult.data?.verifications) {
        setVerifications(verificationsResult.data.verifications);
      }
      if (settingsResult.data?.settings) {
        setSettings(settingsResult.data.settings);
      }
      if (proxiesResult.data?.proxies) {
        setProxies(proxiesResult.data.proxies);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setIsLoading(false);
  };

  const handleCheckLink = async () => {
    if (!verifyUrl) return;
    setIsChecking(true);
    setCheckResult(null);
    setSubmitResult(null);

    const result = await api.checkSheerIDLink(verifyUrl, selectedType);
    if (result.data) {
      setCheckResult(result.data);
    } else {
      setCheckResult({ valid: false, error: result.error });
    }
    setIsChecking(false);
  };

  const handleSubmit = async () => {
    if (!verifyUrl || !selectedType) return;
    setIsSubmitting(true);
    setSubmitResult(null);

    const result = await api.submitSheerIDVerification(verifyUrl, selectedType);
    if (result.data) {
      setSubmitResult(result.data);
      if (result.data.success) {
        setVerifyUrl("");
        setCheckResult(null);
        // Refresh verifications
        const verificationsResult = await api.getSheerIDVerifications();
        if (verificationsResult.data?.verifications) {
          setVerifications(verificationsResult.data.verifications);
        }
      }
    } else {
      setSubmitResult({ success: false, error: result.error });
    }
    setIsSubmitting(false);
  };

  // ==================== MULTI-PROXY HANDLERS ====================

  const handleAddProxy = async () => {
    if (!newProxyName || !newProxyHost || !newProxyPort) return;
    setIsAddingProxy(true);
    const result = await api.addProxy({
      name: newProxyName,
      host: newProxyHost,
      port: parseInt(newProxyPort),
      username: newProxyUsername || undefined,
      password: newProxyPassword || undefined,
    });
    if (result.data?.proxy) {
      setProxies([result.data.proxy, ...proxies]);
      resetProxyForm();
      setShowAddProxy(false);
    }
    setIsAddingProxy(false);
  };

  const handleUpdateProxy = async () => {
    if (!editingProxy || !newProxyName || !newProxyHost || !newProxyPort)
      return;
    setIsAddingProxy(true);
    const result = await api.updateProxy(editingProxy.id, {
      name: newProxyName,
      host: newProxyHost,
      port: parseInt(newProxyPort),
      username: newProxyUsername || undefined,
      password: newProxyPassword || undefined,
    });
    if (result.data?.proxy) {
      setProxies(
        proxies.map((p) => (p.id === editingProxy.id ? result.data!.proxy : p)),
      );
      resetProxyForm();
      setEditingProxy(null);
    }
    setIsAddingProxy(false);
  };

  const handleDeleteProxy = async (proxyId: number) => {
    if (!confirm("Yakin ingin menghapus proxy ini?")) return;
    const result = await api.deleteProxy(proxyId);
    if (result.data) {
      setProxies(proxies.filter((p) => p.id !== proxyId));
    }
  };

  const handleActivateProxy = async (proxyId: number) => {
    const result = await api.activateProxy(proxyId);
    if (result.data?.proxy) {
      setProxies(
        proxies.map((p) => ({
          ...p,
          is_active: p.id === proxyId,
        })),
      );
      // Refresh settings to get updated proxy config
      const settingsResult = await api.getSheerIDSettings();
      if (settingsResult.data?.settings) {
        setSettings(settingsResult.data.settings);
      }
    }
  };

  const handleDeactivateProxy = async (proxyId: number) => {
    const result = await api.deactivateProxy(proxyId);
    if (result.data) {
      setProxies(
        proxies.map((p) => ({
          ...p,
          is_active: false,
        })),
      );
      // Refresh settings
      const settingsResult = await api.getSheerIDSettings();
      if (settingsResult.data?.settings) {
        setSettings(settingsResult.data.settings);
      }
    }
  };

  const handleTestProxy = async (proxyId: number) => {
    setTestingProxyId(proxyId);
    const result = await api.testSavedProxy(proxyId);
    if (result.data) {
      setProxyTestResults({ ...proxyTestResults, [proxyId]: result.data });
      // Refresh proxies to get updated test status
      const proxiesResult = await api.getProxies();
      if (proxiesResult.data?.proxies) {
        setProxies(proxiesResult.data.proxies);
      }
    }
    setTestingProxyId(null);
  };

  const resetProxyForm = () => {
    setNewProxyName("");
    setNewProxyHost("");
    setNewProxyPort("");
    setNewProxyUsername("");
    setNewProxyPassword("");
  };

  const startEditProxy = (proxy: UserProxy) => {
    setEditingProxy(proxy);
    setNewProxyName(proxy.name);
    setNewProxyHost(proxy.host);
    setNewProxyPort(proxy.port.toString());
    setNewProxyUsername(proxy.username || "");
    setNewProxyPassword("");
  };

  const handleIPLookup = async () => {
    setIsLoadingIP(true);
    setCurrentIP(null);

    // Fetch IP directly from browser (not through backend) to get user's real IP
    try {
      // Try ipapi.co first
      let response = await fetch("https://ipapi.co/json/", {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentIP({
          success: true,
          ip: data.ip,
          city: data.city,
          region: data.region,
          country: data.country_name,
          country_code: data.country_code,
          isp: data.org,
          timezone: data.timezone,
          source: "ipapi.co",
        });
        setIsLoadingIP(false);
        return;
      }

      // Fallback to ipinfo.io
      response = await fetch("https://ipinfo.io/json", {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentIP({
          success: true,
          ip: data.ip,
          city: data.city,
          region: data.region,
          country: data.country,
          isp: data.org,
          timezone: data.timezone,
          source: "ipinfo.io",
        });
        setIsLoadingIP(false);
        return;
      }

      // Last fallback to ipify
      response = await fetch("https://api.ipify.org?format=json", {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentIP({
          success: true,
          ip: data.ip,
          source: "ipify.org",
        });
      }
    } catch (error) {
      console.error("IP lookup error:", error);
      setCurrentIP({ success: false, error: "Could not fetch IP" });
    }

    setIsLoadingIP(false);
  };

  const getActiveProxy = () => proxies.find((p) => p.is_active);

  const getSelectedTypeConfig = () => {
    return types.find((t) => t.id === selectedType);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <span className="px-2 py-1 text-xs font-medium bg-green-500/20 text-green-400 rounded-full">
            ✅ Success
          </span>
        );
      case "pending":
        return (
          <span className="px-2 py-1 text-xs font-medium bg-yellow-500/20 text-yellow-400 rounded-full">
            ⏳ Pending
          </span>
        );
      case "failed":
        return (
          <span className="px-2 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded-full">
            ❌ Failed
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs font-medium bg-gray-500/20 text-gray-400 rounded-full">
            {status}
          </span>
        );
    }
  };

  const getTypeIcon = (typeId: string) => {
    const type = types.find((t) => t.id === typeId);
    return type?.icon || "🔐";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <span className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500/20 to-green-600/20 flex items-center justify-center text-2xl">
              🔐
            </span>
            SheerID Verification
          </h1>
          <p className="text-[var(--text-muted)] mt-1">
            Verifikasi akun student/teacher untuk berbagai layanan premium
          </p>
        </div>
        <button
          onClick={() => setShowProxyManager(!showProxyManager)}
          className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] bg-white/5 rounded-lg hover:bg-white/10 transition-colors flex items-center gap-2"
        >
          <span>🛡️</span>
          {getActiveProxy()
            ? `Proxy: ${getActiveProxy()?.name}`
            : "Manage Proxies"}
        </button>
      </div>

      {/* How it Works Info Box */}
      <div className="glass-card p-6 border border-green-500/20">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-green-400">
          <span>📋</span>
          Cara Menggunakan
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-green-400 mb-1">1️⃣</div>
            <div className="font-medium">Buka Layanan</div>
            <p className="text-[var(--text-muted)] text-xs mt-1">
              Buka halaman verifikasi student di YouTube, Spotify, dll
            </p>
          </div>
          <div className="p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-green-400 mb-1">2️⃣</div>
            <div className="font-medium">Copy URL</div>
            <p className="text-[var(--text-muted)] text-xs mt-1">
              Copy URL dari halaman SheerID (yang ada verificationId)
            </p>
          </div>
          <div className="p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-green-400 mb-1">3️⃣</div>
            <div className="font-medium">Pilih Tipe & Submit</div>
            <p className="text-[var(--text-muted)] text-xs mt-1">
              Pilih platform dan paste URL lalu Submit
            </p>
          </div>
          <div className="p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-green-400 mb-1">4️⃣</div>
            <div className="font-medium">Tunggu Hasil</div>
            <p className="text-[var(--text-muted)] text-xs mt-1">
              Verifikasi instant atau pending 24-48 jam
            </p>
          </div>
        </div>
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <p className="text-xs text-yellow-400">
            <strong>💡 Tips:</strong> Gunakan residential proxy dan pastikan{" "}
            <code>curl_cffi</code> terinstall untuk hasil terbaik. SheerID
            menggunakan TLS fingerprinting dan AI document review.
          </p>
        </div>
      </div>

      {/* Multi-Proxy Manager Panel */}
      {showProxyManager && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <span>🛡️</span>
              My Proxies
            </h3>
            <button
              onClick={() => {
                resetProxyForm();
                setShowAddProxy(true);
                setEditingProxy(null);
              }}
              className="px-4 py-2 text-sm font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
            >
              <span>➕</span>
              Add Proxy
            </button>
          </div>

          {/* Current IP Display */}
          <div className="mb-4 p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold flex items-center gap-2">
                <span>🌐</span>
                Your Current IP
              </h4>
              <button
                onClick={handleIPLookup}
                disabled={isLoadingIP}
                className="px-3 py-1 text-xs font-medium text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20 transition-colors disabled:opacity-50"
              >
                {isLoadingIP ? "Loading..." : "🔄 Refresh"}
              </button>
            </div>
            {currentIP ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div>
                  <span className="text-gray-400">IP:</span>
                  <span className="ml-2 font-mono">{currentIP.ip}</span>
                </div>
                <div>
                  <span className="text-gray-400">City:</span>
                  <span className="ml-2">{currentIP.city || "-"}</span>
                </div>
                <div>
                  <span className="text-gray-400">Country:</span>
                  <span className="ml-2">{currentIP.country || "-"}</span>
                </div>
                <div>
                  <span className="text-gray-400">ISP:</span>
                  <span className="ml-2 truncate">{currentIP.isp || "-"}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">
                Click refresh to check your current IP
              </p>
            )}
          </div>

          {/* Add/Edit Proxy Form */}
          {(showAddProxy || editingProxy) && (
            <div className="mb-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <h4 className="text-sm font-semibold mb-3 text-blue-400">
                {editingProxy ? "✏️ Edit Proxy" : "➕ Add New Proxy"}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newProxyName}
                    onChange={(e) => setNewProxyName(e.target.value)}
                    placeholder="My US Proxy"
                    className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Host *
                  </label>
                  <input
                    type="text"
                    value={newProxyHost}
                    onChange={(e) => setNewProxyHost(e.target.value)}
                    placeholder="proxy.example.com"
                    className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Port *
                  </label>
                  <input
                    type="number"
                    value={newProxyPort}
                    onChange={(e) => setNewProxyPort(e.target.value)}
                    placeholder="8080"
                    className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    value={newProxyUsername}
                    onChange={(e) => setNewProxyUsername(e.target.value)}
                    placeholder="username"
                    className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium mb-1">
                    Password
                    {editingProxy && editingProxy.username && (
                      <span className="text-gray-400 font-normal ml-2">
                        (kosongkan jika tidak ingin mengubah)
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    value={newProxyPassword}
                    onChange={(e) => setNewProxyPassword(e.target.value)}
                    placeholder={editingProxy ? "••••••••" : "password"}
                    className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-3">
                <button
                  onClick={() => {
                    setShowAddProxy(false);
                    setEditingProxy(null);
                    resetProxyForm();
                  }}
                  className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={editingProxy ? handleUpdateProxy : handleAddProxy}
                  disabled={
                    isAddingProxy ||
                    !newProxyName ||
                    !newProxyHost ||
                    !newProxyPort
                  }
                  className="px-4 py-1.5 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                >
                  {isAddingProxy
                    ? "Saving..."
                    : editingProxy
                      ? "Update"
                      : "Add Proxy"}
                </button>
              </div>
            </div>
          )}

          {/* Proxy List */}
          {proxies.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-4xl mb-2">🛡️</div>
              <p>No proxies saved yet</p>
              <p className="text-sm">Add a proxy to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {proxies.map((proxy) => (
                <div
                  key={proxy.id}
                  className={`p-4 rounded-lg border transition-all ${
                    proxy.is_active
                      ? "bg-green-500/10 border-green-500/30"
                      : "bg-white/5 border-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{proxy.name}</span>
                          {proxy.is_active && (
                            <span className="px-2 py-0.5 text-xs font-medium bg-green-500/20 text-green-400 rounded-full">
                              Active
                            </span>
                          )}
                          {proxy.last_test_success !== null && (
                            <span
                              className={`text-xs ${proxy.last_test_success ? "text-green-400" : "text-red-400"}`}
                            >
                              {proxy.last_test_success ? "✅" : "❌"}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-400 font-mono">
                          {proxy.host}:{proxy.port}
                          {proxy.username && ` (${proxy.username})`}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleTestProxy(proxy.id)}
                        disabled={testingProxyId === proxy.id}
                        className="px-3 py-1.5 text-xs font-medium text-blue-400 bg-blue-500/10 rounded-lg hover:bg-blue-500/20 transition-colors disabled:opacity-50"
                      >
                        {testingProxyId === proxy.id ? "Testing..." : "🧪 Test"}
                      </button>
                      {proxy.is_active ? (
                        <button
                          onClick={() => handleDeactivateProxy(proxy.id)}
                          className="px-3 py-1.5 text-xs font-medium text-yellow-400 bg-yellow-500/10 rounded-lg hover:bg-yellow-500/20 transition-colors"
                        >
                          ⏸️ Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivateProxy(proxy.id)}
                          className="px-3 py-1.5 text-xs font-medium text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20 transition-colors"
                        >
                          ✅ Activate
                        </button>
                      )}
                      <button
                        onClick={() => startEditProxy(proxy)}
                        className="px-3 py-1.5 text-xs font-medium text-gray-400 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteProxy(proxy.id)}
                        className="px-3 py-1.5 text-xs font-medium text-red-400 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition-colors"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  {/* Test Result */}
                  {proxyTestResults[proxy.id] && (
                    <div
                      className={`mt-3 p-2 rounded text-sm ${
                        proxyTestResults[proxy.id].valid
                          ? "bg-green-500/10 text-green-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      {proxyTestResults[proxy.id].valid ? (
                        <span>
                          ✅ Working! IP: {proxyTestResults[proxy.id].ip} (
                          {proxyTestResults[proxy.id].city &&
                            `${proxyTestResults[proxy.id].city}, `}
                          {proxyTestResults[proxy.id].country})
                        </span>
                      ) : (
                        <span>❌ {proxyTestResults[proxy.id].error}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end mt-4">
            <button
              onClick={() => setShowProxyManager(false)}
              className="px-4 py-2 text-sm font-medium text-gray-400 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Submit Verification Form */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Submit Verification</h3>

        {/* Type Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Verification Type
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
            {types.map((type) => (
              <button
                key={type.id}
                onClick={() => setSelectedType(type.id)}
                className={`p-3 rounded-lg border transition-all text-center ${
                  selectedType === type.id
                    ? "border-green-500 bg-green-500/10 text-green-400"
                    : "border-[var(--border-color)] bg-white/5 hover:bg-white/10"
                }`}
              >
                <div className="text-2xl mb-1">{type.icon}</div>
                <div className="text-xs font-medium truncate">{type.name}</div>
                <div className="text-xs text-[var(--text-muted)]">
                  {type.cost} pts
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* URL Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">SheerID URL</label>
          <input
            type="url"
            value={verifyUrl}
            onChange={(e) => {
              setVerifyUrl(e.target.value);
              setCheckResult(null);
              setSubmitResult(null);
            }}
            placeholder="https://services.sheerid.com/verify/...?verificationId=..."
            className="w-full px-4 py-3 bg-white/5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            Paste URL dari halaman verifikasi SheerID (harus mengandung
            verificationId)
          </p>
        </div>

        {/* Check Result */}
        {checkResult && (
          <div
            className={`mb-4 p-4 rounded-lg ${
              checkResult.valid
                ? "bg-green-500/10 border border-green-500/30"
                : "bg-red-500/10 border border-red-500/30"
            }`}
          >
            {checkResult.valid ? (
              <div className="flex items-center gap-2 text-green-400">
                <span>✅</span>
                <span>
                  Link valid! Current step: {checkResult.step || "ready"}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400">
                <span>❌</span>
                <span>{checkResult.error || "Invalid link"}</span>
              </div>
            )}
          </div>
        )}

        {/* Submit Result */}
        {submitResult && (
          <div
            className={`mb-4 p-4 rounded-lg ${
              submitResult.success
                ? "bg-green-500/10 border border-green-500/30"
                : "bg-red-500/10 border border-red-500/30"
            }`}
          >
            {submitResult.success ? (
              <div className="text-green-400">
                <div className="flex items-center gap-2 font-medium">
                  <span>🎉</span>
                  <span>{submitResult.message || "Success!"}</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400">
                <span>❌</span>
                <span>{submitResult.error || "Verification failed"}</span>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleCheckLink}
            disabled={!verifyUrl || isChecking}
            className="px-6 py-3 text-sm font-medium text-[var(--text-secondary)] bg-white/5 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isChecking ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <span>🔍</span>
                Check Link
              </>
            )}
          </button>

          <button
            onClick={handleSubmit}
            disabled={!verifyUrl || !selectedType || isSubmitting}
            className="flex-1 px-6 py-3 text-sm font-medium text-white bg-gradient-to-r from-green-500 to-green-600 rounded-lg hover:from-green-600 hover:to-green-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <span>✅</span>
                Submit Verification - {getSelectedTypeConfig()?.cost || 5} pts
              </>
            )}
          </button>
        </div>
      </div>

      {/* Verification History */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Verification History</h3>

        {verifications.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-muted)]">
            <div className="text-4xl mb-2">📋</div>
            <p>Belum ada riwayat verifikasi</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-[var(--text-muted)] border-b border-[var(--border-color)]">
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">URL</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Result</th>
                  <th className="pb-3 font-medium">Date</th>
                  <th className="pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {verifications.map((v) => (
                  <tr
                    key={v.id}
                    className="border-b border-[var(--border-color)]/50"
                  >
                    <td className="py-3">
                      <span className="text-xl">
                        {getTypeIcon(v.verify_type)}
                      </span>
                      <span className="ml-2 text-sm">{v.verify_type}</span>
                    </td>
                    <td className="py-3">
                      <span className="text-sm text-[var(--text-muted)] font-mono">
                        ...{v.verify_id?.slice(-8) || "N/A"}
                      </span>
                    </td>
                    <td className="py-3">{getStatusBadge(v.status)}</td>
                    <td className="py-3">
                      {v.student_name ? (
                        <span className="text-sm">{v.student_name}</span>
                      ) : v.error_details ? (
                        <span className="text-sm text-red-400 truncate max-w-[150px] block">
                          {v.error_details}
                        </span>
                      ) : (
                        <span className="text-sm text-[var(--text-muted)]">
                          -
                        </span>
                      )}
                    </td>
                    <td className="py-3">
                      <span className="text-sm text-[var(--text-muted)]">
                        {formatDate(v.created_at)}
                      </span>
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => setSelectedVerification(v)}
                        className="text-sm text-green-400 hover:underline"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedVerification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>{getTypeIcon(selectedVerification.verify_type)}</span>
                Verification Details
              </h3>
              <button
                onClick={() => setSelectedVerification(null)}
                className="text-[var(--text-muted)] hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Type:</span>
                <span className="font-medium">
                  {selectedVerification.verify_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Status:</span>
                {getStatusBadge(selectedVerification.status)}
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Points:</span>
                <span>{selectedVerification.points_cost} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Created:</span>
                <span>{formatDate(selectedVerification.created_at)}</span>
              </div>

              {selectedVerification.student_name && (
                <>
                  <hr className="border-[var(--border-color)]" />
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Name:</span>
                    <span>{selectedVerification.student_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Email:</span>
                    <span className="text-sm font-mono">
                      {selectedVerification.student_email}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">School:</span>
                    <span className="text-sm text-right max-w-[200px]">
                      {selectedVerification.school_name}
                    </span>
                  </div>
                </>
              )}

              {selectedVerification.result_message && (
                <div className="p-3 bg-green-500/10 rounded-lg text-sm text-green-400">
                  {selectedVerification.result_message}
                </div>
              )}

              {selectedVerification.error_details && (
                <div className="p-3 bg-red-500/10 rounded-lg text-sm text-red-400">
                  {selectedVerification.error_details}
                </div>
              )}

              {selectedVerification.redirect_url && (
                <a
                  href={selectedVerification.redirect_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full px-4 py-2 text-center text-sm font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors"
                >
                  Open Redirect URL
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
