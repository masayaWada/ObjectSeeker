"""
ObjectSeeker - Azure ADオブジェクトID検索ツール

このパッケージは、Azure ADのユーザー、グループ、アプリケーションの
オブジェクトIDを効率的に検索・取得するためのPython GUIツールです。

主な機能:
- Azure ADオブジェクトの検索
- 直感的なGUI操作
- ワンクリックコピー機能
- Azure CLI認証
- 設定可能なテーマとアクセシビリティ
- 包括的なログ機能
- テスト対応

使用方法:
    from src.app import create_app
    
    root, app = create_app()
    root.mainloop()

バージョン: 1.0.0
作者: ObjectSeeker Team
ライセンス: MIT
"""

__version__ = "1.0.0"
__author__ = "ObjectSeeker Team"
__description__ = "Azure ADのユーザー、グループ、アプリケーションのオブジェクトIDを効率的に検索・取得するGUIツール"
