"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";

interface Command {
  id: number;
  bot_id: number;
  command_name: string;
  response_text: string;
  is_enabled: boolean;
}

interface Bot {
  id: number;
  bot_name: string;
  bot_username: string;
}

const DEFAULT_STORE_COMMANDS = [
  {
    command_name: "/start",
    description: "Pesan selamat datang",
    default_text:
      "Selamat datang di toko kami! 🛒\n\nGunakan menu di bawah untuk melihat produk.",
  },
  {
    command_name: "/menu",
    description: "Menu utama",
    default_text: "📋 Menu Utama\n\nPilih kategori produk di bawah ini:",
  },
  {
    command_name: "/help",
    description: "Bantuan",
    default_text:
      "❓ Bantuan\n\n/start - Mulai\n/menu - Lihat menu\n/order - Pesanan saya\n/help - Bantuan",
  },
  {
    command_name: "/order",
    description: "Cek pesanan",
    default_text: "📦 Pesanan Anda\n\nTidak ada pesanan aktif.",
  },
  {
    command_name: "/contact",
    description: "Kontak admin",
    default_text: "📞 Hubungi Admin\n\nUntuk bantuan, hubungi @admin",
  },
];

export default function StoreCommandsPage() {
  const searchParams = useSearchParams();
  const botId = searchParams.get("bot");

  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<number | null>(
    botId ? Number(botId) : null,
  );
  const [commands, setCommands] = useState<Command[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Editing state
  const [editingCommand, setEditingCommand] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    fetchBots();
  }, []);

  useEffect(() => {
    if (selectedBot) {
      fetchCommands();
    }
  }, [selectedBot]);

  const fetchBots = async () => {
    const result = await api.getBots();
    if (result.data?.bots) {
      const storeBots = result.data.bots.filter(
        (b: any) => b.bot_type === "store",
      );
      setBots(storeBots);
      if (!selectedBot && storeBots.length > 0) {
        setSelectedBot(storeBots[0].id);
      }
    }
    setIsLoading(false);
  };

  const fetchCommands = async () => {
    if (!selectedBot) return;
    setIsLoading(true);
    const result = await api.getBotCommands(selectedBot);
    if (result.data?.commands) {
      setCommands(result.data.commands);
    } else {
      // Initialize with defaults if no commands exist
      setCommands([]);
    }
    setIsLoading(false);
  };

  const getCommandText = (commandName: string): string => {
    const cmd = commands.find((c) => c.command_name === commandName);
    if (cmd) return cmd.response_text;
    const defaultCmd = DEFAULT_STORE_COMMANDS.find(
      (c) => c.command_name === commandName,
    );
    return defaultCmd?.default_text || "";
  };

  const isCommandEnabled = (commandName: string): boolean => {
    const cmd = commands.find((c) => c.command_name === commandName);
    return cmd ? cmd.is_enabled : true;
  };

  const startEditing = (commandName: string) => {
    setEditingCommand(commandName);
    setEditText(getCommandText(commandName));
  };

  const saveCommand = async (commandName: string) => {
    if (!selectedBot) return;
    setIsSaving(true);
    setError("");
    setSuccess("");

    const result = await api.saveBotCommand(selectedBot, {
      command_name: commandName,
      response_text: editText,
      is_enabled: isCommandEnabled(commandName),
    });

    if (result.error) {
      setError(result.error);
    } else {
      setSuccess(`Command ${commandName} berhasil disimpan!`);
      await fetchCommands();
      setEditingCommand(null);
    }
    setIsSaving(false);
  };

  const toggleCommand = async (commandName: string) => {
    if (!selectedBot) return;
    const currentEnabled = isCommandEnabled(commandName);

    await api.saveBotCommand(selectedBot, {
      command_name: commandName,
      response_text: getCommandText(commandName),
      is_enabled: !currentEnabled,
    });

    await fetchCommands();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">⚙️ Commands Configuration</h1>
          <p className="text-[var(--text-muted)]">
            Atur respons bot untuk setiap command
          </p>
        </div>
        <select
          value={selectedBot || ""}
          onChange={(e) => setSelectedBot(Number(e.target.value))}
          className="px-4 py-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]"
        >
          {bots.map((bot) => (
            <option key={bot.id} value={bot.id}>
              {bot.bot_name} ({bot.bot_username})
            </option>
          ))}
        </select>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm">
          {success}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Info Box */}
      <div className="glass-card p-4 border-l-4 border-blue-500">
        <p className="text-sm">
          💡 <strong>Tips:</strong> Pesan yang Anda atur di sini akan otomatis
          digunakan oleh bot Telegram. Anda bisa menggunakan emoji dan format
          teks untuk membuat pesan lebih menarik.
        </p>
      </div>

      {/* Commands List */}
      {isLoading ? (
        <div className="text-center py-10 text-[var(--text-muted)]">
          Loading...
        </div>
      ) : (
        <div className="space-y-4">
          {DEFAULT_STORE_COMMANDS.map((cmd) => (
            <div key={cmd.command_name} className="glass-card p-4">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="font-semibold text-blue-400">
                    {cmd.command_name}
                  </h3>
                  <p className="text-sm text-[var(--text-muted)]">
                    {cmd.description}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isCommandEnabled(cmd.command_name)}
                      onChange={() => toggleCommand(cmd.command_name)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-green-500 transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </label>
                </div>
              </div>

              {editingCommand === cmd.command_name ? (
                <div className="space-y-3">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)] min-h-[120px] font-mono text-sm"
                    placeholder="Masukkan respons command..."
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingCommand(null)}
                      className="px-4 py-2 text-sm rounded-lg bg-gray-500/20 text-gray-400"
                    >
                      Batal
                    </button>
                    <button
                      onClick={() => saveCommand(cmd.command_name)}
                      className="px-4 py-2 text-sm rounded-lg bg-blue-500 text-white"
                      disabled={isSaving}
                    >
                      {isSaving ? "Menyimpan..." : "💾 Simpan"}
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <pre className="p-3 rounded-lg bg-[var(--bg-dark)] text-sm text-[var(--text-muted)] whitespace-pre-wrap font-mono">
                    {getCommandText(cmd.command_name) || cmd.default_text}
                  </pre>
                  <button
                    onClick={() => startEditing(cmd.command_name)}
                    className="mt-3 px-4 py-2 text-sm rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                  >
                    ✏️ Edit Response
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
