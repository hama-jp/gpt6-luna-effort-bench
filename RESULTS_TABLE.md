# 集計(runs)

**揃っていないセル**: なし

## 第1部 ふだんの仕事(T1〜T3)

| 課題 | モデル | effort | n | 得点(各回) | 平均 % | API換算 $/回 | 秒/回 | 出力トークン/回 |
|---|---|---|---:|---|---:|---:|---:|---:|
| t1_feature | gpt-6-luna | low | 2 | 7/7, 7/7 | 100 | 0.0042 | 78 | 2843 |
| t1_feature | gpt-6-luna | medium | 2 | 7/7, 7/7 | 100 | 0.0065 | 103 | 3560 |
| t1_feature | gpt-6-luna | high | 2 | 7/7, 7/7 | 100 | 0.0083 | 167 | 6290 |
| t1_feature | gpt-6-luna | max | 2 | 7/7, 7/7 | 100 | 0.0118 | 235 | 10686 |
| t2_bugfix | gpt-6-luna | low | 2 | 7/8, 8/8 | 94 | 0.0065 | 99 | 3371 |
| t2_bugfix | gpt-6-luna | medium | 2 | 8/8, 7/8 | 94 | 0.0064 | 109 | 3933 |
| t2_bugfix | gpt-6-luna | high | 2 | 8/8, 8/8 | 100 | 0.0057 | 208 | 4852 |
| t2_bugfix | gpt-6-luna | max | 2 | 8/8, 8/8 | 100 | 0.0130 | 290 | 13256 |
| t3_document | gpt-6-luna | low | 2 | 9/16, 9/16 | 56 | 0.0016 | 22 | 334 |
| t3_document | gpt-6-luna | medium | 2 | 16/16, 16/16 | 100 | 0.0018 | 32 | 778 |
| t3_document | gpt-6-luna | high | 2 | 16/16, 16/16 | 100 | 0.0018 | 31 | 1005 |
| t3_document | gpt-6-luna | max | 2 | 16/16, 16/16 | 100 | 0.0029 | 49 | 1820 |

## 第2部 AtCoder ABC476 A〜G(T4)

| モデル | effort | n | 正解数(各回) | 平均 | 各回の正解問題 | API換算 $/回 | 分/回 | 1問あたり $ |
|---|---|---:|---|---:|---|---:|---:|---:|
| gpt-6-luna | low | 3 | 2, 4, 3 | 3.00 | AB / ABCE / ABC | 0.0045 | 1.5 | 0.0015 |
| gpt-6-luna | medium | 3 | 5, 5, 4 | 4.67 | ABCEF / ABCEF / ABCE | 0.0055 | 2.0 | 0.0012 |
| gpt-6-luna | high | 3 | 6, 6, 7 | 6.33 | ABCDEF / ABCDEF / ABCDEFG | 0.0130 | 7.0 | 0.0021 |
| gpt-6-luna | xhigh | 3 | 5, 7, 6 | 6.00 | ABCEF / ABCDEFG / ABCDEF | 0.0436 | 22.5 | 0.0073 |
| gpt-6-luna | max | 3 | 7, 7, 6 | 6.67 | ABCDEFG / ABCDEFG / ABCDEF | 0.0527 | 24.9 | 0.0079 |

## 事前に決めた判定(第2部)

- effort の効き目: max − low = +3.67 問 → **効く**
- 足りる設定(平均正解数が max と 0.5 問以内になる最も低い effort): **high**(費用は max の 0.25 倍)
