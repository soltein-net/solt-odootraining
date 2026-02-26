# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import ssl
import base64
import logging
import sys
from time import time
import time as time_lib
import datetime
import timeit
import xmlrpc.client
import xlrd
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
from functools import wraps
import traceback
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
import os


# Configure logging
def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # File handler
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        f'{log_dir}/odoo_executor_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Global logger
logger = setup_logger('OdooExecutor')


class ModuleState(Enum):
    """Enum for module states."""
    INSTALLED = 'installed'
    UNINSTALLED = 'uninstalled'
    TO_UPGRADE = 'to upgrade'
    TO_INSTALL = 'to install'
    TO_REMOVE = 'to remove'


@dataclass
class OdooInstance:
    """Data class for Odoo instance configuration."""
    name: str
    url: str
    database: str
    user: str = 'admin'
    password: str = ''

    def __str__(self):
        return f"{self.name} ({self.url})"


def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on exception."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                        time_lib.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        return wrapper

    return decorator


def measure_execution_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        try:
            result = func(*args, **kwargs)
            execution_time = time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds")
            raise

    return wrapper


class Timer:
    """Context manager for measuring execution time."""

    def __init__(self, name: str = "Operation", round_ndigits: int = 4):
        self.name = name
        self._round_ndigits = round_ndigits
        self._start_time = None

    def __enter__(self):
        self._start_time = timeit.default_timer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = timeit.default_timer() - self._start_time
        logger.info(f"{self.name} completed in {elapsed:.{self._round_ndigits}f} seconds")

    def elapsed(self) -> float:
        """Get elapsed time since start."""
        if self._start_time is None:
            return 0.0
        return timeit.default_timer() - self._start_time


