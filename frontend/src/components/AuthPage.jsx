import React, { useState } from "react";

const PROFILE_KEY = "orbitguard.profile";

export function getStoredProfile() {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_KEY) || "null");
  } catch {
    return null;
  }
}

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = (event) => {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Enter an email and password to continue.");
      return;
    }

    const existing = getStoredProfile();
    if (mode === "signup") {
      if (!name.trim()) {
        setError("Enter your name to create an operator profile.");
        return;
      }
      const profile = { name: name.trim(), email: email.trim().toLowerCase() };
      localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
      onAuthenticated(profile);
      return;
    }

    if (existing && existing.email !== email.trim().toLowerCase()) {
      setError("That email does not match the local operator profile.");
      return;
    }

    const profile = existing || { name: email.split("@")[0], email: email.trim().toLowerCase() };
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    onAuthenticated(profile);
  };

  return (
    <main className="auth-shell">
      <section className="auth-visual">
        <div className="auth-orbit orbit-one" />
        <div className="auth-orbit orbit-two" />
        <div className="auth-earth">OG</div>
        <span className="eyebrow">Mission control</span>
        <h1>OrbitGuard</h1>
        <p>Conjunction intelligence for the objects that matter most.</p>
      </section>

      <section className="auth-panel">
        <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
            Log in
          </button>
          <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")} type="button">
            Sign up
          </button>
        </div>
        <span className="eyebrow">Operator access</span>
        <h2>{mode === "login" ? "Welcome back" : "Create your profile"}</h2>
        <p className="auth-copy">
          {mode === "login" ? "Continue to your screening workspace." : "Set up a local profile for this browser."}
        </p>

        <form onSubmit={submit} className="auth-form">
          {mode === "signup" && (
            <label>
              Name
              <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" autoComplete="name" />
            </label>
          )}
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="operator@orbitguard.local" autoComplete="email" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter any local password" autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" type="submit">
            {mode === "login" ? "Enter dashboard" : "Create local profile"}
          </button>
        </form>
        <p className="auth-note">Demo mode: profile data stays in this browser until you clear its storage.</p>
      </section>
    </main>
  );
}
