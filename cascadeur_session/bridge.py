"""Cascadeur の csc API への薄いアダプタ。

csc は Cascadeur 内の Python でしか import できないため、このモジュールに
API 呼び出しを集め、他のモジュールは Cascadeur 無しでもテストできるようにしている。
"""


def _csc():
    import csc  # Cascadeur 内でのみ利用可能
    return csc


def application():
    return _csc().app.get_application()


def view_scene():
    """現在の csc.view.Scene。"""
    return application().current_scene()


def domain_scene(scene=None):
    """csc.domain.Scene を返す。run(scene) に view/domain どちらが渡されても扱える。"""
    scene = scene if scene is not None else view_scene()
    return scene.domain_scene() if hasattr(scene, "domain_scene") else scene


def list_objects(scene=None):
    """シーン内の全オブジェクトを (id, name) のリストで返す。"""
    viewer = domain_scene(scene).model_viewer()
    return [(str(oid), viewer.get_object_name(oid)) for oid in viewer.get_objects()]


def export_fbx_all(path, binary=True):
    """シーン全体を FBX に書き出す。"""
    csc = _csc()
    loader = application().get_tools_manager().get_tool("FbxSceneLoader").get_fbx_loader(view_scene())
    settings = csc.fbx.FbxSettings()
    settings.mode = csc.fbx.FbxSettingsMode.Binary if binary else csc.fbx.FbxSettingsMode.Ascii
    loader.set_settings(settings)
    loader.export_all_objects(path)
    return path
