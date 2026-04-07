/**
 * Google OAuth Callback Server (Multi-Account)
 * Usage: CLIENT_ID=xxx CLIENT_SECRET=xxx REDIRECT_URI=xxx bun run oauth-server.ts
 * 
 * Supports multiple Google accounts. After OAuth, detects the email
 * and saves token to /home/.z/google-oauth/tokens/<email>/token.json
 * Also keeps /home/.z/google-oauth/token.json as the "default" (first connected account).
 */

import { mkdirSync, existsSync, readFileSync } from "fs";

const CLIENT_ID = process.env.CLIENT_ID!;
const CLIENT_SECRET = process.env.CLIENT_SECRET!;
const REDIRECT_URI = process.env.REDIRECT_URI!;
const BASE_DIR = "/home/.z/google-oauth";
const TOKENS_DIR = `${BASE_DIR}/tokens`;

const SCOPES = [
  "https://www.googleapis.com/auth/calendar",
  "https://www.googleapis.com/auth/calendar.events",
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.send",
  "https://www.googleapis.com/auth/gmail.modify",
  "https://www.googleapis.com/auth/drive",
  "https://www.googleapis.com/auth/drive.file",
  "https://www.googleapis.com/auth/documents",
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/contacts",
  "https://www.googleapis.com/auth/contacts.readonly",
  "https://www.googleapis.com/auth/userinfo.email",
].join(" ");

const port = parseInt(process.env.PORT || "8085");

mkdirSync(TOKENS_DIR, { recursive: true });

function buildAuthUrl(loginHint?: string): string {
  const params: Record<string, string> = {
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: "code",
    scope: SCOPES,
    access_type: "offline",
    prompt: "consent",
  };
  if (loginHint) params.login_hint = loginHint;
  return `https://accounts.google.com/o/oauth2/v2/auth?${new URLSearchParams(params)}`;
}

async function exchangeCode(code: string): Promise<any> {
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code,
      grant_type: "authorization_code",
      redirect_uri: REDIRECT_URI,
    }),
  });
  return response.json();
}

async function getEmailFromToken(accessToken: string): Promise<string> {
  const resp = await fetch("https://www.googleapis.com/oauth2/v2/userinfo", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const data = await resp.json();
  return data.email || "unknown";
}

function listConnectedAccounts(): string[] {
  const accounts: string[] = [];
  try {
    const entries = require("fs").readdirSync(TOKENS_DIR, { withFileTypes: true });
    for (const e of entries) {
      if (e.isDirectory() && existsSync(`${TOKENS_DIR}/${e.name}/token.json`)) {
        accounts.push(e.name);
      }
    }
  } catch {}
  return accounts;
}

Bun.serve({
  port,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/" || url.pathname === "") {
      const accounts = listConnectedAccounts();
      const accountsHtml = accounts.length > 0
        ? `<div style="margin:20px 0;padding:16px;background:#f0f9f0;border-radius:8px;text-align:left">
            <strong>Connected accounts:</strong>
            <ul style="margin:8px 0">${accounts.map(a => `<li>${a}</li>`).join("")}</ul>
           </div>`
        : "";

      const authUrl = buildAuthUrl();
      return new Response(`
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Google OAuth Setup</title>
          <style>
            body { font-family: system-ui; max-width: 500px; margin: 80px auto; padding: 20px; text-align: center; }
            a.button { display: inline-block; background: #4285f4; color: white; padding: 12px 24px; 
                       text-decoration: none; border-radius: 6px; font-weight: 500; margin: 8px; }
            a.button:hover { background: #3367d6; }
          </style>
        </head>
        <body>
          <h1>Connect Google Account</h1>
          <p>Click below to authorize access to Calendar, Gmail, Drive, Docs, Sheets, and Contacts.</p>
          ${accountsHtml}
          <p><a class="button" href="${authUrl}">Sign in with Google</a></p>
        </body>
        </html>
      `, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    if (url.pathname === "/callback") {
      const code = url.searchParams.get("code");
      const error = url.searchParams.get("error");

      if (error) {
        return new Response(`<h1>Error: ${error}</h1>`, { 
          headers: { "Content-Type": "text/html" } 
        });
      }

      if (code) {
        const tokenData = await exchangeCode(code);
        
        if (tokenData.error) {
          return new Response(`<h1>Error: ${tokenData.error}</h1><p>${tokenData.error_description}</p>`, {
            headers: { "Content-Type": "text/html" }
          });
        }

        const email = await getEmailFromToken(tokenData.access_token);

        const toSave = {
          ...tokenData,
          email,
          client_id: CLIENT_ID,
          client_secret: CLIENT_SECRET,
          obtained_at: new Date().toISOString(),
        };

        const emailDir = `${TOKENS_DIR}/${email}`;
        mkdirSync(emailDir, { recursive: true });
        await Bun.write(`${emailDir}/token.json`, JSON.stringify(toSave, null, 2));

        if (!existsSync(`${BASE_DIR}/token.json`)) {
          await Bun.write(`${BASE_DIR}/token.json`, JSON.stringify(toSave, null, 2));
        }

        const accounts = listConnectedAccounts();

        return new Response(`
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <title>Connected!</title>
            <style>
              body { font-family: system-ui; max-width: 500px; margin: 80px auto; padding: 20px; }
              .success { color: #0a0; }
            </style>
          </head>
          <body>
            <h1 class="success">Connected: ${email}</h1>
            <p>Zo now has access to Calendar, Gmail, Drive, Docs, Sheets, and Contacts for <strong>${email}</strong>.</p>
            <p><strong>All connected accounts:</strong></p>
            <ul>${accounts.map(a => `<li>${a}</li>`).join("")}</ul>
            <p><a href="/">Add another account</a> or close this tab.</p>
          </body>
          </html>
        `, { headers: { "Content-Type": "text/html; charset=utf-8" } });
      }
    }

    return new Response("Not found", { status: 404 });
  },
});

console.log(`OAuth server running on port ${port}`);
console.log(`Redirect URI: ${REDIRECT_URI}`);
console.log(`Tokens directory: ${TOKENS_DIR}`);
