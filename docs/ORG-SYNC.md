# 组织框架快照同步

目标为[firstedu-engineering/codex-app-rebuild](https://github.com/firstedu-engineering/codex-app-rebuild)，保持私有。2026-10-13用户已明确授权发布一版框架，并把发布版本同步到该组织仓库。

初次只读检查时，组织main为`2da22c512900fcc5a87fabfb499f0ed9f2bfc476`，是独立历史的纯框架快照。当时框架运行代码与源仓库一致，主要缺少校管家实践后的方法、复盘和Roadmap更新；不能把个人仓库整段App案例历史合并过去。

当前同步使用[发行程序](RELEASING.md)，从已提交源版本生成同一份快照。方法、复盘和待办随框架保留，案例证据链接固定到源提交；运行代码逐字节一致。发行包补齐合成协议夹具与完整框架测试，组织README明确它是机制验证夹具，不是已交付App。

Duolingo／校管家App实现、预览、ECharts案例查看器、第三方媒体、私有账号及实际探索快照留在源案例，不进入组织快照。四项尚未实现的框架成果继续由Roadmap拥有，版本发布不改变其完成判断。

源提交、逐文件摘要由发行包内`FRAMEWORK-SOURCE.json`拥有；最终标签、组织提交及附件以两边GitHub Release为准。此文只维护目标和范围，不维护发布生命周期。
