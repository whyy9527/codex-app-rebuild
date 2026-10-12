# 校管家 Web 复刻

目标：使用指定技术栈 1:1 复刻 https://tms03.xiaogj.com 。项目目标与完成条件见 [rebuild.json](rebuild.json)，执行方法见 [重建工作流](../../workflows/rebuild/WORKFLOW.md)。

```sh
cd projects/xiaogj-web
nvm use
npx --yes pnpm@11.15.1 install --frozen-lockfile
npx --yes pnpm@11.15.1 dev
```

开发入口 http://127.0.0.1:5183 ，API http://127.0.0.1:3101/api/health 。当前入口是前后端连通检查页，还不是原版复刻页面。

从仓库根构建：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command build
```

[技术约束](TECHNOLOGY.md) · [原版观察契约](reference-contract.json)

登录凭证不写入文件。截图、包含业务数据的观察树及后续会话文件保存在 Git 忽略的 `private/` 下，仅用于本地验证。
