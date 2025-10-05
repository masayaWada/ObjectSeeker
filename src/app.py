"""
メインアプリケーションクラス
"""

import tkinter as tk
from tkinter import messagebox
import threading
import pyperclip
from typing import Optional

from .config import Config
from .logger import Logger
from .azure_client import AzureClient, AzureCLIError
from .graph_api import GraphAPISearcher, AzureGraphAPIError
from .ui_components import AuthFrame, SearchFrame, ResultsFrame, StatusBar
from .ui_theme import ThemeManager, AccessibilityManager
from .exceptions import ObjectSeekerError


class ObjectSeekerApp:
    """ObjectSeekerメインアプリケーション"""

    def __init__(self, root: tk.Tk):
        """
        アプリケーションを初期化

        Args:
            root: Tkinterルートウィンドウ
        """
        self.root = root
        self.logger = Logger()
        self.config = Config()

        # Azure関連のクライアント
        self.azure_client = AzureClient(self.logger)
        self.graph_searcher = GraphAPISearcher(self.azure_client, self.logger)

        # UIテーマとアクセシビリティ
        self.theme_manager = ThemeManager(self.config, self.logger)
        self.accessibility_manager = AccessibilityManager(self.logger)

        try:
            self.setup_application()
            self.setup_ui()
            self.initialize_azure()
        except ObjectSeekerError as e:
            self.logger.error(f"アプリケーション初期化エラー: {e}")
            self.setup_error_ui(str(e))
        except Exception as e:
            self.logger.exception(f"予期しないエラー: {e}")
            self.setup_error_ui(str(e))

    def setup_application(self):
        """アプリケーションの基本設定"""
        self.root.title("ObjectSeeker")

        # ウィンドウサイズの設定
        window_config = self.config.get_window_config()
        width = window_config.get('width', 800)
        height = window_config.get('height', 600)
        resizable = window_config.get('resizable', True)

        self.root.geometry(f"{width}x{height}")
        self.root.resizable(resizable, resizable)

        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # テーマを適用
        self.theme_manager.apply_theme(self.root)

        # アクセシビリティ機能を有効化
        self.accessibility_manager.add_keyboard_shortcuts(self.root)

        self.logger.info("アプリケーションの基本設定が完了しました")

    def setup_ui(self):
        """UIをセットアップ"""
        # メインフレーム
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 認証フレーム
        self.auth_frame = AuthFrame(main_frame, self.azure_client, self.logger)
        self.auth_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 検索フレーム
        self.search_frame = SearchFrame(
            main_frame, self.search_objects, self.logger)
        self.search_frame.grid(
            row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 結果フレーム
        self.results_frame = ResultsFrame(
            main_frame, self.copy_object_id, self.logger)
        self.results_frame.grid(row=2, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # ステータスバー
        self.status_bar = StatusBar(main_frame, self.logger)
        self.status_bar.grid(
            row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.logger.info("UIのセットアップが完了しました")

    def setup_error_ui(self, error_message: str):
        """エラー時のUIをセットアップ"""
        # 既存のウィジェットをクリア
        for widget in self.root.winfo_children():
            widget.destroy()

        # エラーメッセージフレーム
        error_frame = tk.Frame(self.root)
        error_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # エラーメッセージ
        error_label = tk.Label(
            error_frame,
            text=f"アプリケーションの初期化中にエラーが発生しました:\n{error_message}",
            foreground="red",
            justify=tk.LEFT
        )
        error_label.pack(pady=20)

        # 再試行ボタン
        retry_button = tk.Button(
            error_frame,
            text="再試行",
            command=self.retry_initialization
        )
        retry_button.pack(pady=10)

        self.logger.error(f"エラーUIを表示: {error_message}")

    def retry_initialization(self):
        """初期化を再試行"""
        try:
            # 既存のウィジェットをクリア
            for widget in self.root.winfo_children():
                widget.destroy()

            # 再初期化
            self.setup_ui()
            self.initialize_azure()

        except Exception as e:
            self.logger.exception(f"再初期化エラー: {e}")
            self.setup_error_ui(str(e))

    def initialize_azure(self):
        """Azure関連の初期化"""
        try:
            self.status_bar.set_status("Azure CLIを確認中...")

            # Azure CLIのインストール確認
            if not self.azure_client.check_azure_cli_installation():
                self.status_bar.set_error("Azure CLIがインストールされていません")
                self.show_azure_cli_install_guide()
                return

            # 認証情報の更新
            self.azure_client.update_auth_info()

            # 認証フレームの状態を更新
            if self.auth_frame:
                self.auth_frame.update_auth_status()

            if self.azure_client.is_authenticated():
                self.status_bar.set_success("Azure CLI認証が完了しています")
            else:
                self.status_bar.set_status("Azure CLI認証が必要です")

            self.logger.info("Azure関連の初期化が完了しました")

        except AzureCLIError as e:
            self.logger.error(f"Azure初期化エラー: {e}")
            self.status_bar.set_error(f"Azure初期化エラー: {e}")
        except Exception as e:
            self.logger.exception(f"予期しないエラー: {e}")
            self.status_bar.set_error(f"予期しないエラー: {e}")

    def show_azure_cli_install_guide(self):
        """Azure CLIインストールガイダンスを表示"""
        install_guide = """
Azure CLIがインストールされていません。

以下の手順でAzure CLIをインストールしてください：

【Windows】
PowerShellで以下のコマンドを実行：
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\\AzureCLI.msi

【macOS】
brew install azure-cli

【Linux (Ubuntu/Debian)】
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

インストール後、コマンドプロンプトで 'az --version' を実行して確認してください。
        """

        messagebox.showerror("Azure CLI未インストール", install_guide)

    def search_objects(self, search_type: str, query: str):
        """オブジェクト検索を実行"""
        if not self.azure_client.is_authenticated():
            messagebox.showerror("エラー", "まず認証を完了してください。")
            return

        self.status_bar.set_status("検索中...")

        # 検索結果をクリア
        self.results_frame.clear_results()

        # 別スレッドで検索を実行
        search_thread = threading.Thread(
            target=self._search_thread,
            args=(search_type, query)
        )
        search_thread.daemon = True
        search_thread.start()

    def _search_thread(self, search_type: str, query: str):
        """検索処理（別スレッド）"""
        try:
            # 検索設定を取得
            search_config = self.config.get_search_config()
            max_results = search_config.get('max_results', 100)

            # 検索タイプに応じて検索を実行
            if search_type == "user":
                results = self.graph_searcher.search_users(query, max_results)
            elif search_type == "group":
                results = self.graph_searcher.search_groups(query, max_results)
            elif search_type == "application":
                results = self.graph_searcher.search_applications(
                    query, max_results)
            else:
                raise ValueError(f"サポートされていない検索タイプ: {search_type}")

            # 結果をフォーマット
            formatted_results = self.graph_searcher.format_search_results(
                results, search_type)

            # UI更新（メインスレッドで実行）
            self.root.after(0, lambda: self._search_success(formatted_results))

        except AzureGraphAPIError as e:
            error_msg = f"検索エラー: {e}"
            self.root.after(0, lambda: self._search_error(error_msg))
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self.root.after(0, lambda: self._search_error(error_msg))

    def _search_success(self, results):
        """検索成功時の処理"""
        if not results:
            self.status_bar.set_status("検索結果なし")
            messagebox.showinfo("検索結果", "該当するオブジェクトが見つかりませんでした。")
            return

        # 結果をUIに表示
        self.results_frame.add_results(results)
        self.status_bar.set_success(f"検索完了: {len(results)}件の結果")

    def _search_error(self, error_msg):
        """検索エラー時の処理"""
        self.status_bar.set_error(error_msg)
        messagebox.showerror("検索エラー", error_msg)

    def copy_object_id(self, object_id: str):
        """オブジェクトIDをクリップボードにコピー"""
        try:
            pyperclip.copy(object_id)
            self.status_bar.set_success(f"オブジェクトIDをコピーしました: {object_id}")
            messagebox.showinfo(
                "コピー完了",
                f"オブジェクトIDをクリップボードにコピーしました:\n{object_id}"
            )
        except Exception as e:
            self.logger.error(f"コピーエラー: {e}")
            self.status_bar.set_error(f"コピーエラー: {e}")
            messagebox.showerror("コピーエラー", f"コピーに失敗しました: {e}")

    def on_closing(self):
        """アプリケーション終了時の処理"""
        try:
            # 設定を保存
            self.config.save_config()
            self.logger.info("アプリケーションを終了します")
        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")
        finally:
            self.root.destroy()


def create_app():
    """アプリケーションを作成して実行"""
    root = tk.Tk()
    app = ObjectSeekerApp(root)

    # 終了時の処理を設定
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    return root, app
