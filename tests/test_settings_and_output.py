"""Modal options, the split-archive path and the multi-view metadata layout."""


import pytest

from conftest import make_api, tar_members


@pytest.mark.parametrize(
    "raw, expected", [("True", True), ("true", True), ("False", False), ("false", False), ("1", True)]
)
def test_items_flag(run_app, raw, expected):
    _, calls = run_app(make_api(), **{"modal.state.items": raw})
    assert calls[0]["download_videos"] is expected


def test_bad_flag_fails_early(run_app):
    with pytest.raises(ValueError):
        run_app(make_api(), **{"modal.state.items": "maybe"})


def test_parallel_downloads_option_is_passed(run_app):
    _, calls = run_app(make_api(), **{"modal.state.max_parallel_video_downloads": "3"})
    assert calls[0]["semaphore"] == 3


def test_split_result_uploads_parts_and_sets_output_directory(run_app, monkeypatch):
    api = make_api()
    import supervisely as sly

    real_archive = sly.fs.archive_directory

    def tiny_split(dir_, tar_path, split=None, chunk_size_mb=50):
        assert split == 2 * 1024**3
        return real_archive(dir_, tar_path, split=1024)  # force several parts on tiny data

    monkeypatch.setattr(sly.fs, "archive_directory", tiny_split)
    run_app(api, **{"modal.state.split_result": "true", "modal.state.split_size": "2"})
    remotes = [dst for _, _, dst in api.file.uploaded]
    assert len(remotes) > 1
    prefix = "/tmp/supervisely/export/Export Videos in Supervisely format/77_10_Videos/"
    assert all(r.startswith(prefix) for r in remotes)
    assert api.recorded.outputs[0][0] == "directory"


MULTIVIEW_META = {
    "classes": [],
    "tags": [{"name": "group", "value_type": "any_string", "color": "#FF0000"}],
    "projectSettings": {
        "multiView": {"enabled": True, "tagName": "group", "tagId": None, "isSynced": False},
        "labelingInterface": "multi_view",
    },
}


def test_multiview_writes_metadata_files_main_import_reads(run_app):
    """MultiViewVideoConverter reads <dataset>/metadata/<video name>.meta.json."""
    api = make_api(MULTIVIEW_META)
    _, calls = run_app(api)
    assert calls[0]["save_video_info"] is True
    (_, local, _), = api.file.uploaded
    members = tar_members(local)
    assert "Videos/parent/datasets/child/metadata/child.mp4.meta.json" in members
    assert "Videos/other/metadata/other.mp4.meta.json" in members
    assert not any("/video_info/" in m for m in members)
