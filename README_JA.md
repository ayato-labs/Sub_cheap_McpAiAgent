# Sub-cheap-McpAiAgent

**Sub-cheap-McpAiAgent** は、Claude 3.5 Sonnet などの高性能な「メインAI」のトークン消費量とコストを劇的に削減するために設計された、Model Context Protocol (MCP) サーバーです。

コードの初稿作成や技術コンテキストの翻訳といった、最もトークンを消費する「泥臭い作業」を安価なサブLLM（Google Gemini, ローカルの Ollama, または Genspark）に委譲します。メインAIは「指揮官（アーキテクト）」としての役割に専念させることができます。

## 🌟 主な機能

- **「建築家とアルバイト」の役割分担**: メインAI（建築家）が設計し、サブLLM（アルバイト）がコードを書くという分担に特化した設計。
- **Streamable HTTP (SSE) トランスポート**: 複数のAIエージェントによる並列実行に対応。Stdio 方式の「1対1」の制限を解消しました。
- **マルチバックエンド対応**: `.env` の設定一つで、**Google Gemini**, **ローカルの Ollama**, **Genspark (検索AI)** を自由に使い分け可能です。
- **ドラフト優先パイプライン**:
    1. **翻訳**: 日本語の指示を自動で英語に変換。
    2. **圧縮**: 大規模なコードコンテキストを動的に要約。
    3. **下書き**: アーキテクトが洗練させるための「叩き台（ドラフト）」品質のコードを生成。
- **堅牢な運用**: ステートレスHTTPモード、ホスト名ベースのエンドポイント、100文字制限のコードスタイルを採用。

## 🏗️ 設計思想

本プロジェクトの根幹は **「建築家とアルバイト」** モデルです：
- **メインAI（あなた）は建築家**: 高度な推論、設計、最終的な品質責任を負います。
- **サブLLMはアルバイト**: 指示に従ってコードをタイピングする「泥臭い作業」を担当します。
- **「叩き台（ドラフト）」品質の許容**: サブLLMの出力が完璧である必要はありません。多少のミスや不足は「ドラフト」として許容し、建築家が最終的に清書することで、システムをシンプルかつ高速に保ちます。

## 🚀 クイックスタート (Windows)

1.  **セットアップ**:
    `setup.bat` を実行して依存関係をインストールします（`uv` を使用）。

2.  **環境変数の設定**:
    `.env.example` を参考に `.env` ファイルを作成します。
    ```env
    AI_PROVIDER=gemini
    GOOGLE_API_KEY=あなたのキー
    ```

3.  **サーバーの起動**:
    `run.bat` を実行します。サーバーが `http://127.0.0.1:10300/mcp` で起動します。**このウィンドウは開いたままにしてください。**

4.  **Claude Desktop への登録**:
    `claude_desktop_config.json` に URL を追加します：
    ```json
    {
      "mcpServers": {
        "sub-cheap-mcp": {
          "url": "http://127.0.0.1:10300/mcp"
        }
      }
    }
    ```

## 📄 意思決定記録 (ADR)

- [ADR-0008: AIプロバイダーの明示的指定](docs/ADR/ADR-0008-explicit-ai-provider-configuration.md)
- [ADR-0009: Genspark CLI の統合](docs/ADR/ADR-0009-adoption-of-genspark-ai-provider.md)
- [ADR-0010: 建築家とアルバイトの分担モデル](docs/ADR/ADR-0010-architect-parttimer-delegation-model.md)
- [ADR-0011: Streamable HTTP への移行](docs/ADR/ADR-0011-switch-to-http-transport.md)
- [すべてのADRを表示](docs/ADR/)


## 🗺️ ロードマップと将来の展望

**現在のフェーズ (個人開発者向けMVP):**
現在、モデルのルーティングは `.env` ファイルによる明示的な指定に依存しています。これは、ユーザー自身がAPIキーを持ち込む「BYOK（Bring Your Own Key）」環境やローカル環境での実行を前提とした意図的な設計です。タスクの難易度を自動判定して高価なモデルへ勝手に切り替えたり、マシンのVRAMを超えるモデルをロードしたりする「自動タスクルーター」は導入していません。これにより、ユーザーはAPIコストとローカルリソースを100%制御し続けることができます。

**将来のSaaSフェーズ:**
マネージドなSaaSプラットフォームへと進化する際には、以下の実装を計画しています：
- **インテリジェント・タスクルーター**: プロンプトの複雑さを自動評価し、利益率とパフォーマンスを最大化するためにTier 1（Flash等）とTier 2（Pro/Opus等）のモデル間で自動ルーティングを行います。
- **自動QAリトライループ**: 静的解析（Semgrep等）に基づいてエラーを検知し、メインAIに結果を返す前にサブエージェント内部で自動修正ループを回します。

## 🏢 商用・ビジネス利用への対応 (Commercial & Business Use Ready)

本プロジェクトは、企業のビジネス環境やプロプライエタリなシステム内でも安全にご利用いただけるよう、コピーレフト型ライセンス（GPLなど）を排除し、寛容なオープンソースライセンス（Permissive License: MIT, Apache 2.0, BSD）の技術スタックのみで構築されています。

**依存ソフトウェア・ライセンス一覧:**
*   **[Ollama](https://github.com/ollama/ollama/blob/main/LICENSE)** (Local LLM Server): `MIT License`
*   **[FastMCP](https://github.com/jlowin/fastmcp/blob/main/LICENSE)** (MCP Framework): `MIT License`
*   **[google-genai](https://github.com/googleapis/python-genai/blob/main/LICENSE)** (Gemini SDK): `Apache License 2.0`
*   **[requests](https://github.com/psf/requests/blob/main/LICENSE)** (HTTP Client): `Apache License 2.0`
*   **[loguru](https://github.com/Delgan/loguru/blob/master/LICENSE)** (Logging): `MIT License`
*   **[python-dotenv](https://github.com/theskumar/python-dotenv/blob/main/LICENSE)** (Env Config): `BSD-3-Clause`

> **⚠️ 免責事項 (Important Disclaimer): AIモデル（重み）、API利用規約、およびライセンスの最終確認について**
> 1. **AIモデルとAPI**: 本MCPサーバーおよび上記の依存ソフトウェアはすべて商用利用可能なライセンスですが、**バックエンドとして呼び出す「AIモデル（重みデータ）」や「外部APIサービス」のライセンスおよび利用規約は、各プロバイダーに依存します。** 例：Ollama経由で使用するローカルモデル（Gemma, Llama等）や、Google AI StudioのAPI規約については、お客様のビジネス要件（MAU上限、商用利用の可否など）に合致するか各自でご確認ください。
> 2. **最終確認の責任**: 本ドキュメントのライセンス情報の正確性には万全を期しておりますが、**実際の商用・ビジネス利用におけるすべてのソフトウェアおよびモデルのライセンス適合性に関する「最終的な確認と遵守の責任」は、全面的にお客様（使用者）ご自身にあるものとします。**

## ⚖️ ライセンス

MIT License. 詳細は [LICENSE](LICENSE) をご覧ください。
