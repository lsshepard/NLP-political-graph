#!/usr/bin/env python3
"""Main entry point for running the pipeline"""

from pipeline import Pipeline


def main():
    """Main entry point"""
    pipeline = Pipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
