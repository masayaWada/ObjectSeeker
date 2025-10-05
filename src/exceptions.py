"""
カスタム例外クラス
"""


class ObjectSeekerError(Exception):
    """ObjectSeekerの基底例外クラス"""
    pass


class ConfigurationError(ObjectSeekerError):
    """設定関連のエラー"""
    pass


class AuthenticationError(ObjectSeekerError):
    """認証関連のエラー"""
    pass


class SearchError(ObjectSeekerError):
    """検索関連のエラー"""
    pass


class UIError(ObjectSeekerError):
    """UI関連のエラー"""
    pass


class AzureCLIError(ObjectSeekerError):
    """Azure CLI関連のエラー"""
    pass


class AzureGraphAPIError(ObjectSeekerError):
    """Azure Graph API関連のエラー"""
    pass
