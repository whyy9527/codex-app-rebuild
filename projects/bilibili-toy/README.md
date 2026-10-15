# Bilibili Toy 本地复刻案例

原版入口：<https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html>。
目标与完成条件由 `rebuild.json` 连接原生 Goal；方法见仓库复刻工作流。

当前可运行基线使用原站公开发布的静态应用代码、数据、字体与素材，
加上本仓库编写的本地启动器和宿主外壳。这不是独立重写的应用源码。
发布包和原始证据保存在被 Git 忽略的 `private/` 中，不随仓库再分发。
来源及摘要由准备命令写入 `private/resources.json`。

从仓库根运行：

```sh
python3 projects/bilibili-toy/tools/prepare.py
python3 projects/bilibili-toy/tools/serve.py --port 4617
```

打开 <http://127.0.0.1:4617/>。准备命令需要 curl 和原版公开资源可访问；
本地服务只监听 loopback。准备成功后应用数据与素材从本地读取。
宿主 SDK、服务工作线程及遥测不注入本地基线。Bilibili 平台侧栏当前
为本地外壳，保留的外链会打开原站；与原版的差异仍需验收。

共同 E2E 使用 `scenarios.json` 与 `frontend-contract.json`。原生 UI 回放
须由当前 Codex 在 `cua_repl` 中给 `tools/e2e_native.mjs` 的
`installNavigationE2E` 传入实际 Edge App、`node:fs/promises` 和
`private/e2e-bridge` 路径，并逐条 await 服务请求。运行前选中目标
原版或本地标签页；来源守卫不匹配会停止，不争抢其他标签页。

```sh
python3 projects/bilibili-toy/tools/e2e.py source --out projects/bilibili-toy/private/reference-new
python3 projects/bilibili-toy/tools/e2e.py candidate --out projects/bilibili-toy/private/candidate-new
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command compare --observed projects/bilibili-toy/private/candidate-new/observed.json --out projects/bilibili-toy/private/comparison-new.json
```

RSI 使用 `rsi/config.json` 与 `tools/native.mjs`，桥接方法相同；每次 collect
须实际服务新的发现与独立评价请求。历史池是不可覆写的探针证据，
不是浏览器远程状态备份。页面刷新保留浏览器存储与真实时钟。

历史结果与局限见 `evidence/`。导航、方法接线或单元测试通过不能
替代完整视觉、播放、声音、预测保存与移动端验收。
