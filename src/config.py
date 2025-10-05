"""
設定管理モジュール
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """アプリケーション設定を管理するクラス"""

    def __init__(self, config_file: Optional[str] = None):
        """
        設定を初期化

        Args:
            config_file: 設定ファイルのパス（デフォルトはユーザーディレクトリ）
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config = self._load_default_config()
        self.load_config()

    def _get_default_config_path(self) -> str:
        """デフォルトの設定ファイルパスを取得"""
        config_dir = Path.home() / ".objectseeker"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.json")

    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を読み込み"""
        return {
            "window": {
                "width": 800,
                "height": 600,
                "resizable": True
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
            }
        }

    def load_config(self) -> None:
        """設定ファイルから設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"設定ファイルの読み込みエラー: {e}")

    def save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"設定ファイルの保存エラー: {e}")

    def _merge_config(self, loaded_config: Dict[str, Any]) -> None:
        """読み込んだ設定を既存の設定にマージ"""
        def merge_dict(base: Dict, update: Dict) -> None:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, loaded_config)

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得（ドット記法対応）"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """設定値を設定（ドット記法対応）"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_window_config(self) -> Dict[str, Any]:
        """ウィンドウ設定を取得"""
        return self.get('window', {})

    def get_search_config(self) -> Dict[str, Any]:
        """検索設定を取得"""
        return self.get('search', {})

    def get_azure_config(self) -> Dict[str, Any]:
        """Azure設定を取得"""
        return self.get('azure', {})
