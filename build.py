"""
ビルドスクリプト
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """コマンドを実行"""
    print(f"\n{description}...")
    print(f"実行コマンド: {command}")

    try:
        result = subprocess.run(command, shell=True,
                                check=True, capture_output=True, text=True)
        print("✓ 成功")
        if result.stdout:
            print(f"出力: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失敗: {e}")
        if e.stderr:
            print(f"エラー: {e.stderr}")
        return False


def clean_build():
    """ビルドディレクトリをクリーンアップ"""
    print("\nビルドディレクトリをクリーンアップ中...")

    try:
        dirs_to_clean = ['build', 'dist', '__pycache__']
        files_to_clean = ['*.spec']

        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                try:
                    shutil.rmtree(dir_name)
                    print(f"✓ {dir_name} を削除")
                except PermissionError as e:
                    print(f"⚠ {dir_name} の削除に失敗（権限エラー）: {e}")
                except Exception as e:
                    print(f"⚠ {dir_name} の削除に失敗: {e}")

        # .specファイルを削除
        for spec_file in Path('.').glob('*.spec'):
            try:
                spec_file.unlink()
                print(f"✓ {spec_file} を削除")
            except PermissionError as e:
                print(f"⚠ {spec_file} の削除に失敗（権限エラー）: {e}")
            except Exception as e:
                print(f"⚠ {spec_file} の削除に失敗: {e}")

        print("✓ クリーンアップが完了しました")
        return True

    except Exception as e:
        print(f"✗ クリーンアップ中にエラーが発生: {e}")
        return False


def install_dependencies():
    """依存関係をインストール"""
    print("\n依存関係をインストール中...")

    commands = [
        "pip install -r requirements.txt"
    ]

    for command in commands:
        if not run_command(command, f"依存関係インストール: {command}"):
            print("⚠ 依存関係のインストールに失敗しましたが、ビルドを続行します")

    return True


def run_tests():
    """テストを実行"""
    print("\nテストを実行中...")

    # pytestがインストールされているかチェック
    try:
        import pytest
        if not run_command("python -m pytest tests/ -v", "テスト実行"):
            print("⚠ テストが失敗しましたが、ビルドを続行します")
    except ImportError:
        print("⚠ pytestがインストールされていません。テストをスキップします")

    return True


def build_executable():
    """実行ファイルをビルド"""
    print("\n実行ファイルをビルド中...")

    # PyInstallerコマンド（Windows用に調整）
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--name=ObjectSeeker",
        "--add-data=src;src",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=requests",
        "--hidden-import=pyperclip",
        "--hidden-import=json",
        "--hidden-import=subprocess",
        "--hidden-import=threading",
        "main.py"
    ]

    command = " ".join(pyinstaller_cmd)

    if not run_command(command, "PyInstallerビルド"):
        return False

    return True


def create_release_package():
    """リリースパッケージを作成"""
    print("\nリリースパッケージを作成中...")

    # リリースディレクトリを作成
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # 実行ファイルをコピー
    exe_file = Path("dist/ObjectSeeker.exe")
    if exe_file.exists():
        shutil.copy2(exe_file, release_dir / "ObjectSeeker.exe")
        print("✓ ObjectSeeker.exe をコピー")
    else:
        print("✗ ObjectSeeker.exe が見つかりません")
        return False

    # READMEをコピー
    readme_file = Path("README.md")
    if readme_file.exists():
        shutil.copy2(readme_file, release_dir / "README.md")
        print("✓ README.md をコピー")

    # LICENSEをコピー
    license_file = Path("LICENSE")
    if license_file.exists():
        shutil.copy2(license_file, release_dir / "LICENSE")
        print("✓ LICENSE をコピー")

    # requirements.txtをコピー
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        shutil.copy2(requirements_file, release_dir / "requirements.txt")
        print("✓ requirements.txt をコピー")

    print(f"\n✓ リリースパッケージが作成されました: {release_dir.absolute()}")
    return True


def main():
    """メイン関数"""
    print("ObjectSeeker ビルドスクリプト")
    print("=" * 50)

    # 現在のディレクトリを確認
    if not Path("main.py").exists():
        print("✗ main.py が見つかりません。プロジェクトルートで実行してください。")
        sys.exit(1)

    # ビルドプロセスを実行
    steps = [
        ("クリーンアップ", clean_build),
        ("依存関係インストール", install_dependencies),
        ("テスト実行", run_tests),
        ("実行ファイルビルド", build_executable),
        ("リリースパッケージ作成", create_release_package)
    ]

    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_func():
            print(f"\n✗ {step_name} が失敗しました。ビルドを中止します。")
            sys.exit(1)

    print("\n" + "="*50)
    print("✓ ビルドが完了しました！")
    print("✓ リリースパッケージは 'release' ディレクトリに作成されました。")
    print("="*50)


if __name__ == "__main__":
    main()
