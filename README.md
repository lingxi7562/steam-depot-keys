# steam-depot-keys

青云入库工具用的**密钥库同步仓库**。

GitHub Actions 每 6 小时把上游两套公开 depot 密钥库合并成一份，强制推送到 `data` 分支。
仓库始终保持单次提交，不会因为长期同步而膨胀。

## 为什么需要它

公开的 depot 密钥库只有两套不同的数据：

| 来源 | 条数 | 特点 |
| --- | --- | --- |
| `SteamAutoCracks/ManifestHub` | 约 28.8 万 | 老游戏全，被 20+ 仓库镜像（内容完全相同） |
| `api.993499094.xyz`（Sudama） | 约 24.2 万 | 新上架游戏更新快 |

两套互补。合并后一份文件就能覆盖，工具不用再分别下 16MB + 18MB。

## 产物

`data` 分支：

- `depotkeys.json` — 合并后的密钥库（`{"<depot/appid>": "<64位hex>"}`）
- `meta.json` — 更新时间、条数、各源状态

访问地址（国内建议走代理）：

```
https://raw.githubusercontent.com/<owner>/steam-depot-keys/data/depotkeys.json
https://ghfast.top/https://raw.githubusercontent.com/<owner>/steam-depot-keys/data/depotkeys.json
```

## 手动触发

Actions 页面点 `Run workflow`，或本地：

```bash
python3 scripts/sync.py
```

产物写到 `out/`。
