# 校管家 Web 复刻

目标是用指定技术栈 1:1 复刻 https://tms03.xiaogj.com 。完整目标见 [rebuild.json](rebuild.json)，方法见 [重建工作流](../../workflows/rebuild/WORKFLOW.md)。原生 Goal 仍在推进完整范围。

```sh
cd projects/xiaogj-web
nvm use
npx --yes pnpm@11.15.1 install --frozen-lockfile
npx --yes pnpm@11.15.1 dev
```

本地入口 http://127.0.0.1:5183 ，API http://127.0.0.1:3101 。当前已实现首页首版、顶部菜单、待办展开与配置、数据周期和图表、自定义草稿、快捷操作选择和搜索。学员信息管理已实现初始列表，并通过 Prisma 读取独立的 MySQL 8 数据库；其余业务页仍是导航壳。登录、权限、完整查询、业务写入和首页偏好持久化尚未完成。

首页读取 `private/reference/home-data.json`，按共享的 `homeSnapshot` Zod 契约校验；数据缺失或不合法返回 503，不生成替代业务数据。私有观察与媒体不进入 Git。Vite 从 `private/assets/` 读取原版已观察的 logo、头像、企业标记、背景、图标字体和 SVG 图标，构建产物也不提交。新的检出环境需要先从授权会话准备这些本地输入。

学员页需要先准备 MySQL 8，并在忽略的 `private/database.env` 设置 `DATABASE_URL`。连接仅供本地候选使用，与原版账号无关。执行 `pnpm --filter @xiaogj/api db:migrate`，再执行 `pnpm --filter @xiaogj/api db:import-students`，将授权观察产生的 `private/reference/students-data.json` 原子导入本地数据库。构建自动生成 Prisma Client。当前只持有默认首屏数据，其他页或非空搜索返回 503，不以首屏子集冒充完整查询。共同验收入口见 [students-scenarios.json](students-scenarios.json)。

本机已初始化的独立数据库可从项目目录重启：

```sh
MYSQL84_BIN="$(brew --prefix mysql@8.4)/bin"
"$MYSQL84_BIN/mysqld" --no-defaults --datadir="$PWD/private/mysql84" --socket="$PWD/private/mysql84.sock" --pid-file="$PWD/private/mysql84.pid" --log-error="$PWD/private/mysql84.log" --port=33084 --bind-address=127.0.0.1 --mysqlx=OFF
```

该命令只适用于已有的私有数据目录。新环境需先初始化独立数据库并准备自己的连接信息。

从仓库根验证：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command build
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command typecheck
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command test
python3 -m workflows.rebuild.project status --workspace . --project projects/xiaogj-web/rebuild.json
```

第一组共同场景见 [home-scenarios.json](home-scenarios.json)，两端通过 CUA 采集真实完整 AX 和原生截图，再转换为模具事实。它尚不是自动 UI 回放驱动，也不代表完整业务验收。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures <相对捕获目录> --out <新的事实文件.json>
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_frontend --observed <事实文件.json> --out <新的结果文件.json>
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command frontier --out <新的探针列表.json>
```

[技术约束](TECHNOLOGY.md) · [原版观察](reference-contract.json) · [前端模具](frontend-contract.json) · [实际探索历史](exploration-history.json) · [首页证据与局限](evidence/2026-10-12-home.md) · [学员页与数据库验证](evidence/2026-10-12-students.md)
