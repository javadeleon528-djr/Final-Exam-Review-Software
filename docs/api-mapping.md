# 页面与接口对照（B1）

版本 0.3　更新：2026-11-04　状态：待伙伴互审

> **B1 的验收标准**：每个页面操作都能找到对应接口。
> 本文件按完整的 T01 用户流程对照接口；原先发现的“缺创建考试、缺确认范围”两个断点已补进契约。
> 错误格式（B3）和预览分离检查（B4）已拆到 `error-format.md`，本文件只讲 B1。

---

## 一、四句话说完这张图

| 页面 | 用户做什么 | 接口 | 后端回什么 |
| --- | --- | --- | --- |
| 创建课程抽屉 | 填名字，点创建 | `POST /courses` | 新课程的 `id` |
| 考试范围页 | 打开页面 | `GET /courses/{course_id}/points` | 知识点树 + 自评状态 |
| 考试范围页 | 创建考试 | `POST /courses/{course_id}/exams` | 新考试的 `id` |
| 考试范围页 | 勾选考点，自动保存 | `PUT /exams/{exam_id}/scope-draft` | 新的草稿版本号 |
| 考试范围页 | 确认考点 | `POST /exams/{exam_id}/scope-confirmations` | 不可变的 `scope_version` |
| 日程设置 | 修改某日可用分钟 | `PUT /availability/{date}` | 全局日期设置及受影响任务 |
| 用户规划页 | 点「生成计划」 | `POST /plan-previews` | `202` + `job_id`（不是计划） |
| 用户规划页 | 等待预览完成 | `GET /jobs/{job_id}` | 预览和受影响课程 |
| 用户规划页 | 确认预览 | `POST /plan-applications` | 调整批次 ID 与各考试的新计划版本 |
| 用户规划页 | 撤销最近一次补排 | `POST /plan-undo` | 恢复安排后的新计划版本 |
| 今日复习／任务卡 | 手动改日期、时长、锁定 | `PATCH /plan-tasks/{task_id}` | 更新后的任务与计划版本 |
| 今日复习／任务卡 | 确认完成 | `POST /plan-tasks/{task_id}/complete` | 已完成任务与计划版本 |

一个页面可以对应多个接口。例如「考试范围页」需要先读取课程知识点和范围草稿，保存草稿后再确认正式范围。

---

## 二、四个操作逐个说清

### 操作 1｜创建课程

| 项 | 内容 |
| --- | --- |
| 谁在什么时候调 | 用户点「创建课程」按钮时 |
| 接口 | `POST /api/v1/courses` |
| 请求带什么 | `name`（必填）、`description`（选填） |
| 成功回什么 | `201` + `data.id`（课程编号，后面全靠它） |
| 会怎么失败 | `400` 名字为空；`409` 已有同名课程 |
| 前端拿到后干什么 | 用返回的 `id` 跳转到这门课的考试范围页 |

```json
// 发出去
{ "name": "高等数学", "description": "2026 秋季学期" }

// 回过来
{
  "data": { "id": "course_1", "name": "高等数学", "description": "2026 秋季学期",
            "created_at": "2026-11-01T08:00:00Z", "archived_at": null },
  "meta": { "request_id": "req_01" }
}
```

**为什么要返回 id**：用户后面做的每件事（加资料、排计划、出卷）都必须指明「是哪门课」。没有 id，前端就不知道自己在操作什么。

---

### 操作 2｜读取知识点

| 项 | 内容 |
| --- | --- |
| 谁在什么时候调 | 用户打开「考试范围」页时，页面加载那一刻 |
| 接口 | `GET /api/v1/courses/{course_id}/points` |
| 请求带什么 | 路径里的 `course_id`；不用带请求体 |
| 成功回什么 | 知识点树，每个点带 `self_status`（自评）和 `ai_status`（AI 建议） |
| 会怎么失败 | `404` 课程不存在；`200` + 空数组表示还没建知识点（这是正常状态，不是错误） |
| 前端拿到后干什么 | 画章节树，画每个点后面的四态选择器 |

```json
{
  "data": {
    "course_id": "course_1",
    "points": [
      { "id": "point_1", "course_id": "course_1", "parent_id": null, "name": "函数的极限",
        "self_status": "not_started", "ai_status": null, "version": 1 },
      { "id": "point_2", "course_id": "course_1", "parent_id": null, "name": "函数的导数",
        "self_status": "basic", "ai_status": null, "version": 1 }
    ]
  },
  "meta": { "request_id": "req_02", "version": 1 }
}
```

**两个必须注意的地方**：

1. **`self_status` 和 `ai_status` 是两个字段，不是一个**。界面上并排显示，AI 永远不能改自评。如果合成一个字段，这条规则就守不住了。
2. **空数组不是错误**。用户只填了课程名就建课，这时候一个知识点都没有，页面应该显示「还没有知识点，可以手动添加」，而不是弹报错。

---

### 操作 3｜保存考试范围草稿

| 项 | 内容 |
| --- | --- |
| 谁在什么时候调 | 用户勾选/取消考点之后（可以防抖后自动存，也可以点「保存」） |
| 接口 | `PUT /api/v1/exams/{exam_id}/scope-draft` |
| 请求带什么 | `items[]`（每个点的 `point_id`、`included`、`priority`）、`expected_version` |
| 成功回什么 | 新的 `draft_version`，以及纳入几个、几个是重点 |
| 会怎么失败 | `404` 考试不存在；`409` 版本过期；`400` 知识点不属于这门课 |
| 前端拿到后干什么 | 更新本地的版本号，下次保存带上它 |

