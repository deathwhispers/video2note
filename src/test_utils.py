from src.utils import logger, ensure_dir, load_config, is_mock

# 测试日志
logger.info("日志测试成功")

# 测试目录创建
ensure_dir("./downloads/test")
logger.info("目录创建测试成功")

# 测试配置加载
cfg = load_config()
logger.info(f"config keys: {list(cfg['config'].keys())}")
logger.info(f"providers keys: {list(cfg['providers'].keys())}")

# 测试 mock
logger.info(f"当前 mock 状态: {is_mock()}")
