#!/bin/bash -x
pushd $( dirname "${BASH_SOURCE[0]}" )

VERSION="conductor-${RELEASE_VERSION}-0.x86_64"

mkdir -p build/{BUILDROOT,RPMS,SPECS}
mkdir -p build/BUILDROOT/${VERSION}/opt/conductor
mkdir -p build/BUILDROOT/${VERSION}/etc/profile.d

cp -r ../../bin \
      ../../conductor \
      ../../maya_shelf \
      ../../nuke_menu \
      ../../clarisse_shelf \
       build/BUILDROOT/${VERSION}/opt/conductor

cp conductor.spec build/SPECS
mv build/BUILDROOT/${VERSION}/opt/conductor/bin/conductor \
    build/BUILDROOT/${VERSION}/opt/conductor/bin/conductor_client
cp conductor build/BUILDROOT/${VERSION}/opt/conductor/bin/
cp conductor.sh build/BUILDROOT/${VERSION}/etc/profile.d

for dist_ver in 6 7; do
    cp -r build build-${dist_ver}
    docker run -i \
      -v ${WORKSPACE}/installers/Python-2.7.11:/root/src \
      -v $(pwd)/build-${dist_ver}/BUILDROOT/${VERSION}/opt/conductor/python:/root/python \
      -v $(pwd)/build-python.sh:/root/build-python.sh \
      centos:${dist_ver} \
      /root/build-python.sh
    
    pushd build-${dist_ver}
    rpmbuild --define "_topdir ${PWD}" \
         --define "_version ${RELEASE_VERSION}" \
         -bb SPECS/conductor.spec
    popd
done
