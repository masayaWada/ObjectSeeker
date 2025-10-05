# ObjectSeeker

**ObjectSeeker**は、Azure ADのユーザー、グループ、アプリケーションのオブジェクトIDを効率的に検索・取得するためのPython GUIツールです。Terraformでの権限付与作業を効率化することを目的としています。

## 🚀 主な機能

- **🔍 オブジェクト検索**: ユーザー、グループ、アプリケーションのオブジェクトIDを検索
- **🎯 直感的なGUI**: tkinterベースの使いやすいユーザーインターフェース
- **📋 ワンクリックコピー**: 検索結果のオブジェクトIDをダブルクリックでクリップボードにコピー
- **🔐 Azure CLI認証**: `az login`を使用した簡単な認証
- **⚙️ 設定可能**: JSON設定ファイルによるカスタマイズ
- **📝 ログ機能**: 詳細なログ出力とデバッグ情報
- **🧪 テスト対応**: 包括的なテストスイート

## 📋 前提条件

### 実行ファイル版（推奨）
- Windows 10以上
- Azure CLI（`az`コマンド）がインストールされていること
- Azure ADテナントへのアクセス権限

### ソースコード版
- Python 3.7以上
- Azure CLI（`az`コマンド）がインストールされていること
- Azure ADテナントへのアクセス権限

## 🛠️ インストール

### 方法1: 実行ファイル（推奨）

1. **実行ファイルをダウンロード**
   - `ObjectSeeker.exe`をダウンロード
   - 任意のフォルダに配置

2. **Azure CLIをインストール**（下記の「Azure CLIのインストールと認証」を参照）

3. **実行**
   - `ObjectSeeker.exe`をダブルクリックして起動

### 方法2: ソースコードから実行

1. **リポジトリをクローンまたはダウンロード**
```bash
git clone <repository-url>
cd ObjectSeeker
```

2. **依存関係をインストール**
```bash
pip install -r requirements.txt
```

3. **アプリケーションを実行**
```bash
python main.py
```

## 🔧 Azure CLIのインストールと認証

このツールを使用するには、Azure CLIがインストールされ、認証されている必要があります。

### Azure CLIのインストール

#### Windows
```powershell
# PowerShellで実行
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\AzureCLI.msi
```

#### macOS
```bash
brew install azure-cli
```

#### Linux (Ubuntu/Debian)
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Azure CLI認証

1. **Azure CLIでログイン**
```bash
az login
```

2. **ブラウザが開くので、Azureアカウントでログイン**

3. **認証完了後、適切なサブスクリプションが選択されているか確認**
```bash
az account show
```

4. **必要に応じてサブスクリプションを切り替え**
```bash
az account list --output table
az account set --subscription "サブスクリプション名"
```

## 📖 使用方法

### 1. アプリケーションの起動

**実行ファイル版**:
- `ObjectSeeker.exe`をダブルクリック

**ソースコード版**:
```bash
python main.py
```

### 2. Azure CLI認証の確認

アプリケーション起動時に、Azure CLIの認証状態が自動的に確認されます。

- **✅ 認証済み**: 緑色で「認証済み」と表示
- **❌ 未認証**: 赤色で「未認証 - 'az login' を実行してください」と表示

### 3. 認証情報の更新

認証状態が「未認証」の場合は：

1. **コマンドプロンプトまたはPowerShellで `az login` を実行**
2. **アプリケーションの「認証」ボタンをクリック**

### 4. オブジェクト検索

1. **検索タイプ**を選択：
   - `user`: ユーザー検索
   - `group`: グループ検索
   - `application`: アプリケーション検索

2. **検索クエリ**に入力：
   - ユーザー: メールアドレス、ユーザー名、表示名の一部
   - グループ: グループ名、メールアドレスの一部
   - アプリケーション: アプリケーション名の一部

3. **検索**ボタンをクリックまたはEnterキーを押下

### 5. 結果の確認とコピー

検索結果がテーブルに表示されます。オブジェクトIDをコピーするには：

- 該当する行を**ダブルクリック**
- オブジェクトIDがクリップボードにコピーされます
- 確認ダイアログが表示されます

## ⚙️ 設定

アプリケーションは `~/.objectseeker/config.json` で設定をカスタマイズできます。

### 設定例

```json
{
  "window": {
    "width": 1000,
    "height": 700,
    "resizable": true
  },
  "search": {
    "max_results": 100,
    "timeout": 30
  },
  "azure": {
    "graph_api_version": "v1.0",
    "resource": "https://graph.microsoft.com"
  },
  "ui": {
    "theme": "default",
    "font_size": 10
  },
  "logging": {
    "level": "INFO",
    "max_log_files": 7
  }
}
```

### 設定項目

