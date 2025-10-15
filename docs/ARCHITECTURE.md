# アーキテクチャドキュメント

## システム構成図

```mermaid
graph TB
    subgraph "User Layer"
        U[開発者]
        FU[エンドユーザー]
    end

    subgraph "Frontend Layer"
        FE[React + TypeScript]
        D[Dashboard]
        T[Templates]
        UT[UseTemplate]
        L[Login]
    end

    subgraph "Backend Layer"
        API[Flask API]
        A[Auth Service]
        TS[Template Service]
        SS[Sheets Service]
        JS[Jobs Service]
    end

    subgraph "External Services"
        GS[Google Sheets]
        GA[Google Auth]
        FG[Figma API]
        FB[Firebase Storage]
    end

    subgraph "Figma Plugin"
        FP[Figma Plugin]
        TG[Template Generator]
    end

    U -->|Issue作成| GH
    FU -->|アクセス| FE
    FE -->|API Call| API
    API -->|認証| A
    API -->|テンプレート管理| TS
    API -->|データ保存| SS
    API -->|ジョブ管理| JS
    A -->|OAuth| GA
    SS -->|Read/Write| GS
    TS -->|画像取得| FG
    TS -->|画像保存| FB
    FP -->|テンプレート登録| API
    TG -->|生成| FG

    style U fill:#e1f5ff
    style FU fill:#e1f5ff
    style FE fill:#fff4e6
    style API fill:#f3e5f5
    style GS fill:#e8f5e9
    style FP fill:#fce4ec
```

## データフロー図

### テンプレート使用フロー

```mermaid
sequenceDiagram
    participant User as エンドユーザー
    participant FE as Frontend
    participant API as Backend API
    participant Sheets as Google Sheets
    participant Figma as Figma API
    participant Storage as Firebase Storage

    User->>FE: テンプレート選択
    FE->>API: GET /api/templates/:id
    API->>Sheets: テンプレート情報取得
    Sheets-->>API: テンプレートデータ
    API-->>FE: テンプレート詳細
    FE->>User: 入力フォーム表示

    User->>FE: データ入力・送信
    FE->>API: POST /api/templates/:id/use
    API->>API: ジョブ作成
    API->>Figma: テンプレート複製
    Figma-->>API: 複製完了
    API->>Figma: レイヤーにデータ挿入
    Figma-->>API: 更新完了
    API->>Figma: 画像エクスポート
    Figma-->>API: 画像データ
    API->>Storage: 画像アップロード
    Storage-->>API: 画像URL
    API->>Sheets: ジョブ情報更新
    API-->>FE: 完了通知
    FE->>User: 結果表示・ダウンロード
```

### Figmaプラグイン登録フロー

```mermaid
sequenceDiagram
    participant Designer as デザイナー
    participant Plugin as Figma Plugin
    participant Figma as Figma API
    participant API as Backend API
    participant Sheets as Google Sheets

    Designer->>Plugin: テンプレート選択
    Plugin->>Figma: フレーム情報取得
    Figma-->>Plugin: レイヤー構造
    Plugin->>Designer: フィールド設定UI表示
    Designer->>Plugin: フィールド設定
    Plugin->>Figma: サムネイル生成
    Figma-->>Plugin: サムネイル画像
    Plugin->>API: POST /api/templates/register
    API->>Sheets: テンプレート保存
    Sheets-->>API: 保存完了
    API-->>Plugin: 登録完了
    Plugin->>Designer: 成功メッセージ
```

## コンポーネント構成

### Frontend (React)

```
frontend/src/
├── pages/
│   ├── Login.tsx          # 認証画面
│   ├── Dashboard.tsx      # ダッシュボード
│   ├── Templates.tsx      # テンプレート一覧
│   └── UseTemplate.tsx    # テンプレート使用画面
├── components/
│   ├── PrivateRoute.tsx   # 認証ルート
│   └── TemplateDetailModal.tsx  # 詳細モーダル
├── utils/
│   └── auth.ts            # 認証ユーティリティ
├── App.tsx                # メインアプリ
└── main.tsx               # エントリーポイント
```

### Backend (Flask)

```
backend/
├── app.py                 # メインアプリケーション
├── api/
│   └── jobs.py           # ジョブAPI（非同期処理）
└── services/
    └── sheets.py         # Google Sheets連携
```

### Figma Plugin

```
figma-plugin/
├── code.ts               # プラグインロジック
└── ui.html               # プラグインUI
```

## 技術スタック

### Frontend
- **React 18** - UIフレームワーク
- **TypeScript** - 型安全
- **Vite** - ビルドツール
- **TailwindCSS** - スタイリング
- **React Router** - ルーティング
- **Vitest** - テストフレームワーク
- **React Testing Library** - コンポーネントテスト

### Backend
- **Flask** - Pythonウェブフレームワーク
- **Google API Client** - Google連携
- **Firebase Admin SDK** - Firebase連携

