# WeRead Vault

**微信读书的本地数据库 —— 一个带 Agent Skill 的 CLI。** 把书架、划线、想法、阅读统计归档进本机 SQLite，可查询、可视化、可导出，AI 直接读，数据不上传。

![WeRead Vault Dashboard](docs/assets/dashboard.png)

> 个人数据归档工具，不是微信读书官方客户端。请遵守微信读书服务条款，只同步自己的数据。

## 特点

- 🔒 **本地优先**：所有数据只存在本机一个 SQLite 文件里，可备份、可迁移、可离线，永远不上传；网页只监听 `127.0.0.1`。
- 📚 **完整书架**：同步整个书架（800+ 本，含无笔记的书与公众号分组），不只是有笔记的那几百本。
- 📊 **阅读统计看板**：纯 SVG 零依赖渲染——本周/本月/今年/全部切换、同比、读得最多排行、偏好分类、24 小时时段、GitHub 式划线热力图、单次时长分布（还给「碎片化严重」这样的结论）。
- 🔥 **不只是你自己**：每本书能看「大家都在划的句子」（含人数、可按原文顺序）和公开书评；还能搜微信读书书城、看同作者的相关书。
- 🤖 **AI 原生**：CLI 暴露整套微信读书 API + 只读 SQL 查询 + 已解析统计 JSON，可直接交给 Claude Code、Codex、OpenClaw 等 agent；自带荐书 Skill。
- 📝 **导出到你的知识库**：Markdown（含封面、可合并他人热门划线并去重）、Obsidian、flomo、Notion。
- 🧰 **零第三方依赖**：纯 Python 标准库 + SQLite，有 Python 就能跑。

## 把这段发给 AI agent，它会帮你装好

适用于 Claude Code、Codex、OpenClaw 等任意能执行本机命令的 agent：

```text
请帮我安装并运行 WeRead Vault（本地优先的微信读书归档工具，数据只存本机 SQLite，不上传）：
1. 克隆（务必带 submodule，需 Python 3.10+）：
   git clone --recurse-submodules https://github.com/dull-bird/weread-vault
2. 进入仓库后安装：python -m pip install -e .
3. 初始化并自检：weread-vault init && weread-vault status
4. 同步需要微信读书官方 Agent Skill 的 WEREAD_API_KEY。请提醒我自行到 https://weread.qq.com/r/weread-skills 获取，
   并只让我在本地终端 export 或在网页里保存——不要把 key 贴进对话，也不要写进任何文件或提交到仓库。
5. 设置好 key 后同步：weread-vault sync
6. 打开本地网页浏览书架、划线、想法和阅读统计：weread-vault serve --open
7. 如果我用 Obsidian：导出 Markdown（一书一文件、保留我已有的 frontmatter）：
   weread-vault export markdown --out "<我的 Obsidian 库路径>/WeReadNotes"
```

如果你的 agent 支持 Skill，可安装本仓库的 [`skills/weread-vault-cli`](skills/weread-vault-cli/SKILL.md)，把「同步微信读书」「导出到 Obsidian」「打开 Dashboard」直接映射到安全的 CLI 操作。

## 手动安装

