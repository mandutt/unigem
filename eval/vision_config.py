"""비전 타워 구성 확인."""
import json
import os

from transformers import AutoConfig

ck = r"C:\code\unigem\data\models\embeddinggemma-2-f9972ac2"
cfg = AutoConfig.from_pretrained(ck)
print("top keys", [k for k in dir(cfg) if "vision" in k.lower()][:20])
vc = getattr(cfg, "vision_config", None)
if vc is not None:
    d = vc.to_dict()
    print(json.dumps({k: d[k] for k in d if k in (
        "hidden_size", "num_hidden_layers", "num_attention_heads", "intermediate_size",
        "image_size", "patch_size", "num_channels", "pooling_type")}, indent=1))
print("image_token_id", getattr(cfg, "image_token_id", None),
      "image_token_index", getattr(cfg, "image_token_index", None))
