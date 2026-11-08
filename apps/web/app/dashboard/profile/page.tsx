"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { User, Mail, ShieldCheck, KeyRound, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type Profile } from "@/lib/api-client";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        setProfile(p);
        setDisplayName(p.display_name || "");
        setFullName(p.full_name || "");
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load profile");
        setIsLoading(false);
      });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const updated = await api.updateMe({
        display_name: displayName.trim() || undefined,
        full_name: fullName.trim() || undefined,
      });
      setProfile(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-rf-text">Account Profile</h1>
        <p className="text-xs text-rf-text-secondary mt-1">
          Manage your personal identity, display preferences, and credentials
        </p>
      </div>

      {error && (
        <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rf-crimson flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="p-3 rounded bg-green-500/10 border border-green-500/30 text-xs text-green-300 flex items-center gap-2">
          <Check className="w-4 h-4 text-green-500" />
          <span>Profile changes saved successfully.</span>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>User Details</CardTitle>
          <CardDescription>Your public and workspace identity information</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-6 text-center text-xs text-rf-text-muted">Loading profile...</div>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="flex items-center gap-4 pb-2">
                <div className="w-14 h-14 rounded-full bg-rf-surface border border-rf-border flex items-center justify-center font-bold text-lg text-rf-text">
                  {(displayName || fullName || profile?.email || "U")[0].toUpperCase()}
                </div>
                <div>
                  <div className="font-medium text-sm text-rf-text">
                    {displayName || fullName || "User"}
                  </div>
                  <div className="font-mono text-xs text-rf-text-secondary">{profile?.email}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text" htmlFor="displayName">
                    Display Name
                  </label>
                  <input
                    id="displayName"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Alex (SEO Lead)"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text" htmlFor="fullName">
                    Full Legal / Official Name
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alexandra Smith"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text">Linked Primary Email</label>
                <div className="flex items-center justify-between p-2.5 rounded-md border border-rf-border bg-rf-surface/50 text-xs">
                  <span className="font-mono text-rf-text">{profile?.email}</span>
                  <Badge variant="outline" className="border-green-500/50 text-green-400 bg-green-500/10 text-[10px]">
                    Verified
                  </Badge>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Button
                  type="submit"
                  disabled={isSaving}
                  className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8"
                >
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      {/* Security & Credentials */}
      <Card>
        <CardHeader>
          <CardTitle>Security & Password</CardTitle>
          <CardDescription>Authentication security settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-md border border-rf-border bg-rf-surface/50 text-xs">
            <div className="flex items-center gap-2.5">
              <KeyRound className="w-4 h-4 text-rf-crimson" />
              <div>
                <div className="font-medium text-rf-text">Account Password</div>
                <div className="text-rf-text-secondary text-[11px]">Last changed securely</div>
              </div>
            </div>
            <Link
              href="/forgot-password"
              className="px-3 py-1.5 rounded border border-rf-border bg-rf-surface text-xs text-rf-text hover:bg-rf-border/50 transition-colors"
            >
              Reset Password
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
