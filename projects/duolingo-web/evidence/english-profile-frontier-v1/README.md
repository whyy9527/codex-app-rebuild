# 未访问的排行榜访客档案分支

上一批frontier选中了实际排行榜底部访客链接。复用仍存活的原版浏览器，当前只有空白标签，重新进入排行榜后确认525宝石、2连胜和5红心；标签消失原因未知。实际点击页脚链接进入独立访客档案，侧栏个人档案仍指向注册入口；不能混成同一页面。

## 实际探索

1. 档案首次显示制作头像引导；实际“下次再说”关闭，显示加入月份、2天连胜、204总经验及成就。
2. “显示全部”的真实href为`/profile//achievements`，实际跳到`/errors/404.html`；保留原版错误，不臆造正常成就页。
3. 浏览器返回后实际“邀请好友”打开分享浮层，关闭恢复档案。未复制或分享；含私人邀请token的PNG只留在本机artifacts，提交JSON已脱敏，此状态整图参考pending。
4. 点击实际role=button的DIV头像，进入`/settings/avatar`，15个肤色radio，初始完成禁用。
5. 选择第二肤色→完成启用；改回第一肤色→完成仍启用；未保存直接reload→第一肤色选中且完成禁用。不能以当前值是否变化替代实际脏状态行为。

[逐动作记录](transitions.json)、[原始公开观察](source)、[下一步与未访分支](exploration-feedback.json)。原版source日期、分数和加入月份是当前访客夹具的事实，不是通用常量规则。

## 模具与候选现状

采集器旧版只读DOM checked属性，使ARIA radio的15个状态全部null；现追加实际aria-checked回退，同时覆盖actions和visible记录。原始null样本与修正后选中、改回、reload样本都保留。没有把未采到的初始状态事后改写。

v56原样保留v55的3188项，追加658，共3846。8实际状态覆盖文本、同视口整图、控件角色/几何/可用性/实际checked；源投影649pass、9pending。它仅证明规格投影一致。旧候选二进制重新评估87pass、15fail、3744not_run；新增658项全部not_run，本批没有新Swift实现或原生运行。既有两张排行榜整图仍fail，不能当新页面验收。邀请图像和8状态的实际音频仍pending。

14 Node检查、JS语法、Python编译、冻结字节复现、旧要求保留、实际15radio状态、证据路径及脱敏检查通过。下一批先实现独立档案及导航，继续观察头像保存/返回后再实现持久化；整图、交互和声音均须继续。历史反馈实际选出漏页，不构成RSI因果收益，真实匹配预算消融仍未完成。

## 复跑

从仓库根运行，输出目录/回执文件必须不存在：

```sh
node --check projects/duolingo-web/capture-visible-state.mjs
node --test projects/duolingo-web/reference-challenge-identity.test.mjs projects/duolingo-web/reference-current-step.test.mjs projects/duolingo-web/public-reference-challenge.test.mjs
python3 projects/duolingo-web/freeze-profile-frontier.py --out-dir artifacts/profile-frontier-freeze-new
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v56.json --observed projects/duolingo-web/evidence/english-profile-frontier-v1/reference.json --out artifacts/profile-frontier-source-new.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v56.json --observed projects/duolingo-web/evidence/english-leaderboard-visual-v1/native-final/observed-colors.json --out artifacts/profile-frontier-prior-candidate-new.json
```

前端回执因未运行/失败而退出1，应检查逐项结果。原版新鲜采集使用现有capture-visible-state.mjs；顺序见transitions，须先确认当前访客状态及实际控件，不能直接复用历史账号数字路径。
