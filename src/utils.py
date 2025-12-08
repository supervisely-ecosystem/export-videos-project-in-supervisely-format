import os
import supervisely as sly
from supervisely.io.fs import mkdir, silent_remove, remove_dir
from supervisely.io.json import load_json_file, dump_json_file

def create_metadata_files(project_dir: str):
    """Create metadata files for multi-view video projects."""
    sly.logger.info("Creating metadata files for multi-view project...")
    for root, dirs, files in os.walk(project_dir):
        if os.path.basename(root) == "video_info":
            dataset_dir = os.path.dirname(root)
            metadata_dir = os.path.join(dataset_dir, "metadata")
            mkdir(metadata_dir)
            for video_info_file in files:
                if not video_info_file.endswith(".json"):
                    continue
                    
                video_info_path = os.path.join(root, video_info_file)
                try:
                    video_info = load_json_file(video_info_path)
                    video_meta = video_info.get("meta", {})
                    video_name = video_info_file[:-5]
                    metadata_file = os.path.join(metadata_dir, f"{video_name}.meta.json")
                    dump_json_file(video_meta, metadata_file, indent=4)
                    silent_remove(video_info_path)
                except Exception as e:
                    sly.logger.warning(f"Failed to process {video_info_file}: {e}")
            sly.logger.info(f"Created metadata files in: {metadata_dir}")
    
    sly_project = sly.VideoProject(project_dir, sly.OpenMode.READ)
    for dataset in sly_project.datasets:
        dataset: sly.VideoDataset
        remove_dir(os.path.join(dataset.directory, "video_info"))