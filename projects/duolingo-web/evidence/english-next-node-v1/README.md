# 第二路径节点：新题型与角色绘制来源

2026-10-11，原版已完成第一节点四课，通过实际“开始 +10经验”进入第二节点。首次进入为听音配对（entry.json），随后显式捕获工具reload生成另一个实例，不能把两者当同一题序。新session.json包含15题，接口潜在类型包括translate/listenMatch/listenComplete/completeReverseTranslation/speak；只有现场访问才计实际探索。

replay-01.json实际接受Coffee, please!→咖啡谢谢与欢迎→welcome两题，随后停在listenMatch。旧回放身份器没有新题型的选项模型，报告choice_set_changed；这不能证明原版动态换题。失败保留，不放宽旧文字题身份核对。

接着实际点击听音按钮，用当前播放URL匹配此实例公开pairs并选择译文，四组配对完成，reference-listen-match-feedback.png显示“真厉害！”及继续。继续后过渡DOM同时保留新旧两份header，通用唯一定位失败，原始listen-match-transition-failure.txt保留；由于回调在返回前抛错，逐组操作JSON没有成功返回，不能伪称已有四条独立回执。随后独立读取稳定可见challenge，listen-complete-entry.json与PNG证明进入“输入所缺单词”，显示textbox“or coffee?”。尚未输入、提交或观察后续口语题；候选尚不支持本节点。

Canvas检查与实际帧显示Falstaff/Oscar全身角色由118×175画布绘制，与character.image.svg及character.url的半身裁切图不同。reference-next-question-*-canvas-0.png是画布所在区域的实际截图，可能包含叠层/相邻元素，不是已经提取好的透明资源。发现公共WASM并未确认其具体渲染器或动画资源绑定。辅助CDN请求属于smart_tip_en_zs，不冒认动画文件。

本轮发现改进了素材探索方向，还没有证明RSI策略收益。下一步读取当前听音填词的完整交互与错误/重练、观察口语/反向翻译，建立下一版需求与Swift题型；继续解决真实动画绑定、听感及跨端同状态验证。第二节点不复用第一节点旧课冒充完成。
