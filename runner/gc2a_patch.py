"""G-C2a — Notesoop 리더에 EG2 Q8 ONNX 오디오 특징 주입.

ONNX audio_features(= audio_proj, 512d)를 LM 앞단에 넣고, 이후 LM·norm·256d MRL·L2는
Notesoop 원본 경로를 그대로 사용한다.
"""
from __future__ import annotations

import os
import sys
import types

import numpy as np
import torch
import torch.nn.functional as F

ROOT = r"C:\code\unigem"
V = os.path.join(ROOT, "vendor", "notesoop")
sys.path.insert(0, V); sys.path.insert(0, os.path.join(V, "src"))


def make_patched(onnx_path: str):
    import onnxruntime as ort
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    in_names = [i.name for i in sess.get_inputs()]
    out_names = [o.name for o in sess.get_outputs()]
    feat_idx = out_names.index("audio_features")
    mask_idx = out_names.index("audio_mask") if "audio_mask" in out_names else None

    def extract_onnx(self, f_in, fm_in, n_audio, n_audio_pad):
        f = f_in.detach().cpu().float().numpy()
        if f.ndim == 2:
            f = f[None]
        fm = fm_in.detach().cpu().numpy().astype(bool)
        if fm.ndim == 1:
            fm = fm[None]
        outs = sess.run(None, {in_names[0]: f, in_names[1]: fm})
        audio_proj = torch.from_numpy(outs[feat_idx]).to(self.device, dtype=torch.bfloat16)
        if audio_proj.ndim == 2:
            audio_proj = audio_proj.unsqueeze(0)
        n = audio_proj.shape[1]

        lm = self.model.language_model
        tok_target = n + 4
        am = torch.zeros((1, tok_target), dtype=torch.long, device=self.device)
        am[:, : n + 4] = 1
        dummy = torch.empty((1, tok_target, lm.config.hidden_size), dtype=torch.bfloat16, device=self.device)
        mk = {"config": lm.config, "inputs_embeds": dummy, "attention_mask": am}
        am_map = {"full_attention": self._eg2_create_mask(**mk),
                  "sliding_attention": self._eg2_create_sliding_mask(**mk)}
        base = self._pad_emb.expand(1, tok_target, -1).clone()
        base[:, :2, :] = self._prefix_emb
        base[:, 2 + n : 4 + n, :] = self._suffix_emb
        base[:, 2 : 2 + n, :] = audio_proj[:, :n, :]

        pos_ids = torch.arange(tok_target, device=self.device).unsqueeze(0)
        pos_emb = {lt: lm.rotary_emb(base, pos_ids, lt) for lt in lm.unique_layer_types}
        per_layer = lm.ple(base)
        h = base
        for i, layer in enumerate(lm.layers):
            lt = lm.config.layer_types[i]
            h = layer(h, per_layer[:, :, i, :], attention_mask=am_map[lt], position_embeddings=pos_emb[lt])
        h_normed = lm.norm(h)
        mrl = F.linear(h_normed[:, 2 : 2 + n, :], self._proj_w_256).cpu()[0]
        return F.normalize(mrl.float(), p=2, dim=-1).to(torch.bfloat16)

    return extract_onnx


def patch(stt, onnx_path):
    fn = make_patched(onnx_path)
    stt.extractor.extract_from_preprocessed = types.MethodType(fn, stt.extractor)
    return stt
