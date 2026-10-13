# 校管家 Web 复刻

校管家 TMS 的本地复刻试验，采用用户指定的 realus-ops 技术栈。试验已结束，尚未达到完整 1:1；范围、验证结论与未完成项见 [案例结论](STATUS.md)。

在已准备本地数据库和私有输入的本机，双击 **预览.command**，或从仓库根运行：

```sh
python3 -m projects.xiaogj-web.tools.preview
```

程序构建并启动所需本地服务、检查登录与业务接口，然后打开 http://127.0.0.1:5183 。终端中按 Ctrl+C 退出；只关闭本次启动的服务。账号见忽略目录 `private/local-auth.json`，与原版账号不同。仅验证启动可加 `--check --no-open`；已有构建可加 `--skip-build`。

新检出环境缺少私有数据库、账号与素材时不能直接复原本机内容；程序会报告缺失，不生成假数据或连接原版。准备方法见 [SETUP.md](SETUP.md)。

[项目入口与命令](rebuild.json) · [技术约束](TECHNOLOGY.md) · [本次结论](STATUS.md) · [框架迭代复盘](../../docs/XIAOGJ-LESSONS.md) · [重建工作流](../../workflows/rebuild/WORKFLOW.md)
