# 本地认证实现与实际验证

本批消费已有 Safari 登录准备证据，补候选认证实现，没有新增原版业务探针。后续未知分支仍从固定 RSI 协议的真实 collect 开始，不能将本批资源准备补写成探索树。

## 来源与实现边界

`auth-scenarios.json` 固定原版空表单、弱密码提醒、取消提醒和关闭宣传层后的首页 AX 哈希。原版凭证只用于原版；候选由 `db:seed-local-auth` 生成独立随机强密码账号和 JWT 配置，保存在忽略目录，文件权限 0600。原版业务与媒体不提交。

登录布局与公开登录资源准备来自已观察页面及其公开资源 URL，资源留在 `private/assets/`。背景照片、随机排列和 150 秒动画参数参考公开脚本，属于实现参考，不是实际动画一致性的观察结果；没有把原版脚本或样式复制进仓库。

候选使用 NestJS、ts-rest/Zod、Prisma/MySQL、bcryptjs、JWT 和 HttpOnly/SameSite=Lax Cookie。JWT 限定算法、issuer 和 audience；数据库会话支持过期、禁用账号和撤销。业务 API 默认需要认证，修改请求校验指定 Origin。生产 Cookie 设置 Secure。认证配置缺失时启动失败。八小时有效期及错误文案是候选实现决策，原版对应规则仍未知。静态资源未纳入访问权限，Cognito、CASL 和数据范围尚未实现。

## 实际运行

- 迁移 `202610120004_auth` 已应用，独立本地账号已准备。
- Node 24.18 / pnpm 11.15.1 构建、类型检查和现有首页三项测试通过。实际候选构建入口为 `index-z4O_dt-j.js`、`index-DlvMWsKz.css`。
- `auth.integration.test.mjs` 对运行中的候选 API 三项测试通过：匿名业务访问拒绝，错误／无效登录拒绝，Cookie 属性，登录后业务访问，跨 Origin 修改拒绝，退出撤销以及旧 Cookie／非法 JWT 拒绝。测试账号不会输出到日志。
- 原生 Edge 实际刷新匿名页面后进入登录页，填写独立候选凭证并提交后进入首页；再次刷新仍进入已认证首页。只保存空表单和提交后状态，没有保存填写凭证的表单。
- 根目录 `python3 -m unittest discover -v`：91 项通过（50.256 秒）。

## 共同验收与未完成

候选捕获在 `private/auth-candidate-20261012/`。`compare_auth` 读取两端实际 AX，校验原版证据哈希，再判定共同要求；驱动不自报通过。当前结果六项 pass、一项 not_run，整体失败并返回非零退出码。

第一次比较将弱密码提醒缺失判 fail，保留 `shared-result.json`。复核发现前置条件不同：原版授权账号触发弱密码提醒，候选是独立随机强密码，不能据此比较相同政策。`preparation.json` 明确记录此差异；`shared-precondition-checked-result.json` 保留 actual=false、expected=true，把该项记 not_run，未放宽断言。候选目前没有弱密码提醒实现。

原版与候选窗口尺寸不同，随机照片和动画状态也未对齐，登录严格视觉验收尚未运行。宣传层、恢复密码实际旅程、原版错误凭证反馈及完整认证权限仍待探索与实现；恢复密码链接存在不能证明流程可用。浏览器刷新已验证，API 重启后的会话恢复尚未实际验证。本批结果不能完成全站复刻 Goal。
