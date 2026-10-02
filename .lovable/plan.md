# Restore rich inbox results

## Changes
- Keep every exam, scoring, reply, retry, and HTML-report flow unchanged.
- Harden only the personal result markdown so dynamic titles, metrics, section names, and question links cannot invalidate Telegram rich formatting.
- Preserve the existing rich table layout, reply-to-start-card behavior, Try Again button, and normal HTML fallback.

## Verification
- Run Python syntax/import checks.
- Confirm the final private-result handler still points to the rich implementation and no later override replaces it.
