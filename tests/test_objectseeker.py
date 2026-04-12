"""
テストモジュール
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Optional
import json

from src.config import Config
from src.logger import Logger
from src.azure_client import AzureClient, AzureCLIError
from src.graph_api import GraphAPISearcher, AzureGraphAPIError, is_valid_guid


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


class TestIsValidGuid(unittest.TestCase):
    """is_valid_guid のテスト"""

    def test_valid_guid(self):
        self.assertTrue(is_valid_guid("11111111-2222-3333-4444-555555555555"))

    def test_valid_guid_with_whitespace(self):
        self.assertTrue(is_valid_guid("  11111111-2222-3333-4444-555555555555  "))

    def test_empty_string(self):
        self.assertFalse(is_valid_guid(""))

    def test_none(self):
        self.assertFalse(is_valid_guid(None))

    def test_invalid_format(self):
        self.assertFalse(is_valid_guid("not-a-guid"))
        self.assertFalse(is_valid_guid("1111-2222-3333-4444-5555"))


class TestGraphAPISearcherAdditional(unittest.TestCase):
    """search_groups / search_applications / unexpected error のテスト"""

    def setUp(self):
        self.logger = Logger("TestLogger")
        self.azure_client = Mock()
        self.azure_client.is_authenticated.return_value = True
        self.azure_client.access_token = 'test-token'
        self.searcher = GraphAPISearcher(self.azure_client, self.logger)

    @patch('requests.get')
    def test_search_groups_success(self, mock_get):
        response = Mock()
        response.json.return_value = {'value': [{'id': 'g1', 'displayName': 'G'}]}
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        results = self.searcher.search_groups('G')
        self.assertEqual(len(results), 1)

    @patch('requests.get')
    def test_search_applications_success(self, mock_get):
        response = Mock()
        response.json.return_value = {'value': [{'id': 'a1', 'displayName': 'A'}]}
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        results = self.searcher.search_applications('A')
        self.assertEqual(len(results), 1)

    def test_search_groups_not_authenticated(self):
        self.azure_client.is_authenticated.return_value = False
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.search_groups('x')

    def test_search_applications_not_authenticated(self):
        self.azure_client.is_authenticated.return_value = False
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.search_applications('x')

    @patch('requests.get')
    def test_search_unexpected_error(self, mock_get):
        mock_get.side_effect = RuntimeError("boom")
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.search_users('x')

    @patch('requests.get')
    def test_lookup_unexpected_error_wrapped(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.side_effect = RuntimeError("bad json")
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.lookup_by_principal_id("11111111-2222-3333-4444-555555555555")

    def test_format_directory_object_unknown_type(self):
        results = [{'@odata.type': '', 'id': 'x', 'displayName': 'n'}]
        formatted = self.searcher.format_directory_object_results(results)
        self.assertEqual(formatted[0]['type'], 'unknown')


class TestGraphAPISearcherPrincipalIdLookup(unittest.TestCase):
    """プリンシパルID逆引き機能のテスト"""

    VALID_GUID = "11111111-2222-3333-4444-555555555555"

    def setUp(self):
        self.logger = Logger("TestLogger")
        self.azure_client = Mock()
        self.azure_client.is_authenticated.return_value = True
        self.azure_client.access_token = 'test-token'
        self.searcher = GraphAPISearcher(self.azure_client, self.logger)

    def _mock_response(self, mock_get, odata_type: str, extra: Optional[dict] = None):
        response = Mock()
        response.status_code = 200
        data = {
            '@odata.type': odata_type,
            'id': self.VALID_GUID,
            'displayName': 'Test Object',
        }
        if extra:
            data.update(extra)
        response.json.return_value = data
        response.raise_for_status.return_value = None
        mock_get.return_value = response

    @patch('requests.get')
    def test_lookup_user(self, mock_get):
        self._mock_response(mock_get, '#microsoft.graph.user',
                            {'mail': 'u@example.com', 'userPrincipalName': 'u@example.com'})
        results = self.searcher.lookup_by_principal_id(self.VALID_GUID)
        self.assertEqual(len(results), 1)
        formatted = self.searcher.format_directory_object_results(results)
        self.assertEqual(formatted[0]['type'], 'user')
        self.assertEqual(formatted[0]['object_id'], self.VALID_GUID)

    @patch('requests.get')
    def test_lookup_group(self, mock_get):
        self._mock_response(mock_get, '#microsoft.graph.group')
        results = self.searcher.lookup_by_principal_id(self.VALID_GUID)
        formatted = self.searcher.format_directory_object_results(results)
        self.assertEqual(formatted[0]['type'], 'group')

    @patch('requests.get')
    def test_lookup_service_principal(self, mock_get):
        self._mock_response(mock_get, '#microsoft.graph.servicePrincipal')
        results = self.searcher.lookup_by_principal_id(self.VALID_GUID)
        formatted = self.searcher.format_directory_object_results(results)
        self.assertEqual(formatted[0]['type'], 'servicePrincipal')

    @patch('requests.get')
    def test_lookup_application(self, mock_get):
        self._mock_response(mock_get, '#microsoft.graph.application')
        results = self.searcher.lookup_by_principal_id(self.VALID_GUID)
        formatted = self.searcher.format_directory_object_results(results)
        self.assertEqual(formatted[0]['type'], 'application')

    @patch('requests.get')
    def test_lookup_not_found_returns_empty(self, mock_get):
        response = Mock()
        response.status_code = 404
        mock_get.return_value = response
        results = self.searcher.lookup_by_principal_id(self.VALID_GUID)
        self.assertEqual(results, [])

    def test_lookup_not_authenticated(self):
        self.azure_client.is_authenticated.return_value = False
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.lookup_by_principal_id(self.VALID_GUID)

    def test_lookup_invalid_guid(self):
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.lookup_by_principal_id("not-a-guid")

    @patch('requests.get')
    def test_lookup_network_error(self, mock_get):
        import requests as _requests
        mock_get.side_effect = _requests.exceptions.ConnectionError("net down")
        with self.assertRaises(AzureGraphAPIError):
            self.searcher.lookup_by_principal_id(self.VALID_GUID)


class TestResultsFrameHandleCopy(unittest.TestCase):
    """ResultsFrame のクリック列ベースコピー処理のテスト"""

    def _make_frame(self, result_type: str = "object"):
        from src.ui_components import ResultsFrame
        frame = ResultsFrame.__new__(ResultsFrame)
        frame.result_type = result_type
        frame.on_copy = Mock()
        frame.logger = Mock()
        frame.results_tree = MagicMock()
        return frame

    def _event(self, x: int = 10, y: int = 20):
        ev = Mock()
        ev.x = x
        ev.y = y
        return ev

    def test_resolve_object_tab_name_column(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "I001"
        frame.results_tree.identify_column.return_value = "#1"
        frame.results_tree.item.return_value = (
            "alice", "Alice", "a@x.com", "11111111-1111-1111-1111-111111111111", "user")
        result = frame._resolve_clicked_cell(self._event())
        self.assertEqual(result, ("名前", "alice"))

    def test_resolve_object_tab_email_column(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "I001"
        frame.results_tree.identify_column.return_value = "#3"
        frame.results_tree.item.return_value = (
            "alice", "Alice", "a@x.com", "oid", "user")
        self.assertEqual(
            frame._resolve_clicked_cell(self._event()), ("メール", "a@x.com"))

    def test_resolve_object_tab_object_id_column(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "I001"
        frame.results_tree.identify_column.return_value = "#4"
        frame.results_tree.item.return_value = (
            "alice", "Alice", "a@x.com", "oid-xyz", "user")
        self.assertEqual(
            frame._resolve_clicked_cell(self._event()), ("オブジェクトID", "oid-xyz"))

    def test_resolve_role_tab_role_name(self):
        frame = self._make_frame("role")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "R001"
        frame.results_tree.identify_column.return_value = "#1"
        frame.results_tree.item.return_value = ("Reader", "閲覧者", "desc")
        self.assertEqual(
            frame._resolve_clicked_cell(self._event()), ("ロール名（英語）", "Reader"))

    def test_resolve_role_tab_description(self):
        frame = self._make_frame("role")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "R001"
        frame.results_tree.identify_column.return_value = "#3"
        frame.results_tree.item.return_value = ("Reader", "閲覧者", "読み取り権限")
        self.assertEqual(
            frame._resolve_clicked_cell(self._event()), ("説明", "読み取り権限"))

    def test_resolve_returns_none_on_heading(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "heading"
        self.assertIsNone(frame._resolve_clicked_cell(self._event()))

    def test_resolve_returns_none_on_separator(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "separator"
        self.assertIsNone(frame._resolve_clicked_cell(self._event()))

    def test_resolve_returns_none_on_empty_row(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = ""
        self.assertIsNone(frame._resolve_clicked_cell(self._event()))

    def test_resolve_returns_none_on_empty_value(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "I001"
        frame.results_tree.identify_column.return_value = "#3"
        frame.results_tree.item.return_value = ("alice", "Alice", "", "oid", "user")
        self.assertIsNone(frame._resolve_clicked_cell(self._event()))

    def test_resolve_returns_none_on_out_of_range_column(self):
        frame = self._make_frame("role")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "R001"
        frame.results_tree.identify_column.return_value = "#9"
        frame.results_tree.item.return_value = ("Reader", "閲覧者", "desc")
        self.assertIsNone(frame._resolve_clicked_cell(self._event()))

    def test_handle_copy_invokes_on_copy_with_column_name(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "cell"
        frame.results_tree.identify_row.return_value = "I001"
        frame.results_tree.identify_column.return_value = "#4"
        frame.results_tree.item.return_value = (
            "alice", "Alice", "a@x.com", "oid-xyz", "user")
        frame.handle_copy(self._event())
        frame.on_copy.assert_called_once_with("oid-xyz", "オブジェクトID")

    def test_handle_copy_skips_when_unresolved(self):
        frame = self._make_frame("object")
        frame.results_tree.identify_region.return_value = "heading"
        frame.handle_copy(self._event())
        frame.on_copy.assert_not_called()


if __name__ == '__main__':
    # テストを実行
    unittest.main(verbosity=2)
