# minicp

MiniCPの講義を参考にしながら、制約プログラミングソルバーをPythonとRustで実装する学習用プロジェクトです。

まず読みやすいPython実装を作り、同じ振る舞いをする部品をRustとPyO3で実装して比較します。現在は、バックトラック可能な整数状態とSparse Setを実装しています。

## セットアップ

Python 3.12、Rust、[uv](https://docs.astral.sh/uv/)を使用します。

```console
uv sync
```

`uv sync`によりRust拡張もビルドされ、`minicp._rust`としてインポートできるようになります。

## Rust拡張のビルド

`src/lib.rs`などのRustコードを編集した後は、プロジェクトルートで次を実行します。

```console
uv run maturin develop
```

これは開発用のRust拡張をビルドし、現在の仮想環境へインストールします。変更後の基本的な確認手順は次のとおりです。

```console
uv run maturin develop
uv run pytest
```

最適化を有効にしたRust拡張をビルドする場合は、`--release`を指定します。

```console
uv run maturin develop --release
```

Rust拡張を直接読み込めることは、次のコマンドで確認できます。

```console
uv run python -c "from minicp._rust import SparseSet; print(SparseSet(1, 3).values())"
```

期待される出力は次のとおりです。

```text
[1, 2, 3]
```

JupyterでRust拡張を使用している場合、再ビルド後も古い共有ライブラリが読み込まれていることがあります。その場合はJupyterカーネルを再起動します。

## Python版Sparse Set

Python版は`StateManager`と連携しているため、変更を保存・復元できます。

```python
from minicp import SparseSet, StateManager

manager = StateManager()
domain = SparseSet(manager, minimum=2, maximum=6)

manager.save()
domain.remove(4)

assert not domain.contains(4)
assert domain.size == 4

manager.restore()

assert domain.contains(4)
assert domain.size == 5
```

## Rust版Sparse Set

Rust版は内部実装を明示するため、非公開モジュール`minicp._rust`から利用します。現時点では基本的な集合操作のみを実装し、状態の保存・復元はまだPython版だけが対応しています。

```python
from minicp._rust import SparseSet

domain = SparseSet(minimum=2, maximum=6)
domain.remove(4)

assert not domain.contains(4)
assert domain.size == 4
assert domain.min == 2
assert domain.max == 6
assert set(domain.values()) == {2, 3, 5, 6}
```

通常のコードではPython版を`minicp`から利用します。`minicp._rust`は挙動の比較や実装実験のための内部APIです。

## テスト

```console
uv run pytest
```

Python版とRust版の共通テストにより、以下の操作が同じ結果になることを確認します。

- `contains(value)`
- `remove(value)`
- `size`
- `min` / `max`
- `values()`

静的チェックは次のコマンドで実行できます。

```console
uv run ruff check src tests
uv run ty check
```
