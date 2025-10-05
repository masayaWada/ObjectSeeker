"""
テストモジュール
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import json

from src.config import Config
from src.logger import Logger
from src.azure_client import AzureClient, AzureCLIError
from src.graph_api import GraphAPISearcher, AzureGraphAPIError


class TestConfig(unittest.TestCase):
    """Configクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.config = Config(self.config_file)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)

    def test_default_config(self):
        """デフォルト設定のテスト"""
        self.assertIsNotNone(self.config.get('window'))
        self.assertIsNotNone(self.config.get('search'))
        self.assertIsNotNone(self.config.get('azure'))

    def test_set_and_get(self):
        """設定値の設定と取得のテスト"""
        self.config.set('test.value', 'test_data')
        self.assertEqual(self.config.get('test.value'), 'test_data')

    def test_save_and_load(self):
        """設定の保存と読み込みのテスト"""
        self.config.set('test.value', 'test_data')
        self.config.save_config()

        # 新しいConfigインスタンスで読み込み
        new_config = Config(self.config_file)
        self.assertEqual(new_config.get('test.value'), 'test_data')


class TestLogger(unittest.TestCase):
    """Loggerクラスのテスト"""

    def test_logger_creation(self):
        """ロガーの作成テスト"""
        logger = Logger("TestLogger")
        self.assertIsNotNone(logger.logger)

    def test_log_levels(self):
        """ログレベルのテスト"""
        logger = Logger("TestLogger")

        # 各ログレベルがエラーなく実行されることを確認
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


class TestAzureClient(unittest.TestCase):
    """AzureClientクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.logger = Logger("TestLogger")
        self.client = AzureClient(self.logger)

    @patch('subprocess.run')
    def test_check_azure_cli_installation_success(self, mock_run):
        """Azure CLIインストール確認の成功テスト"""
        mock_run.return_value.returncode = 0

        result = self.client.check_azure_cli_installation()
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_check_azure_cli_installation_failure(self, mock_run):
        """Azure CLIインストール確認の失敗テスト"""
        mock_run.return_value.returncode = 1

        result = self.client.check_azure_cli_installation()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_get_account_info_success(self, mock_run):
        """アカウント情報取得の成功テスト"""
        mock_account_info = {
            'tenantId': 'test-tenant-id',
            'name': 'test-account'
        }
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_account_info)

        self.client.az_path = 'az'
        result = self.client.get_account_info()

        self.assertEqual(result['tenantId'], 'test-tenant-id')

    @patch('subprocess.run')
    def test_get_access_token_success(self, mock_run):
        """アクセストークン取得の成功テスト"""
        mock_token_info = {
            'accessToken': 'test-access-token'
        }
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_token_info)

        self.client.az_path = 'az'
        result = self.client.get_access_token()

        self.assertEqual(result, 'test-access-token')

    def test_is_authenticated(self):
        """認証状態確認のテスト"""
        # 未認証状態
        self.assertFalse(self.client.is_authenticated())

        # 認証済み状態
        self.client.access_token = 'test-token'
        self.client.tenant_id = 'test-tenant'
        self.assertTrue(self.client.is_authenticated())


class TestGraphAPISearcher(unittest.TestCase):
    """GraphAPISearcherクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.logger = Logger("TestLogger")
        self.azure_client = Mock()
        self.azure_client.is_authenticated.return_value = True
        self.azure_client.access_token = 'test-token'

        self.searcher = GraphAPISearcher(self.azure_client, self.logger)

    @patch('requests.get')
    def test_search_users_success(self, mock_get):
        """ユーザー検索の成功テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'id': 'user-id-1',
                    'displayName': 'Test User',
                    'mail': 'test@example.com',
                    'userPrincipalName': 'test@example.com'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = self.searcher.search_users('test')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['displayName'], 'Test User')

    def test_search_users_not_authenticated(self):
        """未認証状態でのユーザー検索テスト"""
        self.azure_client.is_authenticated.return_value = False

        with self.assertRaises(AzureGraphAPIError):
            self.searcher.search_users('test')

    def test_format_search_results(self):
        """検索結果フォーマットのテスト"""
        raw_results = [
            {
                'id': 'user-id-1',
                'displayName': 'Test User',
                'mail': 'test@example.com',
                'userPrincipalName': 'test@example.com'
            }
        ]

        formatted_results = self.searcher.format_search_results(
            raw_results, 'user')

        self.assertEqual(len(formatted_results), 1)
        self.assertEqual(formatted_results[0]['name'], 'Test User')
        self.assertEqual(formatted_results[0]['object_id'], 'user-id-1')
        self.assertEqual(formatted_results[0]['type'], 'user')


if __name__ == '__main__':
    # テストを実行
    unittest.main(verbosity=2)
