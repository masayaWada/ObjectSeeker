"""
Azure ロール名検索モジュール
"""

from typing import List, Dict, Any, Optional
from .logger import Logger
from .exceptions import AzureCLIError


class RoleSearcher:
    """Azureロール名検索クラス"""

    def __init__(self, azure_client, logger: Optional[Logger] = None):
        """
        ロール検索クライアントを初期化

        Args:
            azure_client: AzureClientインスタンス
            logger: ロガーインスタンス
        """
        self.azure_client = azure_client
        self.logger = logger or Logger()
        self._role_cache: Optional[List[Dict[str, Any]]] = None

    def _get_role_definitions(self) -> List[Dict[str, Any]]:
        """
        ロール定義を取得（キャッシュ付き）

        Returns:
            ロール定義のリスト
        """
        if self._role_cache is None:
            self.logger.debug("ロール定義を取得中...")
            try:
                # 組み込みロールを取得（スコープを指定しない）
                self._role_cache = self.azure_client.get_role_definitions()
            except AzureCLIError as e:
                self.logger.error(f"ロール定義の取得エラー: {e}")
                raise

        return self._role_cache

    def search_roles(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        ロールを検索
        
        処理フロー:
        ④英語名、日本語名どちらにも検索をかけて、合致するロールIDを抽出する
        ⑤抽出したロールIDに紐づく、ロール名（英語、日本語）・説明をツールに表示する

        Args:
            query: 検索クエリ（日本語名または英語名）
            max_results: 最大結果数

        Returns:
            検索結果のリスト
        """
        self.logger.info(f"④検索開始: query='{query}'")

        if not self.azure_client.is_authenticated():
            raise AzureCLIError("認証されていません")

        try:
            # 統合済みのロール定義を取得
            role_definitions = self._get_role_definitions()
            self.logger.info(f"検索対象ロール数: {len(role_definitions)}件")

            query_lower = query.lower()
            query_original = query

            # ④英語名、日本語名どちらにも検索をかけて、合致するロールIDを抽出する
            matched_role_ids = []
            
            for role_def in role_definitions:
                properties = role_def.get('properties', {})
                role_id = role_def.get('id', '')
                
                # 英語名を取得
                role_name = properties.get('roleName', '') or role_def.get('roleName', '')
                english_display_name = properties.get('displayName', '')
                
                # 日本語名を取得
                japanese_display_name = properties.get('displayName_ja', '')
                japanese_description = properties.get('description_ja', '')
                
                # 検索条件：英語名または日本語名に一致するか
                matches_english = (
                    query_lower in role_name.lower() or
                    query_original in role_name or
                    (english_display_name and (
                        query_lower in english_display_name.lower() or
                        query_original in english_display_name
                    ))
                )
                
                matches_japanese = (
                    (japanese_display_name and (
                        query_lower in japanese_display_name.lower() or
                        query_original in japanese_display_name
                    )) or
                    (japanese_description and (
                        query_lower in japanese_description.lower() or
                        query_original in japanese_description
                    ))
                )
                
                if matches_english or matches_japanese:
                    matched_role_ids.append(role_id)
            
            self.logger.info(f"④検索完了: {len(matched_role_ids)}件のロールIDが一致")
            
            # ⑤抽出したロールIDに紐づく、ロール名（英語、日本語）・説明をツールに表示する
            results = []
            for role_def in role_definitions:
                role_id = role_def.get('id', '')
                if role_id in matched_role_ids:
                    properties = role_def.get('properties', {})
                    
                    # ロール名（英語）
                    role_name = properties.get('roleName', '') or role_def.get('roleName', '')
                    
                    # 表示名（日本語）
                    japanese_display_name = properties.get('displayName_ja', '')
                    japanese_description = properties.get('description_ja', '')
                    
                    # 表示名が空の場合、説明文の最初の部分を使用
                    # 説明文の最初の部分が日本語名になっている可能性がある
                    if not japanese_display_name and japanese_description:
                        # 説明文の最初の部分を取得（「。」や「は」で区切る）
                        desc_first = japanese_description.split('。')[0].split('は')[0].split('を')[0].split('に')[0].split('が')[0].split('の')[0].strip()
                        # 「ロール」などの接尾辞を削除
                        if desc_first.endswith('ロール'):
                            desc_first = desc_first[:-3]
                        # 長すぎる場合は無視（50文字以内）
                        if desc_first and len(desc_first) <= 50:
                            japanese_display_name = desc_first
                    
                    # 説明（日本語版を優先、なければ英語版）
                    description = japanese_description or properties.get('description', '')
                    
                    formatted_item = {
                        'role_name': role_name,
                        'display_name': japanese_display_name,
                        'description': description,
                        'id': role_id
                    }
                    
                    results.append(formatted_item)
                    
                    if len(results) >= max_results:
                        break
            
            self.logger.info(f"⑤表示用データ準備完了: {len(results)}件の結果")
            return results

        except AzureCLIError as e:
            self.logger.error(f"ロール検索エラー: {e}")
            raise
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self.logger.error(error_msg)
            raise AzureCLIError(error_msg)

    def get_role_name_from_japanese(self, japanese_name: str) -> Optional[str]:
        """
        日本語ロール名から英語のロール名を取得

        Args:
            japanese_name: 日本語のロール名（例：「閲覧者」）

        Returns:
            英語のロール名（例：「Reader」）。見つからない場合はNone
        """
        self.logger.debug(f"日本語ロール名から英語名を取得: {japanese_name}")

        try:
            role_definitions = self._get_role_definitions()

            for role_def in role_definitions:
                properties = role_def.get('properties', {})

                # 表示名を複数の場所から取得
                display_name = (
                    role_def.get('name', '') or
                    properties.get('roleName', '') or
                    role_def.get('displayName', '') or
                    properties.get('displayName', '')
                )

                role_name = (
                    role_def.get('roleName', '') or
                    properties.get('roleName', '')
                )

                # 表示名が日本語名と一致する場合（部分一致も許可）
                if japanese_name in display_name or display_name == japanese_name:
                    self.logger.info(
                        f"ロール名を取得: {japanese_name} -> {role_name}")
                    return role_name

            self.logger.warning(f"ロール名が見つかりませんでした: {japanese_name}")
            return None

        except AzureCLIError as e:
            self.logger.error(f"ロール名取得エラー: {e}")
            raise
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self.logger.error(error_msg)
            raise AzureCLIError(error_msg)

    def clear_cache(self):
        """ロール定義のキャッシュをクリア"""
        self._role_cache = None
        self.logger.debug("ロール定義のキャッシュをクリアしました")
