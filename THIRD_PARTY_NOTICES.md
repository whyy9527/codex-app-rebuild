# 第三方内容与许可范围

根目录 [MIT License](LICENSE) 授权本项目原创代码和文档。它不重新授权第三方作品、商标或服务，也不将网页可访问性解释为开源授权。

## Duolingo 案例

`projects/education-swift/Sources/LingoSeed/Resources/Reference/` 包含为比较原版体验采集的字体、图形、语音、音效和动画；`projects/duolingo-web/` 及历史实验的证据、契约和夹具也可能包含原版截图、录音、页面文字或课程内容。资源来源记录在案例资源清单和证据中。

这些第三方内容不属于本项目的 MIT 授权，权利归其原权利人。仓库未附带将 Duolingo 素材用于其他产品或再分发的授权；使用本项目原创工具的 MIT 许可不能代替这类授权。复用教育软件基座时应提供自己有权使用的内容和素材。

Duolingo 案例是已结束、未达到 1:1 的独立技术实践。Duolingo 名称及标识仅用于识别参考产品，不表示合作、官方客户端或背书。

## 依赖与研究来源

依赖由各自项目授权；安装依赖不会将其变为本项目的原创内容。当前案例引用：

| 项目 | 上游许可入口 | 用途 |
| --- | --- | --- |
| Rive iOS | [MIT](https://github.com/rive-app/rive-ios/blob/main/LICENSE) | Swift 动画运行时 |
| Lottie | [Apache-2.0](https://github.com/airbnb/lottie-spm/blob/main/LICENSE) | Swift 动画运行时 |
| Playwright | [Apache-2.0](https://github.com/microsoft/playwright/blob/main/LICENSE) | 浏览器观察与回放 |
| Pillow | [上游许可](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | 按需图像比较 |
| @nestjs/jwt | [MIT](https://github.com/nestjs/jwt/blob/master/LICENSE) | 校管家案例 JWT 签发与校验 |
| bcryptjs | [BSD-3-Clause](https://github.com/dcodeIO/bcrypt.js/blob/main/LICENSE) | 校管家案例本地密码哈希 |
| cookie-parser | [MIT](https://github.com/expressjs/cookie-parser/blob/master/LICENSE) | 校管家案例 Cookie 解析 |
| pinyin-pro | [MIT](https://github.com/zh-lx/pinyin-pro/blob/main/LICENSE) | 校管家案例的姓名首字母搜索 |

锁定版本由案例的依赖清单管理，具体版本随附的许可与通知仍然适用。Dream-RSI、Cordis 的论文及实现来源保留在 [研究说明](docs/RESEARCH.md)；本仓库对它们的引用不改变原作者的权利，也不表示完整复现其算法。
