"use client";

/**
 * Google OAuth callback page.
 *
 * The backend handles the full OAuth code exchange at /api/auth/google/callback/
 * and returns a JSON response with access_token + refresh_token.
 *
 * If the backend is configured to redirect back to the frontend with tokens in
 * the URL fragment, this page handles that. Otherwise the user is redirected
 * directly from the backend JSON response to the dashboard via a fetch.
 */

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Completing Google sign-in...');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    // Handle tokens passed as query params from backend redirect
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');

    if (accessToken && refreshToken) {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('auth_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      setTimeout(() => { setStatus('success'); }, 0)
      setTimeout(() => {
          setMessage('Signed in successfully!');
        }, 0)
      setTimeout(() => router.push('/dashboard'), 1000);
      return;
    }

    if (error) {
      setTimeout(() => setStatus('error'), 0);
      setTimeout(() => setMessage(`Google sign-in was denied: ${error}`), 0);
      setTimeout(() => router.push('/login'), 3000);
      return;
    }

    if (!code || !state) {
      setTimeout(() => setStatus('error'), 0);
      setTimeout(() => setMessage('Invalid callback parameters.'), 0);
      setTimeout(() => router.push('/login'), 3000);
      return;
    }

    // Exchange code at the backend and get tokens
    const exchange = async () => {
      try {
        const resp = await fetch(
          `${API_BASE}/api/auth/google/callback/?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
          { headers: { 'Accept': 'application/json' } }
        );

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.error || 'Google authentication failed.');
        }

        const data = await resp.json();
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('auth_token', data.access_token);
          if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
          setStatus('success');
          setMessage('Signed in successfully!');
          setTimeout(() => router.push('/dashboard'), 800);
        } else {
          throw new Error('No token received from server.');
        }
      } catch (err: unknown) {
        setStatus('error');
        setMessage(err instanceof Error ? err.message : 'Authentication failed.');
        setTimeout(() => router.push('/login'), 3000);
      }
    };

    exchange();
  }, [router, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4 p-8">
        {status === 'loading' && (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
            <p className="text-lg font-medium">{message}</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto" />
            <p className="text-lg font-medium text-green-600">{message}</p>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="h-12 w-12 text-destructive mx-auto" />
            <p className="text-lg font-medium text-destructive">{message}</p>
            <p className="text-sm text-muted-foreground">Redirecting to login...</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
      </div>
    }>
      <GoogleCallbackContent />
    </Suspense>
  );
}