需要 Python 3.10+，无第三方依赖。API Key 从 [微信读书官方 Skill](https://weread.qq.com/r/weread-skills) 获取（可选安装）。

```bash
git clone --recurse-submodules https://github.com/dull-bird/weread-vault.git
cd weread-vault && python -m pip install -e .
weread-vault init
export WEREAD_API_KEY='你的 key'   # 仅同步需要；查看本地数据不需要
weread-vault sync                  # 拉取书架、笔记、统计
weread-vault serve --open          # 打开 http://127.0.0.1:8765/
```

漏了 submodule 就补：`git submodule update --init --recursive`。

## 桌面安装包与升级

不想碰命令行？到 **[Releases](https://github.com/dull-bird/weread-vault/releases/latest)** 下载对应平台的单文件程序（macOS / Windows），双击即启动本地 Dashboard 并自动打开浏览器，在网页里粘贴 API Key 同步即可。检查与获取更新：

```bash
weread-vault update             # 检查是否有新版本
weread-vault update --download  # 下载对应平台的安装包到当前目录
```

> 安装包由 GitHub Actions 在打 `v*` tag 时用 PyInstaller 自动构建（见 `.github/workflows/release.yml`）。项目主页：<https://dull-bird.github.io/weread-vault/>。

## 阅读统计

按本周 / 本月 / 今年 / 全部切换，所有数字随之更新；GitHub 式热力图展示每日划线活跃度（多年）。全部来自历史快照，随每次同步累积，能看到长期趋势。

![阅读统计](docs/assets/reading-stats.png)

## 书籍详情

进度与推荐值用进度条体现书间差异，划线/想法用颜色标记。四个 tab：**我的笔记 / 热门划线 / 书评 / 相关推荐**——每条笔记都能一键复制，还能跳转到微信读书。

![书籍详情](docs/assets/book-detail.png)

热门划线可按「原文顺序」或「按热度」排列，看到大家都在划的句子（含人数）：

![热门划线](docs/assets/popular-highlights.png)

## 常用命令

```bash
weread-vault sync                  # 日常增量同步（书架 + 笔记 + 统计）
weread-vault sync info             # 补全评分/字数/出版社/ISBN（一次性回填）
weread-vault status                # 本地库数量与最近同步状态
weread-vault serve --open          # 本地网页预览

# 导出
weread-vault export markdown --out ~/Documents/weread-notes
weread-vault sync popular && \
  weread-vault export markdown --out ~/Documents/weread-notes --with-popular   # 合并他人热门划线（去重）
weread-vault export flomo --webhook "$FLOMO_WEBHOOK"
weread-vault export notion --token "$NOTION_TOKEN" --database "$NOTION_DATABASE_ID"

# 备份 / 换账号
weread-vault backup --out ~/Backups/weread-vault.db
weread-vault reset --yes           # 清空本地阅读数据（换账号前用，不影响 API Key）
```

所有命令可加 `--db /path/to/file.db` 使用另一份数据库（不同账号开独立库，避免串扰）。

## 给 AI agent 的微信读书 API

CLI 把整套微信读书 Skill API 暴露成命令，输出 JSON，让 agent 直接取数据——书城搜索、他人热门划线、公开书评、富书籍信息等：

```bash
weread-vault apis                       # 列出全部接口及参数（agent 自助发现）
weread-vault search "三体" --count 5     # 书城搜索
weread-vault book <bookId> popular      # 他人热门划线（含人数）
weread-vault book <bookId> reviews      # 公开书评
weread-vault api <endpoint> key=value   # 任意接口原样透传
```

让 AI 灵活分析本地数据：

```bash
weread-vault query --schema     # 表结构 + 字段说明 + 示例 SQL（AI 据此写查询）
weread-vault query "SELECT title, rating FROM books WHERE rating>0 ORDER BY rating DESC LIMIT 10"
weread-vault stats              # 已解析统计 JSON（周期 / 热力图 / 单次时长 / 读得最多）
```

接入 Claude Code 后，问「我评分最高的书」「哪个分类笔记最多」，AI 会自己 `query --schema` 再写 SQL 回答。荐书 Skill [`skills/weread-recommend`](skills/weread-recommend/SKILL.md) 会结合你的口味、书城和联网，按主题推荐不与已读重复的书。

> 官方接口不开放全书正文，「划线前后那一整段原文」拿不到；也不提供「某一年每本书读了多久」。这些限制我们如实标注，不虚构数据。

## OpenClaw 定时同步

用 OpenClaw cron 每天唤起一个隔离任务，让 agent 跑同步并导出到 Obsidian：

```json
{
  "name": "weread-vault daily sync",
  "schedule": { "kind": "cron", "expr": "0 7 * * *", "tz": "Asia/Shanghai" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "先读取 ~/.weread.env 获取 WEREAD_API_KEY，在 ~/projects/weread-vault 运行 weread-vault sync，成功后 weread-vault export markdown --out \"~/Documents/Obsidian Vault/微信读书\"。失败保留日志，不要打印 API Key。",
    "timeoutSeconds": 1800
  },
  "delivery": { "mode": "announce" }
}
```

## 同步是怎样保证安全的

`weread-vault sync` 分段进行：分页拉取书目并记录每本书的远端变更标记；只同步新增/有变更的书，每本书的划线和想法先完整拉取、两类请求都成功后才用一个 SQLite 事务写入并推进标记——失败的书不标记「已同步」，下次自动重试；阅读统计按时间快照保存，不覆盖旧快照。

`vendor/tencent-weread-skill` 是腾讯 [Tencent/WeChatReading](https://github.com/Tencent/WeChatReading) 的 submodule。更新官方协议：`./scripts/update-official-skill.sh`，审阅后再升级 `SKILL_VERSION` 并跑测试。

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