```json
// 发出去
{
  "expected_version": 0,
  "items": [
    { "point_id": "point_1", "included": true,  "priority": "normal" },
    { "point_id": "point_2", "included": true,  "priority": "important" },
    { "point_id": "point_3", "included": false, "priority": "normal" }
  ]
}
```

**三个关键设计**：

1. **整份覆盖，不是打补丁**。每次提交的是「完整勾选清单」，后端整份替换。不是发「把 point_3 改成不考」，而是发当前的全貌。这样不会因为顺序错乱算错。
2. **`expected_version` 是防撞车用的**。用户打开页面时后端是第 0 版；如果他勾了半天，期间别人在另一台电脑改过（变成第 3 版），他提交时带 0 就会收到 `409`，前端弹窗让他看差异。**不能默默覆盖。**
3. **草稿不是正式范围**。草稿可以反复改、可以为空。真正的「确认」是另一个接口，会产生不可变的 `scope_version`。

---

### 操作 4｜生成计划预览

| 项 | 内容 |
| --- | --- |
| 谁在什么时候调 | 用户在「用户规划」页点「生成计划」时 |
| 接口 | `POST /api/v1/plan-previews` |
| 请求带什么 | 受影响考试 ID、各考试范围和计划版本、全局日程版本、补排策略 |
| 成功回什么 | **`202` + `job_id`**，不是排好的计划 |
| 会怎么失败 | `409` 范围或日程版本已过期；`422` 输入约束互相矛盾。单纯时间不够仍返回预览，并列出未排入任务 |
| 前端拿到后干什么 | **轮询 `GET /jobs/{job_id}`**，直到状态变成 `done` 再取预览结果；`failed` 显示原因 |

```json
// 第一步：提交
{ "exam_ids": ["exam_1"], "scope_versions": {"exam_1": 1},
  "base_plan_versions": {"exam_1": 0}, "availability_version": 1,
  "strategy": "balanced" }

// 立刻回来
{ "data": { "job_id": "job_01", "status": "queued" }, "meta": { "request_id": "req_03" } }

// 第二步：轮询 GET /jobs/job_01，跑完后
{ "data": { "job_id": "job_01", "status": "done",
            "result": { "preview_id": "prev_01", "affected_exam_ids": ["exam_1"], "feasible_before_exam": true,
                        "moved_tasks": [ { "task_id": "tsk_05", "from": "2026-11-02", "to": "2026-11-04", "minutes": 45 } ],
                        "unscheduled_tasks": [] } }, "meta": { "request_id": "req_04" } }
```

**这个操作是异步的**，因为排一份计划要几秒钟到几十秒。前端不能干等，必须轮询。所以这个「操作」实际是两次请求：先提交，再查任务。

---

## 三、完整链路与覆盖检查

| 顺序 | 用户动作 | 接口 | 契约状态 |
| --- | --- | --- | --- |
| 1 | 建课，或重新打开课程列表 | `POST/GET /courses` | 已写 |
| 2 | 手工建知识点、查看知识点、自评 | `POST/GET /courses/{course_id}/points`、`PUT /points/{point_id}/self-status` | 已写 |
| 3 | 创建考试、读取考试列表 | `POST/GET /courses/{course_id}/exams` | 已写 |
| 4 | 读取／保存范围草稿，确认／读取正式范围 | `GET/PUT /exams/{exam_id}/scope-draft`、`POST /exams/{exam_id}/scope-confirmations`、`GET /exams/{exam_id}/scope` | 已写 |
| 5 | 设置全局每日时间或某天不可学 | `GET/PUT /study-preferences`、`GET /availability`、`PUT /availability/{date}` | 已写 |
| 6 | 生成计划预览、查询处理进度 | `POST /plan-previews`、`GET /jobs/{job_id}` | 已写 |
| 7 | 确认应用并查看正式计划 | `POST /plan-applications`、`GET /exams/{exam_id}/plan` | 已写 |
| 8 | 撤销最近一次调整 | `POST /plan-undo` | 已写 |
| 9 | 手动调整、确认完成任务 | `PATCH /plan-tasks/{task_id}`、`POST /plan-tasks/{task_id}/complete` | 已写 |

原先的两个断点“创建考试”和“确认范围”已经补上。预览有 `preview_id`，但不会写正式计划；应用时重新检查所有课程在同一天的总分钟数。

## 四、需要伙伴互审的规则

1. 示例数据里的四态统一为 `not_started / not_mastered / basic / mastered`，重点统一为 `normal / important`。自评和 AI 建议始终是两个字段。
2. `availability` 以全局日期为键。某天改成 0 分钟，要列出所有受影响课程；已完成任务不移动。
3. 新考试第一次生成计划时还没有 `plan_id`，所以计划预览与应用通过考试 ID 集合和 `preview_id` 衔接。
4. `POST /plan-previews` 返回 `202 + job_id`；前端轮询 `GET /jobs/{job_id}`。用户确认之前不写正式计划。
5. 当前契约覆盖 T01 的建课到计划执行。资料导入、在线答题、批改报告等接口将在对应开发任务中继续细化。