### DevOps & CI/CD
- **GitHub Actions** - 26+ ワークフロー
- **Miyabi Framework** - 自律型開発環境
- **7 AI Agents** - 自動化エージェント

## セキュリティアーキテクチャ

```mermaid
graph LR
    subgraph "認証層"
        GA[Google OAuth 2.0]
        JWT[JWT トークン]
    end

    subgraph "認可層"
        AC[アクセス制御]
        PR[Private Routes]
    end

    subgraph "データ保護"
        ENV[環境変数]
        FB[Firebase Security Rules]
        GS[Sheets Permissions]
    end

    GA --> JWT
    JWT --> AC
    AC --> PR
    ENV --> GA
    ENV --> FB
    ENV --> GS

    style GA fill:#e8f5e9
    style JWT fill:#fff3e0
    style ENV fill:#ffebee
```

### セキュリティ対策

1. **認証**
   - Google OAuth 2.0による認証
   - JWTトークンでセッション管理
   - トークンの有効期限管理

2. **認可**
   - Private Routeによるページアクセス制御
   - APIエンドポイントの認証チェック

3. **データ保護**
   - 環境変数で機密情報管理
   - `.env`ファイルを`.gitignore`に含める
   - Firebase Security Rulesによるストレージ保護
   - Google Sheetsのアクセス権限管理

4. **通信**
   - HTTPS通信必須
   - CORSポリシー設定

## デプロイメント構成

```mermaid
graph TB
    subgraph "開発環境"
        DEV[Local Development]
    end

    subgraph "CI/CD"
        GH[GitHub Actions]
        TEST[自動テスト]
        BUILD[ビルド]
        DEPLOY[デプロイ]
    end

    subgraph "本番環境"
        FE_PROD[Frontend\nFirebase Hosting]
        BE_PROD[Backend\nGoogle Cloud Run]
        DB_PROD[Database\nGoogle Sheets]
    end

    DEV -->|Push| GH
    GH --> TEST
    TEST -->|成功| BUILD
    BUILD --> DEPLOY
    DEPLOY --> FE_PROD
    DEPLOY --> BE_PROD
    BE_PROD --> DB_PROD

    style TEST fill:#e8f5e9
    style BUILD fill:#fff3e0
    style DEPLOY fill:#e1f5ff
```

## Miyabi Agentアーキテクチャ

```mermaid
graph TB
    subgraph "Coordinator Layer"
        C[CoordinatorAgent]
    end

    subgraph "Specialist Agents"
        I[IssueAgent]
        CG[CodeGenAgent]
        R[ReviewAgent]
        T[TestAgent]
        P[PRAgent]
        D[DeploymentAgent]
    end

    subgraph "External Services"
        GH[GitHub]
        AN[Anthropic API]
    end

    GH -->|Webhook| C
    C -->|Decompose| I
    C -->|Assign| CG
    C -->|Assign| R
    C -->|Assign| T
    C -->|Assign| P
    C -->|Assign| D
    CG -->|Generate| AN
    R -->|Quality Check| CG
    T -->|Test| CG
    P -->|Create PR| GH
    D -->|Deploy| GH

    style C fill:#e1f5ff
    style I fill:#f3e5f5
    style CG fill:#fff4e6
    style R fill:#fce4ec
```

## パフォーマンス最適化

### Frontend
- **Code Splitting** - ルート単位での分割
- **Lazy Loading** - 画像の遅延読み込み
- **Memoization** - React.memoによる再レンダリング防止
- **Virtual Scrolling** - 長いリストの仮想化

### Backend
- **非同期処理** - ジョブキューで重い処理を分離
- **キャッシング** - Sheets APIのレスポンスキャッシュ
- **バッチ処理** - 複数リクエストの一括処理

### Network
- **CDN** - Firebase Hostingによる配信
- **圧縮** - gzip/brotli圧縮
- **HTTP/2** - マルチプレクシング

## モニタリング

```mermaid
graph LR
    APP[Application] -->|Logs| LOG[Cloud Logging]
    APP -->|Metrics| MON[Cloud Monitoring]
    APP -->|Errors| ERR[Error Tracking]

    LOG --> DASH[Dashboard]
    MON --> DASH
    ERR --> DASH

    DASH -->|Alerts| TEAM[開発チーム]

    style APP fill:#e1f5ff
    style DASH fill:#fff4e6
    style TEAM fill:#e8f5e9
```

### 監視項目
- **可用性** - アップタイム監視
- **パフォーマンス** - レスポンスタイム
- **エラー率** - HTTP 5xx エラー
- **使用率** - API呼び出し回数
- **ユーザー数** - アクティブユーザー

## スケーラビリティ

### 水平スケーリング
- Firebase Hostingの自動スケール
- Cloud Runのオートスケーリング

### 垂直スケーリング
- インスタンスサイズの調整
- メモリ・CPUの増強

### データベース
- Google Sheetsの読み取りキャッシュ
- 将来的にCloud Firestoreへの移行検討

---

📐 このドキュメントはプロジェクトの成長と共に更新されます。
