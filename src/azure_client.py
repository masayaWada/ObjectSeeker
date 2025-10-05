"""
Azure Graph API クライアントモジュール
"""

import subprocess
import json
import shutil
import os
from typing import Optional, Dict, List, Any
from .logger import Logger
from .exceptions import AzureCLIError, AzureGraphAPIError


class AzureClient:
    """Azure Graph APIクライアント"""

    def __init__(self, logger: Optional[Logger] = None):
        """
        Azureクライアントを初期化

        Args:
            logger: ロガーインスタンス
        """
        self.logger = logger or Logger()
        self.access_token: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.az_path: Optional[str] = None

    def find_azure_cli_path(self) -> Optional[str]:
        """Azure CLIのパスを検索"""
        self.logger.debug("Azure CLIパスを検索中...")

        # 一般的なAzure CLIのパス
        possible_paths = [
            'az',  # PATHに登録されている場合
            'az.cmd',  # Windows
            'az.exe',  # Windows
            r'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd',
            r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd',
            r'C:\Users\{}\AppData\Local\Programs\Python\Python*\Scripts\az.cmd'.format(
                os.getenv('USERNAME', '')),
        ]

        # 環境変数PATHから検索
        for path in os.environ.get('PATH', '').split(os.pathsep):
            az_path = os.path.join(path, 'az.cmd')
            if os.path.exists(az_path):
                self.logger.debug(f"Azure CLIパス発見: {az_path}")
                return az_path
            az_path = os.path.join(path, 'az.exe')
            if os.path.exists(az_path):
                self.logger.debug(f"Azure CLIパス発見: {az_path}")
                return az_path

        # shutil.whichを使用して検索
        az_path = shutil.which('az')
        if az_path:
            self.logger.debug(f"Azure CLIパス発見: {az_path}")
            return az_path

        # 直接パスで検索
        for path in possible_paths:
            if shutil.which(path):
                found_path = shutil.which(path)
                self.logger.debug(f"Azure CLIパス発見: {found_path}")
                return found_path

        self.logger.warning("Azure CLIパスが見つかりませんでした")
        return None

    def check_azure_cli_installation(self) -> bool:
        """Azure CLIがインストールされているかチェック"""
        self.logger.debug("Azure CLIインストール状況をチェック中...")

        self.az_path = self.find_azure_cli_path()
        if not self.az_path:
            return False

        try:
            result = subprocess.run(
                [self.az_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            is_installed = result.returncode == 0
            if is_installed:
                self.logger.info("Azure CLIが正常にインストールされています")
            else:
                self.logger.warning("Azure CLIのバージョン確認に失敗しました")
            return is_installed
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Azure CLIチェックエラー: {e}")
            return False

    def get_account_info(self) -> Dict[str, Any]:
        """現在のアカウント情報を取得"""
        if not self.az_path:
            raise AzureCLIError("Azure CLIパスが設定されていません")

        self.logger.debug("アカウント情報を取得中...")

        try:
            result = subprocess.run(
                [self.az_path, 'account', 'show'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise AzureCLIError(f"アカウント情報の取得に失敗: {result.stderr}")

            account_info = json.loads(result.stdout)
            self.logger.info("アカウント情報を正常に取得しました")
            return account_info

        except json.JSONDecodeError as e:
            raise AzureCLIError(f"アカウント情報の解析に失敗: {e}")
        except subprocess.TimeoutExpired:
            raise AzureCLIError("アカウント情報の取得がタイムアウトしました")

    def get_access_token(self, resource: str = "https://graph.microsoft.com") -> str:
        """アクセストークンを取得"""
        if not self.az_path:
            raise AzureCLIError("Azure CLIパスが設定されていません")

        self.logger.debug(f"アクセストークンを取得中... (リソース: {resource})")

        try:
            result = subprocess.run([
                self.az_path, 'account', 'get-access-token',
                '--resource', resource
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                raise AzureCLIError(f"アクセストークンの取得に失敗: {result.stderr}")

            token_info = json.loads(result.stdout)
            access_token = token_info.get('accessToken')

            if not access_token:
                raise AzureCLIError("アクセストークンが取得できませんでした")

            self.logger.info("アクセストークンを正常に取得しました")
            return access_token

        except json.JSONDecodeError as e:
            raise AzureCLIError(f"アクセストークンの解析に失敗: {e}")
        except subprocess.TimeoutExpired:
            raise AzureCLIError("アクセストークンの取得がタイムアウトしました")

    def authenticate(self) -> bool:
        """Azure CLI認証を実行"""
        self.logger.info("Azure CLI認証を開始...")

        if not self.az_path:
            self.logger.error("Azure CLIパスが設定されていません")
            return False

        try:
            # az loginを実行（対話的に）
            result = subprocess.run([self.az_path, 'login'], text=True)

            if result.returncode == 0:
                self.logger.info("Azure CLI認証が成功しました")
                # 認証成功後、認証情報を更新
                self.update_auth_info()
                return True
            else:
                self.logger.error("Azure CLI認証に失敗しました")
                return False

        except Exception as e:
            self.logger.error(f"Azure CLI認証エラー: {e}")
            return False

    def update_auth_info(self) -> None:
        """認証情報を更新"""
        self.logger.debug("認証情報を更新中...")

        try:
            # アカウント情報を取得
            account_info = self.get_account_info()
            self.tenant_id = account_info.get('tenantId')

            # アクセストークンを取得
            self.access_token = self.get_access_token()

            self.logger.info("認証情報の更新が完了しました")

        except AzureCLIError as e:
            self.logger.error(f"認証情報の更新に失敗: {e}")
            self.tenant_id = None
            self.access_token = None

    def is_authenticated(self) -> bool:
        """認証状態を確認"""
        return bool(self.access_token and self.tenant_id)

    def get_auth_status(self) -> Dict[str, Any]:
        """認証状態の詳細情報を取得"""
        return {
            'is_authenticated': self.is_authenticated(),
            'tenant_id': self.tenant_id,
            'has_access_token': bool(self.access_token),
            'az_path': self.az_path
        }
