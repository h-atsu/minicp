# Learning context

## Goal

MiniCPの講義を通して、制約プログラミングソルバーの動作原理を理解する。

最初に読みやすいPython実装を作り、挙動と設計を理解した後、Rustの学習を
兼ねて安定した部品を移植する。性能や機能の多さより、アルゴリズムと状態変化を
コードから追えることを優先する。

## Current course progress

MiniCPの講義04まで視聴済み。実装は講義02の中核である可逆状態、ドメイン、
変数通知、制約伝播、fix-point、深さ優先探索を使ってN-Queensを解ける段階から、
講義03以降で使う境界更新APIの追加へ進んでいる。

## Implemented

### Python

- 素朴なtrailing方式の`StateManager`
- `StateInt`
- 可逆な`SparseSet`
- 可逆な購読リストとしての`StateStack`
- `IntVar`とfix/domain/bound変更通知
- `SparseSet`と`IntVar`の`remove_below`、`remove_above`
- `Constraint`基底クラス
- offset付き`NotEqual`: `x != y + offset`
- 制約伝播キューとfix-pointを管理する`Solver`
- 状態保存・復元を行う`DFSearch`
- 探索統計とsolution listener
- pairwise `NotEqual`によるN-Queensモデル
- 4-Queensと8-Queensの解数を検証するテスト
- 挙動を対話的に確認するN-Queens notebook

### Rust

- PyO3で公開する基本的な`SparseSet`
- Python版との共通テストで、基本的な集合操作を比較
- Rust版の状態保存・復元は未実装

## Current architecture

```text
N-Queens model
    |
    v
DFSearch -- save / restore
    |
    v
Solver -- propagation queue / fix-point
    |
    v
Constraint -- subscriptions / propagation
    |
    v
IntVar -- domain events
    |
    v
SparseSet -- reversible domain storage
    |
    v
StateManager
```

## Deliberate simplifications

以下は現段階では不足ではなく、理解を優先した意図的な選択である。

- `StateManager`は正しく復元できる素朴なtrailであり、同一探索レベルで同じ
  状態を複数回変更した場合は変更ごとに記録する。
- 最適化された`Trailer`の世代管理と`Copier`は未実装。
- Java版の独立した`IntDomain`層は作らず、`IntVar`が`SparseSet`を直接保持する。
- Variable Viewは未実装。N-Queensの対角線はoffset付き`NotEqual`で表現する。
- branchingはユーザーが明示的に渡し、探索木の走査だけを`DFSearch`が担当する。
- `IntVar`は必ず1つの`Solver`に属するが、`Solver`は全変数の一覧をまだ管理しない。
- N-Queensは`AllDifferent`を使わず、講義02で実装可能な`NotEqual`へ分解する。
- Javaの`Impl`クラスや不要なinterface階層は、そのままPythonへ移植しない。

## Important design decisions

- Python実装を読みやすい参照実装とし、Rustは理解後の移植先とする。
- 制約のactive状態と変数ドメインはバックトラック可能にする。
- 制約のscheduled状態は伝播キューがfix-pointで空になるという前提で通常の
  `bool`として扱う。
- 探索中に追加された購読を復元できるよう、制約の購読リストには`StateStack`を
  使用する。
- 解は状態復元前に不変な`tuple`へコピーする。
- 変数選択・値選択の方針と、DFSによる探索木の走査を分離する。

## Possible next steps

講義03・04の内容を段階的に実装する候補:

1. Offset、Opposite、Scale Variable View
2. bound-consistentな`Sum`
3. `BoolVar`とreified constraint
4. `Element1D`
5. 素朴なTable constraint
6. `StateSparseBitSet`
7. Compact Table

講義02の補完候補として、`StateManager`のcontext manager、同一探索レベルでの
trail重複記録の抑制、汎用branching、`Copier`も残っている。

これらは一度に実装せず、次の講義内容や確認したい動作に合わせて選ぶ。

## Maintenance

新しいセッションで作業を始める際は、この文書と`AGENTS.md`を現在のコードと
照合する。実装状況や意図的な設計判断が変わった場合は、この文書も同じ変更で
更新する。
