---
name: weread-recommend
description: Recommend books for the user by combining their WeRead reading taste (via the weread-vault CLI), the WeRead bookstore, other readers' highlights/reviews, and external web search. Use when the user asks for book recommendations, "推荐几本关于X的书", what to read next, books on a topic/keyword, or similar-to-a-book suggestions. Requires the weread-vault CLI and WEREAD_API_KEY.
---

# WeRead 荐书工作流

用 `weread-vault` CLI 把「用户的真实阅读口味 + 微信读书书城 + 他人划线书评 + 外部联网」结合起来，给出有依据、贴合口味、且不与已读重复的书单。所有命令输出 JSON 到 stdout，需要 `WEREAD_API_KEY`（已配置在本机；绝不打印或外传）。

## 何时用

用户说「推荐几本关于 X 的书」「接下来读什么」「有没有类似《Y》的书」「我最近想了解 Z 主题」等。

## 步骤

1. **读懂口味**（除非用户只要某个明确主题）：
   ```bash
   weread-vault stats          # 偏好分类/作者/时段、总阅读、readStat
   ```
   从 `overall.categories` / `overall.authors` 提炼用户偏好；这是个性化的依据。

2. **确认已读，避免重复**：
   ```bash
   weread-vault api /user/notebooks count=1   # totalBookCount/totalNoteCount
   ```
   需要逐本判重时，可让用户提供书名，或用书架数据（如果有本地库可 `--db` 查询 books 表）。

3. **按主题/关键词搜书城**：
   ```bash
   weread-vault search "<主题或关键词>" --count 10
   ```
   从 `results[].books[].bookInfo` 取候选书的 `bookId/title/author`。

4. **评估候选书质量与共鸣点**：
   ```bash
   weread-vault book <bookId> info       # newRating(推荐值,满分1000)/评分人数/字数
   weread-vault book <bookId> popular    # 他人最多人划的句子——看这本书到底讲什么、戳中什么
   weread-vault book <bookId> reviews    # 公开书评口碑
   ```

5. **借微信读书自家推荐扩展候选**（可选）：
   ```bash
   weread-vault api /book/recommend count=10
   weread-vault api /book/similar bookId=<某本用户喜欢的书> count=10
   ```

6. **联网补充**：用你的 web 搜索工具核实口碑、获取书评/争议/中译质量等书城给不到的信息。

7. **给结论**：推荐 3–6 本，每本给一句**为什么适合这个用户**的理由，绑定到：用户的偏好分类/作者（来自 stats）+ 评分（来自 info）+ 他人共鸣点（来自 popular）。明确标注哪些是用户可能已读。

## 注意

- 官方接口**不提供全书正文**，无法给出原文段落；用 `popular`（他人热门划线）+ 联网书评替代「内容预览」。
- 不要臆造评分或销量；数字只来自 `info` / `popular` 的真实返回。
- 任何情况下不打印 `WEREAD_API_KEY`。
- CLI 用法与接口清单见同仓库的 [`weread-vault-cli`](../weread-vault-cli/SKILL.md)（`weread-vault apis` 可列出全部接口）。
