"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface BotUser {
  id: number;
  telegram_id: string;
  username: string;
  first_name: string;
  last_name: string;
  is_blocked: boolean;
  created_at: string;
}

interface Bot {
  id: number;
  bot_name: string;
  bot_username: string;
}

export default function StoreUsersPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<number | null>(null);
  const [users, setUsers] = useState<BotUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchBots();
  }, []);

  useEffect(() => {
    if (selectedBot) {
      fetchUsers();
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

  const fetchUsers = async () => {
    if (!selectedBot) return;
    setIsLoading(true);
    const result = await api.getBotUsers(selectedBot);
    if (result.data?.users) {
      setUsers(result.data.users);
    }
    setIsLoading(false);
  };

  const filteredUsers = users.filter(
    (user) =>
      (user.username || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.first_name || "").toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">👥 Users</h1>
          <p className="text-[var(--text-muted)]">Pengguna Store Bot</p>
        </div>
        <div className="flex gap-3">
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
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold">{users.length}</p>
          <p className="text-sm text-[var(--text-muted)]">Total Users</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-green-400">
            {users.filter((u) => !u.is_blocked).length}
          </p>
          <p className="text-sm text-[var(--text-muted)]">Aktif</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-red-400">
            {users.filter((u) => u.is_blocked).length}
          </p>
          <p className="text-sm text-[var(--text-muted)]">Blocked</p>
        </div>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Cari user..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full md:w-80 px-4 py-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]"
        />
      </div>

      {/* Users List */}
      {isLoading ? (
        <div className="text-center py-10 text-[var(--text-muted)]">
          Loading...
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <p className="text-[var(--text-muted)]">Belum ada user</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredUsers.map((user) => (
            <div key={user.id} className="glass-card p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                  {(user.first_name || "U").charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-sm text-[var(--text-muted)] truncate">
                    @{user.username || "no_username"}
                  </p>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    user.is_blocked
                      ? "bg-red-500/20 text-red-400"
                      : "bg-green-500/20 text-green-400"
                  }`}
                >
                  {user.is_blocked ? "Blocked" : "Active"}
                </span>
              </div>
              <div className="mt-3 pt-3 border-t border-[var(--border-color)] text-xs text-[var(--text-muted)]">
                <p>ID: {user.telegram_id}</p>
                <p>
                  Bergabung:{" "}
                  {new Date(user.created_at).toLocaleDateString("id-ID")}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
