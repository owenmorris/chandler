# Note:
#   release    - base version number
#   build      - "" or ".dev"
#   checkpoint - "" or "-YYYYMMDD"
#   revision   - "####"
#
#   version    - "%s%s-r%s%s" % (release, build, revision, checkpoint)
#

release = "0.7alpha5"
build = ".dev"
checkpoint = ""
revision = ""

version = "%s%s-r%s%s" % (release, build, revision, checkpoint)

