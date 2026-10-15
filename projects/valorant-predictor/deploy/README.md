# 独立站点发布

用户明确授权 `https://valorant.xinxiayiyan.com/`，并要求先发布当前可用版，
再继续补充明确标注为虚构的剧情、BP 和选手评分。此站点不覆盖现有公司官网。

大陆 ECS 首次部署源站成功，但公网 HTTP 返回阿里云备案拦截页（403），
HTTPS 尚未签发。失败回执保留在 `artifacts/valorant-publication-endpoint-fixed`。
首版改用同一公开仓库的独立 `valorant-site` 分支及 GitHub Pages，
仅把本项目 `valorant` 记录从自建源站 A 调整为 `whyy9527.github.io` CNAME。
其他子域、公司站点和工作流不变。当前发布命令：

```sh
python3 projects/valorant-predictor/scripts/deploy_pages.py --out artifacts/valorant-pages-release
```

脚本只发布构建产物，保留源代码提交 SHA、文件摘要和 Pages 分支 SHA；
不强推分支，拒绝替换其他 Pages 站点或未知 DNS 目标。
提交发布之后，还需要等待 Pages 构建、证书签发并完成公网浏览器验收，
`submitted.json` 本身不代表已上线。以下 ECS 流程保留为源站恢复资料。

从仓库根完成构建、浏览器验收和精确提交推送后运行：

```sh
python3 projects/valorant-predictor/scripts/deploy.py --out artifacts/valorant-publication-new
```

脚本要求项目输入已提交，且当前提交已推到 `origin/main`。使用现有 Aliyun
profile `fenhezhishang`，凭证从本机 CLI 配置读取，不写入代码或公开产物。
通过临时私有 OSS 对象传输已校验压缩包；签名 URL 不打印、不提交，成功后删除
该对象。直接下载 GitHub 的准备探针曾遇到服务器 TLS 连接失败，原记录保留。
`aliyun oss` 还需要显式 `-e` 指定存储桶区域端点；仅配置文件中的 endpoint
曾返回区域不匹配的 403。显式端点已通过私有上传、签名下载与清理探针验证。

所有上传、解压、校验日志及恢复记录位于本项目的 `/var/tmp/valorant-predictor-*`。
首次上传前检查文件系统，拒绝 tmpfs/ramfs；不使用共享服务器的 `/tmp` 暂存大文件。
静态发布目录在 `/opt/valorant-predictor/releases/<git-sha>`，`current` 指向启用版本。
只重建 `valorant-predictor` 容器，使用服务器已有 Nginx 镜像、64 MiB/0.25 CPU
限制和现有代理网络。

只有 `valorant` 子域 A 记录属于本项目；既有不同目标的同名记录会阻止自动覆盖。
Nginx 只写 `proxy_host/valorant-predictor.conf`，先校验再平滑重载。
证书名为 `valorant-predictor`，独立续期 timer 为 `valorant-renew.timer`。
公司官网和工作流的代理配置摘要、健康、完整发布文件摘要和公网关键文件均核验。

发布失败保留暂存目录，不清理其他项目。源站切换前的路径记录在暂存目录的
`previous-release`，代理备份为 `previous-proxy.conf` 或 `before-https-proxy.conf`。
恢复时仅将本项目 `current` 指回已验证旧目录，恢复本项目静态配置，重新创建本项目
容器并检查源站；代理恢复只使用本项目备份，`nginx -t` 成功后才重载。
不要重启共享 ECS、停止其他容器、覆盖公司官网代理或清理别人的暂存目录。

成功后的 `publication.json` 记录公网地址、Git 修订、压缩包摘要和恢复目录。
浏览器公网验收另行运行 `scripts/qa.py --url https://valorant.xinxiayiyan.com/`，
不能只用 HTTP 200 代替实际功能检查。
