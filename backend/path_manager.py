import os
import logging
from typing import Optional

class PathManager:
    """
    Central Path Manager for KaRar platform.
    Ensures absolute paths are avoided and all operations run relative to the workspace root.
    Handles directory validation and lazy initialization of required folders (outputs, temp, logs).
    """
    
    _instance: Optional['PathManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PathManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self):
        # Set workspace root as the directory containing this script's parent folder
        # Assuming directory structure is: workspace_root/backend/path_manager.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.workspace_root = os.path.abspath(os.path.join(current_dir, '..'))
        
        # Standardized directories under workspace root
        self.dirs = {
            'backend': os.path.join(self.workspace_root, 'backend'),
            'config': os.path.join(self.workspace_root, 'config'),
            'outputs': os.path.join(self.workspace_root, 'outputs'),
            'temp': os.path.join(self.workspace_root, 'temp'),
            'logs': os.path.join(self.workspace_root, 'logs'),
            'data': os.path.join(self.workspace_root, 'data'),
        }
        
        # Ensure directories exist upon startup
        self.ensure_directories()
        self._setup_logging()

    def ensure_directories(self):
        """Creates standard workspace directories if they do not exist."""
        for name, path in self.dirs.items():
            if name in ['outputs', 'temp', 'logs']:
                os.makedirs(path, exist_ok=True)

    def _setup_logging(self):
        """Configures standard logging routing directly to logs/pipeline.log."""
        log_file = self.get_path('logs', 'pipeline.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('KaRar')
        self.logger.info("KaRar PathManager successfully initialized. Workspace root locked.")

    def get_path(self, dir_key: str, filename: Optional[str] = None) -> str:
        """
        Retrieves the absolute path for a directory or a specific file in that directory.
        Always resolves safely with workspace boundaries.
        """
        if dir_key not in self.dirs:
            raise KeyError(f"Directory key '{dir_key}' is not registered in KaRar Workspace.")
        
        base_dir = self.dirs[dir_key]
        if filename:
            # Prevent directory traversal attacks or typos in parameters
            clean_filename = os.path.basename(filename)
            return os.path.join(base_dir, clean_filename)
        return base_dir

    def get_relative_path(self, absolute_path: str) -> str:
        """Helper to convert absolute path to a clean workspace-relative path."""
        return os.path.relpath(absolute_path, self.workspace_root)
