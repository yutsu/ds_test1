# Development Guide

## プロジェクト概要

Deep Research Clone - 言語モデルとWeb検索を組み合わせた研究支援ツール（改善版）

### 主要機能
- 🔍 Web検索（Google Custom Search API）
- 🤖 言語モデル（Ollama、OpenAI、Google Gemini）
- 📝 マークダウン出力
- 🎯 自動分析・要約
- 🔄 **反復改善検索** - レビューモデルによる追加検索
- 📚 **詳細引用管理** - 引用元の自動抽出と管理
- ⚙️ **設定ファイル対応** - YAML設定ファイルによる柔軟な設定

## 技術スタック

### 言語・フレームワーク
- **Python 3.9+**
- **uv** - パッケージ管理・仮想環境

### 主要ライブラリ
- `requests` - HTTP通信
- `pydantic` - データバリデーション
- `markdown` - マークダウン処理
- `python-dotenv` - 環境変数管理
- `openai` - OpenAI API
- `google-generativeai` - Google Gemini API
- `ollama` - Ollama API
- `PyYAML` - 設定ファイル管理

### 開発ツール
- `pytest` - テスト
- `black` - コードフォーマット
- `flake8` - リント
- `mypy` - 型チェック

## プロジェクト構造

```
deep_research_clone/
├── main.py              # メインアプリケーション（改善版）
├── pyproject.toml       # プロジェクト設定（uv用）
├── requirements.txt     # 依存関係（pip用）
├── config.example.yaml  # 設定ファイル例
├── config.yaml          # 設定ファイル（要作成）
├── .env                 # 環境変数（要作成）
├── env.example          # 環境変数設定例
├── .gitignore           # Git除外設定
├── README.md            # プロジェクト説明
├── DEVELOPMENT.md       # このファイル
└── idea.md              # アイデアメモ
```

## セットアップ手順

### 1. 依存関係インストール
```bash
uv sync
```

### 2. 環境変数設定
```bash
cp env.example .env
# .envファイルを編集してAPIキーを設定
```

### 3. 設定ファイル作成
```bash
cp config.example.yaml config.yaml
# config.yamlファイルを必要に応じて編集
```

### 4. 実行
```bash
python main.py
```

## 環境変数設定

### 必須設定（使用するAPIに応じて）
```bash
# OpenAI API
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini API
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Custom Search API
GOOGLE_SEARCH_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_SEARCH_ENGINE_ID=xxxxxxxxxxxxxxxxx
```

## アーキテクチャ（改善版）

### クラス設計

#### 1. データクラス
- `SearchResult` - 検索結果（検索クエリ情報付き）
- `Citation` - 引用情報
- `ResearchResult` - 研究結果（引用・追加クエリ情報付き）

#### 2. 設定管理
- `Config` - 設定ファイル管理

#### 3. 言語モデル
- `LanguageModel` - 抽象基底クラス
- `OllamaModel` - Ollamaローカルモデル
- `OpenAIModel` - OpenAI API
- `GoogleGeminiModel` - Google Gemini API

#### 4. 検索・分析
- `WebSearcher` - Web検索
- `CitationManager` - 引用管理
- `DeepResearch` - メイン処理（反復改善版）

### 処理フロー（改善版）
1. ユーザー入力（クエリ）
2. **初期検索実行**
3. **初期分析・要約生成**
4. **反復改善ループ**:
   - レビューモデルで追加検索キーワード生成
   - 追加検索実行
   - 全結果で再分析
5. **最終レポート生成**
6. **引用整理**
7. **マークダウン出力**

## 新機能詳細

### 1. 反復改善検索
- **レビューモデル**: 初期レポートを分析して追加検索キーワードを生成
- **追加検索**: 最大3回の反復で検索範囲を拡大
- **統合分析**: 全検索結果を統合して包括的な分析を実行

### 2. 詳細引用管理
- **自動抽出**: 分析結果から重要な情報源を自動抽出
- **関連度スコア**: 引用の重要度を数値化
- **詳細記録**: 検索クエリ、URL、内容を完全記録

### 3. 設定ファイル対応
- **YAML設定**: 柔軟な設定管理
- **デフォルト値**: 設定ファイルがない場合の自動フォールバック
- **カスタマイズ可能**: プロンプト、検索設定、出力形式をカスタマイズ

### 4. 情報源の信頼性評価・スコアリング（2024年6月追加）
- **自動信頼性評価**: URL・タイトル・スニペットから情報源の信頼性スコア（0.0-1.0）とタイプ（official, news, academic, blog等）を自動判定
- **信頼性スコアによる並び替え・フィルタ**: 検索結果は信頼性スコア順に並び替え、閾値未満は除外可能（config.yamlで閾値設定）
- **分析・レポートへの統合**: 各検索結果・引用に信頼性情報を明示し、プロンプトでも信頼性の高い情報源を優先するよう指示
- **マークダウン出力**: 検索結果・引用一覧に信頼性スコアとタイプを明記
- **テスト追加**: 信頼性評価・並び替え・フィルタリングの単体テストをtest_iteration.pyに追加

