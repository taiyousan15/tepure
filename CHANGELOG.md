# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- フロントエンドテストスイート (70テスト、80%+カバレッジ達成)
- TypeDoc APIドキュメント生成
- アーキテクチャドキュメント (Mermaid図含む)
- テストカバレッジレポート機能

## [0.4.0] - 2025-10-16

### Added
- Sprint 4: Dashboard強化とジョブAPI追加
  - テンプレート詳細モーダルUI実装 (311行)
  - UseTemplate画面の機能拡張 (26行)
  - Google Sheets連携機能追加 (56行)
  - 非同期ジョブ処理API (jobs.py新規)
- テンプレート詳細モーダル
- テンプレート使用画面の実装完了
- Dashboard統計表示機能
- 最近のジョブ一覧表示

### Changed
- APIルーティング調整 (app.py)
- Dashboard UIの大幅改善

## [0.3.0] - 2025-10-16

### Added
- Sprint 3: テンプレート一覧UI改善と登録フォーム画面
  - 検索機能 (リアルタイムフィルタリング)
  - カテゴリフィルター (LP/Banner/SNS/WebApp)
  - プレビュー画像表示
  - レスポンシブグリッドレイアウト
- テンプレート登録フォーム画面

### Changed
- Templates.tsx の全面リニューアル
- UIコンポーネントの改善

## [0.2.0] - 2025-10-16

### Added
- Sprint 2: Figmaプラグイン基本実装とテンプレート登録API
  - Figmaプラグインコア機能 (code.ts 159行)
  - テンプレート登録API
  - フレーム情報取得機能
  - サムネイル生成機能
- プラグインUI (ui.html)

### Changed
- Backend API構造の整理

## [0.1.0] - 2025-10-16

### Added
- Sprint 1: 認証とGoogle Sheets連携実装完了
  - Google OAuth 2.0認証
  - JWT トークン管理
  - Google Sheets API連携
  - PrivateRoute実装
- Login画面
- 認証ユーティリティ (auth.ts 159行)

### Security
- 環境変数による機密情報管理
- .envファイルを.gitignoreに追加

## [0.0.1] - 2025-10-16

### Added
- Sprint 0: プロジェクト雛形作成完了
  - React + TypeScript + Vite フロントエンド
  - Flask バックエンド
  - TailwindCSS スタイリング
  - React Router ルーティング
- 基本的なプロジェクト構造
- package.json設定
- TypeScript設定 (strict mode)
- Vite設定

## [0.0.0] - 2025-10-15

### Added
- 初期プロジェクトセットアップ
- Miyabi Framework統合
  - 7つの自律型AIエージェント
  - 識学理論65ラベル体系
  - GitHub Actions 26+ ワークフロー
- Claude Code設定
  - カスタムスラッシュコマンド
  - Agent定義
- GitHub リポジトリ初期化
- README.md、CLAUDE.md作成
- .gitignore設定

### Infrastructure
- GitHub Actions ワークフロー追加
  - autonomous-agent.yml - 自律型エージェント
  - auto-add-to-project.yml - Project自動追加
  - deploy-pages.yml - GitHub Pages デプロイ
  - economic-circuit-breaker.yml - コスト監視
  - issue-opened.yml - Issue自動処理
  - label-sync.yml - ラベル同期
  - pr-opened.yml - PR自動処理
  - project-sync.yml - Project同期
  - state-machine.yml - 状態機械
  - update-project-status.yml - ステータス更新
  - webhook-event-router.yml - Webhookルーティング
  - webhook-handler.yml - Webhook処理
  - weekly-kpi-report.yml - KPIレポート
  - weekly-report.yml - 週次レポート

---

## 変更タイプの定義

- **Added**: 新機能
- **Changed**: 既存機能の変更
- **Deprecated**: 近く削除される機能
- **Removed**: 削除された機能
- **Fixed**: バグ修正
- **Security**: セキュリティ関連の変更

## リリースノート

各リリースの詳細は [GitHub Releases](https://github.com/taiyousan15/tepure/releases) を参照してください。

---

🌸 Powered by Miyabi - Autonomous AI Development Framework
