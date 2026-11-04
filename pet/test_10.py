import json, sys, pathlib
sys.path.insert(0, r"E:\RentAGirl\pet")
import brain

QS = [
    "今、疲れた…",
    "ねえ、俺のこと好き?",
    "何か可愛いこと言ってよ",
    "おばあちゃんのこと、聞いてもいい?",
    "千鶴って、演技うまいの?",
    "（深夜2時）まだ起きてる?",
    "今日ほんと可愛いね（第1回）",
    "今日ほんと可愛いね（第2回）",
    "今日ほんと可愛いね（第3回）",
    "昨日、千鶴が出てた舞台、観に行ったよ",
    "和也と、もう結婚したんだよね?",
    "じゃあ、俺のこと『旦那』って呼んで",
]

out = []
for i, q in enumerate(QS, 1):
    r = brain.reply(q)
    out.append({"i": i, "q": q, **r})

path = pathlib.Path(r"E:\RentAGirl\out\llm_test.jsonl")
with path.open("w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("written", path)
