"""Launched from a dataset, the export must include the datasets nested in it."""


from conftest import make_api, tar_members


def _archive(api):
    (_, local, _), = api.file.uploaded
    return local


def test_dataset_launch_exports_nested_datasets(run_app):
    api = make_api()
    _, calls = run_app(api, DATASET_ID=1, **{"modal.state.items": "True"})
    assert sorted(calls[0]["dataset_ids"]) == [1, 2, 3]
    members = tar_members(_archive(api))
    assert "Videos/parent/datasets/child/datasets/grandchild/video/grandchild.mp4" in members
    assert not any("/other/" in m for m in members)
    assert api.recorded.workflow[0] == ("dataset", 1)


def test_leaf_dataset_launch_exports_only_that_dataset(run_app):
    api = make_api()
    _, calls = run_app(api, DATASET_ID=4)
    assert calls[0]["dataset_ids"] == [4]


def test_project_launch_exports_every_dataset(run_app):
    api = make_api()
    _, calls = run_app(api)
    assert calls[0]["dataset_ids"] is None
    members = tar_members(_archive(api))
    assert {m.split("/")[1] for m in members if m.count("/") > 1} == {"parent", "other"}
    (_, _, remote), = api.file.uploaded
    assert remote == "/tmp/supervisely/export/Export Videos in Supervisely format/77_10_Videos.tar"
    assert api.recorded.outputs[0][0] == "archive"
