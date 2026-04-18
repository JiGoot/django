# Start Sever
```
source venv/bin/activate
```

# RunServer 
```
python3 manage.py runserver 0.0.0.0:8080
```
```
gunicorn --bind 0.0.0.0:8080 core.wsgi --reload --workers 3
```
delete_image_utility
# Migration dry run
```
python3 manage.py makemigrations  --dry-run
```

# Migration commands
```
python3 manage.py makemigrations  && python3 manage.py migrate
```


# Clean Migrations files
```
find . -type f -name 00\* -delete && find . -name __pycache__ -exec rm -rf {} +
```

```
python3 manage.py makemigrations  && python3 manage.py migrate --fake-initial
```

# Dump necessary data 
```
python3 manage.py dumpdata -e admin -e auth -e contenttypes -e silk > all.json
```

# Dump a store app
```
python3 manage.py dumpdata store > store.json  
```  

# Dump specific app models 
```
python3 manage.py dumpdata store.Section store.Category > store.json
```

# Connect to remote machine 
```
ssh -i ~/keys/jigoot_server_key.pem root@192.46.237.119
```

# Ship to Linode instance 
```
rsync -e "ssh -i ~/keys/jigoot_server_key.pem" -avz --delete --exclude-from='exclude.txt' ./ root@192.46.237.119:~/src/
```



ExecStart=/root/venv/bin/python /root/src/core/tasks/consumer.py --backend rabbitmq


psycopg2.errors.UndefinedColumn: column "name" of relation "django_content_type" does not exist


python3 manage.py migrate contenttypes zero
python3 manage.py migrate contenttypes

psycopg2.errors.NotNullViolation: column "id" of relation "django_q_task" contains null values

❗ If your DB is already corrupted badly
1. Drop the django_content_type table manually (if no valuable data is in it):

2. Then run the migrations again:
`python3 manage.py migrate contenttypes`


```
sudo nano /etc/nginx/sites-available/jigoot
```

```
sudo nginx -t && sudo systemctl reload nginx.service
```

```
sudo systemctl status nginx
```


### Gunicorn 

```
sudo systemctl daemon-reload && sudo systemctl restart gunicorn.service
```

### Logging
journalctl -u qconsumer.service -f
tail -f /path/to/logfile.log


server {
    listen 443 ssl; # managed by Certbot
    server_name jigoot.com www.jigoot.com;

    ssl_certificate /etc/letsencrypt/live/jigoot.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/jigoot.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}