# coding=utf-8
import sys
import unittest

from loguru import logger

if __name__ == "__main__":
    logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
    logger.add("logs/test_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")

    loader = unittest.TestLoader()
    start_dir = "database/"
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)


