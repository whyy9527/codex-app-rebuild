# 阿里云青岛独立发布

用户确认地址为 `https://valorant.xinxiayiyan.com/`，并要求使用现有国内阿里云服务器。
站点部署在青岛 `47.104.152.169` 的独立 `valorant-predictor` 容器。
不覆盖公司官网、根域跳转或工作流应用。

正常更新：完成构建、浏览器验收、精确提交推送后，从仓库根运行：

```sh
python3 projects/valorant-predictor/scripts/deploy.py --out artifacts/valorant-publication-new
```

脚本要求项目输入已提交，且 HEAD 已推到 `origin/main`。凭证仅从本机
Aliyun CLI profile `fenhezhishang` 的保护配置读取，不进入代码和公开产物。
不同机器可用 `--profile <已有配置名>` 显式指定本地配置；脚本先核对其可访问的
实例 ID 与公网地址必须同时匹配上述授权目标，再执行发布。Mini 上已核对
`default` 配置对应此实例；不复制凭证、不改本机默认配置。
通过香港区私有 OSS 临时对象传输压缩包；它仅是私有上传通道，网站仍由青岛
服务器提供。显式指定存储桶区域 endpoint，签名 URL 不打印、不提交，成功后删除对象。

所有上传、解压、摘要与恢复记录在 `/var/tmp/valorant-predictor-*`，拒绝 tmpfs/ramfs。
发布目录为 `/opt/valorant-predictor/releases/<git-sha>`，`current` 指向启用版本。
只重建本站容器，使用已有镜像、64 MiB/0.25 CPU 限制与现有代理网络。
只管理 `valorant` A 记录及 `proxy_host/valorant-predictor.conf`，校验后平滑重载。

## 首次证书与续期

公网 HTTP 存在已观察到的阿里云备案拦截，不能作为证书签发或就绪检查。
首次通过 DNS TXT 验证签发独立 `valorant-predictor` 证书；私钥只存在服务器。
本机 CLI 添加临时 `_acme-challenge.valorant` TXT，验证后只删除本次新增记录。
已有暂存部署需要完成签发或证书到期前续期时运行：

```sh
python3 projects/valorant-predictor/scripts/resume_domestic.py \
  --stage /var/tmp/valorant-predictor-<staged-revision> \
  --out artifacts/valorant-domestic-certificate-new
```

此命令需要该版本暂存目录中的 `unpacked/deploy/https.nginx.conf` 仍在；如已清理，
先执行正常发布命令准备新版本，它会在证书不足30天时停止并保留暂存目录。
当前证书有效期至 2027-01-13；DNS 续期由本机命令协助完成，没有宣称 HTTP
自动续期可靠，也没有在服务器新增云账号凭证。

## 验证与恢复

校验整份源站文件 SHA-256、其他代理配置摘要、公司站点和工作流健康。
本机 curl/urllib 对现有国内站点的 TLS 会重置，而真实 Chromium 可正常访问；
公网关键文件摘要与共享站点通过正常 TLS 的浏览器核验，之后执行完整 UI 验收。
首次字体传输曾超过60秒；已补充 TTF MIME 与 gzip，原始未修改字体仍保持一致。

失败时保留暂存和旧发布。源站回退使用暂存目录 `previous-release`，将本站
`current` 指回已验证旧目录后重建本站容器；配置回退只使用本站备份，先 nginx -t
再 reload。静态容器使用 `/etc/nginx/valorant.conf`，检查及重载必须带 `-c`。
共享 NPM 则使用默认配置。不要重启共享 ECS、停止其他容器或清理其他项目。

`publication.json` 记录发布 Git 修订、压缩包摘要、公网文件摘要和恢复目录。
完整公网 UI 检查：

```sh
python3 projects/valorant-predictor/scripts/qa.py \
  --url https://valorant.xinxiayiyan.com/ --timeout-ms 120000 \
  --out artifacts/valorant-public-browser-new
```

DNS 迁移期间的显式地址验证会单独记录 browser_args，不能冒充普通 DNS 路径。
