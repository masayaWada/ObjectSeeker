"""
Azure Graph API 検索モジュール
"""

import requests
from typing import List, Dict, Any, Optional
from .logger import Logger
from .exceptions import AzureGraphAPIError


class GraphAPISearcher:
    """Azure Graph API検索クラス"""

    def __init__(self, azure_client, logger: Optional[Logger] = None):
        """
        Graph API検索クライアントを初期化

        Args:
            azure_client: AzureClientインスタンス
            logger: ロガーインスタンス
        """
        self.azure_client = azure_client
        self.logger = logger or Logger()
        self.base_url = "https://graph.microsoft.com/v1.0"

    def search_users(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        ユーザーを検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            検索結果のリスト
        """
        self.logger.debug(f"ユーザー検索を実行: {query}")

        if not self.azure_client.is_authenticated():
            raise AzureGraphAPIError("認証されていません")

        endpoint = f"{self.base_url}/users"
        filter_value = (
            f"startswith(displayName,'{query}') or "
            f"startswith(mail,'{query}') or "
            f"startswith(userPrincipalName,'{query}')"
        )

        return self._search_objects(endpoint, filter_value, max_results, "user")

    def search_groups(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        グループを検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            検索結果のリスト
        """
        self.logger.debug(f"グループ検索を実行: {query}")

        if not self.azure_client.is_authenticated():
            raise AzureGraphAPIError("認証されていません")

        endpoint = f"{self.base_url}/groups"
        filter_value = (
            f"startswith(displayName,'{query}') or "
            f"startswith(mail,'{query}')"
        )

        return self._search_objects(endpoint, filter_value, max_results, "group")

    def search_applications(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        アプリケーションを検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            検索結果のリスト
        """
        self.logger.debug(f"アプリケーション検索を実行: {query}")

        if not self.azure_client.is_authenticated():
            raise AzureGraphAPIError("認証されていません")

        endpoint = f"{self.base_url}/applications"
        filter_value = f"startswith(displayName,'{query}')"

        return self._search_objects(endpoint, filter_value, max_results, "application")

    def _search_objects(self, endpoint: str, filter_value: str, max_results: int, object_type: str) -> List[Dict[str, Any]]:
        """
        オブジェクト検索の共通処理

        Args:
            endpoint: APIエンドポイント
            filter_value: フィルター条件
            max_results: 最大結果数
            object_type: オブジェクトタイプ

        Returns:
            検索結果のリスト
        """
        try:
            # 検索パラメータ
            params = {
                '$filter': filter_value,
                '$select': 'id,displayName,mail,userPrincipalName',
                '$top': min(max_results, 100)  # Graph APIの制限
            }

            # ヘッダー
            headers = {
                'Authorization': f'Bearer {self.azure_client.access_token}',
                'Content-Type': 'application/json'
            }

            # 検索リクエスト
            self.logger.debug(f"Graph APIリクエスト: {endpoint}")
            response = requests.get(
                endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            # 結果の解析
            data = response.json()
            results = data.get('value', [])

            self.logger.info(f"{object_type}検索完了: {len(results)}件の結果")
            return results

        except requests.exceptions.RequestException as e:
            error_msg = f"Graph APIリクエストエラー: {e}"
            self.logger.error(error_msg)
            raise AzureGraphAPIError(error_msg)
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self.logger.error(error_msg)
            raise AzureGraphAPIError(error_msg)

    def format_search_results(self, results: List[Dict[str, Any]], object_type: str) -> List[Dict[str, Any]]:
        """
        検索結果をフォーマット

        Args:
            results: 検索結果
            object_type: オブジェクトタイプ

        Returns:
            フォーマットされた結果
        """
        formatted_results = []

        for item in results:
            name = item.get('displayName', '')
            email = item.get('mail', '') or item.get('userPrincipalName', '')
            object_id = item.get('id', '')

            # 表示名の設定
            display_name = name if name else email

            formatted_item = {
                'name': name,
                'display_name': display_name,
                'email': email,
                'object_id': object_id,
                'type': object_type
            }

            formatted_results.append(formatted_item)

        return formatted_results
