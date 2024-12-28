# Prepare db directories

Before the first run, adjust db directories permessions:

```
sudo chown -R 999:999 ./db/data ./db/config
sudo chmod -R 755 ./db/data ./db/config
```

*UID:GID* 999:999 identify user ```mysql``` in the mariadb image.
