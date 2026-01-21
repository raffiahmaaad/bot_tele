"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import api from "@/lib/api";

interface BotDetails {
  id: number;
  bot_username: string;
  bot_name: string;
  bot_type: string;
  pakasir_slug: string | null;
  pakasir_api_key: string | null;
  is_active: boolean;
  created_at: string;
}

interface BotStats {
  total_products: number;
  total_users: number;
  total_transactions: number;
  total_revenue: number;
}

export default function BotSettingsPage() {
  const router = useRouter();
  const params = useParams();
  const botId = Number(params.id);

  const [bot, setBot] = useState<BotDetails | null>(null);
  const [stats, setStats] = useState<BotStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Edit form
  const [botName, setBotName] = useState("");
  const [botType, setBotType] = useState("store");
  const [pakasirSlug, setPakasirSlug] = useState("");
  const [pakasirApiKey, setPakasirApiKey] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    valid?: boolean;
    message?: string;
    error?: string;
  } | null>(null);

  useEffect(() => {
    fetchBot();
  }, [botId]);

  const fetchBot = async () => {
    setIsLoading(true);
    const result = await api.getBot(botId);
    if (result.data) {
      const b = result.data.bot;
      setBot(b);
      setStats(result.data.stats);
      setBotName(b.bot_name || "");
      setBotType(b.bot_type || "store");
      setPakasirSlug(b.pakasir_slug || "");
      setIsActive(b.is_active);
    }
    setIsLoading(false);
  };

  const testPakasir = async () => {
    // Use current form values, or fallback to saved bot values
    const slugToTest = pakasirSlug || bot?.pakasir_slug || "";
    const keyToTest = pakasirApiKey || ""; // For test, we need the new key if provided

    if (!slugToTest) {
      setTestResult({ valid: false, error: "Project Slug belum diisi" });
      return;
    }

    // If no new key provided but bot has existing key, just validate connection
    if (!keyToTest && !bot?.pakasir_api_key) {
      setTestResult({ valid: false, error: "API Key belum diisi" });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    const result = await api.testPakasir(slugToTest, keyToTest || "existing");
    if (result.data) {
      setTestResult(result.data);
    } else {
      setTestResult({
        valid: false,
        error: result.error || "Gagal test koneksi",
      });
    }
    setIsTesting(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setIsSaving(true);

    const result = await api.updateBot(botId, {
      bot_name: botName,
      bot_type: botType,
      pakasir_slug: pakasirSlug || null,
      pakasir_api_key: pakasirApiKey || undefined,
      is_active: isActive,
    });

    if (result.error) {
      setError(result.error);
    } else {
      setSuccess("Pengaturan berhasil disimpan!");
      await fetchBot();
    }
    setIsSaving(false);
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    const result = await api.deleteBot(botId);
    if (result.error) {
      setError(result.error);
      setIsDeleting(false);
    } else {
      router.push("/dashboard/bots");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <svg
            className="w-8 h-8 animate-spin mx-auto mb-4 text-[var(--color-primary)]"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-[var(--text-muted)]">Loading...</p>
        </div>
      </div>
    );
  }

  if (!bot) {
    return (
      <div className="text-center py-10">
        <p className="text-red-400">Bot tidak ditemukan</p>
        <button
          onClick={() => router.push("/dashboard/bots")}
          className="btn-secondary mt-4"
        >
          Kembali
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/dashboard/bots")}
          className="p-2 rounded-lg hover:bg-white/10 transition-colors"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Pengaturan Bot</h1>
          <p className="text-[var(--text-muted)]">{bot.bot_username}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-lg text-sm ${
            bot.is_active
              ? "text-green-400 bg-green-400/10"
              : "text-yellow-400 bg-yellow-400/10"
          }`}
        >
          {bot.is_active ? "✅ Aktif" : "⏸️ Nonaktif"}
        </span>
      </div>

      {/* Stats (Store only) */}
      {botType === "store" && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold">{stats.total_products}</p>
            <p className="text-sm text-[var(--text-muted)]">Produk</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold">{stats.total_users}</p>
            <p className="text-sm text-[var(--text-muted)]">Users</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold">{stats.total_transactions}</p>
            <p className="text-sm text-[var(--text-muted)]">Transaksi</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold">
              Rp {(stats.total_revenue || 0).toLocaleString("id-ID")}
            </p>
            <p className="text-sm text-[var(--text-muted)]">Revenue</p>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm">
          {success}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Basic Info */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">📋 Informasi Bot</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Nama Bot</label>
              <input
                type="text"
                value={botName}
                onChange={(e) => setBotName(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-[var(--color-primary)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Username</label>
              <input
                type="text"
                value={bot.bot_username}
                disabled
                className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] text-[var(--text-muted)] cursor-not-allowed"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Tipe Bot</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: "store", name: "🛒 Store Bot", desc: "Bot toko digital" },
                {
                  id: "sheerid",
                  name: "🔐 SheerID Bot",
                  desc: "Verifikasi student",
                },
              ].map((type) => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => setBotType(type.id)}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    botType === type.id
                      ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10"
                      : "border-[var(--border-color)] hover:border-[var(--color-primary)]/50"
                  }`}
                >
                  <div className="font-medium">{type.name}</div>
                  <div className="text-xs text-[var(--text-muted)]">
                    {type.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-green-500 transition-colors"></div>
              <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
            </label>
            <span className="text-sm">Bot Aktif</span>
          </div>
        </div>

        {/* Pakasir Config (Store only) */}
        {botType === "store" && (
          <div className="glass-card p-6 space-y-4">
            <h2 className="text-lg font-semibold">💳 Konfigurasi Pakasir</h2>
            <p className="text-sm text-[var(--text-muted)]">
              Hubungkan dengan akun Pakasir untuk menerima pembayaran QRIS
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Project Slug
                </label>
                <input
                  type="text"
                  value={pakasirSlug}
                  onChange={(e) => setPakasirSlug(e.target.value)}
                  placeholder="nama-project"
                  className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  API Key
                  {bot.pakasir_api_key && (
                    <span className="text-green-400 text-xs ml-2">
                      ✓ Sudah diatur
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  value={pakasirApiKey}
                  onChange={(e) => setPakasirApiKey(e.target.value)}
                  placeholder={bot.pakasir_api_key ? "••••••••" : "pk_xxxxxx"}
                  className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-blue-500 focus:outline-none"
                />
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Kosongkan jika tidak ingin mengubah
                </p>
              </div>
            </div>

            {/* Test Connection Button */}
            <button
              type="button"
              onClick={testPakasir}
              disabled={isTesting || (!pakasirSlug && !bot.pakasir_slug)}
              className="w-full px-4 py-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 text-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTesting ? "⏳ Testing..." : "🔌 Test Koneksi Pakasir"}
            </button>

            {/* Test Result */}
            {testResult && (
              <div
                className={`p-3 rounded-lg text-sm ${
                  testResult.valid
                    ? "bg-green-500/10 border border-green-500/30 text-green-400"
                    : "bg-red-500/10 border border-red-500/30 text-red-400"
                }`}
              >
                {testResult.valid
                  ? `✅ ${testResult.message}`
                  : `❌ ${testResult.error}`}
              </div>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">⚡ Aksi Cepat</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {botType === "store" && (
              <>
                <button
                  type="button"
                  onClick={() => router.push(`/dashboard/store?bot=${botId}`)}
                  className="p-4 rounded-lg bg-[var(--bg-dark)] hover:bg-white/10 transition-colors text-center"
                >
                  <span className="text-2xl">📦</span>
                  <p className="text-sm mt-2">Kelola Produk</p>
                </button>
                <button
                  type="button"
                  onClick={() =>
                    router.push(`/dashboard/transactions?bot=${botId}`)
                  }
                  className="p-4 rounded-lg bg-[var(--bg-dark)] hover:bg-white/10 transition-colors text-center"
                >
                  <span className="text-2xl">💰</span>
                  <p className="text-sm mt-2">Transaksi</p>
                </button>
                <button
                  type="button"
                  onClick={() =>
                    router.push(`/dashboard/broadcast?bot=${botId}`)
                  }
                  className="p-4 rounded-lg bg-[var(--bg-dark)] hover:bg-white/10 transition-colors text-center"
                >
                  <span className="text-2xl">📢</span>
                  <p className="text-sm mt-2">Broadcast</p>
                </button>
              </>
            )}
            {botType === "sheerid" && (
              <button
                type="button"
                onClick={() => router.push("/dashboard/verification")}
                className="p-4 rounded-lg bg-[var(--bg-dark)] hover:bg-white/10 transition-colors text-center"
              >
                <span className="text-2xl">🔐</span>
                <p className="text-sm mt-2">Verification</p>
              </button>
            )}
            <a
              href={`https://t.me/${bot.bot_username.replace("@", "")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 rounded-lg bg-[var(--bg-dark)] hover:bg-white/10 transition-colors text-center"
            >
              <span className="text-2xl">💬</span>
              <p className="text-sm mt-2">Buka Bot</p>
            </a>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex gap-3">
          <button
            type="submit"
            className="btn-primary flex-1"
            disabled={isSaving}
          >
            {isSaving ? "Menyimpan..." : "💾 Simpan Perubahan"}
          </button>
        </div>
      </form>

      {/* Danger Zone */}
      <div className="glass-card p-6 border border-red-500/30">
        <h2 className="text-lg font-semibold text-red-400">
          ⚠️ Zona Berbahaya
        </h2>
        <p className="text-sm text-[var(--text-muted)] mt-2">
          Menghapus bot akan menghapus semua data terkait termasuk produk,
          transaksi, dan pengguna.
        </p>
        <button
          type="button"
          onClick={() => setShowDeleteConfirm(true)}
          className="mt-4 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/50 text-red-400 hover:bg-red-500/20 transition-colors"
        >
          🗑️ Hapus Bot
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setShowDeleteConfirm(false)}
          />
          <div className="relative glass-card p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-red-400">
              ⚠️ Konfirmasi Hapus
            </h2>
            <p className="text-[var(--text-muted)] mt-3">
              Anda yakin ingin menghapus bot <strong>{bot.bot_name}</strong>?
            </p>
            <p className="text-sm text-red-400 mt-2">
              Tindakan ini tidak dapat dibatalkan!
            </p>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary flex-1"
                disabled={isDeleting}
              >
                Batal
              </button>
              <button
                onClick={handleDelete}
                className="flex-1 px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-white transition-colors disabled:opacity-50"
                disabled={isDeleting}
              >
                {isDeleting ? "Menghapus..." : "Ya, Hapus"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
