#!/bin/sh

export PHP_CLI_SERVER_WORKERS=4

while true
do
    php -S 127.0.0.1:8181
done
