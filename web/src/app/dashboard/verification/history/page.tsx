"use client";

import { useEffect, useState, useCallback } from "react";
import api, {
  SheerIDVerification,
  SheerIDType,
  VerificationStatusResult,
} from "@/lib/api";

export default function VerificationHistoryPage() {
  const [verifications, setVerifications] = useState<SheerIDVerification[]>([]);
  const [types, setTypes] = useState<SheerIDType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVerification, setSelectedVerification] =
    useState<SheerIDVerification | null>(null);

  // Real-time status check state
  const [statusCheckResult, setStatusCheckResult] =
    useState<VerificationStatusResult | null>(null);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [autoRefreshTimer, setAutoRefreshTimer] = useState(0);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  // Auto refresh timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefreshEnabled && autoRefreshTimer > 0) {
      interval = setInterval(() => {
        setAutoRefreshTimer((prev) => {
          if (prev <= 1) {
            // Timer reached 0, check status
            if (selectedVerification) {
              handleCheckStatus(selectedVerification.id);
            }
            return 30; // Reset to 30 seconds
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [autoRefreshEnabled, autoRefreshTimer, selectedVerification]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [typesResult, verificationsResult] = await Promise.all([
        api.getSheerIDTypes(),
        api.getSheerIDVerifications(),
      ]);

      if (typesResult.data?.types) {
        setTypes(typesResult.data.types);
      }
      if (verificationsResult.data?.verifications) {
        setVerifications(verificationsResult.data.verifications);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setIsLoading(false);
  };

  const handleCheckStatus = useCallback(async (verificationId: number) => {
    setIsCheckingStatus(true);
    try {
      const result = await api.checkVerificationStatus(verificationId);
      if (result.data) {
        setStatusCheckResult(result.data);
        // Update the verification in list if status changed
        if (result.data.status) {
          setVerifications((prev) =>
            prev.map((v) =>
              v.id === verificationId
                ? {
                    ...v,
                    status: result.data?.approved
                      ? "success"
                      : result.data?.status || v.status,
                  }
                : v,
            ),
          );
        }
      }
    } catch (error) {
      console.error("Error checking status:", error);
    }
    setIsCheckingStatus(false);
  }, []);

  const handleOpenDetail = (v: SheerIDVerification) => {
    setSelectedVerification(v);
    setStatusCheckResult(null);
    // Auto-start check and timer when opening modal
    setAutoRefreshEnabled(true);
    setAutoRefreshTimer(30);
    // Immediately check status
    handleCheckStatus(v.id);
  };

  const handleEnableAutoRefresh = () => {
    setAutoRefreshEnabled(true);
    setAutoRefreshTimer(30);
    if (selectedVerification) {
      handleCheckStatus(selectedVerification.id);
    }
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
            ✅ Approved
          </span>
        );
      case "pending":
        return (
          <span className="px-2 py-1 text-xs font-medium bg-yellow-500/20 text-yellow-400 rounded-full">
            ⏳ Pending
          </span>
        );
      case "fraud_review":
        return (
          <span className="px-2 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded-full">
            🚫 Fraud Review
          </span>
        );
      case "failed":
      case "error":
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

  const getTypeInfo = (typeId: string) => {
    const type = types.find((t) => t.id === typeId);
    return type || { name: typeId, icon: "🔐" };
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
              📋
            </span>
            Riwayat Verifikasi
          </h1>
          <p className="text-[var(--text-muted)] mt-1">
            Semua riwayat verifikasi SheerID Anda
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 text-sm font-medium text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20 transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white/5 border border-[var(--border-color)]">
          <div className="text-2xl font-bold">{verifications.length}</div>
          <div className="text-sm text-[var(--text-muted)]">Total</div>
        </div>
        <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30">
          <div className="text-2xl font-bold text-green-400">
            {verifications.filter((v) => v.status === "success").length}
          </div>
          <div className="text-sm text-green-400/70">Approved</div>
        </div>
        <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
          <div className="text-2xl font-bold text-yellow-400">
            {verifications.filter((v) => v.status === "pending").length}
          </div>
          <div className="text-sm text-yellow-400/70">Pending</div>
        </div>
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
          <div className="text-2xl font-bold text-red-400">
            {
              verifications.filter((v) =>
                ["failed", "fraud_review", "error"].includes(v.status),
              ).length
            }
          </div>
          <div className="text-sm text-red-400/70">Failed</div>
        </div>
      </div>

      {/* History Table */}
      <div className="glass-card p-6">
        {verifications.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-muted)]">
            <div className="text-5xl mb-3">📋</div>
            <p className="text-lg font-medium">Belum ada riwayat verifikasi</p>
            <p className="text-sm mt-1">
              Submit verifikasi SheerID pertama Anda!
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-[var(--text-muted)] border-b border-[var(--border-color)]">
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Verification ID</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Student</th>
                  <th className="pb-3 font-medium">Points</th>
                  <th className="pb-3 font-medium">Date</th>
                  <th className="pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {verifications.map((v) => {
                  const typeInfo = getTypeInfo(v.verify_type);
                  return (
                    <tr
                      key={v.id}
                      className="border-b border-[var(--border-color)]/50 hover:bg-white/5"
                    >
                      <td className="py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{typeInfo.icon}</span>
                          <span className="text-sm font-medium">
                            {typeInfo.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-4">
                        <span className="text-sm text-[var(--text-muted)] font-mono">
                          {v.verify_id?.slice(0, 12) || "N/A"}...
                        </span>
                      </td>
                      <td className="py-4">{getStatusBadge(v.status)}</td>
                      <td className="py-4">
                        {v.student_name ? (
                          <div>
                            <div className="text-sm font-medium">
                              {v.student_name}
                            </div>
                            <div className="text-xs text-[var(--text-muted)] truncate max-w-[150px]">
                              {v.student_email}
                            </div>
                          </div>
                        ) : v.error_details ? (
                          <span className="text-sm text-red-400 truncate max-w-[150px] block">
                            {v.error_details.slice(0, 30)}...
                          </span>
                        ) : (
                          <span className="text-sm text-[var(--text-muted)]">
                            -
                          </span>
                        )}
                      </td>
                      <td className="py-4">
                        <span className="text-sm font-medium">
                          {v.points_cost} pts
                        </span>
                      </td>
                      <td className="py-4">
                        <span className="text-sm text-[var(--text-muted)]">
                          {formatDate(v.created_at)}
                        </span>
                      </td>
                      <td className="py-4">
                        <button
                          onClick={() => handleOpenDetail(v)}
                          className="text-sm text-green-400 hover:underline"
                        >
                          Check Status
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Modal with Real-time Status Check */}
      {selectedVerification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>
                  {getTypeInfo(selectedVerification.verify_type).icon}
                </span>
                Status Verifikasi
              </h3>
              <button
                onClick={() => {
                  setSelectedVerification(null);
                  setStatusCheckResult(null);
                  setAutoRefreshEnabled(false);
                }}
                className="text-[var(--text-muted)] hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Status Check Controls */}
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => handleCheckStatus(selectedVerification.id)}
                disabled={isCheckingStatus}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {isCheckingStatus ? "Checking..." : "🔍 Check Status Sekarang"}
              </button>
              {!autoRefreshEnabled ? (
                <button
                  onClick={handleEnableAutoRefresh}
                  className="px-4 py-2 text-sm font-medium text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20"
                >
                  ⏱️ Auto
                </button>
              ) : (
                <div className="px-4 py-2 text-sm font-medium text-yellow-400 bg-yellow-500/10 rounded-lg">
                  ⏱️ {autoRefreshTimer}s
                </div>
              )}
            </div>

            {/* Success Celebration Display */}
            {statusCheckResult?.approved && (
              <div className="mb-4 p-6 bg-gradient-to-br from-green-500/20 to-emerald-600/20 rounded-xl border border-green-500/30 text-center">
                <div className="text-4xl mb-2">🎊🎉✨</div>
                <h2 className="text-xl font-bold text-green-400 mb-1">
                  CONGRATULATIONS!
                </h2>
                <div className="text-3xl font-bold text-green-300 mb-2">
                  🏆 VERIFICATION APPROVED! 🏆
                </div>
                <div className="space-y-1 text-sm">
                  <p>
                    🆔 ID:{" "}
                    <span className="font-mono">
                      {selectedVerification.verify_id}
                    </span>
                  </p>
                  <p>
                    ✅ Status:{" "}
                    <span className="font-bold text-green-400">VERIFIED</span>
                  </p>
                  <p>💎 Credits: {statusCheckResult.credits || 0}</p>
                </div>

                {statusCheckResult.claim_url && (
                  <div className="mt-4 p-4 bg-white/10 rounded-lg">
                    <p className="text-sm text-yellow-400 mb-2">
                      🎁 CLAIM YOUR FREE BENEFIT! 🎁
                    </p>
                    <a
                      href={statusCheckResult.claim_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full px-4 py-3 text-sm font-bold text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all"
                    >
                      👇 TAP TO CLAIM 👇
                    </a>
                    <p className="text-xs text-[var(--text-muted)] mt-2">
                      🔗 {statusCheckResult.claim_url}
                    </p>
                  </div>
                )}

                <p className="text-sm text-green-400 mt-4">
                  🚀 Enjoy your FREE Premium! 🚀
                </p>
              </div>
            )}

            {/* Pending/Failed Status Display */}
            {statusCheckResult && !statusCheckResult.approved && (
              <div
                className={`mb-4 p-4 rounded-lg ${
                  statusCheckResult.status === "pending"
                    ? "bg-yellow-500/10 border border-yellow-500/30"
                    : "bg-red-500/10 border border-red-500/30"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">
                    {statusCheckResult.status === "pending" ? "⏳" : "❌"}
                  </span>
                  <span
                    className={`font-bold ${
                      statusCheckResult.status === "pending"
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {statusCheckResult.status_display ||
                      statusCheckResult.status?.toUpperCase()}
                  </span>
                </div>
                <p
                  className={`text-sm ${
                    statusCheckResult.status === "pending"
                      ? "text-yellow-400/80"
                      : "text-red-400/80"
                  }`}
                >
                  {statusCheckResult.message}
                </p>
                {statusCheckResult.status !== "pending" && (
                  <p className="text-xs text-[var(--text-muted)] mt-2">
                    ⚠️ Submit link SheerID baru untuk mencoba lagi.
                  </p>
                )}
              </div>
            )}

            {/* Verification Details */}
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Type:</span>
                <span className="font-medium">
                  {getTypeInfo(selectedVerification.verify_type).name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">
                  Real-time Status:
                </span>
                {statusCheckResult ? (
                  <span
                    className={`font-medium ${statusCheckResult.approved ? "text-green-400" : statusCheckResult.status === "pending" ? "text-yellow-400" : "text-red-400"}`}
                  >
                    {statusCheckResult.status_display ||
                      statusCheckResult.status}
                  </span>
                ) : (
                  <span className="text-[var(--text-muted)]">Loading...</span>
                )}
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
