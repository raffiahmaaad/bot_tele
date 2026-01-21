"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface Transaction {
  id: number;
  bot_id: number;
  user_id: number;
  product_name: string;
  amount: number;
  status: string;
  payment_method: string;
  created_at: string;
}

interface Bot {
  id: number;
  bot_name: string;
  bot_username: string;
}

export default function StoreTransactionsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchBots();
  }, []);

  useEffect(() => {
    if (selectedBot) {
      fetchTransactions();
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

  const fetchTransactions = async () => {
    if (!selectedBot) return;
    setIsLoading(true);
    const result = await api.getTransactions(selectedBot);
    if (result.data?.transactions) {
      setTransactions(result.data.transactions);
    }
    setIsLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500/20 text-green-400";
      case "pending":
        return "bg-yellow-500/20 text-yellow-400";
      case "paid":
        return "bg-blue-500/20 text-blue-400";
      case "cancelled":
        return "bg-red-500/20 text-red-400";
      default:
        return "bg-gray-500/20 text-gray-400";
    }
  };

  const filteredTransactions =
    filter === "all"
      ? transactions
      : transactions.filter((t) => t.status === filter);

  const totalRevenue = transactions
    .filter((t) => t.status === "completed")
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">💰 Transaksi</h1>
          <p className="text-[var(--text-muted)]">
            Riwayat transaksi Store Bot
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

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold">{transactions.length}</p>
          <p className="text-sm text-[var(--text-muted)]">Total Transaksi</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-green-400">
            {transactions.filter((t) => t.status === "completed").length}
          </p>
          <p className="text-sm text-[var(--text-muted)]">Selesai</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-yellow-400">
            {transactions.filter((t) => t.status === "pending").length}
          </p>
          <p className="text-sm text-[var(--text-muted)]">Pending</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-blue-400">
            Rp {totalRevenue.toLocaleString("id-ID")}
          </p>
          <p className="text-sm text-[var(--text-muted)]">Total Revenue</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {["all", "pending", "paid", "completed", "cancelled"].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              filter === status
                ? "bg-blue-500 text-white"
                : "bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-white"
            }`}
          >
            {status === "all"
              ? "Semua"
              : status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Transactions List */}
      {isLoading ? (
        <div className="text-center py-10 text-[var(--text-muted)]">
          Loading...
        </div>
      ) : filteredTransactions.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <p className="text-[var(--text-muted)]">Belum ada transaksi</p>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-[var(--bg-dark)]">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  Produk
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  Amount
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  Tanggal
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((tx) => (
                <tr
                  key={tx.id}
                  className="border-t border-[var(--border-color)]"
                >
                  <td className="px-4 py-3 text-sm">#{tx.id}</td>
                  <td className="px-4 py-3 text-sm">{tx.product_name}</td>
                  <td className="px-4 py-3 text-sm font-medium">
                    Rp {tx.amount.toLocaleString("id-ID")}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${getStatusColor(tx.status)}`}
                    >
                      {tx.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">
                    {new Date(tx.created_at).toLocaleDateString("id-ID")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
