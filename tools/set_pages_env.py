"""Cloudflare Pages の本番環境変数を設定し直す

    python tools/set_pages_env.py

いつ使うか:
  - メール通知が届かなくなり `notification_status` が `skipped` / `failed` になっているとき
  - Brevo の API キーを再発行したとき
  - 通知先アドレスを変えたいとき（下の NOTIFY_TO を書き換えてから実行）

なぜ wrangler ではなくこれを使うか（2026-08-20 に両方で事故を起こしたため）:
  1. `$key | npx wrangler pages secret put ...` は PowerShell のパイプで改行が混入し、
     Brevo が 401「Key not found」を返した。
  2. Cloudflare Pages の平文（plain_text）環境変数は、wrangler.toml に書かれていないと
     `wrangler pages deploy` に削除される。暗号化（secret_text）なら残る。
  → このスクリプトはレジストリから直接値を読み、3つとも secret_text で登録する。

実行後は必ずデプロイすること（環境変数は新しいデプロイから反映される）:
    npx wrangler pages deploy

認証は wrangler の OAuth トークンを流用する。事前に `npx wrangler whoami` を1回叩くと
トークンが更新される。キーの値は画面に出さない。
"""
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
import winreg

WRANGLER_CONFIG = pathlib.Path.home() / "AppData/Roaming/xdg.config/.wrangler/config/default.toml"
ACCOUNT_ID = "19534db9a0b4f7ad9de0571c82028bcd"
PROJECT = "kitakyushu-buppan"
API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}"

# 通知先。カンマ区切りで複数指定できる
NOTIFY_TO = "info@kitakyubuppan.com,goodspeedoffice@gmail.com"
# 送信元。Brevo 側で認証済みのアドレスでなければ送信は失敗する
NOTIFY_FROM = "info@kitakyubuppan.com"


def oauth_token() -> str:
    if not WRANGLER_CONFIG.exists():
        sys.exit(f"wrangler の認証情報がありません: {WRANGLER_CONFIG}\n`npx wrangler login` を実行してください。")
    m = re.search(r'oauth_token\s*=\s*"([^"]+)"', WRANGLER_CONFIG.read_text(encoding="utf-8"))
    if not m:
        sys.exit("oauth_token が見つかりません。`npx wrangler login` を実行してください。")
    return m.group(1)


def user_env(name: str) -> str:
    """Windows のユーザー環境変数を直接読む（シェルを経由しないので改行が混入しない）"""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        try:
            value, _ = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            sys.exit(f"ユーザー環境変数 {name} が見つかりません。")
    value = value.strip()
    if not value:
        sys.exit(f"ユーザー環境変数 {name} が空です。")
    return value


def patch(env_vars: dict) -> dict:
    req = urllib.request.Request(
        API,
        method="PATCH",
        data=json.dumps({"deployment_configs": {"production": {"env_vars": env_vars}}}).encode("utf-8"),
        headers={"Authorization": f"Bearer {oauth_token()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return json.loads(body)
        except Exception:
            sys.exit(f"HTTP {e.code}: {body[:400]}")


brevo_key = user_env("BREVO_API_KEY")
print(f"BREVO_API_KEY をレジストリから読み取りました（{len(brevo_key)} 文字）")

result = patch({
    "BREVO_API_KEY":       {"type": "secret_text", "value": brevo_key},
    "CONTACT_NOTIFY_TO":   {"type": "secret_text", "value": NOTIFY_TO},
    "CONTACT_NOTIFY_FROM": {"type": "secret_text", "value": NOTIFY_FROM},
})

if not result.get("success"):
    sys.exit("設定に失敗しました: " + json.dumps(result.get("errors"), ensure_ascii=False))

env_vars = result["result"]["deployment_configs"]["production"].get("env_vars") or {}
print("\n本番環境に設定された変数:")
for name in sorted(env_vars):
    print(f"  {name} [{env_vars[name].get('type')}]")

missing = {"BREVO_API_KEY", "CONTACT_NOTIFY_TO", "CONTACT_NOTIFY_FROM"} - set(env_vars)
if missing:
    sys.exit(f"\n設定されていない変数があります: {', '.join(sorted(missing))}")

print("\n次にデプロイしてください（環境変数は新しいデプロイから反映されます）:")
print("    npx wrangler pages deploy")
