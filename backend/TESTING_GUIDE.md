# Backend Testing Guide

## 🎯 概要

このドキュメントは、tepureバックエンドの包括的なテストスイートの使用方法を説明します。

## 📦 テストファイル構成

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytestフィクスチャと設定
│   ├── test_app.py              # Flaskアプリケーションテスト (19)
│   ├── test_auth.py             # 認証APIテスト (7)
│   ├── test_jobs.py             # ジョブAPIテスト (27)
│   ├── test_sheets.py           # Google Sheets連携テスト (25)
│   ├── test_templates.py        # テンプレートAPIテスト (6)
│   └── README.md                # テスト詳細ガイド
├── pytest.ini                   # Pytest設定
├── .coveragerc                  # カバレッジ設定
├── requirements-dev.txt         # 開発用依存関係
├── run-tests.sh                 # テスト実行スクリプト
└── TEST_SUMMARY.md              # テスト統計サマリー
```

**合計: 84 テスト関数**

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
cd backend
pip3 install -r requirements-dev.txt
```

### 2. テスト実行

```bash
# 全テスト実行
pytest

# または、スクリプト使用
./run-tests.sh
```

### 3. カバレッジレポート

```bash
# HTMLレポート生成
pytest --cov=. --cov-report=html

# ブラウザで確認
open htmlcov/index.html
```

## 📊 テスト統計

| カテゴリ | テスト数 | 行数 | 主な機能 |
|---------|---------|------|---------|
| **Flaskアプリ** | 19 | 204 | ヘルスチェック、エラーハンドラ、CORS、JWT |
| **認証API** | 7 | 139 | ログイン、ユーザー登録、パスワード検証 |
| **ジョブAPI** | 27 | 458 | ジョブ作成、一覧、更新、ライフサイクル |
| **Google Sheets** | 25 | 391 | テンプレート、ユーザー、ジョブ、監査ログ |
| **テンプレートAPI** | 6 | 143 | テンプレート一覧、詳細、作成 |
| **合計** | **84** | **1,335** | **全機能カバー** |

## 🔍 テストカバレッジ

### 目標

- **全体**: 80%以上
- **API Endpoints**: 90%以上
- **Services**: 85%以上
- **Error Handlers**: 100%

### カバー範囲

#### `test_app.py` - Flaskアプリケーションコア
- ✅ ヘルスチェックエンドポイント
- ✅ 404/500エラーハンドラ
- ✅ CORS設定
- ✅ JWT設定
- ✅ Blueprint登録
- ✅ レート制限
- ✅ Content-Type検証

#### `test_sheets.py` - Google Sheets連携
- ✅ サービス初期化
- ✅ テンプレートCRUD操作
- ✅ ユーザー管理
- ✅ ジョブ管理
- ✅ 監査ログ
- ✅ エラーハンドリング
- ✅ ページネーション

#### `test_jobs.py` - ジョブAPI
- ✅ ジョブ作成（バリデーション含む）
- ✅ ジョブ一覧取得（フィルタ含む）
- ✅ ジョブ詳細取得
- ✅ ジョブステータス更新
- ✅ 認証チェック
- ✅ エラーハンドリング
- ✅ フルライフサイクルテスト

#### `test_auth.py` - 認証API
- ✅ ログイン（成功/失敗）
- ✅ ユーザー登録（成功/失敗）
- ✅ パスワード強度検証
- ✅ メール形式検証

#### `test_templates.py` - テンプレートAPI
- ✅ テンプレート一覧取得
- ✅ テンプレート詳細取得
- ✅ テンプレート作成
- ✅ フィールド取得

## 🛠️ 実行方法

### 基本コマンド

```bash
# 全テスト実行
pytest

# 詳細表示
pytest -v

# 特定ファイル実行
pytest tests/test_app.py

# 特定クラス実行
pytest tests/test_jobs.py::TestCreateJob

# 特定テスト実行
pytest tests/test_jobs.py::TestCreateJob::test_create_job_success
```

### カバレッジオプション

```bash
# カバレッジ付き実行（ターミナル表示）
pytest --cov=. --cov-report=term-missing

# HTMLレポート生成
pytest --cov=. --cov-report=html
open htmlcov/index.html

# JSONレポート生成
pytest --cov=. --cov-report=json
```

### パフォーマンス最適化

```bash
# 並列実行（pytest-xdist）
pytest -n auto

# 最後に失敗したテストのみ再実行
pytest --lf

# 失敗したら即停止
pytest -x

# 最初のN個の失敗で停止
pytest --maxfail=3
```

### マーカーによるフィルタリング

```bash
# APIテストのみ
pytest -m api

# 認証テストのみ
pytest -m auth

# ユニットテストのみ
pytest -m unit

# 統合テストのみ
pytest -m integration

# 遅いテストを除外
pytest -m "not slow"
```

### スクリプト使用

```bash
# デフォルト実行
./run-tests.sh

# 特定ファイル
./run-tests.sh tests/test_app.py

# HTMLレポート生成
./run-tests.sh tests html
```

## 🧪 フィクスチャ

### 基本フィクスチャ

#### `app`
```python
def test_something(app):
    assert app.config['TESTING'] is True
```

#### `client`
```python
def test_endpoint(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
```

#### `auth_headers`
```python
def test_protected(client, auth_headers):
    headers = auth_headers('user@example.com')
    response = client.get('/api/v1/templates', headers=headers)
    assert response.status_code == 200
```

### データフィクスチャ

