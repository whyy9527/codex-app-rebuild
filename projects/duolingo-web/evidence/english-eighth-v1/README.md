# 第八课入口及第七课资源补证

原版第七课后出现“在这里学习英语字母！”引导。节点点击被遮挡、Escape 未关闭，保留 `pronunciation-coach-escape`；实际背景单击关闭引导，见 `coach-background-click.json`，没有强制穿透点击。随后实际进入第八课挑战入口，`entry` 与 `resume-state` 保存页面。API 会话采集重载回到入口；第八课尚未作答或完成。

`session.json` 是新会话的 API 线索，含12道初始挑战，不能当作完整 UI 轨迹。新白名单保留 options、blankRangeStart、blankRangeEnd，但本次没有 isolation 题，尚未验证新的隔离听力 options 实例。

`retained-seventh-media.json` 从保留播放事件按旧 timeOrigin 和第七课 q3 的操作时间定位 radio2 ice 语音。`seventh-resource-binding.json` 记录14个公开语音的字节与哈希，以及实际原版截图裁出的两个波形静态帧；radio1 仍未知。`source-seventh-controls-observed.json` 依据实际 ARIA 快照冻结 radio 角色/disabled 和 Skip 几何，修正旧 enabled 采集忽略 aria-disabled 的问题，旧文件不覆盖。新契约原版事实回放350通过、0失败、1139未覆盖；这是已有事实的回放，不是原版全七课重新操作。

`platform-fonts.json` 用浏览器 CDP 查询当前挑战入口 h2：CSS 为 duolingo-sans，实际中文平台字体为 PingFang SC / PingFangSC-Semibold。该证据仅对应此节点；不能据此推断所有中文页面或候选字体错误。下一步先查询原生实际回退字体，再比较同状态几何。

第八课完整探索、未知分支和 RSI 对照仍待执行。原始 CLI 文本为本地诊断，不作为公开证据提交。
