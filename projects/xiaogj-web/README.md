# 校管家 Web 复刻

目标是用指定技术栈 1:1 复刻 https://tms03.xiaogj.com 。完整目标见 [rebuild.json](rebuild.json)，方法见 [重建工作流](../../workflows/rebuild/WORKFLOW.md)。原生 Goal 仍在推进完整范围。

```sh
cd projects/xiaogj-web
nvm use
npx --yes pnpm@11.15.1 install --frozen-lockfile
npx --yes pnpm@11.15.1 dev
```

本地入口 http://127.0.0.1:5183 ，API http://127.0.0.1:3101 。当前已实现首页首版、顶部菜单、待办展开与配置、数据周期和图表、自定义草稿、快捷操作选择和搜索。学员信息管理已实现列表、查询、重置、分页和已观察学员的详情展开／返回，并通过 Prisma 读取独立的 MySQL 8 数据库；其余业务页仍是导航壳。登录、权限、完整查询、业务写入和首页偏好持久化尚未完成。

首页读取 `private/reference/home-data.json`，按共享的 `homeSnapshot` Zod 契约校验；数据缺失或不合法返回 503，不生成替代业务数据。私有观察与媒体不进入 Git。Vite 从 `private/assets/` 读取原版已观察的 logo、头像、企业标记、背景、图标字体和 SVG 图标，构建产物也不提交。新的检出环境需要先从授权会话准备这些本地输入。

学员页需要先准备 MySQL 8，并在忽略的 `private/database.env` 设置 `DATABASE_URL`。连接仅供本地候选使用，与原版账号无关。执行 `pnpm --filter @xiaogj/api db:migrate`，再执行 `pnpm --filter @xiaogj/api db:import-students`，将授权观察产生的 `private/reference/students-data.json` 原子导入本地数据库。构建自动生成 Prisma Client。当前已导入默认筛选条件下实际采集的 222 条记录，提供按原始顺序分页及查询；其他筛选、姓名首字母和模糊匹配语义仍待观察。共同验收入口见 [students-scenarios.json](students-scenarios.json) 与 [查询场景](student-query-scenarios.json)。

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
python3 -m workflows.rebuild.project preflight --workspace . --project projects/xiaogj-web/rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project projects/xiaogj-web/rebuild.json
```

第一组共同场景见 [home-scenarios.json](home-scenarios.json)，两端通过 CUA 采集真实完整 AX 和原生截图，再转换为模具事实。它尚不是自动 UI 回放驱动，也不代表完整业务验收。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures <相对捕获目录> --out <新的事实文件.json>
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_frontend --observed <事实文件.json> --out <新的结果文件.json>
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command frontier --out <新的探针列表.json>
```

[技术约束](TECHNOLOGY.md) · [原版观察](reference-contract.json) · [前端模具](frontend-contract.json) · [实际探索历史](exploration-history.json) · [首页证据与局限](evidence/2026-10-12-home.md) · [学员页与数据库验证](evidence/2026-10-12-students.md)


查询 RSI 通过项目命令 `rsi_queries_collect` 接续选中池，`rsi_queries_replay --observed <池文件>` 在完整冻结池比较策略。采集命令的私有桥接请求必须由当前 Codex 在 CUA 中装载 `tools/rsi_native_v4.js`，以原生 Edge App、`node:fs/promises` 和工作区内 `private/rsi-bridge` 调用 `installStudentRsiDriver` 并逐条服务。关闭原版密码提示、确认无遮挡后执行；不得改密码，也不得用文件回放代替真实 UI。

共同查询 E2E 的项目命令为 `replay_reference_queries`、`replay` 和 `compare_queries`，均使用新的 `--out`。前两者等待当前 Codex 在 CUA 中装载 `tools/student_query_native_v3.js`，以同样的 App、fs 与 `private/e2e-bridge` 调用 `installStudentQueryE2E`；选择请求对应的原版或候选学员页，再逐条服务。驱动执行相同动作并保存 AX、截图和事实，不接收期待值或自报通过。`compare_queries --observed <observed.json>` 才按共同夹具判定；查询行为通过不能代替完整前端或全站验收。实际结果和失败见 [查询与 RSI 证据](evidence/2026-10-12-rsi-queries.md)。


