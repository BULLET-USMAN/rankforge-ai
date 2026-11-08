import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  const pathname = request.nextUrl.pathname;

  // Static files and internal Next.js assets
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.includes(".")
  ) {
    return response;
  }

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://mock-supabase.rankforge.internal";
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "dummy-anon-key";

  const supabase = createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options)
        );
      },
    },
  });

  // Check for active Supabase session or local dev token cookie
  let hasSession = false;
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      hasSession = true;
    }
  } catch {
    // Supabase auth service unavailable or offline mock
  }

  // Also check dev session cookie for offline/local development & E2E smoke tests
  if (!hasSession) {
    const devToken = request.cookies.get("rf-auth-token")?.value || request.cookies.get("sb-access-token")?.value;
    if (devToken) {
      hasSession = true;
    }
  }

  const isAuthRoute =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/forgot-password") ||
    pathname.startsWith("/reset-password");

  const isProtectedRoute = pathname.startsWith("/dashboard") || pathname.startsWith("/onboarding");

  // Redirect unauthenticated traffic away from dashboard
  if (isProtectedRoute && !hasSession) {
    // If running in development with mock Supabase without auth yet, allow local access
    const isMock = url.includes("mock-supabase") || url.includes(".internal");
    if (!isMock) {
      const redirectUrl = new URL("/login", request.url);
      redirectUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(redirectUrl);
    }
  }

  // Redirect authenticated users away from login/register
  if (isAuthRoute && hasSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