#### `sample_template`
```python
def test_template(sample_template):
    assert sample_template['id'] == 'tpl_test123'
    assert sample_template['name'] == 'Test Template'
```

#### `sample_user`
```python
def test_user(sample_user):
    assert sample_user['email'] == 'test@example.com'
```

#### `sample_job`
```python
def test_job(sample_job):
    assert sample_job['status'] == 'pending'
```

#### `mock_google_sheets`
```python
def test_with_mock(mock_google_sheets):
    mock_google_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [['id', 'name'], ['tpl_1', 'Template 1']]
    }
```

## 🎨 テストパターン

### APIエンドポイントテスト

```python
def test_create_job(client, auth_headers, mock_sheets_client):
    # Arrange - モックの設定
    mock_sheets_client.get_template.return_value = {'id': 'tpl_123', 'name': 'Test'}
    mock_sheets_client.create_fill_job.return_value = 'job_123'

    # Act - APIリクエスト
    headers = auth_headers()
    response = client.post('/api/v1/jobs', headers=headers, json={
        'template_id': 'tpl_123',
        'input_data': {'title': 'Test'}
    })

    # Assert - レスポンス検証
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['job_id'] == 'job_123'
```

### エラーハンドリングテスト

```python
def test_error_handling(client, auth_headers, mock_sheets_client):
    mock_sheets_client.create_fill_job.side_effect = Exception('API Error')

    headers = auth_headers()
    response = client.post('/api/v1/jobs', headers=headers, json={...})

    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data
```

### 統合テスト

```python
def test_full_lifecycle(client, auth_headers, mock_sheets_client):
    # 1. ジョブ作成
    # 2. 一覧取得
    # 3. ステータス更新
    # 4. 監査ログ確認
```

## 📈 カバレッジレポート

### ターミナル表示

```bash
pytest --cov=. --cov-report=term-missing
```

出力例:
```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
app.py                  85      5    94%   45-47, 82-83
api/jobs.py            120      8    93%   201-208
services/sheets.py     180     15    92%   ...
--------------------------------------------------
TOTAL                  850     68    92%
```

### HTMLレポート

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

- 行ごとのカバレッジ表示
- 未実行行のハイライト
- ブランチカバレッジ
- インタラクティブなナビゲーション

### JSONレポート

```bash
pytest --cov=. --cov-report=json
```

CI/CDパイプラインでの使用に適しています。

## 🔧 トラブルシューティング

### テストが失敗する

1. **依存関係の確認**
   ```bash
   pip3 install -r requirements-dev.txt
   ```

2. **環境変数の設定**
   ```bash
   export GOOGLE_SHEETS_ID=test-sheet-id
   export GOOGLE_SERVICE_ACCOUNT_JSON=test-credentials
   ```

3. **キャッシュのクリア**
   ```bash
   pytest --cache-clear
   ```

### カバレッジが低い

```bash
# 未カバーの行を表示
pytest --cov=. --cov-report=term-missing

# HTMLレポートで詳細確認
pytest --cov=. --cov-report=html
```

### インポートエラー

```bash
# Pythonパスの確認
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"

# または、開発モードでインストール
pip3 install -e .
```

## 🔄 CI/CD統合

### GitHub Actions

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          fail_ci_if_error: true
```

## 📚 参考資料

### 内部ドキュメント
- [tests/README.md](tests/README.md) - 詳細なテストガイド
- [TEST_SUMMARY.md](TEST_SUMMARY.md) - テスト統計サマリー
- [pytest.ini](pytest.ini) - Pytest設定
- [.coveragerc](.coveragerc) - カバレッジ設定

### 外部ドキュメント
- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [Python Mock Library](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

## 🎓 ベストプラクティス

### 1. AAA パターン

```python
def test_example():
    # Arrange - 準備
    data = {'key': 'value'}

    # Act - 実行
    result = process(data)

    # Assert - 検証
    assert result == expected
```

### 2. 1テスト1検証

各テストは1つの機能/動作を検証する：

```python
# Good
def test_create_job_success():
    ...

def test_create_job_missing_template_id():
    ...

# Bad
def test_create_job():
    # 複数のケースを1つのテストで検証
    ...
```

### 3. 明確なテスト名

```python
# Good
def test_create_job_returns_201_with_valid_data():
    ...

def test_create_job_returns_400_when_template_id_missing():
    ...

# Bad
def test_job():
    ...
```

### 4. モックの適切な使用

```python
# Good - 外部APIをモック
@patch('api.jobs.sheets_client')
def test_create_job(mock_sheets_client, client):
    mock_sheets_client.create_fill_job.return_value = 'job_123'
    ...

# Bad - 実際のAPIを呼び出す
def test_create_job(client):
    # 実際のGoogle Sheets APIを呼び出す
    ...
```

### 5. テストの独立性

```python
# Good - テストごとにデータをセットアップ
def test_create_template(mock_sheets_client):
    mock_sheets_client.create_template.return_value = 'tpl_123'
    ...

# Bad - 前のテストに依存
template_id = None
def test_create_template():
    global template_id
    template_id = create_template()

def test_get_template():
    get_template(template_id)  # 前のテストに依存
```

## ✅ チェックリスト

- [ ] 依存関係インストール済み
- [ ] 環境変数設定済み
- [ ] 全テストが通る
- [ ] カバレッジ80%以上
- [ ] 新機能にテストを追加
- [ ] CI/CDでテストが実行される

---

**作成日**: 2025-10-16
**総テスト数**: 84
**総行数**: 2,259
**カバレッジ目標**: 80%+
**ステータス**: ✅ 準備完了
