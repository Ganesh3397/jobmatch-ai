"""
Send emails. Picks the first provider that is configured:

1. Brevo HTTP API  -> BREVO_API_KEY + EMAIL_FROM_ADDRESS (a sender verified in Brevo)
                      Works on Render's free plan (Render blocks SMTP ports there).
2. Gmail / SMTP    -> EMAIL_HOST_USER + EMAIL_HOST_PASSWORD (a Gmail *App Password*)
                      Best for running on your laptop.
3. Nothing set     -> emails are only printed in the terminal (console backend).

send_email() returns (ok: bool, error: str). It never raises.
"""
import logging

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

log = logging.getLogger(__name__)


def email_provider():
    if settings.BREVO_API_KEY:
        return "brevo"
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        return "gmail" if "gmail" in settings.EMAIL_HOST else "smtp"
    if "console" not in settings.EMAIL_BACKEND and "locmem" not in settings.EMAIL_BACKEND:
        return "smtp"
    return None


def email_configured():
    return email_provider() is not None


def sender_address():
    p = email_provider()
    if p == "brevo":
        return settings.EMAIL_FROM_ADDRESS
    if p in ("gmail", "smtp") and settings.EMAIL_HOST_USER:
        return settings.EMAIL_HOST_USER
    return settings.EMAIL_FROM_ADDRESS


def _brevo(to, subject, text, html):
    try:
        r = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json",
                     "content-type": "application/json"},
            json={
                "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM_ADDRESS},
                "to": [{"email": to}],
                "subject": subject,
                "textContent": text,
                "htmlContent": html or "<br>".join(text.splitlines()),
            },
            timeout=15,
        )
    except requests.RequestException as e:
        return False, f"Could not reach Brevo: {e}"
    if r.status_code >= 400:
        try:
            msg = r.json().get("message") or r.text
        except ValueError:
            msg = r.text
        hint = ""
        if r.status_code == 401:
            hint = " Check BREVO_API_KEY."
        elif "sender" in msg.lower():
            hint = f" Verify {settings.EMAIL_FROM_ADDRESS} as a sender in Brevo (Senders & IP)."
        return False, f"Brevo error {r.status_code}: {msg}.{hint}"
    return True, ""


def _smtp(to, subject, text, html):
    try:
        conn = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=settings.EMAIL_HOST, port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER, password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS, use_ssl=settings.EMAIL_USE_SSL, timeout=settings.EMAIL_TIMEOUT,
        ) if settings.EMAIL_HOST_USER else get_connection()
        msg = EmailMultiAlternatives(subject, text, f"{settings.EMAIL_FROM_NAME} <{sender_address()}>", [to],
                                     connection=conn)
        if html:
            msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        return True, ""
    except Exception as e:  # smtplib / socket errors
        err = str(e)
        if "535" in err or "Username and Password not accepted" in err:
            err = ("Gmail rejected the login. Use a 16-letter Gmail App Password (not your normal password) "
                   "in EMAIL_HOST_PASSWORD, and turn on 2-Step Verification.")
        elif any(k in err.lower() for k in ("timed out", "unreachable", "refused", "name or service",
                                             "getaddrinfo", "11001", "nodename")):
            err = (f"Could not connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT} ({e}). "
                   "Hosting providers such as Render's free plan block SMTP; use BREVO_API_KEY there.")
        return False, err


def send_email(to, subject, text, html=None):
    provider = email_provider()
    if provider == "brevo":
        ok, err = _brevo(to, subject, text, html)
    elif provider:
        ok, err = _smtp(to, subject, text, html)
    else:
        # not configured: print in the terminal (useful while developing)
        conn = get_connection()
        EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to], connection=conn).send()
        return False, "Email is not configured on the server."
    if not ok:
        log.warning("Email to %s failed: %s", to, err)
    return ok, err
