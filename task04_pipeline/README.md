# 任务 04：双域语料自动化清洗与入库流水线

这个目录提供一版可直接落地的 Python 流水线，负责完成以下工作：

1. 读取 `md / docx / pdf`
2. 文本清洗与去噪
3. 按“文档 -> 章节 -> 条款”进行语义分块
4. 为每个文本块补充元数据
5. 调用任务 03 的 `insert_vectors(data)` 入库

## 目录说明

- `build_chunks.py`: 主脚本
- `task03_adapter.py`: 任务 03 接口适配层
- `source_manifest.example.json`: 来源元数据清单样例

## 推荐目录约定

建议把原始语料和产出结果放成下面这样：

```text
d:\Project\LLM
├─ raw\
├─ outputs\
└─ task04_pipeline\
```

当前仓库里的样例文件已经可以直接作为输入。

## 最小运行方式

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\研究生教育管理规章制度汇编.md" `
  --domain graduate `
  --output "outputs\graduate_chunks.jsonl" `
  --pretty
```

## 带来源元数据的运行方式

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\研究生教育管理规章制度汇编.md" `
  --domain graduate `
  --manifest "task04_pipeline\source_manifest.example.json" `
  --output "outputs\graduate_chunks.jsonl" `
  --pretty
```

## 对接任务 03

当任务 03 已提供 `insert_vectors(data)` 后，可以直接加 `--insert`：

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\研究生教育管理规章制度汇编.md" `
  --domain graduate `
  --output "outputs\graduate_chunks.jsonl" `
  --insert
```

你只需要把真实函数暴露到以下任意模块即可：

- `task03_vector_api.py`
- `vector_api.py`
- `rag/vector_store.py`

函数签名统一为：

```python
def insert_vectors(data: list[dict]) -> None:
    ...
```

## 输出格式

每一行都是一个 JSON 对象，格式如下：

```json
{
  "id": "2a0a4f9f6f2d8d0a",
  "text": "第一条 根据《中华人民共和国学位条例》...",
  "metadata": {
    "domain": "graduate",
    "source_file": "研究生教育管理规章制度汇编.md",
    "source_path": "D:\\Project\\LLM\\研究生教育管理规章制度汇编.md",
    "source_type": "md",
    "source_url": "https://your-official-source.example/graduate-rules",
    "source_name": "高研院研究生处",
    "doc_title": "中国科学院上海高等研究院学位授予工作实施细则（暂行）",
    "doc_code": "沪高院发学位字〔2018〕42号",
    "publish_date": "2018-12-11",
    "publish_year": 2018,
    "section_path": "第一章 总则 > 第一条 根据《中华人民共和国学位条例》...",
    "chunk_id": "2a0a4f9f6f2d8d0a",
    "chunk_index": 1,
    "char_count": 356,
    "token_estimate": 320
  }
}
```

## 当前实现的分块策略

- 先识别汇编中的每一份独立制度文件
- 再识别 `第X章 / 第X条 / 一、 / （一）`
- 优先保持条款完整
- 条款过长时，再按句号、分号切成多个块

这个策略比单纯按固定字数切块更适合法规、制度、办事指南类中文语料，因为检索时更容易命中完整规则。

## 建议你后续补强的两点

1. 给每份原始文件补一份来源清单
   至少包含 `source_url`、`source_name`、`collection`

2. 对党建语料单独维护一份清洗规则
   例如过滤页眉页脚、会议照片说明、目录页、转载声明等

## 后续扩展建议

- 如果党建语料来源是 PDF 扫描件，建议接 OCR
- 如果你们最终接 Milvus，可以把 `collection` 放进 metadata
- 如果任务 07 要做答案溯源，建议 metadata 里继续加：
  - `doc_title`
  - `doc_code`
  - `publish_date`
  - `source_url`
  - `section_path`
