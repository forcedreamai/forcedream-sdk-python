"""Exact port of @forcedream/mcp-server's invoke_agent.ts.

Ported precisely: exact endpoints, exact polling interval ramp (starts 2500ms, +1000ms per
attempt, capped at 6000ms), exact status handling, exact max-wait clamping (5-120s). Invokes
ONCE; never re-invokes on timeout, since that would double-charge -- returns a pollable
task_id instead. Not reconstructed from a description -- read directly from the real,
working source file before writing this, the same discipline as the JS SDK port.
"""
import asyncio
import time
from typing import Optional, TypedDict
import httpx


class InvokeResult(TypedDict, total=False):
    status: str  # 'completed' | 'insufficient' | 'pending' | 'error'
    agent: str
    task_id: Optional[str]
    output: object
    charged_pence: Optional[int]
    proof_id: Optional[str]
    error: Optional[str]
    message: str


async def invoke_agent(
    api_base: str,
    api_key: str,
    agent_slug: str,
    task: str,
    max_wait_seconds: Optional[float] = None,
) -> InvokeResult:
    headers = {'Authorization': f'Bearer {api_key}'}
    max_wait_s = max(5, min(120, max_wait_seconds if max_wait_seconds is not None else 60))
    max_wait_ms = max_wait_s * 1000

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        inv_res = await client.post(
            f'{api_base}/v1/agents/{agent_slug}/invoke',
            headers=headers,
            json={'task': task},
        )
        if inv_res.status_code == 401:
            return InvokeResult(status='error', agent=agent_slug, message='Invalid API key (401).')

        try:
            inv_json = inv_res.json()
        except Exception:
            inv_json = {}

        task_id = inv_json.get('task_id')
        if not task_id:
            err = inv_json.get('error') or inv_json.get('note') or 'no task_id'
            return InvokeResult(
                status='error', agent=agent_slug,
                message=f'Invoke failed (HTTP {inv_res.status_code}): {err}',
            )

        start = time.monotonic()
        interval_ms = 2500
        while (time.monotonic() - start) * 1000 < max_wait_ms:
            await asyncio.sleep(interval_ms / 1000)
            poll_res = await client.get(
                f'{api_base}/v1/agents/{agent_slug}/result/{task_id}',
                headers=headers,
            )
            try:
                d = poll_res.json()
            except Exception:
                d = {}
            status = d.get('status') or d.get('outcome')

            if status in ('completed', 'succeeded') or d.get('ok') is True:
                output = d.get('output')
                is_insufficient = d.get('outcome') == 'insufficient' or (
                    isinstance(output, dict) and output.get('confidence') == 'insufficient'
                )
                if is_insufficient:
                    return InvokeResult(
                        status='insufficient', agent=agent_slug, task_id=task_id,
                        output=output, charged_pence=0,
                        message='Agent returned insufficient evidence and declined rather than fabricate. Charged nothing.',
                    )
                proof_id = d.get('proof_id') or task_id
                return InvokeResult(
                    status='completed', agent=agent_slug, task_id=task_id,
                    output=output, charged_pence=d.get('charged_pence'), proof_id=proof_id,
                    message=f"Completed. Charged {d.get('charged_pence')}p. Cryptographically proven (proof_id {proof_id}).",
                )
            if status == 'insufficient':
                return InvokeResult(
                    status='insufficient', agent=agent_slug, task_id=task_id,
                    output=d.get('output'), charged_pence=0,
                    message='Agent declined (insufficient evidence). Charged nothing.',
                )
            if status == 'charge_failed':
                reason = d.get('reason') or 'insufficient_balance'
                return InvokeResult(
                    status='error', agent=agent_slug, task_id=task_id, charged_pence=0,
                    error='charge_failed',
                    message=f'Charge failed: {reason}. Nothing charged or delivered. Top up and retry.',
                )
            if status in ('failed', 'dead_letter'):
                reason = d.get('reason') or d.get('last_error') or 'unknown'
                return InvokeResult(
                    status='error', agent=agent_slug, task_id=task_id,
                    message=f'Task {status}: {reason}',
                )
            interval_ms = min(interval_ms + 1000, 6000)

    return InvokeResult(
        status='pending', agent=agent_slug, task_id=task_id,
        message=f'Still processing after {max_wait_ms / 1000}s. Not re-invoked (would double-charge). Poll the result later with this task_id.',
    )
