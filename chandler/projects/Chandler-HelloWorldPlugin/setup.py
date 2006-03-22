from setuptools import setup

setup(
    name = "Chandler-HelloWorldPlugin",
    version = "0.1",
    description = "This is just an example plugin project",
    author = "Phillip J. Eby",
    author_email = "pje@telecommunity.com",
    test_suite = "hello_world.tests",
    packages = ["hello_world"],
    include_package_data = True,
    entry_points = {
        "chandler.parcels": ["Hello World = hello_world"]
    }
)

