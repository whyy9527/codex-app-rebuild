# 学费、课消和积分的实际 RSI 与共同模具

## 原版观察与固定协议

以既有已观察学员为入口，原生 CUA 实际打开学费、课消明细、积分默认页签，完整 AX 与原生截图保存在 `private/reference/2026-10-12-student-tabs-preparation`。最初一次使用加载前编号的点击被原生层拒绝，重新读取 AX 后成功；没有在错误页面继续操作。

学费显示一条实际课程余额，默认“显示明细”关闭、不包含剩余数量为零的课程。课消默认最近三十天，日期值是实际观察日对应范围，当前无记录，包含多层表头。积分默认三个筛选选中、十条实际记录，另有规则选择和写入入口。原版仅执行进入、页签点击与返回，没有触发停课、加减分、清零或任何源数据写入。

`rsi-tabs.json`、`student-tabs-scenarios.json`、`student_tabs.py` 与 `student_tabs_native_v1.js` 是独立固定协议。私有种子保存实际来源、期待完整顺序文本、真实输入值和默认列表。每次明确收起并选择就读班级，再打开指定页签；返回恢复精确列表。发现和评价分别实际操作，驱动不接收期待值、不自报 pass。评分只衡量三个固定只读分支，不能证明未知筛选、视觉或全站完成。

该版 text 观察还包括原生 text field 元数据，因此也会检测两端输入框可访问结构差异；没有为候选删减这些要求。日期随观察日冻结，跨日会需要有来源的协议修订，不能把失败悄悄改为通过。

## 历史树、同池回放与再部署失败

`private/rsi-tabs-collect-20261012/iteration-1/collected-pool.json` 保存真实完整树，分数 0、1/3、2/3、1、1/3。原策略在达到三个分支后还采样另一个根分支，没有增加质量。完整冻结池基线 `private/rsi-tabs-baseline-20261012` 得分 0.45。

当前 Codex 根据实际反馈复用已有可执行 `rsi_policy_v1.py`，不是声称另写了新策略；它在 rho=0 停止，并在固定质量 1 后停止。`private/rsi-tabs-revision-20261012` 在同一完整池比较原策略和该策略，得分 0.46、选中版本 1。

`private/rsi-tabs-redeploy-20261012` 真正执行了选中策略的新世界：首分支发现和独立评价完成，第二分支发现完成；累积评价时原生窗口来源守卫报 `Wrong selected detail side`，整个 collect 实际退出 2。终端和私有回执保留，该新世界未完成，不能宣称本协议 RSI 链已成功闭环。项目主 RSI 入口仍保持已有完整再部署的详情协议；页签独立入口指向本次选中池，下一轮需实际重新部署，不与旧协议混池。

## 共同要求与候选产品

第三节点的累积独立评价实际执行了全部三个源旅程。`private/tabs-source-observed-from-rsi-20261012.json` 包装这份实际回执并记录来源，不是额外浏览器执行；共同业务比较 `private/tabs-source-business-20261012/result.json` 四项 pass。

当前 Codex 查看其三个原生截图和对应 AX，确认无遮挡、摘要收起、选中页签与内容一致，再记录与截图 SHA256 绑定的前置状态复核。`tabs-frontend-contract.json` 共 45 项，覆盖严格整图、尺寸、实际表头、日期及复选框角色和值；`private/tabs-source-frontend-result-20261012.json` 45 pass。复核只确认可比较的前置状态，不认定视觉相同；缺少当前复核时图像不可用。

候选共享 Zod 契约增加可选 businessTabs，经既有导入工具写入 MySQL 的 StudentDetail JSON。实际解析原版 AX 表格得到学费 1 行、课消 0 行与两层表头、积分 10 行，不编造其他内容。HTTP 实测返回与导入的三个页签快照完全相同。React 详情新增三个表格与默认查询控件；操作、未观察筛选与写入仍明确 unavailable，不能冒充已实现完整查询。

首轮候选 `private/e2e-candidate-tabs-20261012` 因积分规则文字多空格导致就绪检测失败，进程退出 2。修正候选文本构成，未改驱动或期待；第二轮 `private/e2e-candidate-tabs-v2-20261012` 三条真实旅程完整执行，`private/tabs-candidate-business-v2-20261012/result.json` 四项 pass，包含完整顺序文字、原生输入元数据、输入值和恢复列表。

候选实际截图经逐张查看，仍有查询栏布局、文字间距、表格列宽／高度、图标和分页等差异。`private/tabs-candidate-frontend-result-v2-20261012.json` 为 42 pass、3 严格整图 fail。业务通过不能抵消这些差异、未完成再部署、加载与动态反馈、滚动、过滤、权限、持久化或其他页面范围；原生 Goal 继续 active。

固定协议 inspect 验证：一个完整世界、五节点，协议 `23f34d8fdf00b894d8b1ad312178e59e4bda0b2a66195937d8eff946e19ac21b`；选中策略 SHA256 `4d937cb04db3b2524b76bf61d04e39c80b352b83b3475baa60570fdcdfc19d68`。这不补全失败的新世界。私有导入记录改为分字段来源清单，保留既有详情来源并连接本轮三个页签的实际 AX 与采集时间，再次实际导入成功。

最终验证：构建／类型检查七任务通过，完整仓库 unittest 91 项通过，首页状态测试三项通过，方法预检 connected，git diff --check 通过；前端严格失败和 RSI 再部署失败均保留。
