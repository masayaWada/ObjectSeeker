#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ObjectSeeker メインエントリーポイント
"""

from src.logger import Logger
from src.app import create_app
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """メイン関数"""
    logger = Logger()

    try:
        logger.info("ObjectSeekerを起動しています...")

        # アプリケーションを作成
        root, app = create_app()

        # アプリケーションを実行
        root.mainloop()

    except KeyboardInterrupt:
        logger.info("ユーザーによってアプリケーションが中断されました")
    except Exception as e:
        logger.exception(f"アプリケーション起動エラー: {e}")
        print(f"アプリケーション起動エラー: {e}")
        sys.exit(1)
    finally:
        logger.info("ObjectSeekerを終了しました")


if __name__ == "__main__":
    main()
