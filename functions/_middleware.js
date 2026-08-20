const PRIVATE_PATHS = new Set(["/members-only", "/members-only.html"]);
const PUBLIC_HOSTS = new Set([
  "kitakyusyubuppan.com",
  "www.kitakyusyubuppan.com",
]);
const ACCESS_PROTECTED_URL = "https://kitakyushu-buppan.pages.dev/members-only";

export async function onRequest(context) {
  const url = new URL(context.request.url);

  if (PUBLIC_HOSTS.has(url.hostname) && PRIVATE_PATHS.has(url.pathname)) {
    return Response.redirect(ACCESS_PROTECTED_URL, 302);
  }

  return context.next();
}
