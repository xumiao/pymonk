copy /Y entity.py entity.rpy
copy /Y panda.py panda.rpy
copy /Y yelp.py yelp.rpy
copy /Y tryme.py tryme.rpy
python twistd.py web --path=. --ignore-ext=py --index=Training.html