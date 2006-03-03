# Note:
#
# release  - base version number
# build    - "" or "-checkpointYYYYMMDD"
# revision - "####"
# version  - "%s-r%s%s" % (release, revision, build)
#
# build and revision are calculated by the distribution script
# majorVersion, minorVersion and releaseVersion are calculated
# by the distribution script and inserted here
#

release = "0.7alpha2.dev"
build = ""
revision = "0000"

version = "%s-r%s%s" % (release, revision, build)

