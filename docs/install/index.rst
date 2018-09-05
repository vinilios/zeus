Run Zeus using Docker
=====================


.. notice:

   A docker installation is required to run these steps


1. Create a customized config file::

    $ cp deploy/config.yaml.example deploy/config.yaml
    $ vim deploy/config.yaml


2. Build docker image::

    $ docker build -t grnet/zeus .


3. Create docker container::


    $ docker create -P \
        -v `pwd`/deploy/config.yaml:/etc/puppet/hieraconf/common.yaml \
        -p 8000:8000 \
        --name zeus \
        grnet/zeus


4. Start docker container::

    $ docker start zeus
    $ docker logs -f zeus


5. Wait for a few seconds for initialization scripts to complete and login as 
   administrator using credentials set in `config.yaml`::

    $ open https://127.0.0.1:8000/zeus/auth/auth/login
