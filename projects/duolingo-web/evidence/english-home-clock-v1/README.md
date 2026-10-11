# 原版倒计时与共同时间夹具

上一批主页动画的整图失败暴露了时间夹具缺口：源文案持续变化，Swift仍写死“4 小时”。本批实际观察原版，冻结v48后再修改Swift；没有将动态区域屏蔽，也没有放宽旧2486项要求。新增3个时间状态，每个含实际文案、几何及整图，共2495项。

## 源观察与失败控制

客态中文→英语、八课完成、已开宝箱、525宝石，视口1200×732。原版排行榜公开响应的`response.leaderboard.next_contest_start`为`2026-10-11T10:00:00Z`。独立上下文复制当前状态，仅在内存中使用cookies、localStorage、indexedDB、sessionStorage及实际UA/locale/timezone；不保存会话凭证。原版实际显示“1 小时”“29 分钟”“27 秒”，MutationObserver记录各文案变化的墙钟时刻。详见[source-clock.json](source-clock.json)。

共享`home-clock-scenario-v1.json`取最后一次实际DOM变化时刻；截图前后文案一致，但截图晚于文案变化，不能声称整页时间完全冻结。观测点符合剩余整小时、整分钟、整秒向下取整。下一场开始之后如何刷新/换期未观察，继续进入frontier；v14里的期限是这次源快照，不是已实现的排行榜服务。

先尝试Playwright安装/暂停时钟，发现它作用于整个BrowserContext，新页渲染器持续高CPU、命令仍在运行。仅终止该自有异常渲染器，关闭崩溃页、恢复原页时钟，未重启整个浏览器。简单状态克隆、Playwright固定时间及自定义固定Date均未完成主页加载；精确原因未知。完整状态/环境克隆配正常时间成功，随后仅改变Date读取、保持墙钟持续前进，两个偏移实验成功。真实失败、恢复结果及脱敏控制元数据在[probes](probes)、[clock-probes.json](clock-probes.json)。没有用失败实验推断原版业务规则。

## Swift与严格结果

v14原样保留v13八课115评分题与已有进度数据，只为八课完成快照新增原版观察到的排行榜截止时间。Swift根据时间计算文案，由TimelineView按秒刷新；测试驱动显式传入共同文案时刻，默认产品使用当前时间。v13旧固定快照仍可读取、用于历史回归。原生文字位置比新源参考高1点，已按源修正。

旧二进制三状态全部显示4小时：0pass/9fail/2486not_run。最终三状态文案3pass，严格几何/整图6fail，2486not_run。纵向位置已一致，宽度仍差0.34375、0.0234375、0.1640625点；未用强制矩形冒充字体渲染一致。动画相位仍未控制，整图继续fail，不把文字改善或运动当作1:1完成。原始第一版实现与最终对齐版分开保存，不挑较好截图拼成回执。

开箱回归曾错误使用“已开箱”进度去验“未开箱”，产生两项额外失败；`chest-first`及`chest-opened-seed`保留这个错误，不当产品退化。改回原版开箱前夹具后6状态19pass/12fail/2464not_run，无驱动失败；结果见[verification-summary.json](verification-summary.json)。最终倒计时和正确开箱回归使用同一二进制。30项核心通过，构建成功，冻结契约/参考/场景可重新生成且字节相同。源自比较只验证冻结内部一致，不是Swift通过。本批没有新增RSI消融，也未证明探索收益；原始Dream-RSI/Cordis及负结果仍见[研究文档](../../../../docs/RESEARCH.md)。

## 复跑

从仓库根顺序执行原生任务，输出目录必须全新：

```sh
python3 projects/duolingo-web/freeze-home-clock.py --out-dir artifacts/home-clock-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-clock-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-clock projects/duolingo-web/home-clock-scenario-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v48.json --observed artifacts/home-clock-native-new/observed.json --out artifacts/home-clock-native-new/validation.json
swift projects/duolingo-web/observe-frontend.swift artifacts/home-clock-chest-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest
```

前端比较当前因真实失败返回1。重新观测需要独立源会话：`capture-home-clock.mjs --cli <playwright_cli.sh> --session <源会话> --contest-start <实际观察到的毫秒时间> --out <全新目录>`，不要将旧截止日期当成新的原版事实。脚本只修改独立上下文的Date偏移，真实计时器/RAF继续运行；结束时关闭该上下文。下一步保留动效相位、字体/颜色、后续Practice、登录与换期等[探索队列](frontier.json)，Goal保持active。
