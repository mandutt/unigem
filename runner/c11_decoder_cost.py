"""C-11.3 — T5Gemma 2 디코더 온디맨드 비용 측정(FP32·동적 INT8)."""
from __future__ import annotations

import json
import os
import statistics
import threading
import time

import psutil
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

P = r"C:\code\unigem\data\models\t5gemma-2-270m-270m"
OUT = r"C:\code\unigem\logs\C11_decoder_cost.json"
TMP = r"C:\code\unigem\cache\c11_q8.pt"


def rss():
    return psutil.Process().memory_info().rss / 1e6


class Sampler:
    def __init__(self):
        self.peak = 0
        self.run = False

    def start(self):
        self.run = True
        self.peak = rss()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.run:
            self.peak = max(self.peak, rss())
            time.sleep(0.05)

    def stop(self):
        self.run = False
        return self.peak


def main():
    torch.set_num_threads(6)
    res = {"model": P}
    res["file_mb"] = round(sum(os.path.getsize(os.path.join(P, f)) for f in os.listdir(P)) / 1e6, 1)
    res["safetensors_mb"] = round(os.path.getsize(os.path.join(P, "model.safetensors")) / 1e6, 1)

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(P)
    model = AutoModelForSeq2SeqLM.from_pretrained(P, dtype=torch.float32, low_cpu_mem_usage=True)
    model = model.float()
    model.eval()
    res["load_sec_fp32"] = round(time.time() - t0, 2)
    res["rss_idle_mb"] = round(rss(), 1)
    res["params_m"] = round(sum(p.numel() for p in model.parameters()) / 1e6, 1)

    text = "다음 글을 세 문장으로 요약하라. " + ("한국어 요약 성능을 측정하기 위한 긴 입력 문장이다. " * 30)
    enc = tok(text, return_tensors="pt", truncation=True, max_length=256)
    lat = []
    s = Sampler()
    with torch.inference_mode():
        for i in range(3):
            s.start()
            t = time.time()
            out = model.generate(**enc, max_new_tokens=128, num_beams=1, do_sample=False)
            lat.append(time.time() - t)
            s.stop()
    res["rss_peak_mb"] = round(s.peak, 1)
    res["gen_sec"] = [round(x, 2) for x in lat]
    res["gen_p50"] = round(statistics.median(lat), 2)
    res["out_tokens"] = int(out.shape[1])

    # 동적 INT8 (Linear only) — 크기 측정
    q = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    torch.save(q.state_dict(), TMP)
    res["q8_dynamic_mb"] = round(os.path.getsize(TMP) / 1e6, 1)
    os.remove(TMP)
    res["q8_ratio"] = round(res["q8_dynamic_mb"] / res["safetensors_mb"], 3)

    # 어휘 pruning 추정
    emb = model.get_input_embeddings().weight.numel()
    res["embedding_params_m"] = round(emb / 1e6, 1)
    res["vocab"] = int(model.config.vocab_size)
    for keep in (64000, 96000):
        saved = emb * (1 - keep / res["vocab"]) / 1e6
        res[f"prune_{keep}_saved_params_m"] = round(saved, 1)
        res[f"prune_{keep}_saved_fp32_mb"] = round(saved * 4, 1)
        res[f"prune_{keep}_saved_q8_mb"] = round(saved, 1)

    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
