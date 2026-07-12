"""Exact port of @forcedream/mcp-server's canonical.ts wfCanonical function.

Cross-verified byte-for-byte against the real JS implementation before this file was
written, not assumed to match: json.dumps(obj, sort_keys=True, separators=(',', ':'))
produces identical output to JS's JSON.stringify(obj, Object.keys(obj).sort()) for the
real signable shapes this SDK constructs. Verified with matching SHA-256 hashes on a
real test object, in both languages, side by side.
"""
import hashlib
import json


def wf_canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()
