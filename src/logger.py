"""
ログ管理モジュール
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """アプリケーションログを管理するクラス"""

    def __init__(self, name: str = "ObjectSeeker", log_level: int = logging.INFO):
        """
        ロガーを初期化

        Args:
            name: ロガー名
            log_level: ログレベル
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # 既存のハンドラーをクリア
        self.logger.handlers.clear()

        # ログディレクトリの作成
        self.log_dir = Path.home() / ".objectseeker" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # ファイルハンドラーの設定
        self._setup_file_handler()

        # コンソールハンドラーの設定
        self._setup_console_handler()

    def _setup_file_handler(self) -> None:
        """ファイルハンドラーを設定"""
        log_file = self.log_dir / \
            f"objectseeker_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self) -> None:
        """コンソールハンドラーを設定"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)

    def debug(self, message: str) -> None:
        """デバッグログを出力"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """情報ログを出力"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """警告ログを出力"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """エラーログを出力"""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """クリティカルログを出力"""
        self.logger.critical(message)

    def exception(self, message: str) -> None:
        """例外ログを出力（スタックトレース付き）"""
        self.logger.exception(message)
