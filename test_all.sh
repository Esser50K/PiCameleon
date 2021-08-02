docker run -dt --rm --entrypoint /bin/bash \
    --privileged -v /opt/vc:/opt/vc --env LD_LIBRARY_PATH=/opt/vc/lib \
    -e PYTHONUNBUFFERED=0 --name picameleon_test \
    picameleon:latest

docker cp tests picameleon_test:/tests
docker cp test_all.py picameleon_test:/test_all.py
docker exec picameleon_test /bin/bash -c 'pip3 install picameleon'
docker exec picameleon_test /bin/bash -c 'cd / && python3 -u test_all.py'

docker stop picameleon_test
