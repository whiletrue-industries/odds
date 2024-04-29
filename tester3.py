import asyncio
from odds.frontend import frontend
b = frontend.ODDSFrontend()
with open('sample.txt') as f:
    text = f.read()
    ret = asyncio.run(b.analyze_text(text))
    print(ret)
del b
