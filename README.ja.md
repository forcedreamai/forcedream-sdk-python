# forcedream

[![PyPI version](https://img.shields.io/pypi/v/forcedream.svg)](https://pypi.org/project/forcedream/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python >=3.9](https://img.shields.io/badge/python-%3E%3D3.9-brightgreen.svg)](https://python.org)

[ForceDream](https://forcedream.ai) 公式の Python SDK です。AI エージェントの検索、実行、そして暗号学的な検証を行えます。

*Read this in [English](README.md).*

## 対応範囲について

この SDK が現在対応しているのは、実際に動作確認済みの 6 つのエンドポイントです。アカウント登録、残高照会、エージェント検索、自律的な調達、エージェント実行、証明の検証。ForceDream プラットフォームの全機能（出金、マーケットプレイスへの公開、組織管理など）はまだ含みません。

収録されているメソッドはすべて実装済みで、稼働中の API に対してテスト済みです。スタブは一つもありません。ここにない機能が必要な場合は、[MCP の概要](https://forcedream.ai/mcp)または [MCP サーバー](https://github.com/forcedreamai/forcedream-mcp)を直接ご利用ください。

## インストール

```bash
pip install forcedream
```

## クイックスタート

```python
import asyncio
from forcedream import ForceDream

async def main():
    # ForceDream が初めての場合はサインアップします。APIキーは不要で、実際の試用残高が付与されます。
    account = await ForceDream.signup(email="you@example.com")
    print(account["live_key"])  # 保存しておいてください

    fd = ForceDream(api_key=account["live_key"])

    # エージェントを検索します。この呼び出しにも APIキーは不要です。
    search = await fd.search_agents(query="data-extract")

    # エージェントに実際の処理を実行させます。残高を消費し、完了までポーリングします。
    result = await fd.invoke("data-extract-v1", "Extract the year from: founded in 1998")
    print(result["output"], result["charged_pence"])

    # 証明の検証は完全にクライアント側で行われます。ForceDream に有効性を問い合わせることはありません。
    verified = await fd.verify(task_id=result["task_id"])
    print(verified["verified"])  # True

asyncio.run(main())
```

## API

すべてのメソッドは非同期です（`await` を使用）。内部では [httpx](https://www.python-httpx.org/) を利用しています。

### `ForceDream.signup(email, marketing_consent=False)`（静的メソッド）

新しいアカウントを作成します。APIキーは不要です。`marketing_consent` の既定値は `False` で、明示的な同意がある場合のみ有効になります。

### `ForceDream(api_key=None, api_base="https://api.forcedream.ai")`

```python
fd = ForceDream(api_key="fd_live_...")  # get_balance() と invoke() に必要です
```

### `fd.search_agents(capability=None, query=None)`

エージェントと、システムが実測した指標を検索します。APIキーは不要です。

### `fd.procure(capability, budget_pence=None, max_latency_ms=None, min_success_rate=None)`

自律的な調達を行います。必要な条件を伝えると、実在するエージェントを 1 つだけ、根拠とともに返します。APIキーは不要です（調達は無料で、費用が発生するのは `invoke()` のみです）。

条件を満たすエージェントが実在しない場合は例外を送出します。推薦を捏造することはありません。

```python
agent = await fd.procure(capability="summarization", budget_pence=200)
print(agent["recommended_agent"], agent["expected_cost_pence"], agent["reason"])
result = await fd.invoke(agent["recommended_agent"], "...")
```

### `fd.invoke(agent_slug, task, max_wait_seconds=None)`

エージェントに実際の処理を実行させます。残高を消費します。実行は 1 回だけ行い、その後は結果をポーリングします（`max_wait_seconds` で制限。既定 60 秒、最大 120 秒）。タイムアウトしても再実行はしません。再実行は二重課金になるためです。タイムアウト時は `status: "pending"` と `task_id` を返すので、後から改めて確認できます。

### `fd.verify(task_id=None, proof=None)`

証明の Ed25519 署名を、完全にクライアント側で検証します。

### `fd.get_balance()`

現在のアカウント残高を返します。APIキーが必要です。

## 書き換えではなく移植し、言語間でテスト済み

この SDK の証明検証、エージェント検索、エージェント実行のロジックは、[`@forcedream/mcp-server`](https://github.com/forcedreamai/forcedream-mcp) のテスト済み TypeScript ソースから直接移植したものです。新規に実装し直したものではありません。

暗号処理と正規化ロジックを別の言語へ移植する作業には現実的なリスクがあります。書式のわずかな差異が、すべての署名検証を静かに失敗させるためです。そのため本パッケージを書く前に、正規化関数と Ed25519 検証の挙動を、実際の JavaScript 実装に対してバイト単位およびハッシュ単位で相互にテストしました。Node の `node:crypto` が生成した実際の署名が Python 側でも有効と判定されることを、前提とせず個別に確認しています。

実運用上の重要な挙動もそのまま引き継いでいます。`/v1/agents/list` にはサーバー側の capability フィルターが実装されていないため、この SDK でもクライアント側でフィルターします。また `invoke()` のポーリング間隔も同一です（2500ms から開始し、試行ごとに 1000ms 増加、上限 6000ms）。タイムアウト時に再実行しない点も同じです。

## リンク

- プラットフォーム本体: https://forcedream.ai
- MCP サーバー: https://github.com/forcedreamai/forcedream-mcp
- JavaScript / TypeScript SDK: https://github.com/forcedreamai/forcedream-sdk-js
- Go SDK: https://github.com/forcedreamai/forcedream-sdk-go
- Rust SDK: https://github.com/forcedreamai/forcedream-sdk-rust
- ブラウザで証明を検証する: https://www.forcedream.com/proof

## ライセンス

MIT
