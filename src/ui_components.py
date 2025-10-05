"""
UIコンポーネントモジュール
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List
from .logger import Logger
from .exceptions import UIError


class AuthFrame(ttk.LabelFrame):
    """認証フレーム"""

    def __init__(self, parent, azure_client, logger: Optional[Logger] = None):
        """
        認証フレームを初期化

        Args:
            parent: 親ウィジェット
            azure_client: AzureClientインスタンス
            logger: ロガーインスタンス
        """
        super().__init__(parent, text="Azure CLI認証", padding="5")
        self.azure_client = azure_client
        self.logger = logger or Logger()

        self.setup_ui()
        self.update_auth_status()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(1, weight=1)

        # Tenant ID表示（読み取り専用）
        ttk.Label(self, text="Tenant ID:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.tenant_id_var = tk.StringVar(
            value=self.azure_client.tenant_id or "")
        tenant_entry = ttk.Entry(
            self, textvariable=self.tenant_id_var, width=50, state="readonly")
        tenant_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # 認証ボタン
        self.auth_button = ttk.Button(
            self, text="認証", command=self.authenticate)
        self.auth_button.grid(row=0, column=2, padx=(5, 0))

        # 認証状態表示
        self.auth_status_var = tk.StringVar(value="認証状態を確認中...")
        self.auth_status_label = ttk.Label(
            self, textvariable=self.auth_status_var, foreground="orange")
        self.auth_status_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))

    def authenticate(self):
        """認証を実行"""
        self.logger.info("認証ボタンがクリックされました")

        # 認証状態を更新
        self.auth_status_var.set("認証中...")
        self.auth_status_label.configure(foreground="orange")
        self.auth_button.configure(state="disabled")

        # 認証を実行
        success = self.azure_client.authenticate()

        if success:
            self.update_auth_status()
            messagebox.showinfo("成功", "Azure CLI認証が完了しました。")
        else:
            self.auth_status_var.set("認証に失敗しました")
            self.auth_status_label.configure(foreground="red")
            messagebox.showerror("認証エラー", "Azure CLI認証に失敗しました。")

        self.auth_button.configure(state="normal")

    def update_auth_status(self):
        """認証状態を更新"""
        auth_status = self.azure_client.get_auth_status()

        if auth_status['is_authenticated']:
            self.tenant_id_var.set(auth_status['tenant_id'] or "")
            self.auth_status_var.set("認証済み")
            self.auth_status_label.configure(foreground="green")
        else:
            self.tenant_id_var.set("")
            self.auth_status_var.set("未認証 - 'az login' を実行してください")
            self.auth_status_label.configure(foreground="red")


class SearchFrame(ttk.LabelFrame):
    """検索フレーム"""

    def __init__(self, parent, on_search: Callable, logger: Optional[Logger] = None):
        """
        検索フレームを初期化

        Args:
            parent: 親ウィジェット
            on_search: 検索実行時のコールバック
            logger: ロガーインスタンス
        """
        super().__init__(parent, text="オブジェクト検索", padding="5")
        self.on_search = on_search
        self.logger = logger or Logger()

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(1, weight=1)

        # 検索タイプ
        ttk.Label(self, text="検索タイプ:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.search_type_var = tk.StringVar(value="user")
        search_type_combo = ttk.Combobox(
            self, textvariable=self.search_type_var,
            values=["user", "group", "application"],
            state="readonly", width=15)
        search_type_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # 検索クエリ
        ttk.Label(self, text="検索クエリ:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.search_query_var = tk.StringVar()
        search_entry = ttk.Entry(
            self, textvariable=self.search_query_var, width=50)
        search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        search_entry.bind('<Return>', lambda e: self.execute_search())

        # 検索ボタン
        self.search_button = ttk.Button(
            self, text="検索", command=self.execute_search)
        self.search_button.grid(row=1, column=2, padx=(5, 0))

    def execute_search(self):
        """検索を実行"""
        search_query = self.search_query_var.get().strip()
        search_type = self.search_type_var.get()

        if not search_query:
            messagebox.showerror("エラー", "検索クエリを入力してください。")
            return

        self.logger.info(f"検索実行: {search_type} - {search_query}")
        self.on_search(search_type, search_query)

    def get_search_params(self) -> Dict[str, str]:
        """検索パラメータを取得"""
        return {
            'type': self.search_type_var.get(),
            'query': self.search_query_var.get().strip()
        }


class ResultsFrame(ttk.LabelFrame):
    """検索結果フレーム"""

    def __init__(self, parent, on_copy: Callable, logger: Optional[Logger] = None):
        """
        検索結果フレームを初期化

        Args:
            parent: 親ウィジェット
            on_copy: コピー実行時のコールバック
            logger: ロガーインスタンス
        """
        super().__init__(parent, text="検索結果", padding="5")
        self.on_copy = on_copy
        self.logger = logger or Logger()

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # 結果表示用のTreeview
        columns = ("名前", "表示名", "メール", "オブジェクトID", "タイプ")
        self.results_tree = ttk.Treeview(
            self, columns=columns, show="headings", height=10)

        # 列の設定
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, minwidth=100)

        # スクロールバー
        scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        # グリッド配置
        self.results_tree.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # ダブルクリックでコピー
        self.results_tree.bind('<Double-1>', self.handle_copy)

    def clear_results(self):
        """検索結果をクリア"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def add_results(self, results: List[Dict[str, Any]]):
        """検索結果を追加"""
        self.clear_results()

        for item in results:
            self.results_tree.insert('', 'end', values=(
                item.get('name', ''),
                item.get('display_name', ''),
                item.get('email', ''),
                item.get('object_id', ''),
                item.get('type', '')
            ))

    def handle_copy(self, event):
        """コピー処理を実行"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        object_id = item['values'][3]  # オブジェクトID列

        if object_id:
            self.logger.info(f"オブジェクトIDをコピー: {object_id}")
            self.on_copy(object_id)


class StatusBar(ttk.Label):
    """ステータスバー"""

    def __init__(self, parent, logger: Optional[Logger] = None):
        """
        ステータスバーを初期化

        Args:
            parent: 親ウィジェット
            logger: ロガーインスタンス
        """
        self.status_var = tk.StringVar(value="準備完了")
        super().__init__(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        self.logger = logger or Logger()

    def set_status(self, message: str):
        """ステータスメッセージを設定"""
        self.status_var.set(message)
        self.logger.debug(f"ステータス更新: {message}")

    def set_error(self, message: str):
        """エラーメッセージを設定"""
        self.status_var.set(f"エラー: {message}")
        self.logger.error(f"ステータスエラー: {message}")

    def set_success(self, message: str):
        """成功メッセージを設定"""
        self.status_var.set(message)
        self.logger.info(f"ステータス成功: {message}")
