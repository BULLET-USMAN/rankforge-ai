import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") || "/dashboard";

  // Resolve safe origin in production (supports Vercel edge reverse proxies and custom domains)
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") || "https";
  const effectiveOrigin = process.env.NEXT_PUBLIC_SITE_URL
    ? process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, "")
    : forwardedHost
      ? `${forwardedProto}://${forwardedHost}`
      : origin;

  if (code) {
    try {
      const supabase = await getSupabaseServerClient();
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (!error) {
        return NextResponse.redirect(`${effectiveOrigin}${next}`);
      }
    } catch {
      // Ignore exchange errors and redirect to login
    }
  }

  // Return the user to login with instructions
  return NextResponse.redirect(
    `${effectiveOrigin}/login?error=auth_callback_failed`
  );
}
