# minicp

MiniCPの講義を参考にしながら、制約プログラミングソルバーをPythonとRustで実装する学習用プロジェクトです。

まず読みやすいPython実装を作り、同じ振る舞いをする部品をRustとPyO3で実装して比較します。Python版は講義10までの主要機能、Rust版はTSPモデルに必要な状態管理、制約伝播、探索、最小化までを実装しています。

バックエンドを明示する場合は、同じ名前を持つ名前空間を選びます。

```python
from minicp import python as cp
# from minicp import rust as cp

manager = cp.StateManager()
domain = cp.SparseSet(manager, minimum=2, maximum=6)
```

既存コードとの互換性のため、`from minicp import Solver`のようなトップレベルAPIは
Pythonバックエンドを指します。Rust名前空間には、Python版と同じ振る舞いまで移植・検証できた
APIだけを公開します。現在の`minicp.rust`はTSPに必要な状態管理、ドメイン変数、
伝播エンジン、`AllDifferentDC`、`Circuit`、`Element1D`、`Sum`、DFS、最小化目的を
実装しています。それ以外の制約は引き続きPython版だけで利用できます。

## セットアップ

Python 3.12、Rust、[uv](https://docs.astral.sh/uv/)を使用します。

```console
uv sync
```

`uv sync`によりRust拡張もビルドされ、`minicp._rust`としてインポートできるようになります。

## Rust拡張のビルド

`rust/src/lib.rs`などのRustコードを編集した後は、プロジェクトルートで次を実行します。

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

Rustバックエンドを読み込めることは、次のコマンドで確認できます。

```console
uv run python -c "from minicp import rust as cp; m = cp.StateManager(); print(cp.SparseSet(m, 1, 3).values())"
```

期待される出力は次のとおりです。

```text
[1, 2, 3]
```

JupyterでRust拡張を使用している場合、再ビルド後も古い共有ライブラリが読み込まれていることがあります。その場合はJupyterカーネルを再起動します。

### Rustソースの構成

Rust側もPython側と同様に、学習対象の概念ごとにファイルを分けています。

```text
rust/src/
├── solver.rs, variable.rs
├── search.rs, objective.rs
├── constraints.rs + constraints/
├── algorithms.rs  + algorithms/
├── state.rs       + state/
└── bindings.rs    + bindings/
```

`solver`、`constraints`、`search`などはPyO3に依存しないsolver本体です。
`bindings`はそれらを`minicp._rust`へ公開する薄い層です。複数ファイルのmoduleには
`constraints/mod.rs`ではなく、`constraints.rs`を親にするRust 2018以降の形式を
統一して使用しています。

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

## Python版Solverとインタラクティブな例

Python版には、整数変数、制約伝播、深さ優先探索の最小実装があります。
N-Queensでは各列の女王の行番号を整数変数で表し、同じ行と対角線を
`not_equal`制約で除外します。

学習用の例は`notebooks/`に置き、`# %%`で区切ったPython Interactive Window形式で
モデル構築、探索、結果表示を順番に実行できるようにしています。

```console
uv run python notebooks/n_queens.py
uv run python notebooks/subset_sum_problem.py
uv run python notebooks/stable_matching.py
uv run python notebooks/sudoku.py
uv run python notebooks/circuit.py
uv run python notebooks/tsp.py
```

`notebooks/tsp.py`の`BACKEND`を`"python"`または`"rust"`にすると、同じ
`Circuit`、`Element1D`、`Sum`、branch-and-boundモデルを各backendで実行できます。
性能を比較するときはRust拡張をrelease buildします。

```console
uv run maturin develop --release
uv run python notebooks/tsp.py
```

エディタでは各ファイルを開き、セル単位で実行すると制約伝播前後の状態を
途中で確認できます。

## Rust版Sparse Set

Rust版も`StateManager`と連携し、Python版と同じAPIで変更を保存・復元できます。

```python
from minicp import rust as cp

manager = cp.StateManager()
domain = cp.SparseSet(manager, minimum=2, maximum=6)
manager.save()
domain.remove(4)

assert not domain.contains(4)
assert domain.size == 4
assert domain.min == 2
assert domain.max == 6
assert set(domain.values()) == {2, 3, 5, 6}

manager.restore()
assert domain.contains(4)
```

`minicp._rust`はPyO3の低レベルモジュールであり、通常のコードでは
`minicp.python`または`minicp.rust`を利用します。

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
- `save()` / `restore()`
- `remove_below(value)` / `remove_above(value)`

静的チェックは次のコマンドで実行できます。

```console
uv run ruff check src tests
uv run ty check
```
