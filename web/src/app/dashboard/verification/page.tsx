"use client";

import { useEffect, useState } from "react";
import api, {
  SheerIDType,
  SheerIDVerification,
  SheerIDSettings,
  IPLookupResult,
  ProxyCheckResult,
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

  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  const [proxyEnabled, setProxyEnabled] = useState(false);
  const [proxyHost, setProxyHost] = useState("");
  const [proxyPort, setProxyPort] = useState("");
  const [proxyUsername, setProxyUsername] = useState("");
  const [proxyPassword, setProxyPassword] = useState("");
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  // IP Lookup & Proxy Check state
  const [currentIP, setCurrentIP] = useState<IPLookupResult | null>(null);
  const [isLoadingIP, setIsLoadingIP] = useState(false);
  const [proxyCheckResult, setProxyCheckResult] =
    useState<ProxyCheckResult | null>(null);
  const [isCheckingProxy, setIsCheckingProxy] = useState(false);

  // Detail modal
  const [selectedVerification, setSelectedVerification] =
    useState<SheerIDVerification | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [typesResult, verificationsResult, settingsResult] =
        await Promise.all([
          api.getSheerIDTypes(),
          api.getSheerIDVerifications(),
          api.getSheerIDSettings(),
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
        const s = settingsResult.data.settings;
        setSettings(s);
        setProxyEnabled(s.proxy_enabled);
        setProxyHost(s.proxy_host || "");
        setProxyPort(s.proxy_port?.toString() || "");
        setProxyUsername(s.proxy_username || "");
        setProxyPassword(s.proxy_password || "");
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

  const handleSaveSettings = async () => {
    setIsSavingSettings(true);
    const result = await api.saveSheerIDSettings({
      proxy_enabled: proxyEnabled,
      proxy_host: proxyHost || undefined,
      proxy_port: proxyPort ? parseInt(proxyPort) : undefined,
      proxy_username: proxyUsername || undefined,
      proxy_password: proxyPassword || undefined,
    });

    if (result.data?.settings) {
      setSettings(result.data.settings);
    }
    setIsSavingSettings(false);
    setShowSettings(false);
  };

  const handleIPLookup = async () => {
    setIsLoadingIP(true);
    setCurrentIP(null);
    const result = await api.ipLookup();
    if (result.data) {
      setCurrentIP(result.data);
    }
    setIsLoadingIP(false);
  };

  const handleProxyCheck = async () => {
    if (!proxyHost || !proxyPort) return;
    setIsCheckingProxy(true);
    setProxyCheckResult(null);
    const result = await api.proxyCheck(
      proxyHost,
      parseInt(proxyPort),
      proxyUsername || undefined,
      proxyPassword || undefined,
    );
    if (result.data) {
      setProxyCheckResult(result.data);
    }
    setIsCheckingProxy(false);
  };

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
          onClick={() => setShowSettings(!showSettings)}
          className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] bg-white/5 rounded-lg hover:bg-white/10 transition-colors flex items-center gap-2"
        >
          <span>⚙️</span>
          Proxy Settings
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

      {/* Proxy Settings Panel */}
      {showSettings && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>🛡️</span>
            Proxy & IP Settings
          </h3>

          {/* Current IP Display */}
          <div className="mb-6 p-4 bg-white/5 rounded-lg border border-[var(--border-color)]">
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
                  <span className="text-[var(--text-muted)]">IP:</span>
                  <span className="ml-2 font-mono">{currentIP.ip}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">City:</span>
                  <span className="ml-2">{currentIP.city || "-"}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Country:</span>
                  <span className="ml-2">{currentIP.country || "-"}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">ISP:</span>
                  <span className="ml-2 truncate">{currentIP.isp || "-"}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-[var(--text-muted)]">
                Click refresh to check your current IP
              </p>
            )}
          </div>

          <p className="text-sm text-[var(--text-muted)] mb-4">
            Gunakan residential proxy untuk hasil terbaik. Proxy akan digunakan
            untuk anti-detection.
          </p>

          <div className="space-y-4">
            {/* Enable Toggle */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Enable Proxy</label>
              <button
                onClick={() => setProxyEnabled(!proxyEnabled)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  proxyEnabled ? "bg-green-500" : "bg-gray-600"
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    proxyEnabled ? "translate-x-6" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>

            {proxyEnabled && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Host
                    </label>
                    <input
                      type="text"
                      value={proxyHost}
                      onChange={(e) => setProxyHost(e.target.value)}
                      placeholder="proxy.example.com"
                      className="w-full px-3 py-2 bg-white/5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Port
                    </label>
                    <input
                      type="number"
                      value={proxyPort}
                      onChange={(e) => setProxyPort(e.target.value)}
                      placeholder="8080"
                      className="w-full px-3 py-2 bg-white/5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Username (optional)
                    </label>
                    <input
                      type="text"
                      value={proxyUsername}
                      onChange={(e) => setProxyUsername(e.target.value)}
                      placeholder="username"
                      className="w-full px-3 py-2 bg-white/5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Password (optional)
                    </label>
                    <input
                      type="password"
                      value={proxyPassword}
                      onChange={(e) => setProxyPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3 py-2 bg-white/5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>

                {/* Proxy Check Button & Result */}
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold flex items-center gap-2 text-blue-400">
                      <span>🔍</span>
                      Test Proxy Connection
                    </h4>
                    <button
                      onClick={handleProxyCheck}
                      disabled={isCheckingProxy || !proxyHost || !proxyPort}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                    >
                      {isCheckingProxy ? "Checking..." : "🧪 Test Proxy"}
                    </button>
                  </div>

                  {proxyCheckResult && (
                    <div
                      className={`mt-3 p-3 rounded-lg ${
                        proxyCheckResult.valid
                          ? "bg-green-500/10 border border-green-500/30"
                          : "bg-red-500/10 border border-red-500/30"
                      }`}
                    >
                      {proxyCheckResult.valid ? (
                        <div>
                          <div className="flex items-center gap-2 text-green-400 font-medium mb-2">
                            <span>✅</span>
                            <span>Proxy is working!</span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                            <div>
                              <span className="text-[var(--text-muted)]">
                                Proxy IP:
                              </span>
                              <span className="ml-2 font-mono">
                                {proxyCheckResult.ip}
                              </span>
                            </div>
                            <div>
                              <span className="text-[var(--text-muted)]">
                                City:
                              </span>
                              <span className="ml-2">
                                {proxyCheckResult.city || "-"}
                              </span>
                            </div>
                            <div>
                              <span className="text-[var(--text-muted)]">
                                Country:
                              </span>
                              <span className="ml-2">
                                {proxyCheckResult.country || "-"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-red-400">
                          <span>❌</span>
                          <span>
                            {proxyCheckResult.error || "Proxy check failed"}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSettings}
                disabled={isSavingSettings}
                className="px-4 py-2 text-sm font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {isSavingSettings ? "Saving..." : "💾 Save Settings"}
              </button>
            </div>
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
