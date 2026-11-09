# 期末复习助手前端（T02）

开发环境使用 Node.js 24、React、TypeScript 和 Vite。依赖版本以 `package-lock.json` 为准。

在 `frontend` 目录运行：

```powershell
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173/`。开发服务器将 `/api` 请求转发到 `http://127.0.0.1:8000`。同学 A 的后端启动后，页面会调用 `GET /api/v1/health` 并显示连接状态；后端未启动时显示“暂时无法连接”。

检查构建：`npm run build`。

当前页面只负责 T02 的本机服务联通。课程创建和考试范围页面在 T04 接入业务接口。
