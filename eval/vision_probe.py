"""Gemma4 비전 클래스/시그니처 확인."""
import inspect

import transformers.models.gemma4.modeling_gemma4 as m

names = [n for n in dir(m) if "Vision" in n or "vision" in n]
print(names)
for n in names:
    obj = getattr(m, n)
    if inspect.isclass(obj):
        try:
            print("==", n, inspect.signature(obj.__init__))
            if hasattr(obj, "forward"):
                print("   forward", inspect.signature(obj.forward))
        except Exception as e:
            print("   err", e)
