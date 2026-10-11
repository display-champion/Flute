# Cascadeur 内で実行して、シーン保存・FBX アニメ書き出しに使えそうな API を探す。
# 使い方: python -m cascadeur_session run-file snippets/probe_api.py
# （app / scene / csc はスクリプトサーバーが用意する）

KEYWORDS = ("save", "export", "anim", "frame", "fps", "physics", "posing", "interval", "key")


def show(label, obj):
    names = [n for n in dir(obj) if not n.startswith("_")]
    hits = [n for n in names if any(k in n.lower() for k in KEYWORDS)]
    print("== %s (%s)" % (label, type(obj).__name__))
    print("  関連しそう: " + (", ".join(hits) or "(なし)"))
    print("  全部: " + ", ".join(names))


tm = app.get_tools_manager()
show("app", app)
show("scene_manager", app.get_scene_manager())
show("current_scene", scene)
show("domain_scene", scene.domain_scene())
show("tools_manager", tm)
try:
    show("FbxSceneLoader の loader", tm.get_tool("FbxSceneLoader").get_fbx_loader(scene))
except Exception as e:
    print("FbxSceneLoader: 取得失敗 %r" % e)
try:
    tools = tm.tools()
    print("== ツール一覧")
    for t in tools:
        print("  " + str(t))
except Exception as e:
    print("tools(): 取得失敗 %r" % e)