## 開発時の注意点

### 設定ファイル
- `config.yaml` が存在しない場合はデフォルト設定を使用
- 設定値は `Config.get()` メソッドで安全に取得
- 環境変数は自動的に読み込み

### 反復改善
- 最大反復回数は設定で調整可能（デフォルト3回）
- 追加検索キーワードは重複を自動排除
- 検索結果は累積的に蓄積

### 引用管理
- 関連度スコアの閾値で引用をフィルタリング
- 自動抽出と手動追加の両方に対応
- マークダウン出力で詳細な引用情報を表示

### エラーハンドリング
- APIキーがなくてもダミーデータで動作
- 各言語モデルで個別のエラーハンドリング
- 検索失敗時は空の結果を返す

### 拡張性
- 新しい言語モデルは `LanguageModel` を継承
- 新しい検索エンジンは `WebSearcher` を拡張
- 出力形式は `save_to_*` メソッドで追加
- 設定ファイルで新しいオプションを追加可能

## 今後の改修ポイント

### 短期目標
- [x] 反復改善検索機能
- [x] 詳細引用管理
- [x] 設定ファイル対応
- [ ] PDF出力機能
- [ ] より詳細なエラーメッセージ
- [ ] ログ機能の追加

### 中期目標
- [ ] PowerPoint出力機能
- [ ] Web UI（Streamlit/FastAPI）
- [ ] バッチ処理機能
- [ ] 複数検索エンジン対応
- [ ] 検索結果のキャッシュ機能

### 長期目標
- [ ] データベース連携
- [ ] ユーザー管理
- [ ] APIサーバー化
- [ ] プラグインシステム
- [ ] 機械学習による検索最適化

## テスト戦略

### 単体テスト
```bash
uv run pytest
```

### コード品質
```bash
uv run black .          # フォーマット
uv run flake8 .         # リント
uv run mypy .           # 型チェック
```

### 信頼性評価テスト
```bash
uv run pytest test_reliability_evaluation
```

### 並び替え・フィルタリングテスト
```bash
uv run pytest test_reliability_sorting
```

## トラブルシューティング

### よくある問題

#### 1. uv sync エラー
- `pyproject.toml` の構文エラーを確認
- Python バージョン要件を確認

#### 2. API キーエラー
- `.env` ファイルの存在確認
- API キーの有効性確認
- 環境変数の読み込み確認

#### 3. 設定ファイルエラー
- `config.yaml` のYAML構文を確認
- 設定値の型を確認
- デフォルト設定で動作確認

#### 4. 依存関係エラー
- `uv sync --reinstall` で再インストール
- キャッシュクリア: `uv cache clean`

#### 5. Google Custom Search API 429エラー（Too Many Requests）
- **原因**: API利用制限（クォータ）に達した
- **対処法**:
  - しばらく待ってから再実行（数分〜数時間）
  - Google Cloud Consoleでクォータ使用量を確認
  - 設定ファイルでレート制限を調整（`search.rate_limit.requests_per_second`を下げる）
  - 有料版へのアップグレードを検討

## パフォーマンス最適化

### 現在の制限
- 検索結果: 最大10件（Google API制限）
- 反復回数: 最大3回（設定可能）
- 同時処理: 逐次実行
- メモリ使用: 最小限

### 改善案
- 非同期処理の導入
- 検索結果のキャッシュ機能
- 結果の永続化
- 並列検索の実装

## セキュリティ考慮事項

### API キー管理
- `.env` ファイルは `.gitignore` に含める
- 本番環境では環境変数を使用
- API キーの定期的なローテーション

### 入力検証
- ユーザー入力のサニタイゼーション
- ファイル出力時のパス検証
- 設定ファイルの検証

### 引用の信頼性
- 情報源の信頼性評価
- 引用内容の検証
- 重複情報の統合

### 信頼性スコアの低い情報源はレポートで注意喚起・除外可能
- 引用の信頼性を明示し、ユーザーが判断しやすいよう配慮

## 参考資料

### 公式ドキュメント
- [uv Documentation](https://docs.astral.sh/uv/)
- [OpenAI API](https://platform.openai.com/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [Ollama API](https://ollama.ai/docs/api)
- [PyYAML Documentation](https://pyyaml.org/)

### 関連プロジェクト
- Deep Research（参考元）
- LangChain
- LlamaIndex

---

*最終更新: 2025年*

# 変更履歴
- 2025/06: 情報源の信頼性評価・スコアリング・分析統合・テスト追加
