#!/usr/bin/env bash
set -e

cd /srv/deploy
puppet apply -v zeus.pp

if [ "$1" = 'test' ]; then
  export ZEUS_TESTS_VERBOSE=1
  cd /srv/zeus_app && python manage.py test zeus account_administration --settings=test_settings --noinput
  exit;
fi

if [ "$1" = 'run' ]; then
    tail -f /srv/zeus-data/*log /srv/zeus-data/election_logs/*
    exit;
fi

cd /srv/zeus_app
python manage.py $*;
exit;
