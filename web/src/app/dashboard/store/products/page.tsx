"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface Product {
  id: number;
  bot_id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  category: string;
  is_active: boolean;
}

interface Bot {
  id: number;
  bot_name: string;
  bot_username: string;
}

export default function StoreProductsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<number | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    price: "",
    stock: "",
    category: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchBots();
  }, []);

  useEffect(() => {
    if (selectedBot) {
      fetchProducts();
      // Auto-refresh every 30 seconds for realtime data
      const interval = setInterval(fetchProducts, 30000);
      return () => clearInterval(interval);
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

  const fetchProducts = async () => {
    if (!selectedBot) return;
    setIsLoading(true);
    const result = await api.getProducts(selectedBot);
    if (result.data?.products) {
      setProducts(result.data.products);
    }
    setIsLoading(false);
  };

  const openAddModal = () => {
    setEditingProduct(null);
    setFormData({
      name: "",
      description: "",
      price: "",
      stock: "",
      category: "",
    });
    setError("");
    setIsModalOpen(true);
  };

  const openEditModal = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      description: product.description || "",
      price: product.price.toString(),
      stock: product.stock.toString(),
      category: product.category || "",
    });
    setError("");
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBot) return;
    setError("");
    setIsSaving(true);

    const productData = {
      name: formData.name,
      description: formData.description,
      price: Number(formData.price),
      stock: Number(formData.stock),
      category: formData.category,
    };

    let result;
    if (editingProduct) {
      result = await api.updateProduct(
        selectedBot,
        editingProduct.id,
        productData,
      );
    } else {
      result = await api.createProduct(selectedBot, productData);
    }

    if (result.error) {
      setError(result.error);
    } else {
      await fetchProducts();
      setIsModalOpen(false);
    }
    setIsSaving(false);
  };

  const handleDelete = async (productId: number) => {
    if (!selectedBot || !confirm("Hapus produk ini?")) return;
    await api.deleteProduct(selectedBot, productId);
    await fetchProducts();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">📦 Kelola Produk</h1>
          <p className="text-[var(--text-muted)]">
            Manage produk untuk Store Bot
          </p>
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
          <button
            onClick={fetchProducts}
            className="px-3 py-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:bg-white/10 transition-colors"
            title="Refresh data"
          >
            🔄
          </button>
          <button onClick={openAddModal} className="btn-primary">
            + Tambah Produk
          </button>
        </div>
      </div>

      {/* Products Grid */}
      {isLoading ? (
        <div className="text-center py-10 text-[var(--text-muted)]">
          Loading...
        </div>
      ) : products.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <p className="text-[var(--text-muted)]">Belum ada produk</p>
          <button onClick={openAddModal} className="btn-primary mt-4">
            Tambah Produk Pertama
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product) => (
            <div key={product.id} className="glass-card p-4">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold">{product.name}</h3>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    product.is_active
                      ? "bg-green-500/20 text-green-400"
                      : "bg-gray-500/20 text-gray-400"
                  }`}
                >
                  {product.is_active ? "Aktif" : "Nonaktif"}
                </span>
              </div>
              <p className="text-sm text-[var(--text-muted)] mb-3 line-clamp-2">
                {product.description || "Tidak ada deskripsi"}
              </p>
              <div className="flex justify-between items-center mb-3">
                <span className="text-lg font-bold text-blue-400">
                  Rp {product.price.toLocaleString("id-ID")}
                </span>
                <span className="text-sm text-[var(--text-muted)]">
                  Stock: {product.stock}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => openEditModal(product)}
                  className="flex-1 px-3 py-2 text-sm rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => handleDelete(product.id)}
                  className="px-3 py-2 text-sm rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setIsModalOpen(false)}
          />
          <div className="relative glass-card p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingProduct ? "Edit Produk" : "Tambah Produk"}
            </h2>

            {error && (
              <div className="p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Nama Produk *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)]"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Deskripsi
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)]"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Harga (Rp) *
                  </label>
                  <input
                    type="number"
                    value={formData.price}
                    onChange={(e) =>
                      setFormData({ ...formData, price: e.target.value })
                    }
                    className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Stock *
                  </label>
                  <input
                    type="number"
                    value={formData.stock}
                    onChange={(e) =>
                      setFormData({ ...formData, stock: e.target.value })
                    }
                    className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)]"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Kategori
                </label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) =>
                    setFormData({ ...formData, category: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-lg bg-[var(--bg-dark)] border border-[var(--border-color)]"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn-secondary flex-1"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={isSaving}
                >
                  {isSaving ? "Menyimpan..." : "Simpan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
