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

    def __init__(self, parent, azure_client, on_auth_success: Optional[Callable] = None, logger: Optional[Logger] = None):
        """
        認証フレームを初期化

        Args:
            parent: 親ウィジェット
            azure_client: AzureClientインスタンス
            on_auth_success: 認証成功時のコールバック
            logger: ロガーインスタンス
        """
        super().__init__(parent, text="Azure CLI認証", padding="5")
        self.azure_client = azure_client
        self.on_auth_success = on_auth_success
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
            # 認証成功時のコールバックを呼び出す
            if self.on_auth_success:
                self.on_auth_success()
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


class TabbedSearchFrame(ttk.Frame):
    """タブ付き検索フレーム"""

    def __init__(self, parent, on_object_search: Callable, on_role_search: Callable, azure_client=None, logger: Optional[Logger] = None):
        """
        タブ付き検索フレームを初期化

        Args:
            parent: 親ウィジェット
            on_object_search: オブジェクト検索実行時のコールバック
            on_role_search: ロール検索実行時のコールバック
            azure_client: AzureClientインスタンス
            logger: ロガーインスタンス
        """
        super().__init__(parent)
        self.on_object_search = on_object_search
        self.on_role_search = on_role_search
        self.azure_client = azure_client
        self.logger = logger or Logger()

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # タブの作成
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # オブジェクト検索タブ
        self.object_search_frame = SearchFrame(
            self.notebook, self.on_object_search, self.logger)
        self.notebook.add(self.object_search_frame, text="オブジェクトID検索")

        # ロール名検索タブ
        self.role_search_frame = RoleSearchFrame(
            self.notebook, self.on_role_search, self.azure_client, self.logger)
        self.notebook.add(self.role_search_frame, text="ロール名検索")

    def refresh_role_search_subscriptions(self):
        """ロール検索フレームのサブスクリプション一覧を更新"""
        if self.role_search_frame:
            self.role_search_frame._load_subscriptions()


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


class RoleSearchFrame(ttk.LabelFrame):
    """ロール名検索フレーム"""

    def __init__(self, parent, on_search: Callable, azure_client=None, logger: Optional[Logger] = None):
        """
        ロール名検索フレームを初期化

        Args:
            parent: 親ウィジェット
            on_search: 検索実行時のコールバック
            azure_client: AzureClientインスタンス
            logger: ロガーインスタンス
        """
        super().__init__(parent, text="ロール名検索", padding="5")
        self.on_search = on_search
        self.azure_client = azure_client
        self.logger = logger or Logger()
        self.subscriptions = []
        self.resource_groups = []

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(1, weight=1)

        row = 0

        # サブスクリプション選択
        ttk.Label(self, text="サブスクリプション:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.subscription_var = tk.StringVar()
        self.subscription_combo = ttk.Combobox(
            self, textvariable=self.subscription_var, width=47, state="readonly")
        self.subscription_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))
        self.subscription_combo.bind('<<ComboboxSelected>>', self._on_subscription_selected)
        self.subscription_combo['values'] = ['（すべて - 組み込みロールのみ）']
        self.subscription_combo.current(0)

        # リソースグループ選択
        row += 1
        ttk.Label(self, text="リソースグループ:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.resource_group_var = tk.StringVar()
        self.resource_group_combo = ttk.Combobox(
            self, textvariable=self.resource_group_var, width=47, state="readonly")
        self.resource_group_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))
        self.resource_group_combo['values'] = ['（すべて）']
        self.resource_group_combo.current(0)
        self.resource_group_combo.config(state="disabled")

        # 検索クエリ
        row += 1
        ttk.Label(self, text="ロール名（日本語または英語）:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.search_query_var = tk.StringVar()
        search_entry = ttk.Entry(
            self, textvariable=self.search_query_var, width=50)
        search_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))
        search_entry.bind('<Return>', lambda e: self.execute_search())

        # 検索ボタン
        self.search_button = ttk.Button(
            self, text="検索", command=self.execute_search)
        self.search_button.grid(row=row, column=2, padx=(5, 0), pady=(0, 5))

        # 説明ラベル
        row += 1
        info_label = ttk.Label(
            self,
            text="例: 「閲覧者」と入力すると「Reader」を取得できます。スコープを選択するとカスタムロールも検索できます。",
            foreground="gray"
        )
        info_label.grid(row=row, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)

        # 認証状態が確認できたらサブスクリプション一覧を読み込む
        if self.azure_client and self.azure_client.is_authenticated():
            self._load_subscriptions()

    def _load_subscriptions(self):
        """サブスクリプション一覧を読み込む"""
        if not self.azure_client:
            return

        try:
            self.subscriptions = self.azure_client.get_subscriptions()
            subscription_names = ['（すべて - 組み込みロールのみ）']
            for sub in self.subscriptions:
                name = sub.get('name', '')
                sub_id = sub.get('id', '')
                if name and sub_id:
                    subscription_names.append(f"{name} ({sub_id})")
            self.subscription_combo['values'] = subscription_names
            self.subscription_combo.current(0)
        except Exception as e:
            self.logger.error(f"サブスクリプション一覧の読み込みエラー: {e}")

    def _on_subscription_selected(self, event=None):
        """サブスクリプション選択時の処理"""
        selected = self.subscription_var.get()
        
        if selected == '（すべて - 組み込みロールのみ）':
            self.resource_group_combo['values'] = ['（すべて）']
            self.resource_group_combo.current(0)
            self.resource_group_combo.config(state="disabled")
            return

        # サブスクリプションIDを抽出
        subscription_id = None
        for sub in self.subscriptions:
            name = sub.get('name', '')
            sub_id = sub.get('id', '')
            if f"{name} ({sub_id})" == selected:
                subscription_id = sub_id
                break

        if not subscription_id:
            return

        # リソースグループ一覧を読み込む
        try:
            self.resource_groups = self.azure_client.get_resource_groups(subscription_id)
            resource_group_names = ['（すべて）']
            for rg in self.resource_groups:
                name = rg.get('name', '')
                if name:
                    resource_group_names.append(name)
            self.resource_group_combo['values'] = resource_group_names
            self.resource_group_combo.current(0)
            self.resource_group_combo.config(state="readonly")
        except Exception as e:
            self.logger.error(f"リソースグループ一覧の読み込みエラー: {e}")
            self.resource_group_combo['values'] = ['（すべて）']
            self.resource_group_combo.current(0)
            self.resource_group_combo.config(state="disabled")

    def get_scope(self) -> Optional[str]:
        """
        選択されたスコープを取得

        Returns:
            スコープ文字列（例: /subscriptions/xxx/resourceGroups/yyy）。選択されていない場合はNone
        """
        selected_sub = self.subscription_var.get()
        
        if selected_sub == '（すべて - 組み込みロールのみ）':
            return None

        # サブスクリプションIDを抽出
        subscription_id = None
        for sub in self.subscriptions:
            name = sub.get('name', '')
            sub_id = sub.get('id', '')
            if f"{name} ({sub_id})" == selected_sub:
                subscription_id = sub_id
                break

        if not subscription_id:
            return None

        # リソースグループが選択されているか確認
        selected_rg = self.resource_group_var.get()
        if selected_rg and selected_rg != '（すべて）':
            # リソースグループのIDを取得
            for rg in self.resource_groups:
                if rg.get('name', '') == selected_rg:
                    rg_id = rg.get('id', '')
                    if rg_id:
                        return rg_id
            # IDが見つからない場合は手動で構築
            return f"/subscriptions/{subscription_id}/resourceGroups/{selected_rg}"
        else:
            # サブスクリプションスコープ
            return f"/subscriptions/{subscription_id}"

    def execute_search(self):
        """検索を実行"""
        search_query = self.search_query_var.get().strip()

        if not search_query:
            messagebox.showerror("エラー", "検索クエリを入力してください。")
            return

        scope = self.get_scope()
        self.logger.info(f"ロール検索実行: query='{search_query}', scope='{scope}'")
        self.on_search(search_query, scope)


