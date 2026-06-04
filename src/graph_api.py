"""
Azure Graph API 検索モジュール
"""

import re
import requests
from typing import List, Dict, Any, Optional
from .logger import Logger
from .exceptions import AzureGraphAPIError

GUID_PATTERN = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)

_ODATA_TYPE_MAP = {
    '#microsoft.graph.user': 'user',
    '#microsoft.graph.group': 'group',
    '#microsoft.graph.servicePrincipal': 'servicePrincipal',
    '#microsoft.graph.application': 'application',
}


def is_valid_guid(value: str) -> bool:
    """GUID形式かどうかを検証"""
    if not value:
        return False
    return bool(GUID_PATTERN.match(value.strip()))


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

    def _classify_match(self, name: str, results: List[Dict[str, Any]]) -> Optional[str]:
        """
        検索結果と検索名を比較して一致度を判定する

        Args:
            name: 検索名（完全一致の判定対象）
            results: 検索結果のリスト

        Returns:
            'exact'（displayNameが完全一致）/ 'partial'（部分一致のみ）/ None（結果なし）
        """
        if not results:
            return None

        name_norm = name.strip()
        for item in results:
            if (item.get('displayName', '') or '').strip() == name_norm:
                return 'exact'
        return 'partial'

    def check_existence(self, name: str, max_results: int = 50) -> Dict[str, Any]:
        """
        名前をグループ→アプリケーションの順で検索し、存在の有無と一致度を判定する

        グループとして検索してヒットすればグループ、ヒットしなければ
        アプリケーションとして検索し、それでもヒットしなければ存在なしと判定する。

        Args:
            name: グループ名またはアプリケーション名
            max_results: 各検索の最大結果数

        Returns:
            {
                'name': 検索した名前,
                'status': 'exact' | 'partial' | 'none',
                'symbol': '〇' | '△' | '✕',
                'object_type': 'group' | 'application' | None,
            }
        """
        name_norm = name.strip()
        result = {
            'name': name_norm,
            'status': 'none',
            'symbol': '✕',
            'object_type': None,
        }

        if not name_norm:
            return result

        # グループとして検索
        group_results = self.search_groups(name_norm, max_results)
        match = self._classify_match(name_norm, group_results)
        if match:
            result['object_type'] = 'group'
            result['status'] = match
            result['symbol'] = '〇' if match == 'exact' else '△'
            return result

        # ヒットしなければアプリケーションとして検索
        app_results = self.search_applications(name_norm, max_results)
        match = self._classify_match(name_norm, app_results)
        if match:
            result['object_type'] = 'application'
            result['status'] = match
            result['symbol'] = '〇' if match == 'exact' else '△'
            return result

        # どちらにもヒットしなければ存在なし
        return result

    def lookup_by_principal_id(self, principal_id: str) -> List[Dict[str, Any]]:
        """
        プリンシパルID（オブジェクトID）から逆引き検索

        Args:
            principal_id: GUID形式のプリンシパルID（完全一致）

        Returns:
            該当オブジェクト（user/group/servicePrincipal/application）。該当なしは空リスト。
        """
        self.logger.debug(f"プリンシパルID逆引き: {principal_id}")

        if not self.azure_client.is_authenticated():
            raise AzureGraphAPIError("認証されていません")

        if not is_valid_guid(principal_id):
            raise AzureGraphAPIError(f"不正なGUID形式: {principal_id}")

        principal_id = principal_id.strip()
        endpoint = f"{self.base_url}/directoryObjects/{principal_id}"
        headers = {
            'Authorization': f'Bearer {self.azure_client.access_token}',
            'Content-Type': 'application/json',
        }

        try:
            self.logger.debug(f"Graph APIリクエスト: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=30)

            if response.status_code == 404:
                self.logger.info("プリンシパルID逆引き: 該当なし")
                return []

            response.raise_for_status()
            data = response.json()
            self.logger.info(
                f"プリンシパルID逆引き完了: {data.get('@odata.type', 'unknown')}"
            )
            return [data]

        except requests.exceptions.RequestException as e:
            error_msg = f"Graph APIリクエストエラー: {e}"
            self.logger.error(error_msg)
            raise AzureGraphAPIError(error_msg)
        except AzureGraphAPIError:
            raise
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self.logger.error(error_msg)
            raise AzureGraphAPIError(error_msg)

    def format_directory_object_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        `/directoryObjects/{id}` の結果をフォーマット（`@odata.type` から種別を判定）
        """
        formatted = []
        for item in results:
            odata_type = item.get('@odata.type', '')
            object_type = _ODATA_TYPE_MAP.get(odata_type, odata_type.replace('#microsoft.graph.', '') or 'unknown')
            name = item.get('displayName', '') or ''
            email = item.get('mail', '') or item.get('userPrincipalName', '') or ''
            object_id = item.get('id', '') or ''
            display_name = name if name else email

            formatted.append({
                'name': name,
                'display_name': display_name,
                'email': email,
                'object_id': object_id,
                'type': object_type,
            })
        return formatted

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
