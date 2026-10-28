"""Offline test harness: runs src/main.py against a small in-memory fake of sly.Api.

No Supervisely server is contacted; the SDK project download is replaced by a fake that
writes the folders the real one would (one per selected dataset). Run from the repo root
with the SDK from dev_requirements.txt installed (plus pytest):
    python -m pytest tests
"""

import importlib
import os
import sys
import tarfile
from types import SimpleNamespace

import pytest
import supervisely as sly
import supervisely.project.download as sdk_download

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
APP_MODULES = ("globals", "main", "utils", "workflow")

PROJECT_ID = 10
# tree: 1 "parent" -> 2 "child" -> 3 "grandchild"; 4 "other" at the root
DATASETS = {
    1: ("parent", None),
    2: ("child", 1),
    3: ("grandchild", 2),
    4: ("other", None),
}


def dataset_info(ds_id):
    name, parent = DATASETS[ds_id]
    fields = {f: None for f in sly.DatasetInfo._fields}
    fields.update(id=ds_id, name=name, parent_id=parent, project_id=PROJECT_ID)
    return sly.DatasetInfo(**fields)


def dataset_parents(ds_id):
    parents = []
    parent = DATASETS[ds_id][1]
    while parent is not None:
        parents.insert(0, DATASETS[parent][0])
        parent = DATASETS[parent][1]
    return parents


class FakeDatasetApi:
    def get_tree(self, project_id):
        def children(parent):
            return {
                dataset_info(i): children(i) for i, (_, p) in DATASETS.items() if p == parent
            }

        return children(None)

    def get_nested(self, project_id, dataset_id):
        out = []

        def walk(tree, inside):
            for info, sub in tree.items():
                if inside:
                    out.append(info)
                walk(sub, inside or info.id == dataset_id)

        walk(self.get_tree(project_id), False)
        return out

    def get_info_by_id(self, id):
        return dataset_info(id)


class FakeFileApi:
    def __init__(self):
        self.uploaded = []  # (team_id, local path, remote path)

    def upload(self, team_id, src, dst, progress_cb=None):
        self.uploaded.append((team_id, src, dst))
        return SimpleNamespace(
            id=len(self.uploaded), name=os.path.basename(dst), storage_path=dst, team_id=team_id
        )

    async def upload_bulk_async(self, team_id, src_paths, dst_paths, progress_cb=None, **kw):
        for src, dst in zip(src_paths, dst_paths, strict=False):
            self.uploaded.append((team_id, src, dst))

    def get_info_by_path(self, team_id, path):
        return SimpleNamespace(id=1, path=path, storage_path=path)


def make_api(meta_json=None):
    recorded = SimpleNamespace(outputs=[], workflow=[])
    meta_json = meta_json or {"classes": [], "tags": []}
    api = SimpleNamespace(
        project=SimpleNamespace(
            get_info_by_id=lambda id: SimpleNamespace(id=id, name="Videos", type="videos"),
            get_meta=lambda id, with_settings=False: meta_json,
        ),
        dataset=FakeDatasetApi(),
        file=FakeFileApi(),
        task=SimpleNamespace(
            set_output_archive=lambda *a, **k: recorded.outputs.append(("archive", a, k)),
            set_output_directory=lambda *a, **k: recorded.outputs.append(("directory", a, k)),
        ),
        app=SimpleNamespace(
            workflow=SimpleNamespace(
                add_input_project=lambda i: recorded.workflow.append(("project", i)),
                add_input_dataset=lambda i: recorded.workflow.append(("dataset", i)),
                add_output_file=lambda *a, **k: recorded.workflow.append(("file",)),
                add_output_folder=lambda *a, **k: recorded.workflow.append(("folder",)),
            )
        ),
        recorded=recorded,
    )
    return api


def fake_project_download(calls):
    """Stands in for download_async_or_sync: writes meta.json and one folder per dataset."""

    def _download(api, project_id, dest_dir, dataset_ids=None, **kwargs):
        calls.append({"project_id": project_id, "dataset_ids": dataset_ids, **kwargs})
        os.makedirs(dest_dir, exist_ok=True)
        sly.json.dump_json_file({"classes": [], "tags": []}, os.path.join(dest_dir, "meta.json"))
        selected = DATASETS if dataset_ids is None else [i for i in DATASETS if i in set(dataset_ids)]
        for ds_id in selected:
            parts = dataset_parents(ds_id) + [DATASETS[ds_id][0]]
            ds_dir = os.path.join(dest_dir, "/datasets/".join(parts))
            os.makedirs(os.path.join(ds_dir, "video"), exist_ok=True)
            os.makedirs(os.path.join(ds_dir, "ann"), exist_ok=True)
            name = f"{DATASETS[ds_id][0]}.mp4"
            with open(os.path.join(ds_dir, "video", name), "wb") as f:
                f.write(b"\0" * 16)
            sly.json.dump_json_file({}, os.path.join(ds_dir, "ann", f"{name}.json"))
            if kwargs.get("save_video_info"):
                os.makedirs(os.path.join(ds_dir, "video_info"), exist_ok=True)
                info = {"name": name, "meta": {"camera": name}}
                sly.json.dump_json_file(info, os.path.join(ds_dir, "video_info", f"{name}.json"))
        sly.json.dump_json_file({}, os.path.join(dest_dir, "key_id_map.json"))

    return _download


def tar_members(path):
    with tarfile.open(path) as tar:
        return sorted(m.name for m in tar.getmembers() if m.isfile())


@pytest.fixture
def run_app(monkeypatch, tmp_path):
    """run_app(api, **env) runs the app end to end; returns (main module, download calls)."""

    def _run(api, **env):
        base = {
            "ENV": "production",
            "TASK_ID": "77",
            "TEAM_ID": "1",
            "WORKSPACE_ID": "2",
            "PROJECT_ID": str(PROJECT_ID),
            "SLY_APP_DATA_DIR": str(tmp_path / "app_data"),
        }
        base.update({k: str(v) for k, v in env.items()})
        for key in list(os.environ):
            if key.startswith("modal.state.") or key in ("DATASET_ID", "context.datasetId"):
                monkeypatch.delenv(key, raising=False)
        for key, value in base.items():
            monkeypatch.setenv(key, value)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sly.Api, "from_env", classmethod(lambda cls, *a, **k: api))
        calls = []
        monkeypatch.setattr(sdk_download, "download_async_or_sync", fake_project_download(calls))
        monkeypatch.syspath_prepend(SRC_DIR)
        for name in APP_MODULES:
            sys.modules.pop(name, None)
        main = importlib.import_module("main")  # the pre-fix app ran at import time
        if hasattr(main, "main"):
            main.main()
        return main, calls

    yield _run
    for name in APP_MODULES:
        sys.modules.pop(name, None)
