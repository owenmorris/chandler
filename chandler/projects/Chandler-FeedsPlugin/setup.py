from setuptools import setup

setup(
    name = "Chandler-FeedsPlugin",
    version = "0.1",
    description = "Simple RSS/Atom feed support for Chandler",
    author = "OSAF",
    test_suite = "feeds.tests",
    packages = ["feeds"],
    include_package_data = True,
    entry_points = {
        "chandler.parcels": ["RSS/Atom Feeds = feeds"]
    }
)

