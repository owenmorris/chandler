
def main():
    from distutils.core import setup, Extension
    setup(name='UUIDext', ext_modules=[Extension('UUIDext', sources=['uuid.c',
     'pyuuid.c'])])

if __name__ == "__main__":
    main()
