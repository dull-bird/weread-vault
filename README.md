# WeRead Vault

一个本地优先的微信读书归档工具：用 CLI 把你有权访问的书目、划线、想法和阅读统计同步到本机 SQLite；再用一个只读的本地网页快速浏览和搜索。它不需要账号系统、云端数据库或常驻服务。

> 这是个人数据归档工具，不是微信读书官方客户端。请遵守微信读书的服务条款，只同步自己的数据。

## 为什么是 SQLite

你不需要懂 SQLite 才能使用它。可以把它理解成一个单文件数据库：默认位置是 Linux 的 `~/.local/share/weread-vault/weread-vault.db`（macOS/Windows 会使用各自的用户数据目录）。一个文件就包含所有同步数据，方便备份、迁移和离线浏览；数据库不在这个 Git 仓库里，也不会上传。

## 安装

需要 Python 3.10+。项目没有第三方 Python 依赖。

```bash
git clone --recurse-submodules https://github.com/dull-bird/weread-vault.git
cd weread-vault
python -m pip install -e .
weread-vault init
```

如果克隆时漏了 submodule：

```bash
git submodule update --init --recursive
```

## 最常用的命令

```bash
# 首次或日常增量同步（仅这一步需要 API Key）
export WEREAD_API_KEY='你的 key'
weread-vault sync

# 看本地数据库的数量与最近同步状态
weread-vault status

# 打开本机网页预览：http://127.0.0.1:8765/
weread-vault serve --open

# 导出 Markdown 和创建可迁移的数据库备份
weread-vault export markdown --out ~/Documents/weread-notes
weread-vault backup --out ~/Backups/weread-vault.db
```

所有命令可通过 `--db /path/to/file.db` 使用另一份数据库。网页只监听 `127.0.0.1`，不会暴露到局域网。

## 同步是怎样保证安全的

正常的 `weread-vault sync` 分三段：

1. 分页同步所有有笔记的书目，并保存每本书的远端变更标记。
2. 只同步新增或有变更的书。每本书的划线和分页想法会先完整拉取；只有两类请求都成功后，才用一个 SQLite 事务写入并推进这本书的同步标记。失败的书不会被标记为“已同步”，下次会自动重试。
3. 保存周、月、年、总阅读统计的时间快照，不覆盖旧快照。

`weread-vault sync notes --full-notes` 可用于人工校验或修复，它会重新扫描每一本已有笔记的书。

数据边界由官方 Agent Skill 决定：目前可归档书目、划线、个人想法和统计；仅有数量而没有正文的书签、以及无法由官方接口提供的内容，工具不会虚构成可备份数据。

## 官方 Skill submodule

`vendor/tencent-weread-skill` 是腾讯维护的 [Tencent/WeChatReading](https://github.com/Tencent/WeChatReading) 仓库的 git submodule，当前使用其 `skills/` 下的微信读书 Agent Skill。更新官方协议说明：

```bash
./scripts/update-official-skill.sh
git diff --submodule
```

Submodule 更新不自动改写 CLI 的协议版本；这是有意的。先审阅官方变更、升级 `SKILL_VERSION`、跑测试后再提交，避免一个远端变更直接破坏本地同步。

## 作为 Agent Skill 使用

本仓库附带可安装 Skill：[skills/weread-vault-cli/SKILL.md](skills/weread-vault-cli/SKILL.md)。它规定了同步、导出、备份和本地预览的安全操作流程；可通过下方命令生成 `dist/weread-vault-cli.skill`。

```bash
python /path/to/skill-creator/scripts/package_skill.py skills/weread-vault-cli dist
```

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