| カテゴリ | 項目 | 説明 | デフォルト値 |
|---------|------|------|-------------|
| window | width | ウィンドウの幅 | 800 |
| window | height | ウィンドウの高さ | 600 |
| window | resizable | ウィンドウサイズ変更可能 | true |
| search | max_results | 最大検索結果数 | 100 |
| search | timeout | 検索タイムアウト（秒） | 30 |
| azure | graph_api_version | Graph APIバージョン | v1.0 |
| azure | resource | Graph APIリソース | https://graph.microsoft.com |
| ui | theme | UIテーマ | default |
| ui | font_size | フォントサイズ | 10 |
| logging | level | ログレベル | INFO |
| logging | max_log_files | 保持するログファイル数 | 7 |

## 🔒 認証情報

このツールはAzure CLIの認証情報を使用するため、追加の設定ファイルは不要です。Azure CLIの認証情報は以下の場所に保存されます：

- **Windows**: `%USERPROFILE%\.azure\`
- **macOS/Linux**: `~/.azure/`

**注意**: Azure CLIの認証情報は適切に管理され、定期的に更新されます。

## 🏗️ Terraformでの使用例

取得したオブジェクトIDをTerraformで使用する例：

```hcl
# ユーザーにロールを割り当て
resource "azurerm_role_assignment" "user_role" {
  scope                = "/subscriptions/your-subscription-id"
  role_definition_name = "Contributor"
  principal_id        = "取得したオブジェクトID"
}

# グループにロールを割り当て
resource "azurerm_role_assignment" "group_role" {
  scope                = "/subscriptions/your-subscription-id"
  role_definition_name = "Reader"
  principal_id        = "取得したオブジェクトID"
}

# アプリケーションにロールを割り当て
resource "azurerm_role_assignment" "app_role" {
  scope                = "/subscriptions/your-subscription-id"
  role_definition_name = "Contributor"
  principal_id        = "取得したオブジェクトID"
}
```

## 🐛 トラブルシューティング

### 認証エラー

- **Azure CLIがインストールされていない**: Azure CLIをインストールしてください
- **`az login`が実行されていない**: コマンドプロンプトで `az login` を実行してください
- **認証が期限切れ**: `az login` を再実行して認証を更新してください

### 検索結果が表示されない

- **検索クエリ**が正しく入力されているか確認
- 該当するオブジェクトが存在するか確認
- **Azure CLIの認証**が有効か確認

### 権限エラー

- Azure CLIでログインしたアカウントに、Azure ADの読み取り権限があるか確認
- 必要に応じて管理者に権限の付与を依頼してください

### ログファイルの確認

エラーの詳細は以下のログファイルで確認できます：

- **Windows**: `%USERPROFILE%\.objectseeker\logs\`
- **macOS/Linux**: `~/.objectseeker/logs/`

## 🔒 セキュリティ考慮事項

- Azure CLIの認証情報は適切に管理されています
- 認証情報はローカルに保存され、外部に送信されません
- 定期的に `az login` を実行して認証を更新してください
- ログファイルには機密情報が含まれる可能性があるため、適切に管理してください

## 👨‍💻 開発者向け情報

### プロジェクト構造

```
ObjectSeeker/
├── src/                    # ソースコード
│   ├── __init__.py        # パッケージ初期化
│   ├── app.py             # メインアプリケーション
│   ├── config.py          # 設定管理
│   ├── logger.py          # ログ管理
│   ├── azure_client.py    # Azure CLI クライアント
│   ├── graph_api.py       # Graph API 検索
│   └── ui_components.py   # UIコンポーネント
├── tests/                 # テストコード
│   └── test_objectseeker.py
├── main.py               # エントリーポイント
├── build.py              # ビルドスクリプト
├── requirements.txt      # 依存関係
├── config.example.json   # 設定例
└── README.md            # このファイル
```

### テストの実行

```bash
# すべてのテストを実行
python -m pytest tests/ -v

# カバレッジ付きでテストを実行
python -m pytest tests/ --cov=src --cov-report=html
```

### 実行ファイルのビルド

```bash
# ビルドスクリプトを実行
python build.py
```

または手動で：

```bash
# 依存関係をインストール
pip install -r requirements.txt

# 実行ファイルをビルド
pyinstaller --onefile --noconsole --name=ObjectSeeker main.py
```

### ビルドオプション

- `--onefile`: 単一のexeファイルにパッケージ化
- `--noconsole`: コンソールウィンドウを非表示（GUIアプリケーション用）
- `--windowed`: Windows環境でのウィンドウアプリケーションとして実行

### 配布時の注意事項

- 実行ファイルは約50-100MB程度になります
- 初回実行時にウイルス対策ソフトが警告を表示する場合があります
- 実行ファイルにはPythonランタイムが含まれているため、Pythonのインストールは不要です

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能要望は、GitHubのIssuesページでお知らせください。

### 開発への参加

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [GitHub Wiki](https://github.com/your-repo/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)