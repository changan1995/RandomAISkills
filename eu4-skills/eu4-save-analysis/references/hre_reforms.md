# EU4 神圣罗马帝国 (HRE) 改革 ID 对照表

用于解析存档 `empire={ ... passed_reform="..." }` 块。每条改革在存档里以
`passed_reform="<id>"` 的形式记录，按通过顺序排列。下面左侧是游戏内名称，
右侧是存档中出现的 reform ID。

## 经典主线 (Reichsreform 主干)

| 游戏内名称 | reform id | emperor 变体 id |
|-----------|-----------|----------------|
| Call for Reichsreform | `reichsreform` | `emperor_reichsreform` |
| Institute Reichsregiment | `reichsregiment` | `emperor_reichsregiment` |
| Reform the Hofgericht | `hofgericht` | `emperor_hofgericht` |
| Enact Gemeiner Pfennig | `gemeinerpfennig` | `emperor_gemeinerpfennig` |
| Ewiger Landfriede | `landfriede` | `emperor_landfriede` |
| Proclaim Erbkaisertum | `erbkaisertum` | `emperor_erbkaisertum` |
| Revoke the Privilegia | `privilegia_de_non_appelando` | `emperor_privilegia_de_non_appelando` |
| Renovatio Imperii | `renovatio` | `emperor_renovatio` |

## 新版 / 分支改革 (emperor_ 系列，无经典短 id)

| 游戏内名称 | reform id |
|-----------|-----------|
| Absolute Reichsstabilität | `emperor_reichsstabilitaet` |
| Perpetual Diet | `emperor_perpetual_diet` |
| Create the Landsknechtswesen | `emperor_landsknechtswesen` |
| Establish the Reichstag Collegia | `emperor_reichstag_collegia` |
| Expand the Gemeiner Pfennig | `emperor_expand_gemeiner_pfennig` |
| Embrace Rechenschaft Measures | `emperor_rechenschaft` |
| Geteilte Macht | `emperor_geteilte_macht` |
| Reichskrieg | `emperor_reichskrieg` |
| Curtail the Imperial Estates | `emperor_imperial_estates` |

## 解析备注

- 当前皇帝：`empire={ emperor="<TAG>" }`
- 帝国权威 (Imperial Authority)：`imperial_influence=<float>`
- 选帝侯：`electors={ <TAG> <TAG> ... }`
- 已通过改革：所有 `passed_reform="..."` 行，顺序即通过顺序
- 第一条改革 (reichsreform/emperor_reichsreform) 通常需要帝国权威 ≥ 50
- 两套 id（经典 vs emperor_）对应不同 DLC/版本的改革树；
  Winds of Change (1.37) 之后用的是 emperor_ 分支体系
