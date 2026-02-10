import os
from pathlib import Path

import globals as g
import supervisely as sly
import utils as u
import workflow as w
from supervisely import tqdm_sly
from supervisely.project.download import download_async_or_sync
from supervisely.project.project_settings import LabelingInterface

project = g.api.project.get_info_by_id(g.project_id)
project_name = project.name

project_meta_json = g.api.project.get_meta(g.project_id, with_settings=True)
project_meta = sly.ProjectMeta.from_json(project_meta_json)
is_multiview = project_meta.project_settings.labeling_interface == LabelingInterface.MULTIVIEW

result_dir = os.path.join(g.app_data, g.RESULT_DIR_NAME, project_name)
result_archive_path = os.path.join(g.app_data, g.RESULT_DIR_NAME)
if g.dataset_id is None:
    archive_name = f"{g.task_id}_{g.project_id}_{project_name}.tar"
    w.workflow_input(g.api, g.project_id, "project")
else:
    archive_name = f"{g.task_id}_{g.project_id}_{g.dataset_id[0]}_{project_name}.tar"
    w.workflow_input(g.api, g.dataset_id[0], "dataset")
result_archive = os.path.join(g.app_data, archive_name)
base_export_path = sly.team_files.RECOMMENDED_EXPORT_PATH

download_async_or_sync(
    api=g.api,
    project_id=g.project_id,
    dest_dir=result_dir,
    dataset_ids=g.dataset_id,
    download_videos=g.DOWNLOAD_ITEMS,
    save_video_info=is_multiview,
    log_progress=True,
    semaphore=g.MAX_PARALLEL_VIDEO_DOWNLOADS,
)

if is_multiview:
    u.create_metadata_files(result_dir)
if not g.SPLIT_RESULT:
    sly.fs.archive_directory(result_archive_path, result_archive)
    sly.logger.info("Result directory is archived")
    remote_archive_path = Path(base_export_path) / g.RESULT_DIR_NAME / archive_name
    total_size = sly.fs.get_file_size(result_archive)
    upload_progress = tqdm_sly(
        total=total_size, desc=f"Uploading {archive_name}", unit="B", unit_scale=True
    )
    file_info = g.api.file.upload(
        g.team_id,
        result_archive,
        str(remote_archive_path),
        progress_cb=upload_progress,
    )
    sly.logger.info("Uploaded to Team-Files: {!r}".format(file_info.storage_path))
    g.api.task.set_output_archive(
        g.task_id, file_info.id, archive_name, file_url=file_info.storage_path
    )
    w.workflow_output(g.api, g.team_id, file_info)
else:
    parts_paths = sly.fs.archive_directory(result_archive_path, result_archive, split=g.SPLIT_SIZE)
    if not parts_paths:
        raise RuntimeError("Failed to split the archive into parts.")
    sly.logger.info(f"Result directory is archived into {len(parts_paths)} parts.")

    remote_path = Path(base_export_path) / g.RESULT_DIR_NAME / archive_name
    remote_path = remote_path.with_suffix("")  # Remove .tar ext
    remote_paths = [str(remote_path / Path(part).name) for part in parts_paths]

    loop = sly.utils.get_or_create_event_loop()
    total_size = sum(sly.fs.get_file_size(part) for part in parts_paths)
    progress_cb = tqdm_sly(
        total=total_size, desc=f"Uploading parts of {archive_name}", unit="B", unit_scale=True
    )
    uploading = g.api.file.upload_bulk_async(
        g.team_id,
        parts_paths,
        remote_paths,
        progress_cb=progress_cb,
    )

    loop.run_until_complete(uploading)
    common_prefix = str(Path(remote_paths[0]).parent)
    sly.logger.info(f"Uploaded to Team-Files: {common_prefix}")

    file = g.api.file.get_info_by_path(g.team_id, remote_paths[0])
    g.api.task.set_output_directory(g.task_id, file.id, common_prefix)
    w.workflow_output(g.api, g.team_id, common_prefix)