class ResultsFrame(ttk.LabelFrame):
    """検索結果フレーム"""

    def __init__(self, parent, on_copy: Callable, logger: Optional[Logger] = None, result_type: str = "object"):
        """
        検索結果フレームを初期化

        Args:
            parent: 親ウィジェット
            on_copy: コピー実行時のコールバック
            logger: ロガーインスタンス
            result_type: 結果タイプ（"object" または "role"）
        """
        super().__init__(parent, text="検索結果", padding="5")
        self.on_copy = on_copy
        self.logger = logger or Logger()
        self.result_type = result_type

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # 結果タイプに応じて列を設定
        columns = self._get_columns()

        self.results_tree = ttk.Treeview(
            self, columns=columns, show="headings", height=10)

        # 列の設定
        self._configure_columns(columns)

        # スクロールバー
        self.scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=self.scrollbar.set)

        # グリッド配置
        self.results_tree.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # ダブルクリックでコピー
        self.results_tree.bind('<Double-1>', self.handle_copy)

    def _get_columns(self):
        """結果タイプに応じた列を取得"""
        if self.result_type == "role":
            return ("ロール名（英語）", "表示名（日本語）", "説明")
        else:
            return ("名前", "表示名", "メール", "オブジェクトID", "タイプ")

    def _configure_columns(self, columns):
        """列を設定"""
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, minwidth=100)

    def update_result_type(self, result_type: str):
        """結果タイプを更新して列を再設定"""
        if self.result_type == result_type:
            return

        self.result_type = result_type
        columns = self._get_columns()

        # 既存のTreeviewを削除
        self.results_tree.destroy()

        # 新しいTreeviewを作成
        self.results_tree = ttk.Treeview(
            self, columns=columns, show="headings", height=10)
        self._configure_columns(columns)

        # スクロールバーを再設定
        self.results_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.results_tree.yview)

        # グリッド配置
        self.results_tree.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

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
            if self.result_type == "role":
                # ロール検索結果
                self.results_tree.insert('', 'end', values=(
                    item.get('role_name', ''),
                    item.get('display_name', ''),
                    item.get('description', '')
                ))
            else:
                # オブジェクト検索結果
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
        
        if self.result_type == "role":
            # ロール名をコピー（最初の列）
            role_name = item['values'][0] if item['values'] else ''
            if role_name:
                self.logger.info(f"ロール名をコピー: {role_name}")
                self.on_copy(role_name)
        else:
            # オブジェクトIDをコピー（4番目の列）
            object_id = item['values'][3] if len(item['values']) > 3 else ''
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
