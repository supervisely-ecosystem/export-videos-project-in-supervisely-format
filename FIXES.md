# Fixes: export-videos-project-in-supervisely-format (branch `ecosystem-fixes-2026-10`)

Lifecycle `legacy` (9,544 runs): targeted fixes plus the image move. Not rewritten (kept
`globals.py`/`utils.py`; ~150 lines). Base: `origin/HEAD` b0dacd5 (v1.4.7). Nothing pushed or released.

## Behaviour contract (unchanged except fix 1)

Headless, "Download as" on `videos_project` and `videos_dataset`.

| input | default | meaning |
|---|---|---|
| project / dataset context | | whole project, or the dataset **and the datasets nested in it** (fix 1) |
| `modal.state.items` | `"True"` | `True` videos + annotations, `False` annotations only |
| `modal.state.max_parallel_video_downloads` | `5` | semaphore for the async download |
| `modal.state.split_result` | `false` | split the tar into parts |
| `modal.state.split_size` | `5` | part size, GB |

Output: SDK video project layout (`meta.json`, `key_id_map.json`, `<ds>/video|ann`, nested
`<ds>/datasets/<child>/…`) under a top folder named after the project, archived as
`<task>_<project>[_<dataset>]_<project name>.tar` and uploaded to
`/tmp/supervisely/export/Export Videos in Supervisely format/`; task output = that archive.
Split: parts uploaded to `…/<archive name without .tar>/`, task output = that folder.
Multi-view projects (labeling interface `multi_view`): `video_info` is turned into
`<ds>/metadata/<video>.meta.json`, the layout main-import's `MultiViewVideoConverter` reads.
Workflow: project or dataset in; file or folder out.

## Fixed

| # | commit | bug | test (old → new) |
|---|---|---|---|
| 1 | c13e030 | **Partial export, wrong success.** From a dataset, only that dataset's id went to the SDK download, which filters by exact ids: nested datasets were silently dropped (a parent holding only sub-datasets gave an empty archive). Now the selection is expanded with `api.dataset.get_nested`. | `tests/test_nested_datasets.py`: 2/3 → 3/3 |
| 2 | a31abca | **Python 3.14 / image.** `distutils.util.strtobool` (removed in 3.12; on the 3.14 image it imports only through setuptools' shim) replaced by `globals.to_bool`; script body moved into `main()` under `sly.main_wrapper`; image and SDK moved (below). | `tests/test_settings_and_output.py` (options, split path, multi-view layout): 9 new tests, pass on old and new code |

Total: `pytest` 12 passed in a Python 3.14 venv (SDK 6.74.28) and inside
`supervisely/base-py-sdk-hardened:6.74.28` (Python 3.14.7). Old code with the same tests: 11 passed, 1 failed.

## Intentional changes

- Dataset launch includes nested datasets (fix 1).
- An invalid `items`/`split_result` value fails at start with `ValueError` (before: `strtobool` raised the same way).

## Found, not fixed

- `items=False` still makes the SDK write what it writes for annotation-only video downloads
  (not checked on dev whether that archive re-imports).
- `local.env` uses `modal.state.split_size_gb` (the app reads `split_size`); debug file only.
- No nested video project exists on dev to check fix 1 against the server (setup step below).

## Image

`supervisely/base-py-sdk-hardened:6.74.14` → `supervisely/base-py-sdk-hardened:6.74.28`, SDK
6.74.14 → 6.74.28: the newest SDK `versions.json` allows for `instance_version` 6.17.8
([6.74.10, 6.74.29)); tag exists on Docker Hub. `instance_version` unchanged (6.74.29+ needs 6.17.22).
`dev_requirements.txt` holds only the SDK, so no per-app image; `release.yml` has no build job.
Upload paths checked in 6.74.28: `api.file.upload` with `tqdm_sly` goes through the monitor-aware
`get_partial` branch; `upload_bulk_async` is unchanged from 6.74.14 for this use.

## Dev-check plan

Compare branch vs published (v1.4.7) archives: member list + SHA-256 (videos) and canonical JSON (annotations).

| case | command | expected (branch) | published |
|---|---|---|---|
| project, videos | `uv run ecosystem-fleet/fleet.py run export-videos-project-in-supervisely-format --workspace 733 --project 143 --version ecosystem-fixes-2026-10 --branch` | `Videos example/ds0/video` 2 videos + ann; identical to published | same without `--version/--branch` |
| dataset, annotations only | `… --project 143 --dataset 286 --state items=False --version ecosystem-fixes-2026-10 --branch` | archive name `<task>_143_286_Videos example.tar`, ann only; identical to published | same without `--version/--branch` |
| multi-view | `… --project 6938 --version ecosystem-fixes-2026-10 --branch` | `ds0/metadata/*.meta.json`, no `video_info/`; identical to published | same without `--version/--branch` |
| split | `… --project 143 --state split_result=true --state split_size=1 --version ecosystem-fixes-2026-10 --branch` | task output is the folder `…/<task>_143_Videos example/`, 1 part (small project) | same without `--version/--branch` |
| nested from a dataset (setup needed) | create "agents export-videos nested" in ws 733 with datasets `parent` → `child` → `grandchild`, copy one video of project 143 into each; `… --project <id> --dataset <parent id> --version ecosystem-fixes-2026-10 --branch` | 3 videos under `parent/`, `parent/datasets/child/`, `…/datasets/grandchild/` | published: only `parent`'s video |
