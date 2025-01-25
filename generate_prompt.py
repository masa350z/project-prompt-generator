#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import sys

# 収集対象の拡張子 (小文字で定義し、チェック時は小文字化)
TARGET_EXTENSIONS = {
    # C/C++/ヘッダ
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh',
    # Java, Kotlin
    '.java', '.kt',
    # C#
    '.cs',
    # Go
    '.go',
    # Rust
    '.rs',
    # Swift
    '.swift',
    # JS/TS
    '.js', '.jsx', '.ts', '.tsx',
    # PHP
    '.php',
    # Python
    '.py',
    # Ruby
    '.rb',
    # Shell / Batch / PowerShell
    '.sh', '.bat', '.cmd', '.ps1',
    # Config / Text
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.config', '.env',
    '.md', '.txt',
    # その他特別ファイル名
}
# 拡張子がないが対象にしたいファイル名（Dockerfileなど）
TARGET_FILENAMES = {
    'makefile', 'dockerfile', 'readme',  # 大文字小文字区別無しに扱いたい例
    'requirements.txt', 'pipfile', 'package.json',
    'tsconfig.json', 'composer.json'
}

# 無視したいディレクトリ (先頭一致でフィルタするために小文字で定義)
IGNORE_DIRNAMES = [
    '.git', 'node_modules', '__pycache__'
]

# 無視したいファイル名・拡張子
IGNORE_FILENAMES = {
    '.gitignore',  # プロジェクトに直接必要ない(今回は除外する)
    # ビルド成果物など
    '.pyc', '.o', '.class', '.exe', '.dll', '.so',
}


def is_target_file(file_path: str) -> bool:
    """
    収集対象のファイルかどうかを判定する。
    """
    base_name = os.path.basename(file_path)
    _, ext = os.path.splitext(base_name)

    # 小文字にして判定する
    base_name_lower = base_name.lower()
    ext_lower = ext.lower()

    # 無視すべきファイル名に合致すれば除外
    if base_name_lower in IGNORE_FILENAMES:
        return False

    # 拡張子があれば、その拡張子が対象リストにあるか
    if ext_lower in TARGET_EXTENSIONS:
        return True

    # 拡張子がない場合でも、特定のファイル名(例: Makefile, Dockerfile等)が対象か
    if ext_lower == '' and base_name_lower in TARGET_FILENAMES:
        return True

    return False


def is_ignore_dir(dir_name: str) -> bool:
    """
    無視したいディレクトリかどうかを判定する。
    ディレクトリ名はすべて小文字にして先頭一致でチェック。
    """
    dir_name_lower = dir_name.lower()
    for ignore_name in IGNORE_DIRNAMES:
        if dir_name_lower.startswith(ignore_name):
            return True
    return False


def get_directory_structure(root_path: str) -> str:
    """
    ルートディレクトリ以下の構造をツリー状の文字列で返す。
    """
    lines = []

    def recurse_dir(current_path: str, prefix: str = ""):
        # ディレクトリ内の要素を取得してソート
        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return  # アクセス権がない場合などはスキップ

        for i, item in enumerate(items):
            item_path = os.path.join(current_path, item)
            # 無視するディレクトリなどを除外
            if os.path.isdir(item_path) and is_ignore_dir(item):
                continue

            # 末尾要素判定 (ツリー描画用)
            connector = "└──" if i == len(items) - 1 else "├──"

            lines.append(prefix + connector + " " + item)

            if os.path.isdir(item_path):
                # ディレクトリなら再帰
                # 下層に降りる際のprefixを整形
                deeper_prefix = prefix + \
                    ("    " if i == len(items) - 1 else "│   ")
                recurse_dir(item_path, deeper_prefix)

    base_name = os.path.basename(os.path.abspath(root_path))
    lines.append(base_name)
    recurse_dir(root_path)
    return "\n".join(lines)


def collect_files(root_path: str):
    """
    root_path以下の全対象ファイルのパス(相対パス)をリストで返す。
    """
    target_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 無視ディレクトリを除外
        dirnames[:] = [d for d in dirnames if not is_ignore_dir(d)]

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if is_target_file(file_path):
                # 相対パスに変換して管理
                rel_path = os.path.relpath(file_path, root_path)
                target_files.append(rel_path)
    target_files.sort()
    return target_files


def main():
    parser = argparse.ArgumentParser(
        description="指定ディレクトリ以下のプログラムや設定ファイルを収集し、ディレクトリ構成とともにテキスト出力します。"
    )
    parser.add_argument(
        "--dir", "-d",
        default=".",
        help="対象のディレクトリ(デフォルトは現在のディレクトリ)"
    )
    parser.add_argument(
        "--out", "-o",
        default="output.txt",
        help="出力先のファイル名(デフォルト: output.txt)"
    )
    args = parser.parse_args()

    root_path = os.path.abspath(args.dir)
    out_path = os.path.abspath(args.out)

    # ディレクトリ構成を取得
    directory_tree = get_directory_structure(root_path)

    # 対象ファイルを収集
    files_to_list = collect_files(root_path)

    # 出力ファイルを開いて書き込む
    with open(out_path, mode="w", encoding="utf-8") as f:
        # 1. ディレクトリ構成出力
        f.write("=== Directory Structure ===\n")
        f.write(directory_tree)
        f.write("\n\n")

        # 2. ファイル内容出力
        f.write("=== File Contents ===\n")
        for rel_path in files_to_list:
            abs_path = os.path.join(root_path, rel_path)
            f.write(f"--- {rel_path} ---\n")
            try:
                with open(abs_path, mode="r", encoding="utf-8", errors="replace") as fp:
                    content = fp.read()
            except Exception as e:
                content = f"[読み込みエラー: {e}]\n"
            f.write(content)
            f.write("\n")

    print(f"完了しました。出力先: {out_path}")


if __name__ == "__main__":
    main()
