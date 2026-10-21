---
title: "项目：axum + serde 的内存待办事项 API"
type: 实战项目
difficulty: 中等
stack:
  - axum 0.8
  - tokio
  - serde
  - uuid
  - tower-http
tags:
  - rust/实战
aliases:
  - 项目-Web API 服务
  - todo-api
一句话: 用 axum 0.8 加一份 HashMap 状态实现待办事项的 REST 增删改查，并把所有失败统一成 JSON 错误响应。
---

# 项目：Web API 服务 todo-api

## 目标

做一个内存版待办事项服务：`GET /todos`、`POST /todos`、`GET|PATCH|DELETE /todos/{id}`；数据放进程里（重启即丢），重点练路由拆分、状态共享与统一 JSON 错误三件事。

## 技术栈

| 用途 | crate / 标准库 |
| --- | --- |
| HTTP 框架、路由、提取器 | `axum` 0.8 |
| 异步运行时与读写锁 | `tokio`（`macros`、`rt-multi-thread`） |
| 请求/响应 JSON | `serde`（`derive`）、`serde_json` |
| ID、集合与日志 | `uuid`（`v4`、`serde`）、`HashMap`、`tower-http`（`trace`） |

## 第 1 步：初始化项目

```bash
cargo new todo-api
cd todo-api
cargo add axum
cargo add tokio --features macros,rt-multi-thread
cargo add serde --features derive
cargo add serde_json
cargo add uuid --features v4,serde
cargo add tower-http --features trace
cargo add tracing tracing-subscriber
```

`Cargo.toml` 的依赖部分（`axum` 0.8 的路径参数写 `/{id}`，0.7 及更早是 `/:id`，抄旧教程会直接 404）：

```toml
[package]
name = "todo-api"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.8"
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4", "serde"] }
tower-http = { version = "0.6", features = ["trace"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

## 第 2 步：数据模型与共享状态

```rust
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize)]
pub struct Todo {
    pub id: Uuid,
    pub title: String,
    pub done: bool,
}

#[derive(Debug, Deserialize)]
pub struct CreateTodo {
    pub title: String,
}

/// 两个 Option 表达「没传就不改」，PATCH 才能只改单个字段
#[derive(Debug, Deserialize)]
pub struct PatchTodo {
    pub title: Option<String>,
    pub done: Option<bool>,
}

/// 全局状态：Arc 让每个请求共享同一份数据，RwLock 允许多读单写
#[derive(Clone, Default)]
pub struct AppState {
    pub todos: Arc<RwLock<HashMap<Uuid, Todo>>>,
}
```

`AppState` 必须 `Clone`（`axum` 会给每个请求复制一份 `State`），但 `Arc` 只复制指针；锁要用 **tokio** 的版本，`std` 的 `MutexGuard` 不满足 `Send`，跨 `.await` 直接编译失败。

## 第 3 步：统一 JSON 错误响应

```rust
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

#[derive(Debug)]
pub enum ApiError {
    NotFound(Uuid),
    Invalid(String),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, msg) = match self {
            ApiError::NotFound(id) => (StatusCode::NOT_FOUND, format!("待办 {id} 不存在")),
            ApiError::Invalid(why) => (StatusCode::BAD_REQUEST, why),
        };
        // 前端只需要认一种失败格式：{"error": "..."}
        (status, Json(serde_json::json!({ "error": msg }))).into_response()
    }
}
```

处理器统一返回 `Result<T, ApiError>`，`?` 一抛就变成 HTTP 响应，业务代码里不用再手写状态码分支。

## 第 4 步：五个处理器

```rust
use axum::extract::{Path, State};

async fn list(State(st): State<AppState>) -> Json<Vec<Todo>> {
    Json(st.todos.read().await.values().cloned().collect())
}

