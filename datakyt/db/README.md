# PostgreSQL docker image with a database for a Datakyt project

This image contains an initial database schema.

## Build image

To build this image simply run `docker build -t datakyt/docker-postgres:<version> .`

## Run image

To run this image invoke `docker run -e POSTGRES_PASSWORD=<password> datakyt/docker-postgres`

Or you can use image id and  you can get it with `docker image ls`  

then  `docker run -e POSTGRES_PASSWORD=<password> <IMAGE ID> `

## Access the container

To access the container on your host or server you need to use `docker exec -it <name of container> bash`

Now you are ‘inside’ your container. We can access postgresql.

`root@cb9222b1f718:/# psql -U postgres`
`psql (10.3 (Debian 10.3-1.pgdg90+1))`
`Type "help" for help.`