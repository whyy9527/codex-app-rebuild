# 技术约束

用户指定采用 [realus-ops](https://github.com/firstedu-engineering/realus-ops) 的技术列表；只参考工具链和依赖，不复制其私有业务实现。2026-10-12 经 GitHub API 核对参考提交 `278cd8bd082ff181392d9ad24baa8f253b8241b9` 的根、web、api、contracts、auth、db、datetime 和 spreadsheets 包清单。

| 层 | 参考仓库实际依赖 |
| --- | --- |
| 工具链 | Node 24.18.0、pnpm 11.15.1、TypeScript ^6.0.3、Turborepo ^2.10.1 |
| Web | React ^19.2.7、Vite ^8.1.0、Tailwind ^4.3.2、CVA、clsx、tailwind-merge、Lucide、React Day Picker |
| 路由与状态 | TanStack Router、TanStack Query、Zustand |
| API | NestJS ^11.1.18、Express ^5.2.1、ts-rest ^3.52.1、Zod 3.25.76 |
| 数据 | MySQL 8（用户约束）、Prisma/client/adapter-mariadb 7.9.1、mariadb ^3、Prisma Migrate |
| 认证与权限 | AWS Cognito SDK、aws-jwt-verify、jsonwebtoken、bcryptjs、cookie-parser、CASL ability/prisma |
| 国际化与时间 | i18next、react-i18next、date-fns 4、@date-fns/tz |
| 表格与金额 | xlsx 0.18.5、xlsx-js-style 1.2.0、decimal.js |
| AI 助手 | @page-agent/core 和 page-controller 1.12.4；用户要求后端代理 DeepSeek deepseek-flash |
| 文件与邮件 | @aws-sdk/client-s3、@aws-sdk/s3-request-presigner、@aws-sdk/client-ses |

项目锁文件拥有本案例实际安装版本。依赖分层接入，不将安装包视为业务已完成。当前开发入口只验证 React → 共享 ts-rest 契约 → NestJS 健康检查；数据库、认证、权限及业务页面尚待实现。原版是功能与视觉的验收来源，参考仓库不是本案例业务规格。

项目 `.nvmrc` 指定 Node 24.18.0；首轮本机当前 Node 为 24.13.1；随后通过 npx 提供的 Node 24.18.0 完成无缓存构建及类型检查，未修改全局运行时。开发服务绑定本机 127.0.0.1；不部署或连接参考仓库的 AWS、数据库等基础设施。
