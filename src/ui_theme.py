"""
UIテーマとスタイル管理
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
from .config import Config
from .logger import Logger


class ThemeManager:
    """テーマとスタイルを管理するクラス"""

    def __init__(self, config: Config, logger: Optional[Logger] = None):
        """
        テーママネージャーを初期化

        Args:
            config: 設定インスタンス
            logger: ロガーインスタンス
        """
        self.config = config
        self.logger = logger or Logger()
        self.current_theme = self.config.get('ui.theme', 'default')
        self.font_size = self.config.get('ui.font_size', 10)

        # テーマ定義
        self.themes = {
            'default': {
                'colors': {
                    'bg': '#f0f0f0',
                    'fg': '#000000',
                    'select_bg': '#0078d4',
                    'select_fg': '#ffffff',
                    'button_bg': '#e1e1e1',
                    'button_fg': '#000000',
                    'entry_bg': '#ffffff',
                    'entry_fg': '#000000',
                    'frame_bg': '#f0f0f0',
                    'success': '#107c10',
                    'warning': '#ff8c00',
                    'error': '#d13438'
                },
                'fonts': {
                    'default': ('Segoe UI', 9),
                    'heading': ('Segoe UI', 10, 'bold'),
                    'small': ('Segoe UI', 8)
                }
            },
            'dark': {
                'colors': {
                    'bg': '#2d2d2d',
                    'fg': '#ffffff',
                    'select_bg': '#0078d4',
                    'select_fg': '#ffffff',
                    'button_bg': '#404040',
                    'button_fg': '#ffffff',
                    'entry_bg': '#404040',
                    'entry_fg': '#ffffff',
                    'frame_bg': '#2d2d2d',
                    'success': '#107c10',
                    'warning': '#ff8c00',
                    'error': '#d13438'
                },
                'fonts': {
                    'default': ('Segoe UI', 9),
                    'heading': ('Segoe UI', 10, 'bold'),
                    'small': ('Segoe UI', 8)
                }
            }
        }

    def get_current_theme(self) -> Dict[str, Any]:
        """現在のテーマを取得"""
        return self.themes.get(self.current_theme, self.themes['default'])

    def apply_theme(self, root: tk.Tk):
        """テーマを適用"""
        theme = self.get_current_theme()
        colors = theme['colors']

        # スタイルの設定
        style = ttk.Style()

        # 基本スタイル
        style.configure('TFrame', background=colors['frame_bg'])
        style.configure(
            'TLabel', background=colors['frame_bg'], foreground=colors['fg'])
        style.configure(
            'TButton', background=colors['button_bg'], foreground=colors['button_fg'])
        style.configure(
            'TEntry', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'])
        style.configure(
            'TCombobox', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'])
        style.configure(
            'Treeview', background=colors['bg'], foreground=colors['fg'])
        style.configure(
            'Treeview.Heading', background=colors['button_bg'], foreground=colors['button_fg'])

        # フォントの適用
        fonts = theme['fonts']
        self._apply_fonts(root, fonts)

        self.logger.info(f"テーマ '{self.current_theme}' を適用しました")

    def _apply_fonts(self, widget, fonts: Dict[str, tuple]):
        """フォントを適用"""
        try:
            # デフォルトフォントを設定
            default_font = fonts['default']
            widget.option_add('*Font', default_font)

            # 特定のウィジェットにフォントを適用
            for widget_type, font in fonts.items():
                if widget_type != 'default':
                    widget.option_add(f'*{widget_type}*Font', font)

        except Exception as e:
            self.logger.error(f"フォント適用エラー: {e}")

    def get_color(self, color_name: str) -> str:
        """色を取得"""
        theme = self.get_current_theme()
        return theme['colors'].get(color_name, '#000000')

    def get_font(self, font_name: str = 'default') -> tuple:
        """フォントを取得"""
        theme = self.get_current_theme()
        return theme['fonts'].get(font_name, theme['fonts']['default'])

    def set_theme(self, theme_name: str):
        """テーマを変更"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.config.set('ui.theme', theme_name)
            self.logger.info(f"テーマを '{theme_name}' に変更しました")
        else:
            self.logger.warning(f"不明なテーマ: {theme_name}")


class AccessibilityManager:
    """アクセシビリティ機能を管理するクラス"""

    def __init__(self, logger: Optional[Logger] = None):
        """
        アクセシビリティマネージャーを初期化

        Args:
            logger: ロガーインスタンス
        """
        self.logger = logger or Logger()
        self.high_contrast = False
        self.large_fonts = False

    def enable_high_contrast(self, root: tk.Tk):
        """ハイコントラストモードを有効化"""
        self.high_contrast = True

        # ハイコントラストカラーを設定
        root.configure(bg='#000000')

        # スタイルを更新
        style = ttk.Style()
        style.configure('TFrame', background='#000000')
        style.configure('TLabel', background='#000000', foreground='#ffffff')
        style.configure('TButton', background='#ffffff', foreground='#000000')

        self.logger.info("ハイコントラストモードを有効化しました")

    def disable_high_contrast(self, root: tk.Tk):
        """ハイコントラストモードを無効化"""
        self.high_contrast = False

        # デフォルトカラーに戻す
        root.configure(bg='#f0f0f0')

        self.logger.info("ハイコントラストモードを無効化しました")

    def enable_large_fonts(self, root: tk.Tk):
        """大きなフォントを有効化"""
        self.large_fonts = True

        # フォントサイズを大きくする
        root.option_add('*Font', ('Segoe UI', 12))

        self.logger.info("大きなフォントを有効化しました")

    def disable_large_fonts(self, root: tk.Tk):
        """大きなフォントを無効化"""
        self.large_fonts = False

        # デフォルトフォントサイズに戻す
        root.option_add('*Font', ('Segoe UI', 9))

        self.logger.info("大きなフォントを無効化しました")

    def add_tooltips(self, widget, text: str):
        """ツールチップを追加"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(tooltip, text=text, background='#ffffcc',
                             relief='solid', borderwidth=1, font=('Segoe UI', 8))
            label.pack()

            # 3秒後にツールチップを削除
            widget.after(3000, tooltip.destroy)

        widget.bind('<Enter>', show_tooltip)

    def add_keyboard_shortcuts(self, root: tk.Tk):
        """キーボードショートカットを追加"""
        # Ctrl+Q: 終了
        root.bind('<Control-q>', lambda e: root.quit())

        # Ctrl+R: 認証更新
        root.bind('<Control-r>', lambda e: self._refresh_auth())

        # Ctrl+F: 検索フォーカス
        root.bind('<Control-f>', lambda e: self._focus_search())

        # Escape: 検索クリア
        root.bind('<Escape>', lambda e: self._clear_search())

        self.logger.info("キーボードショートカットを追加しました")

    def _refresh_auth(self):
        """認証を更新"""
        # このメソッドは実際のアプリケーションで実装
        pass

    def _focus_search(self):
        """検索フィールドにフォーカス"""
        # このメソッドは実際のアプリケーションで実装
        pass

    def _clear_search(self):
        """検索をクリア"""
        # このメソッドは実際のアプリケーションで実装
        pass
