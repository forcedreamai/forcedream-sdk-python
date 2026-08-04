# Security Policy

## Reporting a vulnerability

If you find a security issue in this SDK (not the ForceDream platform itself),
please report it privately rather than opening a public issue.

Email: security@forcedream.ai

Please include:
- A description of the issue
- Steps to reproduce
- The version of `forcedream` affected

We aim to acknowledge reports within 5 business days.

## Reporting a platform issue

If you find a security issue in the ForceDream API or platform itself (not this
SDK's code), report it via the same email above rather than through this
SDK repository.

## Supported versions

Only the latest published version on PyPI receives security fixes. Please
upgrade before reporting an issue to confirm it's still present.

## API keys

This SDK never logs, caches, or transmits your `fd_live_` key anywhere except
directly to `api.forcedream.ai` over HTTPS, as part of the `Authorization`
header on requests that require billing. Treat your key as a secret.
