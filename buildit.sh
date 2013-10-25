#!/bin/bash
if [ $1 = "mac" ]
then
    python2.4 setup.py py2app
    mkdir deffnet
    mv dist/* deffnet
    cp -R templates deffnet
    cp COPYING deffnet
    cp gpl.txt deffnet
    cp README.txt deffnet
    hdiutil create -srcfolder deffnet deffnet.dmg
    rm -rf dist
    rm -rf build
    rm -rf deffnet
elif [ $1 = "win" ]
then
    mkdir deffnet
    cp -R templates deffnet
    cp icons/deffnet.ico deffnet
    cp BeautifulSoup.py deffnet
    cp configs.py deffnet
    cp dircopy.py deffnet
    cp deffnet.py deffnet
    cp openanything.py deffnet
    cp setup.py deffnet
    cp COPYING deffnet
    cp gpl.txt deffnet
    cp README.txt deffnet
    zip -r9 deffnet-winsource.zip deffnet -x \*.DS_Store
    rm -rf deffnet
elif [ $1 = "source" ]
then
    mkdir deffnet
    cp -R templates deffnet
    cp -R icons deffnet
    cp BeautifulSoup.py deffnet
    cp configs.py deffnet
    cp dircopy.py deffnet
    cp deffnet.py deffnet
    cp openanything.py deffnet
    cp setup.py deffnet
    cp Info.plist deffnet    
    cp buildit.sh deffnet
    cp COPYING deffnet
    cp gpl.txt deffnet
    cp README.txt deffnet
    zip -r9 deffnet-source.zip deffnet -x \*.DS_Store
    rm -rf deffnet
fi
