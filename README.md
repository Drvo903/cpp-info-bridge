# CPP 信息桥

每日北京时间 09:20 / 21:20（UTC 01:20 / 13:20）通过 GitHub Actions 查询 CPP 公开活动接口，输出 JSON 供江浙沪 ACG 周报读取。

- `data/status.json`：运行时间、采集状态、关键词错误和分页截断信息。
- `data/latest.json`：仅在至少一个关键词采集成功时更新，避免失败覆盖已有数据。
- `sync.py`：直接访问 CPP 原站 `eventMainListV2.do`；不依赖失效的 mihoyo.su 第三方实例。
- `.github/workflows/sync.yml`：手动及每日定时运行。

## 首次验证
在 Actions → Sync CPP events → Run workflow 手动执行。绿色成功只是工作流执行成功；请以 `status.json` 中 `collector_status` 为准。若失败，工作流也会显示红色，错误保留在 `status.json`。

## 注意
接口是从开源 [WindowsNoEditor/CPP_Search](https://github.com/WindowsNoEditor/CPP_Search) 项目核实的公开调用方式，并非 CPP 官方授权 API；可能受访问策略、响应结构变化影响。关键词最多抓取 8 页，每个关键词超过 80 条会在 `keyword_counts` 中标记 `truncated`。数据不代表 CPP 全站完整活动列表。采集应尊重站点服务条款，遇到限制不要绕过访问控制。
