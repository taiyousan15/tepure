# パフォーマンス最適化ガイド

## 概要

このドキュメントでは、tepure（Figmaテンプレート自動化システム）のパフォーマンス最適化戦略とLighthouse監査の実施方法を説明します。

## パフォーマンス目標

### Core Web Vitals

| 指標 | 目標値 | 現在値 | ステータス |
|------|--------|--------|-----------|
| **LCP** (Largest Contentful Paint) | < 2.5s | TBD | 🔄 |
| **FID** (First Input Delay) | < 100ms | TBD | 🔄 |
| **CLS** (Cumulative Layout Shift) | < 0.1 | TBD | 🔄 |
| **FCP** (First Contentful Paint) | < 2.0s | TBD | 🔄 |
| **TTI** (Time to Interactive) | < 3.5s | TBD | 🔄 |

### Lighthouse スコア目標

| カテゴリ | 目標スコア | 現在値 | ステータス |
|---------|----------|--------|-----------|
| **Performance** | ≥ 90 | TBD | 🔄 |
| **Accessibility** | ≥ 90 | TBD | 🔄 |
| **Best Practices** | ≥ 90 | TBD | 🔄 |
| **SEO** | ≥ 90 | TBD | 🔄 |

---

## Lighthouse 監査実行方法

### ローカル実行

```bash
# Lighthouse CLI インストール
npm install -g @lhci/cli lighthouse

# フロントエンドビルド
cd frontend
npm run build

# Lighthouse 実行
lhci autorun

# または、個別実行
lighthouse http://localhost:3000 --view
```

### CI/CD 自動実行

GitHub Actions で自動的に実行されます：

```yaml
# .github/workflows/build.yml
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - name: Run Lighthouse CI
        run: lhci autorun
```

### レポート確認

```bash
# HTML レポート生成
lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html

# レポート閲覧
open ./lighthouse-report.html
```

---

## フロントエンド最適化

### 1. コード分割 (Code Splitting)

**現状**:
```typescript
// ❌ 全てを一度に読み込み
import Dashboard from './pages/Dashboard';
import Templates from './pages/Templates';
```

**最適化**:
```typescript
// ✅ 動的インポート
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Templates = lazy(() => import('./pages/Templates'));

<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/templates" element={<Templates />} />
  </Routes>
</Suspense>
```

### 2. 画像最適化

**最適化戦略**:
- WebP形式使用
- 遅延読み込み (Lazy Loading)
- レスポンシブ画像
- CDN配信

```tsx
// ✅ 最適化された画像
<img
  src={template.preview_url}
  alt={template.name}
  loading="lazy"
  decoding="async"
  srcSet={`
    ${template.preview_url}?w=400 400w,
    ${template.preview_url}?w=800 800w,
    ${template.preview_url}?w=1200 1200w
  `}
  sizes="(max-width: 640px) 400px, (max-width: 1024px) 800px, 1200px"
/>
```

### 3. バンドルサイズ最適化

```bash
# バンドルサイズ分析
npm run build
npx vite-bundle-visualizer

# 最適化
- Tree Shaking 有効化
- 不要な依存関係削除
- lodash → lodash-es
- moment → date-fns
```

**目標**:
- Initial Bundle: < 200 KB
- Total Bundle: < 500 KB

### 4. キャッシング戦略

```typescript
// Service Worker によるキャッシング
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.example\.com\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 5 * 60, // 5分
              },
            },
          },
        ],
      },
    }),
  ],
});
```

### 5. React パフォーマンス最適化

```typescript
// ✅ useMemo でメモ化
const filteredTemplates = useMemo(() => {
  return templates.filter(t =>
    t.name.includes(searchTerm) &&
    (category === 'all' || t.category === category)
  );
}, [templates, searchTerm, category]);

// ✅ useCallback でコールバック固定
const handleSearch = useCallback((term: string) => {
  setSearchTerm(term);
}, []);

// ✅ React.memo でコンポーネントメモ化
export default React.memo(TemplateCard, (prev, next) => {
  return prev.template.id === next.template.id;
});

// ✅ 仮想スクロール
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={templates.length}
  itemSize={200}
  width="100%"
>
  {TemplateRow}
</FixedSizeList>
```

---

## バックエンド最適化

### 1. データベースクエリ最適化

```python
# ✅ バッチ取得
def get_templates_batch(template_ids: List[str]):
    # Google Sheets API: batchGet
    ranges = [f"Templates!A{i}:Z{i}" for i in template_ids]
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=SPREADSHEET_ID,
        ranges=ranges
    ).execute()
    return result['valueRanges']

# ✅ キャッシング
from functools import lru_cache

@lru_cache(maxsize=128)
def get_template_by_id(template_id: str):
    return sheets_service.get_template(template_id)
```

