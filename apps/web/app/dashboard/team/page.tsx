"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Mail,
  Shield,
  Clock,
  Trash2,
  Copy,
  Check,
  AlertCircle,
  MoreVertical,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type OrganizationMember, type OrganizationInvitation } from "@/lib/api-client";

export default function TeamManagementPage() {
  const [organizations, setOrganizations] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>("");
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "editor" | "viewer">("viewer");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccessLink, setInviteSuccessLink] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Load organizations
  useEffect(() => {
    api
      .listOrganizations()
      .then((orgs) => {
        if (orgs && orgs.length > 0) {
          setOrganizations(orgs);
          setSelectedOrgId(orgs[0].id);
        } else {
          setIsLoading(false);
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to load organizations");
        setIsLoading(false);
      });
  }, []);

  // Load team data when selected organization changes
  useEffect(() => {
    if (!selectedOrgId) return;
    setIsLoading(true);
    setError(null);

    Promise.all([api.listMembers(selectedOrgId), api.listInvitations(selectedOrgId)])
      .then(([mems, invites]) => {
        setMembers(mems || []);
        setInvitations(invites || []);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load team data");
        setIsLoading(false);
      });
  }, [selectedOrgId]);

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId || !inviteEmail.trim()) return;

    setIsInviting(true);
    setError(null);
    setInviteSuccessLink(null);

    try {
      const res = await api.createInvitation(selectedOrgId, {
        invited_email: inviteEmail.trim(),
        invited_role: inviteRole,
      });

      if (res.manual_link) {
        setInviteSuccessLink(`${window.location.origin}${res.manual_link}`);
      }
      setInviteEmail("");
      // Refresh invitations list
      const updated = await api.listInvitations(selectedOrgId);
      setInvitations(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create invitation");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    if (!selectedOrgId) return;
    try {
      await api.revokeInvitation(selectedOrgId, inviteId);
      setInvitations(invitations.filter((i) => i.id !== inviteId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to revoke invitation");
    }
  };

  const handleRoleChange = async (memberId: string, newRole: string) => {
    if (!selectedOrgId) return;
    try {
      const updated = await api.updateMemberRole(selectedOrgId, memberId, newRole);
      setMembers(members.map((m) => (m.id === memberId ? updated : m)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update role");
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!selectedOrgId) return;
    if (!confirm("Are you sure you want to remove this member from the workspace?")) return;

    try {
      await api.removeMember(selectedOrgId, memberId);
      setMembers(members.filter((m) => m.id !== memberId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove member");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-rf-text">Team & Workspace Access</h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Manage workspace members, role-based authorization, and active invitations
          </p>
        </div>
        <div className="flex items-center gap-2">
          {organizations.length > 1 && (
            <select
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
              className="h-8 px-2.5 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:outline-none"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          )}
          <Button
            onClick={() => setShowInviteModal(true)}
            className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Invite Member</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rf-crimson flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rf-text-muted hover:text-rf-text text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Active Members Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Workspace Members</CardTitle>
              <CardDescription>Users who have authenticated access to this workspace</CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              {members.length} {members.length === 1 ? "member" : "members"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-xs text-rf-text-muted">Loading team roster...</div>
          ) : members.length === 0 ? (
            <div className="py-8 text-center text-xs text-rf-text-muted">No members found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-rf-border text-rf-text-muted font-medium">
                    <th className="pb-2.5">User</th>
                    <th className="pb-2.5">Email</th>
                    <th className="pb-2.5">Role</th>
                    <th className="pb-2.5">Joined</th>
                    <th className="pb-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rf-border/40">
                  {members.map((member) => (
                    <tr key={member.id} className="hover:bg-rf-surface/40 transition-colors">
                      <td className="py-3 font-medium text-rf-text">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-rf-surface border border-rf-border flex items-center justify-center font-mono text-[11px] text-rf-text font-bold">
                            {(member.display_name || member.full_name || member.email)[0].toUpperCase()}
                          </div>
                          <span>{member.display_name || member.full_name || "Workspace Member"}</span>
                        </div>
                      </td>
                      <td className="py-3 font-mono text-rf-text-secondary">{member.email}</td>
                      <td className="py-3">
                        <Badge
                          variant="outline"
                          className={`capitalize font-mono text-[10px] ${
                            member.role === "owner"
                              ? "border-rf-crimson text-rf-crimson bg-rf-crimson/10"
                              : member.role === "admin"
                              ? "border-amber-500/50 text-amber-400 bg-amber-500/10"
                              : member.role === "editor"
                              ? "border-blue-500/50 text-blue-400 bg-blue-500/10"
                              : "border-rf-border text-rf-text-secondary"
                          }`}
                        >
                          {member.role}
                        </Badge>
                      </td>
                      <td className="py-3 text-rf-text-muted font-mono text-[11px]">
                        {new Date(member.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 text-right">
                        {member.role !== "owner" && (
                          <div className="flex items-center justify-end gap-1.5">
                            <select
                              value={member.role}
                              onChange={(e) => handleRoleChange(member.id, e.target.value)}
                              className="h-7 px-2 rounded border border-rf-border bg-rf-surface text-[11px] text-rf-text focus:outline-none"
                            >
                              <option value="admin">Admin</option>
                              <option value="editor">Editor</option>
                              <option value="viewer">Viewer</option>
                            </select>
                            <button
                              onClick={() => handleRemoveMember(member.id)}
                              className="p-1.5 rounded hover:bg-rf-surface text-rf-text-muted hover:text-rf-crimson transition-colors"
                              title="Remove member"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Invitations Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Pending Invitations</CardTitle>
              <CardDescription>Invited team members awaiting account activation</CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              {invitations.length} pending
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {invitations.length === 0 ? (
            <div className="py-6 text-center text-xs text-rf-text-muted">
              No pending invitations for this workspace.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-rf-border text-rf-text-muted font-medium">
                    <th className="pb-2.5">Invited Email</th>
                    <th className="pb-2.5">Assigned Role</th>
                    <th className="pb-2.5">Invited By</th>
                    <th className="pb-2.5">Expires</th>
                    <th className="pb-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rf-border/40">
                  {invitations.map((inv) => (
                    <tr key={inv.id} className="hover:bg-rf-surface/40 transition-colors">
                      <td className="py-3 font-mono text-rf-text">{inv.invited_email}</td>
                      <td className="py-3">
                        <Badge variant="outline" className="capitalize font-mono text-[10px]">
                          {inv.invited_role}
                        </Badge>
                      </td>
                      <td className="py-3 text-rf-text-secondary">{inv.inviter_name || "Team Member"}</td>
                      <td className="py-3 font-mono text-rf-text-muted text-[11px]">
                        {new Date(inv.expires_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => handleRevokeInvite(inv.id)}
                          className="text-[11px] px-2 py-1 rounded border border-rf-border hover:bg-rf-crimson/10 hover:border-rf-crimson/30 hover:text-red-300 transition-colors"
                        >
                          Revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-rf-bg-secondary border border-rf-border rounded-lg shadow-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <h3 className="font-semibold text-sm text-rf-text">Invite Team Member</h3>
              <button
                onClick={() => {
                  setShowInviteModal(false);
                  setInviteSuccessLink(null);
                }}
                className="text-rf-text-muted hover:text-rf-text"
              >
                ✕
              </button>
            </div>

            {inviteSuccessLink ? (
              <div className="space-y-3">
                <div className="p-3 rounded bg-green-500/10 border border-green-500/30 text-xs text-green-300">
                  Invitation created successfully. In local development mode, you can copy the acceptance link below:
                </div>
                <div className="p-2.5 rounded bg-rf-surface border border-rf-border font-mono text-[11px] text-rf-text break-all flex items-center justify-between gap-2">
                  <span className="truncate">{inviteSuccessLink}</span>
                  <button
                    onClick={() => copyToClipboard(inviteSuccessLink)}
                    className="p-1.5 rounded hover:bg-rf-bg-secondary text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy link"
                  >
                    {copiedLink ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                <Button
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteSuccessLink(null);
                  }}
                  className="w-full text-xs h-8 bg-rf-surface border border-rf-border text-rf-text hover:bg-rf-border/50"
                >
                  Done
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSendInvite} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text" htmlFor="inviteEmail">
                    Recipient Email
                  </label>
                  <input
                    id="inviteEmail"
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="teammate@company.com"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text" htmlFor="inviteRole">
                    Workspace Role
                  </label>
                  <select
                    id="inviteRole"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:border-rf-crimson focus:outline-none"
                  >
                    <option value="viewer">Viewer — Read-only access to sites and audits</option>
                    <option value="editor">Editor — Can add/edit sites and trigger audits</option>
                    <option value="admin">Admin — Can manage team members and settings</option>
                  </select>
                </div>

                <div className="pt-2 flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowInviteModal(false)}
                    className="text-xs h-8"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isInviting}
                    className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8"
                  >
                    {isInviting ? "Creating..." : "Send Invitation"}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