学员页前端事实由 `python3 -m projects.xiaogj-web.tools.student_frontend_observations --captures <共同查询捕获目录> --out <新事实文件>` 读取；再用项目命令 `compare_students_frontend --observed <事实文件> --out <新结果文件>` 按 [学员前端契约](students-frontend-contract.json) 验收。当前严格比较失败，见查询与 RSI 证据。

当前 `rsi_collect/rsi_replay` 入口接续详情协议的完整池；旧查询协议保留独立入口，不混池。分页共同场景由 `replay_reference_pagination`、`replay_pagination`、`compare_pagination` 调用。原生桥接入口为 `tools/student_pagination_native_v2.js` 的 `installStudentPagination`，桥接目录 `private/pagination-bridge`，同一驱动服务 RSI 与两端 E2E。独立固定协议见 `rsi-pagination.json`，`rsi_pagination_collect/rsi_pagination_replay --observed <池文件>` 接续完整池；不得与查询协议混池。协议身份、源数据顺序差异及再部署结果见 [分页证据](evidence/2026-10-12-pagination-rsi.md)。

分页前端事实用 `python3 -m projects.xiaogj-web.tools.pagination_frontend_observations --captures <原生捕获目录> --out <新事实文件>` 提取，项目命令 `compare_pagination_frontend` 比较输入值、角色、截图尺寸及严格整图。缺少输入框事实记 unavailable，空字符串与缺失值分别处理；原版和候选使用同一契约。

详情协议见 `rsi-detail.json` 和 `student-detail-scenarios-v3.json`，原生桥接为 `tools/student_detail_native_v4.js` 的 `installStudentDetail`，目录 `private/detail-bridge`。`rsi_detail_collect` 接续选中池，`rsi_detail_replay --observed <完整池>` 回放；共同业务命令为 `replay_reference_detail`、`replay_detail`、`compare_detail`。前端用 `python3 -m projects.xiaogj-web.tools.detail_frontend_observations_v2 --captures <捕获目录> --review <实际截图复核.json> --out <新事实文件>` 提取，再执行 `compare_detail_frontend`。入口、准备限制、失败与来源见 [详情证据](evidence/2026-10-12-student-detail-rsi.md)；当前主 RSI 协议是已完整再部署的详情协议。

详情持久化准备：在已导入学员列表后，以授权观察准备忽略的 `private/reference/student-detail.json`（data、observedAt、provenance），执行 `pnpm --filter @xiaogj/api db:import-student-detail`。仅导入有来源的详情，未采集学员返回 503；照片按实际观察来源准备在私有资源目录；学费、课消明细和积分已实现实际观察的默认表格；其他筛选、页签和写入仍未完成。

详情前端契约见 `detail-frontend-contract-v2.json`，旧契约与带加载遮罩的参考捕获保留。复核文件的 states 按详情状态提供实际截图 sha256、unobscured 与 same_state；当前 Codex 必须查看对应截图及 AX 后记录，不能用测试成功自动填入。缺少或过期复核使图像结果 unavailable，加载过程另列未完成要求。

详情业务页签协议见 `rsi-tabs.json` 和 `student-tabs-scenarios.json`。`rsi_tabs_collect` 从选中池实际再部署，`rsi_tabs_replay --observed <完整池>` 同池回放；原生桥接用 `tools/student_tabs_native_v1.js` 的 `installStudentTabs` 与 `private/tabs-bridge`。共同业务命令为 `replay_reference_tabs`、`replay_tabs`、`compare_tabs`。前端用 `python3 -m projects.xiaogj-web.tools.tabs_frontend_observations --captures <实际目录> --review <截图复核.json> --out <新事实文件>` 提取，再执行 `compare_tabs_frontend`。准备限制、真实回执和未完成再部署见 [页签证据](evidence/2026-10-12-student-tabs-rsi.md)。
