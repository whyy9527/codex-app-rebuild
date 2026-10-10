# 听力反馈补词、颜色与截图色彩空间修复

本批先冻结 v16：保留 v15 全部1497项，新增反馈的实际 `No ice, please.` 和四项答题前后背景/边框像素，共1502项。原版 DOM 父文本已有完整句子，但 before PNG 隐藏 ice、feedback PNG 显示 ice，因此必须核对阶段，不能只读 DOM 推断视觉状态。完整源题目 tokens 与反馈 PNG 共同确认，不将 API 当实际交互证据。

默认 v9 仍为七课102题，从 v8 增加可选 feedbackHint、正确反馈静态波形，不修改 v8。`compile-radio-feedback.py` 可重建数据及源 PNG 派生资源；`resource-binding.json` 绑定实际源图、裁剪区域与 SHA256。正确反馈绿背景215/255/184、边框165/237/110、图标文字88/167/0来自实际源图/DOM证据。静态源波形不是动画等价证明。

## 真实验证与未通过项

Swift构建通过，21业务检查、50框架测试通过。`focused` 实际radio2点击并接受；`seventh` 用归档六课完成/生命2进度，在完整v9中走完第七课（跳过、输入偏好、正常匹配、radio2、口语暂缓、插入、重练、结算），81状态、walk_error=null。这里没有重新从空进度执行全部七课；不能套用旧构建430状态结果。

v17保留v16并加入此次实际探索的第八课下次再说→主页→重进入口9项，共1511项。第七课运行对完整v17为353通过、33失败、1125未覆盖。新增反馈5项中：补词与前后背景三项通过，前后边框两项失败（原版229/229/229 vs候选230/230/230；原版165/237/110 vs候选167/238/112）。保持零容差，没有把色差改成通过。九项第八课需求未覆盖。两对同视口整页截图仍 different；冰字的绿色/下划线、气泡、角色、题头、反馈、听力暂缓及实际声音仍未全部对齐。

## 截图 ICC 反例与修复

原始macOS PNG带 Display ICC，浏览器PNG无ICC（按CSS/sRGB解释）。之前直接 `.convert('RGB')` 比的是不同色彩空间的字节。新背景raw RGB223/254/191，经嵌入ICC转换后为215/255/184，与原版匹配。`capture_color.py` 统一至sRGB，再按实测窗口几何裁剪并Lanczos降采样；保留ICC摘要和输入文件哈希，不改源PNG、不加遮罩或容差。

`before` 与 `focused` 内的旧 raw RGB 回执保留，不能用于颜色等价结论；`observed-srgb` / `frontend-srgb-result` 为更正的色彩空间回执。完整第七课仅新sRGB结果。共同前端比较器要求颜色事实显式声明sRGB，缺失空间或RGB数据记unavailable。纯文本、几何、核心检查均不替代颜色检查。

## 复跑

```sh
python3 projects/duolingo-web/compile-radio-feedback.py
projects/duolingo-web/run-native-course.sh artifacts/seventh-feedback-new \
  projects/duolingo-web/fixture-reference-en-zh-v9.json \
  --seed-progress projects/duolingo-web/evidence/english-seventh-native-v1/radio-missing-ax/progress.json \
  --start-lesson-index 6 --walk-course --exercise-input-modes --exercise-source-skip --reference-color-scheme light
python3 projects/duolingo-web/sample-radio-colors.py --native artifacts/seventh-feedback-new \
  --observed artifacts/seventh-feedback-new/observed.json --out artifacts/seventh-feedback-new/observed-srgb.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v17.json \
  --observed artifacts/seventh-feedback-new/observed-srgb.json --out artifacts/seventh-feedback-new/frontend-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/seventh-feedback-new \
  --pairs projects/duolingo-web/evidence/english-radio-layout-v1/pairs.json --out artifacts/seventh-feedback-new/visual-result.json
```

图像采样/资源脚本使用Pillow及其ImageCms；框架核心仍无第三方Python依赖。色彩转换前后均保存原始观察。完整Goal active；真实匹配预算RSI探索消融未执行，不能把本批补漏或色彩修复称作RSI收益。