### 2. APIレスポンス最適化

```python
# ✅ gzip圧縮
from flask_compress import Compress
compress = Compress(app)

# ✅ ページネーション
@app.route('/api/v1/templates')
def get_templates():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    templates = get_all_templates()
    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        'templates': templates[start:end],
        'total': len(templates),
        'page': page,
        'per_page': per_page
    })

# ✅ フィールド選択
@app.route('/api/v1/templates')
def get_templates():
    fields = request.args.get('fields', '').split(',')
    templates = get_all_templates()

    if fields and fields[0]:
        templates = [{k: v for k, v in t.items() if k in fields}
                     for t in templates]

    return jsonify({'templates': templates})
```

### 3. 非同期処理

```python
# ✅ バックグラウンドジョブ
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def generate_image_async(template_id: str, data: dict):
    # 重い処理を非同期で実行
    result = figma_service.generate_image(template_id, data)
    return result

@app.route('/api/v1/templates/<id>/use', methods=['POST'])
def use_template(id):
    data = request.json

    # 非同期ジョブ作成
    job = generate_image_async.delay(id, data)

    return jsonify({
        'job_id': job.id,
        'status': 'pending'
    })
```

---

## ネットワーク最適化

### 1. CDN配信

```json
// Firebase Hosting + CDN
{
  "hosting": {
    "public": "dist",
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      },
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

### 2. HTTP/2 & HTTP/3

Firebase Hosting は自動的に HTTP/2 と HTTP/3 をサポート。

### 3. リソースヒント

```html
<!-- Preconnect -->
<link rel="preconnect" href="https://api.example.com">
<link rel="preconnect" href="https://fonts.googleapis.com">

<!-- DNS Prefetch -->
<link rel="dns-prefetch" href="https://storage.googleapis.com">

<!-- Preload -->
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/main.js" as="script">
```

---

## モニタリング

### 1. Real User Monitoring (RUM)

```typescript
// Web Vitals 計測
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: any) {
  // Google Analytics など
  gtag('event', metric.name, {
    value: Math.round(metric.value),
    event_category: 'Web Vitals',
  });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### 2. パフォーマンスダッシュボード

```bash
# Firebase Performance Monitoring
npm install firebase

// frontend/src/firebase.ts
import { getPerformance } from 'firebase/performance';

const perf = getPerformance(app);
```

### 3. 定期監査

```yaml
# .github/workflows/performance-audit.yml
name: Performance Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # 毎週日曜日

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - name: Run Lighthouse
        run: lhci autorun

      - name: Check thresholds
        run: |
          # スコアが90未満の場合、Issueを作成
          if [ $PERF_SCORE -lt 90 ]; then
            gh issue create --title "Performance degradation detected"
          fi
```

---

## チェックリスト

### デプロイ前チェック

- [ ] Lighthouse Performance スコア ≥ 90
- [ ] LCP < 2.5s
- [ ] CLS < 0.1
- [ ] FCP < 2.0s
- [ ] バンドルサイズ < 500KB
- [ ] 画像最適化完了
- [ ] キャッシュヘッダー設定
- [ ] Gzip圧縮有効
- [ ] Service Worker設定
- [ ] CDN配信設定

### 継続的最適化

- [ ] 週次 Lighthouse 監査
- [ ] 月次 RUM データ分析
- [ ] 四半期ごとのパフォーマンスレビュー
- [ ] 新機能追加時のパフォーマンステスト

---

## トラブルシューティング

### Q1: LCP が遅い

**原因**:
- 大きな画像
- フォントの読み込み
- CSSブロッキング

**対策**:
- 画像を WebP に変換
- フォントプリロード
- Critical CSS のインライン化

### Q2: CLS が高い

**原因**:
- 画像サイズ未指定
- 動的コンテンツ挿入
- Web フォント読み込み

**対策**:
- 画像に width/height 指定
- スケルトンスクリーン使用
- font-display: swap 設定

### Q3: バンドルサイズが大きい

**原因**:
- 不要なライブラリ
- Tree Shaking 未実施
- 重複コード

**対策**:
- Bundle Analyzer で分析
- 動的インポート
- ライブラリの最小化

---

## リソース

- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [React Performance](https://react.dev/learn/render-and-commit)
- [Vite Performance](https://vitejs.dev/guide/performance.html)

---

📊 継続的なパフォーマンス監視とチューニングで、最高のユーザー体験を提供しましょう。
