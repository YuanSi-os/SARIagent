from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


def get_insert_vectors() -> Callable[[list[dict[str, Any]]], Any]:
    """
    统一适配任务 03 的 insert_vectors(data)。

    你后续只需要把真实函数暴露到以下任意一个模块中即可：
    1. task03_vector_api.insert_vectors
    2. vector_api.insert_vectors
    3. rag.vector_store.insert_vectors
    """

    candidates = [
        ("task03_vector_api", "insert_vectors"),
        ("vector_api", "insert_vectors"),
        ("rag.vector_store", "insert_vectors"),
    ]

    for module_name, attr_name in candidates:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            continue
        insert_fn = getattr(module, attr_name, None)
        if callable(insert_fn):
            return insert_fn

    raise RuntimeError(
        "未找到任务 03 的 insert_vectors(data)。"
        "请在 task03_vector_api.py、vector_api.py 或 rag/vector_store.py 中暴露该函数。"
    )
