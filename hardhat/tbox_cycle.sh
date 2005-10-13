HHDIR=`pwd`
while true; do
  cd $HHDIR
  $HHDIR/tbox.sh "$*"

  echo Sleeping for 5 minutes
  sleep 300
done
