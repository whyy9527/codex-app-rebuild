# 首页周期状态的共同驱动与实际内容比较

上一轮完成近期开班卡片，本轮将已有首页周期记录接入共同模具。原版窗口安排仍未确认，没有重启原版 collect，没有宣称新原版运行或完整 RSI 再部署。

## 固定来源和动作

来源为 `private/reference/2026-10-12-home` 的 baseline-final、week、month、student-week、student-month 实际 AX。`home-periods-scenarios.json` 固定五个来源的 SHA256，并拥有两端共享的区域、动作和顺序；驱动与比较器共同读取它，避免分别维护场景。参考文件变化时比较器返回 unavailable，必须形成有来源的契约修订，不能悄悄更改预期。

候选实际 AX 中周期控件为 toggle button，原版记录为 button；驱动按实际角色定位。候选金额指标的文字合并在链接名称中，没有独立 text 子节点。比较器因此从两端实际指标链接读取完整名称及值，不依赖子文本存在，不用期望补造事实。学员动态读取区域内全部数字开头的按钮名称。

## 实际执行与结果

当前候选运行代码与上轮已构建版本一致，本轮没有产品源码变更。通过 CUA 在已知候选 URL 守卫下滚动回首页顶部，执行数据概览今日／本周／本月以及学员动态本周／本月。驱动只执行动作、采集实际完整 AX 和回执，不返回 pass 或读取比较预期。

首次候选捕获保存在 `private/home-periods-candidate-20261012`。场景改为单一 JSON 入口后，实际重新执行最终驱动，捕获在 `private/home-periods-candidate-20261012-shared`。金额指标和六项学员动态计数在五个状态均与固定参考一致：5 pass、0 fail、5 not_run。五项未运行分别保留周期前端比较；本轮未提供两端配对并复核的周期截图，不能以内容通过代替视觉、选中样式、动效或声音验收。

在明确的私有负例副本中修改月度学员计数，比较结果 4 pass、1 fail、5 not_run，实际退出 1。原始捕获、回执和固定来源没有改写。此副本只是验证比较器的负例，不是一次新的 UI 执行。

项目 run 的 observed 输入要求实际文件，第一次传捕获目录被入口拒绝为 missing contract input。已将比较入口连接到实际 actions.json 文件，以相邻捕获读取事实；最终项目入口实际运行成功得到上述比较结果。比较整体仍退出 1，因为前端 not_run，不包装为全通过。

完整仓库 unittest 91 项通过，方法 preflight connected，`git diff --check` 通过。connected 仅证明既有 RSI 方法接线，不是本轮原版部署回执。

## 复跑

通过 CUA 调用 `home_periods_native_v1.js` 的 captureHomePeriods，传入对应原生 app、fs、side 与新的私有 out。来源守卫中断时保留部分事实，不自行争抢前台；原版须先满足可持续控制及真实准备状态，不能用这些捕获文件恢复服务端。

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_periods --observed projects/xiaogj-web/private/home-periods-candidate-20261012-shared/actions.json --out projects/xiaogj-web/private/home-periods-result-new.json
```

仍未知其他日期／输入方式、实时数据刷新、指标点击导航、权限、保存和持久化。全范围 Goal 保持 active；没有用当前快照或这五个状态重定义需求全集。
