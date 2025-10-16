# Backend Tests

バックエンドAPIの包括的なテストスイート

## テストの構成

```
backend/tests/
├── conftest.py           # pytest設定とフィクスチャ
├── test_app.py          # Flaskアプリケーションのテスト
├── test_auth.py         # 認証APIのテスト
├── test_templates.py    # テンプレートAPIのテスト
├── test_sheets.py       # Google Sheets連携のテスト
└── test_jobs.py         # ジョブAPIのテスト
```

## テストの実行

### 全テスト実行

```bash
cd backend
pytest
```

### 特定のテストファイルを実行

```bash
pytest tests/test_app.py
pytest tests/test_sheets.py
pytest tests/test_jobs.py
```

### 特定のテストクラスを実行

```bash
pytest tests/test_jobs.py::TestCreateJob
```

### 特定のテスト関数を実行

```bash
pytest tests/test_jobs.py::TestCreateJob::test_create_job_success
```

### カバレッジレポート生成

```bash
# HTML形式
pytest --cov=. --cov-report=html
open htmlcov/index.html

# ターミナル表示
pytest --cov=. --cov-report=term-missing

# JSON形式
pytest --cov=. --cov-report=json
```

### 並列実行（高速化）

```bash
# 自動的にCPUコア数に応じて並列実行
pytest -n auto
```

### マーカーを使った実行

```bash
# APIテストのみ
pytest -m api

# 認証テストのみ
pytest -m auth

# ユニットテストのみ
pytest -m unit

# 統合テストのみ
pytest -m integration
```

## テストカバレッジ目標

| カテゴリ | 目標カバレッジ |
|---------|--------------|
| 全体 | 80%+ |
| API Endpoints | 90%+ |
| Services | 85%+ |
| Error Handlers | 100% |

## フィクスチャ

### `app`
Flask アプリケーションインスタンス（テストモード）

```python
def test_something(app):
    assert app.config['TESTING'] is True
```

### `client`
Flask テストクライアント

```python
def test_endpoint(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
```

### `auth_headers`
認証ヘッダー生成関数

```python
def test_protected_endpoint(client, auth_headers):
    headers = auth_headers('user@example.com')
    response = client.get('/api/v1/templates', headers=headers)
    assert response.status_code == 200
```

### `sample_template`
テスト用テンプレートデータ

```python
def test_template(sample_template):
    assert sample_template['id'] == 'tpl_test123'
```

### `sample_user`
テスト用ユーザーデータ

```python
def test_user(sample_user):
    assert sample_user['email'] == 'test@example.com'
```

### `sample_job`
テスト用ジョブデータ

```python
def test_job(sample_job):
    assert sample_job['status'] == 'pending'
```

## モッキング戦略

### Google Sheets APIのモック

```python
from unittest.mock import patch

@patch('api.jobs.sheets_client')
def test_create_job(mock_sheets_client, client, auth_headers):
    mock_sheets_client.create_fill_job.return_value = 'job_123'
    # テストコード
```

### 環境変数のモック

```python
import os

def test_with_env():
    os.environ['GOOGLE_SHEETS_ID'] = 'test-id'
    # テストコード
```

## テストパターン

### APIエンドポイントテスト

```python
def test_endpoint(client, auth_headers):
    headers = auth_headers()
    response = client.post('/api/v1/jobs', headers=headers, json={
        'template_id': 'tpl_123',
        'input_data': {'title': 'Test'}
    })

    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'job_id' in data
```

### 認証テスト

```python
def test_unauthorized_access(client):
    response = client.get('/api/v1/jobs')
    assert response.status_code == 401
```

### エラーハンドリングテスト

```python
def test_invalid_request(client, auth_headers):
    headers = auth_headers()
    response = client.post('/api/v1/jobs', headers=headers, json={})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
```

### モックを使った外部API呼び出しテスト

```python
from unittest.mock import MagicMock

def test_sheets_integration(sheets_client, mock_sheets_service):
    mock_sheets_service.spreadsheets().values().get().execute.return_value = {
        'values': [['id', 'name'], ['tpl_1', 'Template 1']]
    }

    templates = sheets_client.get_templates()
    assert len(templates) == 1
```

## トラブルシューティング

### テストが失敗する場合

1. **環境変数の確認**
   ```bash
   export GOOGLE_SHEETS_ID=test-sheet-id
   export GOOGLE_SERVICE_ACCOUNT_JSON=test-credentials
   ```

2. **依存関係のインストール**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **キャッシュのクリア**
   ```bash
   pytest --cache-clear
   ```

### カバレッジが低い場合

```bash
# 未カバーの行を表示
pytest --cov=. --cov-report=term-missing

# HTMLレポートで詳細確認
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## CI/CD統合

### GitHub Actions

```yaml
- name: Run tests
  run: |
    cd backend
    pytest --cov=. --cov-report=xml --cov-report=term

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./backend/coverage.xml
```

## ベストプラクティス

1. **AAA パターン** (Arrange-Act-Assert)
   ```python
   def test_example():
       # Arrange - 準備
       data = {'key': 'value'}

       # Act - 実行
       result = process(data)

       # Assert - 検証
       assert result == expected
   ```

2. **1テスト1検証**
   - 各テストは1つの機能/動作を検証する
   - テスト名は検証内容を明確に示す

3. **モックの適切な使用**
   - 外部APIは常にモックする
   - データベース操作もモックする
   - ファイルI/Oもモックする

4. **テストの独立性**
   - テストは任意の順序で実行できる
   - テスト間で状態を共有しない

## 参考資料

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [Python Mock Library](https://docs.python.org/3/library/unittest.mock.html)