async fn create(State(st): State<AppState>, Json(body): Json<CreateTodo>) -> Result<(StatusCode, Json<Todo>), ApiError> {
    let title = body.title.trim();
    if title.is_empty() {
        return Err(ApiError::Invalid("title 不能为空".into()));
    }
    let todo = Todo { id: Uuid::new_v4(), title: title.to_string(), done: false };
    st.todos.write().await.insert(todo.id, todo.clone());
    Ok((StatusCode::CREATED, Json(todo)))
}

async fn get_one(State(st): State<AppState>, Path(id): Path<Uuid>) -> Result<Json<Todo>, ApiError> {
    st.todos.read().await.get(&id).cloned().map(Json).ok_or(ApiError::NotFound(id))
}

async fn update(State(st): State<AppState>, Path(id): Path<Uuid>, Json(body): Json<PatchTodo>) -> Result<Json<Todo>, ApiError> {
    let mut db = st.todos.write().await;
    let todo = db.get_mut(&id).ok_or(ApiError::NotFound(id))?;
    if let Some(title) = body.title.filter(|t| !t.trim().is_empty()) { todo.title = title; }
    if let Some(done) = body.done { todo.done = done; }
    Ok(Json(todo.clone()))
}

async fn remove(State(st): State<AppState>, Path(id): Path<Uuid>) -> Result<StatusCode, ApiError> {
    let gone = st.todos.write().await.remove(&id);
    gone.map(|_| StatusCode::NO_CONTENT).ok_or(ApiError::NotFound(id))
}
```

`get_mut` 拿到可变引用后直接改字段再 `clone()` 返回；`read().await.get(...).cloned()` 里的临时守卫在语句结束就释放，不会跨 `.await`。`create` 只在 `title` 非空时插入，`update` 里没传的字段保持原值。

## 第 5 步：路由与启动

```rust
use axum::routing::get;
use axum::Router;
use tower_http::trace::TraceLayer;

/// 抽成函数：以后写集成测试时，传一个全新的 AppState 就能直接调
pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/todos", get(list).post(create))
        .route("/todos/{id}", get(get_one).patch(update).delete(remove))
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt().init();
    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000").await?;
    tracing::info!("监听 http://{}", listener.local_addr()?);
    axum::serve(listener, app(AppState::default())).await
}
```

## 运行与验证

```bash
cargo run
# 另开一个终端
curl -s -X POST localhost:3000/todos -H 'content-type: application/json' -d '{"title":"写笔记"}'
curl -s localhost:3000/todos
curl -si -X DELETE localhost:3000/todos/$ID
curl -si localhost:3000/todos/$ID   # 404 + {"error":"待办 ... 不存在"}
```

把 `$ID` 换成乱码会返回 `400` 纯文本：`Path<Uuid>` 在提取阶段就拒绝了，还没走到我们的 `ApiError`。想让这类失败也返回 JSON，得自定义 `rejection`，或者先用 `Path<String>` 再手动解析。

## 扩展方向

1. 用 `sqlx` + SQLite 持久化，把 `AppState` 里的 `HashMap` 换成连接池。
2. `list` 加分页与 `done` 过滤；用 `tower::ServiceExt::oneshot` 直接把 `Router` 当服务调，集成测试不用起端口。
3. 加一层中间件做 API Key 或 JWT 鉴权；用 `utoipa` 生成 OpenAPI。
4. `axum::serve(...).with_graceful_shutdown(...)` 配合 `tokio::signal` 做优雅关闭。

## 相关

- [[07-结构体|结构体]]：`Todo`、`AppState` 的字段设计与 `#[derive]`。
- [[12-集合类型|集合类型]]：`HashMap` 的增删查，以及这里为什么不用 `BTreeMap`。
- [[22-异步编程|异步编程]]：`async fn`、`.await` 与 `#[tokio::main]` 的关系。
- [[sync.RwLock|RwLock]]：读写锁的语义，以及交叉持锁会死锁的坑。
- [[sync.Arc|Arc]]：多请求共享状态为什么是 `Arc` 而不是 `Rc`。
- [[11-错误处理|错误处理]]：错误类型设计与 `?` 的传播路径。

下一个项目：[[03-并发爬虫|并发爬虫]]。