class OdooConnection:
    """Manages connection to an Odoo instance."""

    def __init__(self, instance: OdooInstance):
        self.instance = instance
        self.common = None
        self.models = None
        self.uid = None
        self._connected = False
        self.logger = logger.getChild(f"Connection[{instance.name}]")

    @retry_on_exception(max_retries=3, delay=2.0)
    def connect(self) -> None:
        """Establish connection to Odoo instance."""
        try:
            self.logger.info(f"Connecting to {self.instance}")

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self.common = xmlrpc.client.ServerProxy(
                f'{self.instance.url}/xmlrpc/2/common',
                context=ssl_context
            )
            self.models = xmlrpc.client.ServerProxy(
                f'{self.instance.url}/xmlrpc/2/object',
                context=ssl_context
            )

            self.uid = self.common.authenticate(
                self.instance.database,
                self.instance.user,
                self.instance.password,
                {}
            )

            if not self.uid:
                raise ConnectionError("Authentication failed")

            self._connected = True
            self.logger.info(f"Successfully connected to {self.instance}")

        except Exception as e:
            self.logger.error(f"Failed to connect to {self.instance}: {str(e)}")
            raise

    def execute_kw(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
        """Execute method on Odoo model."""
        if not self._connected:
            self.connect()

        args = args or []
        kwargs = kwargs or {}

        try:
            return self.models.execute_kw(
                self.instance.database,
                self.uid,
                self.instance.password,
                model,
                method,
                args,
                kwargs
            )
        except xmlrpc.client.Fault as e:
            self.logger.error(f"XML-RPC fault on {model}.{method}: {e.faultString}")
            raise
        except Exception as e:
            self.logger.error(f"Error executing {model}.{method}: {str(e)}")
            raise

    def get_server_version(self) -> str:
        """Get Odoo server version."""
        try:
            version_info = self.common.version()
            return version_info.get('server_version', 'Unknown')
        except Exception as e:
            self.logger.error(f"Failed to get server version: {str(e)}")
            return 'Unknown'


class Executor:
    """Executes operations on Odoo instances."""

    def __init__(self, instances: List[OdooInstance]):
        self.instances = instances
        self.connections: Dict[str, OdooConnection] = {}
        self.logger = logger.getChild("Executor")

    def _get_connection(self, instance: OdooInstance) -> OdooConnection:
        """Get or create connection for instance."""
        if instance.name not in self.connections:
            conn = OdooConnection(instance)
            conn.connect()
            self.connections[instance.name] = conn
        return self.connections[instance.name]

    @measure_execution_time
    def test_login(self) -> Dict[str, bool]:
        """Test login to all instances."""
        results = {}

        for instance in self.instances:
            self.logger.info(f"Testing login to {instance}")
            try:
                conn = self._get_connection(instance)
                uuid = conn.execute_kw(
                    'ir.config_parameter',
                    'get_param',
                    ['database.uuid']
                )
                version = conn.get_server_version()
                self.logger.info(f"Successfully connected to {instance} (Version: {version}, UUID: {uuid})")
                results[instance.name] = True
            except Exception as e:
                self.logger.error(f"Failed to connect to {instance}: {str(e)}")
                results[instance.name] = False

        return results

    @measure_execution_time
    def update_module_list(self) -> Dict[str, bool]:
        """Update module list on all instances."""
        results = {}

        for instance in self.instances:
            self.logger.info(f"Updating module list on {instance}")
            try:
                conn = self._get_connection(instance)
                conn.execute_kw('ir.module.module', 'update_list', [])
                self.logger.info(f"Successfully updated module list on {instance}")
                results[instance.name] = True
            except Exception as e:
                self.logger.error(f"Failed to update module list on {instance}: {str(e)}")
                results[instance.name] = False

        return results

    def _get_module_info(self, conn: OdooConnection, module_name: str) -> Optional[Dict]:
        """Get module information."""
        try:
            modules = conn.execute_kw(
                'ir.module.module',
                'search_read',
                [[('name', '=', module_name)], ['id', 'name', 'state']]
            )
            return modules[0] if modules else None
        except Exception as e:
            self.logger.error(f"Failed to get module info for {module_name}: {str(e)}")
            return None

    def _get_downstream_dependencies(self, conn: OdooConnection, module_id: int) -> List[Dict]:
        """Get downstream dependencies of a module."""
        try:
            downstream_ids = conn.execute_kw(
                'ir.module.module',
                'downstream_dependencies',
                [[module_id]]
            )
            if downstream_ids:
                return conn.execute_kw(
                    'ir.module.module',
                    'search_read',
                    [[('id', 'in', downstream_ids)], ['id', 'name']]
                )
            return []
        except Exception as e:
            self.logger.error(f"Failed to get downstream dependencies: {str(e)}")
            return []

    @measure_execution_time
    def module_update(self, modules: List[str], wait_between: int = 5) -> Dict[str, List[str]]:
        """Update modules on all instances."""
        results = {}

        for instance in self.instances:
            instance_logger = self.logger.getChild(f"Update[{instance.name}]")
            instance_logger.info(f"Starting module update on {instance}")

            updated_modules = []
            failed_modules = []

            try:
                conn = self._get_connection(instance)

                for idx, module_name in enumerate(modules):
                    with Timer(f"Update {module_name} on {instance.name}"):
                        module_info = self._get_module_info(conn, module_name)

                        if not module_info:
                            instance_logger.warning(f"Module {module_name} not found")
                            failed_modules.append(module_name)
                            continue

                        state = ModuleState(module_info['state'])
                        if state not in [ModuleState.INSTALLED, ModuleState.TO_UPGRADE]:
                            instance_logger.warning(
                                f"Module {module_name} is in state {state.value}, skipping"
                            )
                            continue

                        try:
                            # Get downstream dependencies
                            downstream = self._get_downstream_dependencies(conn, module_info['id'])

                            # Update module
                            conn.execute_kw(
                                'ir.module.module',
                                'button_immediate_upgrade',
                                [module_info['id']]
                            )

                            updated_modules.append(module_name)
                            instance_logger.info(f"Successfully updated module {module_name}")

                            if downstream:
                                downstream_names = [m['name'] for m in downstream]
                                instance_logger.info(
                                    f"Also updated downstream dependencies: {', '.join(downstream_names)}"
                                )
                                updated_modules.extend(downstream_names)

                            # Wait between updates if not the last module
                            if wait_between and idx < len(modules) - 1:
                                instance_logger.debug(f"Waiting {wait_between} seconds before next update")
                                time_lib.sleep(wait_between)

                        except Exception as e:
                            instance_logger.error(f"Failed to update module {module_name}: {str(e)}")
                            failed_modules.append(module_name)

                results[instance.name] = {
                    'updated': list(set(updated_modules)),
                    'failed': failed_modules
                }

            except Exception as e:
                instance_logger.error(f"Critical error during module update: {str(e)}")
                results[instance.name] = {
                    'updated': [],
                    'failed': modules
                }

        return results



    @measure_execution_time
    def module_status(self, modules: List[str]) -> Dict[str, Dict[str, str]]:
        """Check module status on all instances."""
        results = {}

        for instance in self.instances:
            self.logger.info(f"Checking module status on {instance}")
            instance_status = {}

            try:
                conn = self._get_connection(instance)

                module_infos = conn.execute_kw(
                    'ir.module.module',
                    'search_read',
                    [[('name', 'in', modules)], ['name', 'state']]
                )

                for module_info in module_infos:
                    instance_status[module_info['name']] = module_info['state']

                # Check for missing modules
                found_modules = set(m['name'] for m in module_infos)
                missing_modules = set(modules) - found_modules
                for module in missing_modules:
                    instance_status[module] = 'not_found'

                results[instance.name] = instance_status

            except Exception as e:
                self.logger.error(f"Failed to check module status on {instance}: {str(e)}")
                results[instance.name] = {module: 'error' for module in modules}

        return results



# Example configuration
LOCALHOST = OdooInstance(
    name='LOCALHOST',
    url='http://localhost:8069',
    database='OdootrainingNleon',
    user='admin',
    password='admin'
)


def main():
    """Main execution function."""
    # Set up logging
    logger.info("Starting Odoo Executor")

    # Define instances
    instances = [
        LOCALHOST,
        # Add more instances here
        # Add more instances as needed
    ]

    if not instances:
        logger.warning("No instances configured. Please add instances to the list.")
        return

    # Create executor manager
    manager = Executor(instances)

    # Test login
    logger.info("=" * 80)
    logger.info("Testing connections...")
    manager.test_login()
    #manager.update_module_list()
    #results = manager.module_status(['purchase'])

    #for instance_name, result in results.items():
     #   logger.info(f"{result}")

    # Example: Update modules
    modules_to_update = ['solt_library']
    #logger.info("=" * 80)
    #logger.info(f"Updating modules: {modules_to_update}")
    manager.module_update(modules_to_update, wait_between=5)


    logger.info("=" * 80)
    logger.info("Execution completed")


if __name__ == '__main__':
    main()
