# MCP-AIWorker

[![CI](https://github.com/ayato-labs/MCP-AIWorker/actions/workflows/ci.yml/badge.svg)](https://github.com/ayato-labs/MCP-AIWorker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English Version is here](README.md)

**MCP-AIWorker** は、Claude 5 (Fable 5) などの高性能な「メインAI」のトークン消費量とAPIコストを劇的に削減するために設計された、Model Context Protocol (MCP) サーバーです。

定型的なコードの下書き作成、日本語から英語へのコンテキスト翻訳、数千行に及ぶビルド・テストログの要約など、トークン消費が激しく機械的な作業を安価なサブLLM（Google Gemini Flash、ローカルのOllama、またはGenspark Search AI）に委譲（アウトソーシング）し、メインAIは意思決定とシステム設計（**Architect**）に専念させます。

---

## 💸 なぜ MCP-AIWorker なのか？

AIエージェントによるテスト実行やソースコード全体の分析、リファクタリングなどの「試行錯誤ループ」は、コンテキストウィンドウを一瞬で消費し、高額なAPIコストを引き起こします。

本プロジェクトの **Architect-Worker（設計者と作業者）分業パラダイム** は、以下のメリットをもたらします。
*   **最大90%のコスト削減**: コード量が多くなりがちな下書き作成や翻訳処理を、無料枠のあるAPIやローカルモデルにオフロードします。*（注：90%削減はプロンプトキャッシュやローカルLLMをフル活用した場合の理論値・最大期待値であり、メインAIによる重複したファイル全体の単発読み込みが発生するユースケースでは30%〜40%程度の削減に落ち着きます）*
*   **開発速度の向上**: メインAIとのやり取りに必要なデータペイロードサイズを抑え、思考ループを高速化します。
*   **自己修復ループの排除**: 安価なモデル自身に完璧なコードを書かせるための、トークンを浪費するリトライ・検証ループを意図的に排除しています。サブLLMが出力した「叩き台（下書き）」を設計者（メインAI）が直接修正・インテグレーションすることで、最も効率よく安全な動作を実現します。

---

## 🏗️ Architect-Worker 分業モデル

```
                   +------------------------+
                   |       メインAI         |
                   |      (Architect)       |  <-- システム設計・最終検証
                   +-----------+------------+
                               |
                       MCP Tool Calls
                               v
                   +-----------+------------+
                   |      MCP-AIWorker      |
                   +-----------+------------+
                               |
               +---------------+---------------+
               |               |               |
               v               v               v
        +------------+   +------------+  +------------+
        |   Gemini   |   |   Ollama   |  |  Genspark  |  <-- 安価・ローカルLLM
        |   (API)    |   |  (ローカル)  |  |  (検索)    |      が泥臭いコーディング
        +------------+   +------------+  +------------+      やログ要約を担当
```

---

## 🌟 主な機能

*   **設計と実装の分離**: 下書きの作成処理をサブLLMに外部委託し、メインAIは高次元の設計と結合テストのみを管理します。
*   **Streamable HTTP (SSE) トランスポート**: FastMCPを採用したSSEトランスポートにより、複数のサブエージェントや複数スレッドからのツール並行実行に対応。従来のstdioによる1対1接続の制限を突破しています。
*   **堅牢なコード抽出パイプライン**: XMLタグマークアップ、切り捨てやタグ未クローズ時のコード救済処理、Markdownブロックへの自動フォールバック処理を組み合わせた多段階のパース制御。
*   **英語翻訳パイプライン**: 日本語での指示や参照コード内のコメントを自動的に英語へ翻訳してからサブLLMに渡すことで、モデルの理解度を最大化しトークン数を圧縮します。
*   **コンテキスト圧縮**: 長大な参照コードを構造（関数シグネチャ、型定義）を維持したまま最小限のロジックに自動圧縮します。
*   **実行ログ要約**: ビルドやテスト実行などのコマンドを実行し、数百行に上る標準出力・エラー出力を安価なサブLLMで要約。必要なエラー原因のみをメインAIへ送り返すことで、トークン枠を強力に保護します。

---

## 🚀 クイックスタート (Windows)

### 1. 環境構築
`uv` を利用し、ローカルの仮想環境へ依存関係をインストールします。
```bash
setup.bat
```

### 2. 環境変数の設定 (`.env`)
`.env.example` をコピーして `.env` ファイルを作成します。
```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=your-api-key-here
```

### 3. サーバーの起動
起動スクリプトを実行します。
```bash
run.bat
```
サーバーが `http://127.0.0.1:10300/mcp` で起動します。窓を開けたままにしてください。

### 4. Claude Desktop への登録
設定ファイル (`claude_desktop_config.json`) にエンドポイントを追記します。
```json
{
  "mcpServers": {
    "mcp-ai-worker": {
      "url": "http://127.0.0.1:10300/mcp"
    }
  }
}
```

---

## 🛠️ 提供されるツール

### `draft_code`
指定したファイルの特定行範囲にコードの下書き（叩き台）を作成し、書き込みます。
*   **path**: 対象ファイルの絶対パス。
*   **instruction**: コードの変更指示や追加要件。
*   **start_line / end_line** (オプション): 置換対象の行範囲。
*   **reference_context** (オプション): モデルに参照させたい関連クラスやユーティリティコード。

### `find_and_draft_edit`
リポジトリ全体を `grep-ast` 等でスキャンして影響箇所を特定し、そのファイルおよびクラスをピンポイントで抽出して修正の下書きを作成・書き込みます。

### `execute_command`
指定したコマンド（テスト、静的解析など）を実行し、その実行結果ログをサブLLMで簡潔なサマリーに要約して返します。

### `fetch_and_summarize_url`
指定された HTTPS URL からテキストコンテンツを抽出し、サブLLMを使用して正確な要約を生成してトークン消費を節約します（静的HTMLが必要です。シングルページアプリケーション（SPA）はサポートされていません）。
*   **url** (string): 取得する絶対 HTTPS URL。
*   **instruction** (オプション string): 要約時に特定してほしいフォーカス指示。


---

## 📄 アーキテクチャ決定レコード (ADR)

トレードオフと設計決定の記録：
*   [ADR-0010: Architect-Worker 分業モデル](docs/ADR/ADR-0010-architect-parttimer-delegation-model.md)
*   [ADR-0011: Streamable HTTP 移行](docs/ADR/ADR-0011-switch-to-http-transport.md)
*   [ADR-0012: 出力制御とタグ救済](docs/ADR/ADR-0012-robust-output-control-and-prompt-externalization.md)
*   [ADR-0013: 実行ログ要約エンジン](docs/ADR/ADR-0013-terminal-execution-log-summarization.md)

---

## ⚖️ ライセンス

MIT License。詳細は [LICENSE](LICENSE) を参照してください。
