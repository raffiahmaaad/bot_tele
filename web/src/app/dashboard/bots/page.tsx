"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface Bot {
  id: number;
  bot_username: string;
  bot_name: string;
  bot_type: string;
  is_active: boolean;
  products_count: number;
  users_count: number;
  transactions_count: number;
}

const BOT_TYPES = [
  {
    id: "store",
    name: "Store Bot",
    icon: "🛒",
    description: "Bot toko digital dengan pembayaran QRIS",
  },
  {
    id: "sheerid",
    name: "SheerID Bot",
    icon: "🔐",
    description: "Bot verifikasi student/teacher",
  },
];

export default function BotsPage() {
  const router = useRouter();
  const [bots, setBots] = useState<Bot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form state
  const [newBotToken, setNewBotToken] = useState("");
  const [botType, setBotType] = useState("store");
  const [pakasirSlug, setPakasirSlug] = useState("");
  const [pakasirApiKey, setPakasirApiKey] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState("");
  const [pakasirTestResult, setPakasirTestResult] = useState<{
    valid?: boolean;
    message?: string;
    error?: string;
  } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    fetchBots();
  }, []);

  const fetchBots = async () => {
    const result = await api.getBots();
    if (result.data?.bots) {
      setBots(result.data.bots);
    }
    setIsLoading(false);
  };

  const handleAddBot = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsAdding(true);

    const result = await api.createBot(
      newBotToken,
      botType,
      botType === "store" ? pakasirSlug : undefined,
      botType === "store" ? pakasirApiKey : undefined,
    );

    if (result.error) {
      setError(result.error);
      setIsAdding(false);
      return;
    }

    // Refresh bots list
    await fetchBots();
    closeModal();
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setNewBotToken("");
    setBotType("store");
    setPakasirSlug("");
    setPakasirApiKey("");
    setError("");
    setIsAdding(false);
    setPakasirTestResult(null);
    setIsTesting(false);
  };

  const testPakasir = async () => {
    if (!pakasirSlug || !pakasirApiKey) {
      setPakasirTestResult({
        valid: false,
        error: "Isi slug dan API key terlebih dahulu",
      });
      return;
    }
    setIsTesting(true);
    setPakasirTestResult(null);
    const result = await api.testPakasir(pakasirSlug, pakasirApiKey);
    if (result.data) {
      setPakasirTestResult(result.data);
    } else {
      setPakasirTestResult({
        valid: false,
        error: result.error || "Gagal test koneksi",
      });
    }
    setIsTesting(false);
  };

  const getBotTypeInfo = (type: string) => {
    return BOT_TYPES.find((t) => t.id === type) || BOT_TYPES[0];
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Bot Saya</h1>
          <p className="text-[var(--text-muted)]">
            Kelola bot Telegram toko Anda
          </p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn-primary">
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Tambah Bot
        </button>
      </div>

      {/* Bots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {bots.map((bot) => {
          const typeInfo = getBotTypeInfo(bot.bot_type);
          return (
            <div key={bot.id} className="glass-card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center text-white font-bold text-xl">
                    {typeInfo.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold">
                      {bot.bot_name || "Unnamed Bot"}
                    </h3>
                    <p className="text-sm text-[var(--text-muted)]">
                      {bot.bot_username}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`px-2 py-1 text-xs rounded-lg ${
                      bot.is_active
                        ? "text-green-400 bg-green-400/10"
                        : "text-yellow-400 bg-yellow-400/10"
                    }`}
                  >
                    {bot.is_active ? "Aktif" : "Nonaktif"}
                  </span>
                  <span className="px-2 py-0.5 text-xs rounded bg-white/10 text-[var(--text-muted)]">
                    {typeInfo.name}
                  </span>
                </div>
              </div>

              {bot.bot_type === "store" && (
                <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                  <div className="p-3 rounded-lg bg-[var(--bg-dark)]">
                    <p className="text-lg font-bold">
                      {bot.products_count || 0}
                    </p>
                    <p className="text-xs text-[var(--text-muted)]">Produk</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-dark)]">
                    <p className="text-lg font-bold">{bot.users_count || 0}</p>
                    <p className="text-xs text-[var(--text-muted)]">Users</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-dark)]">
                    <p className="text-lg font-bold">
                      {bot.transactions_count || 0}
                    </p>
                    <p className="text-xs text-[var(--text-muted)]">Order</p>
                  </div>
                </div>
              )}

              {bot.bot_type === "sheerid" && (
                <div className="mb-4 p-3 rounded-lg bg-[var(--bg-dark)]">
                  <p className="text-sm text-[var(--text-muted)]">
                    🔐 Verifikasi YouTube, Spotify, Apple TV+, dll
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => router.push(`/dashboard/bots/${bot.id}`)}
                  className="btn-secondary flex-1 !py-2 !text-sm"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                  </svg>
                  Setting
                </button>
                {bot.bot_type === "store" && (
                  <button
                    onClick={() =>
                      router.push(`/dashboard/store?bot=${bot.id}`)
                    }
                    className="btn-primary flex-1 !py-2 !text-sm"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                      />
                    </svg>
                    Produk
                  </button>
                )}
                {bot.bot_type === "sheerid" && (
                  <button
                    onClick={() => router.push(`/dashboard/verification`)}
                    className="btn-primary flex-1 !py-2 !text-sm"
                  >
                    🔐 Verify
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {/* Add Bot Card */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="glass-card p-6 border-2 border-dashed border-[var(--border-color)] hover:border-[var(--color-primary)] transition-colors flex flex-col items-center justify-center min-h-[250px] text-[var(--text-muted)] hover:text-white"
        >
          <div className="w-16 h-16 rounded-2xl bg-[var(--bg-dark)] flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </div>
          <p className="font-medium">Tambah Bot Baru</p>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Hubungkan bot Telegram Anda
          </p>
        </button>
      </div>

      {/* Add Bot Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={closeModal} />
          <div className="relative glass-card p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Tambah Bot Baru</h2>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleAddBot} className="space-y-4">
              {/* Bot Token */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Bot Token <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="w-full px-4 py-3 rounded-xl bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)] transition-all font-mono text-sm"
                  value={newBotToken}
                  onChange={(e) => setNewBotToken(e.target.value)}
                />
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Dapatkan dari @BotFather menggunakan /newbot
                </p>
              </div>

              {/* Bot Type Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Tipe Bot <span className="text-red-400">*</span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {BOT_TYPES.map((type) => (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setBotType(type.id)}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        botType === type.id
                          ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10"
                          : "border-[var(--border-color)] bg-[var(--bg-dark)] hover:border-[var(--color-primary)]/50"
                      }`}
                    >
                      <span className="text-2xl">{type.icon}</span>
                      <div className="mt-2 font-medium">{type.name}</div>
                      <div className="text-xs text-[var(--text-muted)] mt-1">
                        {type.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Pakasir Config (Store Only) */}
              {botType === "store" && (
                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30 space-y-3">
                  <h4 className="text-sm font-semibold text-blue-400 flex items-center gap-2">
                    💳 Pakasir Payment Config
                    <span className="text-xs font-normal text-[var(--text-muted)]">
                      (opsional)
                    </span>
                  </h4>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Pakasir Project Slug
                    </label>
                    <input
                      type="text"
                      placeholder="project-slug"
                      className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-blue-500 focus:outline-none"
                      value={pakasirSlug}
                      onChange={(e) => setPakasirSlug(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Pakasir API Key
                    </label>
                    <input
                      type="password"
                      placeholder="pk_xxxxxx"
                      className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] focus:border-blue-500 focus:outline-none"
                      value={pakasirApiKey}
                      onChange={(e) => setPakasirApiKey(e.target.value)}
                    />
                  </div>

                  {/* Test Connection Button */}
                  <button
                    type="button"
                    onClick={testPakasir}
                    disabled={isTesting || !pakasirSlug || !pakasirApiKey}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 text-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isTesting ? "⏳ Testing..." : "🔌 Test Koneksi Pakasir"}
                  </button>

                  {/* Test Result */}
                  {pakasirTestResult && (
                    <div
                      className={`p-2 rounded-lg text-sm ${
                        pakasirTestResult.valid
                          ? "bg-green-500/10 border border-green-500/30 text-green-400"
                          : "bg-red-500/10 border border-red-500/30 text-red-400"
                      }`}
                    >
                      {pakasirTestResult.valid
                        ? `✅ ${pakasirTestResult.message}`
                        : `❌ ${pakasirTestResult.error}`}
                    </div>
                  )}

                  <p className="text-xs text-[var(--text-muted)]">
                    Konfigurasi ini bisa diatur nanti di halaman Setting bot
                  </p>
                </div>
              )}

              {/* SheerID Info */}
              {botType === "sheerid" && (
                <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                  <h4 className="text-sm font-semibold text-green-400 flex items-center gap-2">
                    🔐 SheerID Bot Info
                  </h4>
                  <p className="text-xs text-[var(--text-muted)] mt-2">
                    Bot ini akan dapat memverifikasi akun student/teacher untuk
                    YouTube, Spotify, Apple TV+, dan layanan lainnya.
                  </p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn-secondary flex-1"
                  disabled={isAdding}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={isAdding || !newBotToken}
                >
                  {isAdding ? "Menambahkan..." : "Tambahkan Bot"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
