"""儿童版表扬海报图片生成 — 调用 Hermes image_generate"""

import os
from pathlib import Path
from datetime import datetime

def generate(prompt: str, ptype: str, child_name: str) -> str:
    """
    调用 Hermes image_generate 生成表扬海报。
    返回本地保存的文件路径。
    """
    from hermes_tools import image_generate

    # 生成图片
    result = image_generate(
        prompt=prompt,
        aspect_ratio="portrait",
    )

    image_url = result.get("image")
    if not image_url:
        raise ValueError("Hermes image_generate returned no image URL")

    # 如果是 URL，下载到本地
    save_dir = Path.home() / "Pictures" / "dizical-praise"
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{ptype}_{child_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = save_dir / filename

    if image_url.startswith("http"):
        import urllib.request
        urllib.request.urlretrieve(image_url, save_path)
    else:
        # 已经是本地路径
        pass

    return str(save_path)
