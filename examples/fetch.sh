if [ "$#" -lt 1 ]; then
	version="0.2"
else
	version="$1"
fi

curl --user-agent "Test App/$version" localhost:8000/testapp.xml

if [ "$#" -lt 1 ]; then
	echo 
	echo "You can specify an optional version number:"
	echo "    $0 [version]"
fi

