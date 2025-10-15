# Frontend Tests

React Testing LibraryとVitestを使用したフロントエンドコンポーネントのテストスイート。

## テスト構成

- **テストフレームワーク**: Vitest
- **テストライブラリ**: React Testing Library
- **環境**: jsdom
- **カバレッジプロバイダー**: v8

## テスト対象コンポーネント

### 1. Dashboard.test.tsx (18 tests)
メインダッシュボードページのテスト。

**テストカバレッジ**:
- ステートメント: 99.16%
- ブランチ: 86.66%
- 関数: 88.88%

**テスト内容**:
- レンダリングとローディング状態
- データフェッチング（テンプレート、ジョブ）
- 統計カードの表示
- クイックアクションボタン
- 最近のジョブセクション
- ナビゲーション機能
- エラーハンドリング
- 認証トークンの送信

### 2. Templates.test.tsx (26 tests)
テンプレート一覧ページのテスト。

**テストカバレッジ**:
- ステートメント: 100%
- ブランチ: 94.11%
- 関数: 100%

**テスト内容**:
- レンダリングと初期状態
- 検索機能（大文字小文字を区別しない）
- カテゴリフィルター（all, LP, Banner, SNS, WebApp）
- テンプレートカードの表示
- プレビュー画像の表示
- テンプレートアクション（使用、詳細）
- モーダルの開閉
- 複合フィルター（検索 + カテゴリ）
- エラーハンドリング

### 3. UseTemplate.test.tsx (26 tests)
テンプレート使用ページのテスト。

**テストカバレッジ**:
- ステートメント: 98.22%
- ブランチ: 86.04%
- 関数: 85.71%

**テスト内容**:
- レンダリングと初期状態
- テンプレート詳細のフェッチ
- プレビュー画像の表示
- フォームフィールドの表示
- 必須フィールドのバリデーション
- デフォルト値の設定
- フォーム入力の変更
- フォーム送信
- 成功時の処理（アラート、ナビゲーション）
- エラーハンドリング
- 送信中の状態表示

## テストの実行方法

```bash
# すべてのテストを実行
npm test

# テストを1回だけ実行
npm run test:run

# UIモードでテストを実行
npm run test:ui

# カバレッジレポート生成
npm run test:coverage
```

## テストユーティリティ

### tests/utils.tsx

便利なヘルパー関数：

- `renderWithRouter()` - React RouterのBrowserRouterでラップしたレンダリング
- `mockFetchResponse()` - fetch APIのレスポンスをモック
- `mockFetchError()` - fetchエラーをモック
- `mockFetchWithHandler()` - カスタムfetchハンドラー
- `setAuthToken()` - 認証トークンをlocalStorageに設定
- `clearLocalStorage()` - localStorageをクリア
- `createMockTemplate()` - テンプレートモックデータ生成
- `createMockJob()` - ジョブモックデータ生成
- `createMockField()` - フィールドモックデータ生成
- `createMockTemplateDetail()` - テンプレート詳細モックデータ生成

### tests/setup.ts

テスト環境のセットアップ：

- `@testing-library/jest-dom` のインポート
- 各テスト後の自動クリーンアップ
- `localStorage` のモック
- `fetch` のモック
- `matchMedia` のモック
- `IntersectionObserver` のモック

## カバレッジ目標

- **目標**: 80%以上
- **現在の達成状況**:
  - Dashboard.tsx: ✅ 99.16%
  - Templates.tsx: ✅ 100%
  - UseTemplate.tsx: ✅ 98.22%

## ベストプラクティス

1. **コンポーネントのレンダリング**: `renderWithRouter()` を使用してRouterコンテキストを提供
2. **非同期処理**: `waitFor()` を使用して非同期更新を待つ
3. **ユーザーインタラクション**: `userEvent` を使用してリアルなユーザー操作をシミュレート
4. **API モック**: 各テストで適切な fetch レスポンスをモック
5. **認証**: `setAuthToken()` を使用してテスト前に認証状態を設定

## 注意事項

- テストは TypeScript strict モードで記述されています
- すべてのテストはクリーンアップされるため、相互に影響しません
- React Testing Library の原則に従い、実装の詳細ではなく、ユーザーの視点でテストしています

## トラブルシューティング

### act() 警告が出る場合

コンポーネントが非同期で状態を更新する場合、`waitFor()` を使用して更新を待ちます。

```typescript
await waitFor(() => {
  expect(screen.getByText('期待するテキスト')).toBeInTheDocument();
});
```

### 複数の要素が見つかる場合

`getByText()` の代わりに `getAllByText()` を使用し、配列で検証します。

```typescript
const elements = screen.getAllByText('テキスト');
expect(elements.length).toBe(2);
```

### fetch が呼ばれない場合

テストの beforeEach で fetch をモックしていることを確認してください。

```typescript
beforeEach(() => {
  vi.clearAllMocks();
  mockFetchResponse({ data: 'test' });
});
```

## 関連ドキュメント

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library User Event](https://testing-library.com/docs/user-event/intro)
- [jsdom](https://github.com/jsdom/jsdom)

---

**総テスト数**: 70 tests
**成功率**: 100%
**平均実行時間**: ~10秒
