# tepure

🎨 **Figma Template Automation System** - Autonomous development powered by **Miyabi** AI framework

## 🌟 Project Overview

自動化されたWebアプリ/LPテンプレート生成システム。Figmaで30種類以上のテンプレートを管理し、ユーザーが選択したテンプレートに任意のテキスト・色・枠線を自動適用してAIで生成コンテンツを量産できる仕組みを提供します。

### Key Features

- 🔐 **JWT認証** - セキュアなユーザー認証とロールベースアクセス制御
- 📊 **Dashboard** - リアルタイムメトリクスとジョブ監視
- 🎨 **Template Management** - Figmaテンプレートの一覧・検索・詳細表示
- 🤖 **AI Generation** - LLMエージェントによる自動コンテンツ生成
- 📈 **Monitoring** - 監査ログ、レート制限、コスト追跡
- 🚀 **CI/CD** - 完全自動化されたテスト・ビルド・デプロイ

### Tech Stack

- **Backend**: Flask (Python 3.11+), Flask-JWT-Extended, Google Sheets API, Anthropic API
- **Frontend**: React 18+, Vite, TypeScript, Tailwind CSS
- **Figma Plugin**: TypeScript, Figma Plugin API
- **AI Framework**: Miyabi (Autonomous Operations)
- **Infrastructure**: Firebase Hosting, Google Cloud Run
- **Testing**: pytest, Vitest, Playwright
- **CI/CD**: GitHub Actions, Lighthouse CI

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Cloud Platform account
- Anthropic API key
- Figma API token

### Backend Setup

```bash
# Clone repository
git clone https://github.com/taiyousan15/tepure.git
cd tepure

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
cp ../.env.sample .env
# Edit .env with your actual credentials

# Run tests
pytest

# Start development server
flask run --port 5001
```

### Frontend Setup

```bash
# In project root
npm install

# Start development server
cd frontend
npm run dev
```

### Environment Variables

Copy `.env.sample` to `.env` and configure:

```bash
# Required
JWT_SECRET=<your-secret-key>
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=<base64-encoded-json>
LLM_API_KEY=<anthropic-api-key>
FIGMA_API_TOKEN=<figma-token>

# Google Sheets IDs
SHEETS_USERS_ID=<spreadsheet-id>
SHEETS_TEMPLATES_ID=<spreadsheet-id>
SHEETS_JOBS_ID=<spreadsheet-id>
SHEETS_AUDITLOGS_ID=<spreadsheet-id>
```

## 📁 Project Structure

```
tepure/
├── backend/                    # Flask API server
│   ├── app/                   # Application code
│   │   ├── __init__.py       # Flask app factory
│   │   ├── api_v1.py         # API routes
│   │   ├── auth.py           # JWT authentication
│   │   ├── schemas.py        # Pydantic models
│   │   ├── sheets.py         # Google Sheets integration
│   │   ├── jobs.py           # Job queue management
│   │   ├── agents.py         # LLM agent integration
│   │   └── metrics.py        # Monitoring and metrics
│   ├── tests/                # Backend tests (pytest)
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Container image
│   └── gunicorn.conf.py     # Production server config
├── frontend/                  # React application
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   └── utils/           # Utilities
│   ├── tests/               # Frontend tests (Vitest)
│   └── dist/                # Build output
├── e2e/                      # E2E tests (Playwright)
├── figma-plugin/            # Figma plugin code
├── .github/workflows/       # CI/CD pipelines
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── PERFORMANCE.md      # Performance guide
│   └── api/                # API documentation
└── .claude/                 # Miyabi agent configs

```

## 🧪 Testing

### Run All Tests

```bash
# Frontend tests
npm test

# Backend tests
cd backend
pytest

# E2E tests
npm run test:e2e

# With coverage
npm test -- --coverage
cd backend && pytest --cov
```

### Test Coverage

- **Frontend**: 80%+ (Target achieved)
- **Backend**: 80%+ (Target)
- **E2E**: Major user flows covered

## 🚀 Deployment

### Production Deployment

```bash
# Build frontend
cd frontend
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Deploy backend to Cloud Run
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/tepure-api
gcloud run deploy tepure-api \
  --image gcr.io/$GCP_PROJECT_ID/tepure-api \
  --region asia-northeast1 \
  --platform managed
```

### CI/CD

GitHub Actions automatically:
- Runs tests on PR/push
- Checks code quality
- Builds and deploys on merge to main
- Runs Lighthouse audits
- Generates coverage reports

See `.github/workflows/` for details.

## 📊 Monitoring

- **Lighthouse CI**: Performance monitoring (90+ target)
- **Cloud Monitoring**: Error rates, latency
- **Audit Logs**: All user actions tracked
- **Cost Tracking**: LLM token usage per job

## 🔒 Security

- ✅ JWT authentication with refresh tokens
- ✅ Role-based access control (admin/user)
- ✅ Password hashing (Argon2/BCrypt)
- ✅ Rate limiting (30 req/min global, 5 req/min per user)
- ✅ CORS restrictions
- ✅ Audit logging
- ✅ Environment variable secrets
- ✅ Security score: 100/100

## 📈 Performance

- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1
- **Lighthouse Score**: 90+ (all categories)

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Performance Guide](docs/PERFORMANCE.md)
- [API Documentation](docs/api/index.html)
- [Testing Guide](backend/TESTING_GUIDE.md)
- [Changelog](CHANGELOG.md)

## 🤝 Contributing

This project uses the Miyabi autonomous development framework:

1. Create an Issue with feature description
2. Miyabi agents automatically analyze and label
3. CodeGenAgent implements the feature
4. ReviewAgent checks quality (80+ score required)
5. TestAgent runs all tests
6. PRAgent creates Draft PR
7. Human review and merge

## 📝 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

- **Miyabi Framework** - Autonomous AI development
- **識学理論 (Shikigaku Theory)** - Organizational design principles
- **Claude Code** - AI-powered development assistant

---

🌸 **Powered by Miyabi** - Beauty in Autonomous Development

**Made with ❤️ using Claude Code**
